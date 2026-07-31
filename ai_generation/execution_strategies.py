"""
Execution Strategies — CPU Offload, Tensor Parallelism, Pipeline Parallelism.

Based on ACOS Research: Execution Strategy Library
Implements execution strategies for model inference with fallback chains.
"""
import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class StrategyType(str, Enum):
    SINGLE_GPU = "single_gpu"
    CPU_OFFLOAD = "cpu_offload"
    DISK_OFFLOAD = "disk_offload"
    TENSOR_PARALLEL = "tensor_parallel"
    PIPELINE_PARALLEL = "pipeline_parallel"
    EXPERT_PARALLEL = "expert_parallel"
    DATA_PARALLEL = "data_parallel"
    SEQUENCE_PARALLEL = "sequence_parallel"


class StrategyStatus(str, Enum):
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class HardwareProfile:
    gpu_count: int = 0
    gpu_vram_gb: List[float] = field(default_factory=list)
    cpu_ram_gb: float = 0.0
    cpu_cores: int = 0
    pcie_bandwidth_gbps: float = 32.0  # PCIe 4.0 x16
    nvlink: bool = False
    infiniband: bool = False

    @classmethod
    def detect(cls) -> "HardwareProfile":
        profile = cls()
        try:
            import torch
            if torch.cuda.is_available():
                profile.gpu_count = torch.cuda.device_count()
                for i in range(profile.gpu_count):
                    props = torch.cuda.get_device_properties(i)
                    profile.gpu_vram_gb.append(props.total_memory / (1024**3))
        except Exception:
            pass
        try:
            import psutil
            profile.cpu_ram_gb = psutil.virtual_memory().total / (1024**3)
            profile.cpu_cores = psutil.cpu_count(logical=False) or os.cpu_count() or 1
        except Exception:
            pass
        # stdlib fallback (psutil is optional): never leave cpu_cores unknown
        if not profile.cpu_cores:
            profile.cpu_cores = os.cpu_count() or 1
        return profile


@dataclass
class ModelRequirements:
    model_size_gb: float = 0.0
    min_vram_gb: float = 0.0
    recommended_vram_gb: float = 0.0
    supports_cpu_offload: bool = True
    supports_tensor_parallel: bool = False
    supports_pipeline_parallel: bool = False
    supports_expert_parallel: bool = False
    supports_data_parallel: bool = False
    supports_sequence_parallel: bool = False
    supports_quantization: bool = True
    quantization_options: List[str] = field(default_factory=lambda: ["int8", "int4"])


@dataclass
class ExecutionPlan:
    strategy: StrategyType
    primary_device: str = "cuda:0"
    offload_layers: List[int] = field(default_factory=list)
    offload_to_cpu: bool = False
    offload_to_disk: bool = False
    parallel_config: Dict[str, Any] = field(default_factory=dict)
    estimated_latency_ms: float = 0.0
    estimated_vram_usage_gb: float = 0.0
    estimated_cpu_ram_usage_gb: float = 0.0
    confidence: float = 1.0
    fallback_strategy: Optional[StrategyType] = None


class ExecutionStrategy:
    """Base class for execution strategies."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.hardware = HardwareProfile.detect()
        self._status = StrategyStatus.UNKNOWN

    @property
    def strategy_type(self) -> StrategyType:
        raise NotImplementedError

    def can_execute(self, requirements: ModelRequirements) -> bool:
        raise NotImplementedError

    def create_plan(self, requirements: ModelRequirements) -> Optional[ExecutionPlan]:
        raise NotImplementedError

    def get_status(self) -> StrategyStatus:
        return self._status

    def set_status(self, status: StrategyStatus):
        self._status = status


class CPUOffloadStrategy(ExecutionStrategy):
    """
    CPU Offload Strategy (EXE-04).

    Offloads model layers to CPU when GPU VRAM is insufficient.
    Uses DeepSpeed ZeRO-Infinity or native runtime support.
    """

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.CPU_OFFLOAD

    def can_execute(self, requirements: ModelRequirements) -> bool:
        if not requirements.supports_cpu_offload:
            return False
        total_vram = sum(self.hardware.gpu_vram_gb)
        cpu_ram = self.hardware.cpu_ram_gb
        return cpu_ram >= requirements.model_size_gb

    def create_plan(self, requirements: ModelRequirements) -> Optional[ExecutionPlan]:
        if not self.can_execute(requirements):
            return None

        total_vram = sum(self.hardware.gpu_vram_gb) if self.hardware.gpu_vram_gb else 0
        vram_needed = requirements.min_vram_gb

        if total_vram >= vram_needed:
            return ExecutionPlan(
                strategy=StrategyType.SINGLE_GPU,
                primary_device="cuda:0",
                estimated_vram_usage_gb=vram_needed,
                confidence=0.95,
                fallback_strategy=StrategyType.CPU_OFFLOAD,
            )

        layers_to_offload = int((vram_needed - total_vram) / requirements.model_size_gb * 100)
        return ExecutionPlan(
            strategy=StrategyType.CPU_OFFLOAD,
            primary_device="cuda:0",
            offload_to_cpu=True,
            estimated_vram_usage_gb=total_vram,
            estimated_cpu_ram_usage_gb=requirements.model_size_gb,
            confidence=0.7,
            fallback_strategy=StrategyType.DISK_OFFLOAD,
        )


class DiskOffloadStrategy(ExecutionStrategy):
    """Disk Offload Strategy - uses disk for model weights (EXE-10)."""

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.DISK_OFFLOAD

    def can_execute(self, requirements: ModelRequirements) -> bool:
        # Always available as last resort if enough disk space
        import shutil
        free_space = shutil.disk_usage("/").free / (1024**3)
        return free_space >= requirements.model_size_gb

    def create_plan(self, requirements: ModelRequirements) -> Optional[ExecutionPlan]:
        if not self.can_execute(requirements):
            return None
        import shutil
        free_space = shutil.disk_usage("/").free / (1024**3)

        return ExecutionPlan(
            strategy=StrategyType.DISK_OFFLOAD,
            primary_device="cpu",
            offload_to_disk=True,
            parallel_config={"offload_path": "/tmp/model_offload"},
            estimated_vram_usage_gb=0,
            estimated_cpu_ram_usage_gb=requirements.model_size_gb,
            confidence=0.5,
            fallback_strategy=None,
        )


class SingleGPUStrategy(ExecutionStrategy):
    """Single GPU execution (EXE-02)."""

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.SINGLE_GPU

    def can_execute(self, requirements: ModelRequirements) -> bool:
        total_vram = sum(self.hardware.gpu_vram_gb) if self.hardware.gpu_vram_gb else 0
        return total_vram >= requirements.min_vram_gb

    def create_plan(self, requirements: ModelRequirements) -> Optional[ExecutionPlan]:
        if not self.can_execute(requirements):
            return None

        total_vram = sum(self.hardware.gpu_vram_gb) if self.hardware.gpu_vram_gb else 0
        return ExecutionPlan(
            strategy=StrategyType.SINGLE_GPU,
            primary_device="cuda:0",
            estimated_vram_usage_gb=requirements.min_vram_gb,
            estimated_latency_ms=100,
            confidence=0.95,
            fallback_strategy=StrategyType.CPU_OFFLOAD,
        )


class TensorParallelStrategy(ExecutionStrategy):
    """Tensor Parallelism - splits model across GPUs (EXE-05)."""

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.TENSOR_PARALLEL

    def can_execute(self, requirements: ModelRequirements) -> bool:
        if not requirements.supports_tensor_parallel:
            return False
        if self.hardware.gpu_count < 2:
            return False
        return True

    def create_plan(self, requirements: ModelRequirements) -> Optional[ExecutionPlan]:
        if not self.can_execute(requirements):
            return None

        gpus = self.hardware.gpu_count
        vram_per_gpu = sum(self.hardware.gpu_vram_gb) / gpus if self.hardware.gpu_vram_gb else 0

        return ExecutionPlan(
            strategy=StrategyType.TENSOR_PARALLEL,
            primary_device=f"cuda:0",
            parallel_config={
                "tensor_parallel_size": gpus,
                "devices": [f"cuda:{i}" for i in range(gpus)],
            },
            estimated_vram_usage_gb=vram_per_gpu,
            estimated_latency_ms=300,
            confidence=0.7,
            fallback_strategy=StrategyType.CPU_OFFLOAD,
        )


class PipelineParallelStrategy(ExecutionStrategy):
    """Pipeline Parallelism - splits model across GPUs by layers (EXE-06)."""

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.PIPELINE_PARALLEL

    def can_execute(self, requirements: ModelRequirements) -> bool:
        if not requirements.supports_pipeline_parallel:
            return False
        if self.hardware.gpu_count < 2:
            return False
        return True

    def create_plan(self, requirements: ModelRequirements) -> Optional[ExecutionPlan]:
        if not self.can_execute(requirements):
            return None

        gpus = self.hardware.gpu_count
        stages = min(gpus, 4)

        return ExecutionPlan(
            strategy=StrategyType.PIPELINE_PARALLEL,
            primary_device=f"cuda:0",
            parallel_config={
                "pipeline_parallel_size": gpus,
                "stages": stages,
                "devices": [f"cuda:{i}" for i in range(gpus)],
            },
            estimated_vram_usage_gb=requirements.model_size_gb / gpus if gpus > 0 else 0,
            estimated_latency_ms=400,
            confidence=0.65,
            fallback_strategy=StrategyType.TENSOR_PARALLEL,
        )


class ExpertParallelStrategy(ExecutionStrategy):
    """Expert Parallelism (MoE) - distributes experts across GPUs (EXE-07)."""

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.EXPERT_PARALLEL

    def can_execute(self, requirements: ModelRequirements) -> bool:
        if not getattr(requirements, 'supports_expert_parallel', False):
            return False
        if self.hardware.gpu_count < 2:
            return False
        return True

    def create_plan(self, requirements: ModelRequirements) -> Optional[ExecutionPlan]:
        if not self.can_execute(requirements):
            return None

        gpus = self.hardware.gpu_count

        return ExecutionPlan(
            strategy=StrategyType.EXPERT_PARALLEL,
            primary_device=f"cuda:0",
            parallel_config={
                "expert_parallel_size": gpus,
                "devices": [f"cuda:{i}" for i in range(gpus)],
            },
            estimated_vram_usage_gb=requirements.model_size_gb / gpus if gpus > 0 else 0,
            estimated_latency_ms=250,
            confidence=0.6,
            fallback_strategy=StrategyType.TENSOR_PARALLEL,
        )


class DataParallelStrategy(ExecutionStrategy):
    """Data Parallelism - replicates model across GPUs, splits batch (EXE-08)."""

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.DATA_PARALLEL

    def can_execute(self, requirements: ModelRequirements) -> bool:
        if not getattr(requirements, 'supports_data_parallel', False):
            return False
        if self.hardware.gpu_count < 2:
            return False
        return True

    def create_plan(self, requirements: ModelRequirements) -> Optional[ExecutionPlan]:
        if not self.can_execute(requirements):
            return None

        gpus = self.hardware.gpu_count

        return ExecutionPlan(
            strategy=StrategyType.DATA_PARALLEL,
            primary_device=f"cuda:0",
            parallel_config={
                "data_parallel_size": gpus,
                "devices": [f"cuda:{i}" for i in range(gpus)],
            },
            estimated_vram_usage_gb=requirements.model_size_gb,
            estimated_latency_ms=300,
            confidence=0.55,
            fallback_strategy=StrategyType.TENSOR_PARALLEL,
        )


class SequenceParallelStrategy(ExecutionStrategy):
    """Sequence/Context Parallelism - splits sequence across GPUs (EXE-09)."""

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.SEQUENCE_PARALLEL

    def can_execute(self, requirements: ModelRequirements) -> bool:
        if not getattr(requirements, 'supports_sequence_parallel', False):
            return False
        if self.hardware.gpu_count < 2:
            return False
        return True

    def create_plan(self, requirements: ModelRequirements) -> Optional[ExecutionPlan]:
        if not self.can_execute(requirements):
            return None

        gpus = self.hardware.gpu_count

        return ExecutionPlan(
            strategy=StrategyType.SEQUENCE_PARALLEL,
            primary_device=f"cuda:0",
            parallel_config={
                "sequence_parallel_size": gpus,
                "devices": [f"cuda:{i}" for i in range(gpus)],
            },
            estimated_vram_usage_gb=requirements.model_size_gb / gpus if gpus > 0 else 0,
            estimated_latency_ms=350,
            confidence=0.5,
            fallback_strategy=StrategyType.PIPELINE_PARALLEL,
        )


class StrategySelector:
    """
    Selects the optimal execution strategy based on hardware and model requirements.
    """

    STRATEGY_ORDER = [
        StrategyType.SINGLE_GPU,
        StrategyType.TENSOR_PARALLEL,
        StrategyType.PIPELINE_PARALLEL,
        StrategyType.CPU_OFFLOAD,
        StrategyType.DISK_OFFLOAD,
        StrategyType.EXPERT_PARALLEL,
        StrategyType.DATA_PARALLEL,
        StrategyType.SEQUENCE_PARALLEL,
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.strategies = {
            StrategyType.SINGLE_GPU: SingleGPUStrategy(config),
            StrategyType.CPU_OFFLOAD: CPUOffloadStrategy(config),
            StrategyType.DISK_OFFLOAD: DiskOffloadStrategy(config),
            StrategyType.TENSOR_PARALLEL: TensorParallelStrategy(config),
            StrategyType.PIPELINE_PARALLEL: PipelineParallelStrategy(config),
            StrategyType.EXPERT_PARALLEL: ExpertParallelStrategy(config),
            StrategyType.DATA_PARALLEL: DataParallelStrategy(config),
            StrategyType.SEQUENCE_PARALLEL: SequenceParallelStrategy(config),
        }

    def select_strategy(self, requirements: ModelRequirements) -> Optional[ExecutionPlan]:
        """Select the best available strategy for the given requirements."""
        candidates = []

        for stype in self.STRATEGY_ORDER:
            strategy = self.strategies.get(stype)
            if strategy is None:
                continue
            if strategy.can_execute(requirements):
                plan = strategy.create_plan(requirements)
                if plan:
                    candidates.append(plan)

        if not candidates:
            return None

        # Sort by confidence (highest first), then by estimated latency
        candidates.sort(key=lambda p: (-p.confidence, p.estimated_latency_ms))
        best = candidates[0]

        # Add fallback chain
        best.fallback_strategy = candidates[1].strategy if len(candidates) > 1 else None

        return best

    def get_all_plans(self, requirements: ModelRequirements) -> List[ExecutionPlan]:
        """Get all viable execution plans."""
        plans = []
        for stype in self.STRATEGY_ORDER:
            strategy = self.strategies.get(stype)
            if strategy and strategy.can_execute(requirements):
                plan = strategy.create_plan(requirements)
                if plan:
                    plans.append(plan)
        return plans


# Convenience functions
def create_cpu_offload_plan(model_size_gb: float, gpu_vram_gb: float,
                             cpu_ram_gb: float) -> Optional[ExecutionPlan]:
    """Create a CPU offload plan for given hardware."""
    hw = HardwareProfile()
    hw.gpu_vram_gb = [gpu_vram_gb] if gpu_vram_gb > 0 else []
    hw.cpu_ram_gb = cpu_ram_gb

    req = ModelRequirements(
        model_size_gb=model_size_gb,
        min_vram_gb=model_size_gb,
        recommended_vram_gb=model_size_gb * 1.2,
    )

    strategy = CPUOffloadStrategy()
    strategy.hardware = hw
    return strategy.create_plan(req)


def create_execution_plan(requirements: ModelRequirements,
                           config: Optional[Dict[str, Any]] = None) -> Optional[ExecutionPlan]:
    """Create the optimal execution plan for given requirements."""
    selector = StrategySelector(config)
    return selector.select_strategy(requirements)
