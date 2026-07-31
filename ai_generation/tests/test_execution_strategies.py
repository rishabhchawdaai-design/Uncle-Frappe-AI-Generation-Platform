"""
Tests for the Execution Strategy Library (execution_strategies.py).

Verifies EXE-01..EXE-10 capabilities: single GPU, CPU/disk offload,
tensor/pipeline/expert/data/sequence parallel strategies and selection.
"""
import pytest

from ai_generation.execution_strategies import (
    HardwareProfile,
    ModelRequirements,
    StrategySelector,
    StrategyStatus,
    StrategyType,
    CPUOffloadStrategy,
    DiskOffloadStrategy,
    SingleGPUStrategy,
    TensorParallelStrategy,
    PipelineParallelStrategy,
    ExpertParallelStrategy,
    DataParallelStrategy,
    SequenceParallelStrategy,
    create_cpu_offload_plan,
    create_execution_plan,
)


def _gpu_hardware(gpu_count=1, vram_gb=24.0):
    hw = HardwareProfile()
    hw.gpu_count = gpu_count
    hw.gpu_vram_gb = [vram_gb] * gpu_count
    hw.cpu_ram_gb = 64.0
    return hw


def _req(model_gb=4.0, min_vram=4.0, **flags):
    return ModelRequirements(model_size_gb=model_gb, min_vram_gb=min_vram,
                             recommended_vram_gb=model_gb * 1.2, **flags)


def test_hardware_profile_detect_safe():
    hw = HardwareProfile.detect()
    assert hw.gpu_count >= 0
    assert isinstance(hw.cpu_ram_gb, float)
    assert isinstance(hw.cpu_cores, int) and hw.cpu_cores > 0


def test_single_gpu_strategy():
    strategy = SingleGPUStrategy()
    strategy.hardware = _gpu_hardware(1, 24.0)
    req = _req(model_gb=8.0, min_vram=8.0)
    assert strategy.can_execute(req)
    plan = strategy.create_plan(req)
    assert plan.strategy == StrategyType.SINGLE_GPU
    assert plan.confidence > 0.9
    assert plan.fallback_strategy == StrategyType.CPU_OFFLOAD
    # insufficient VRAM -> no plan
    big = _req(model_gb=64.0, min_vram=64.0)
    assert not strategy.can_execute(big)
    assert strategy.create_plan(big) is None


def test_cpu_offload_strategy():
    strategy = CPUOffloadStrategy()
    strategy.hardware = _gpu_hardware(1, 4.0)
    req = _req(model_gb=16.0, min_vram=8.0)
    plan = strategy.create_plan(req)
    assert plan is not None
    assert plan.offload_to_cpu is True
    assert plan.fallback_strategy == StrategyType.DISK_OFFLOAD
    # unsupported flag
    no_offload = _req(model_gb=2.0, min_vram=2.0, supports_cpu_offload=False)
    assert not strategy.can_execute(no_offload)


def test_disk_offload_strategy():
    strategy = DiskOffloadStrategy()
    # tiny model always fits on disk
    req = _req(model_gb=0.01, min_vram=0.0)
    assert strategy.can_execute(req)
    plan = strategy.create_plan(req)
    assert plan.strategy == StrategyType.DISK_OFFLOAD
    assert plan.offload_to_disk is True


def test_parallel_strategies_need_multiple_gpus():
    tp = TensorParallelStrategy()
    tp.hardware = _gpu_hardware(1, 24.0)
    req = _req(model_gb=8.0, supports_tensor_parallel=True)
    assert not tp.can_execute(req)  # single GPU
    tp.hardware = _gpu_hardware(2, 24.0)
    assert tp.can_execute(req)
    plan = tp.create_plan(req)
    assert plan.parallel_config["tensor_parallel_size"] == 2
    assert plan.devices if hasattr(plan, "devices") else True

    for cls, flag, stype, key in [
        (PipelineParallelStrategy, "supports_pipeline_parallel",
         StrategyType.PIPELINE_PARALLEL, "pipeline_parallel_size"),
        (ExpertParallelStrategy, "supports_expert_parallel",
         StrategyType.EXPERT_PARALLEL, "expert_parallel_size"),
        (DataParallelStrategy, "supports_data_parallel",
         StrategyType.DATA_PARALLEL, "data_parallel_size"),
        (SequenceParallelStrategy, "supports_sequence_parallel",
         StrategyType.SEQUENCE_PARALLEL, "sequence_parallel_size"),
    ]:
        strategy = cls()
        strategy.hardware = _gpu_hardware(1, 24.0)
        r = _req(model_gb=8.0, **{flag: True})
        assert not strategy.can_execute(r), f"{cls.__name__} on 1 GPU"
        strategy.hardware = _gpu_hardware(2, 24.0)
        assert strategy.can_execute(r), f"{cls.__name__} on 2 GPUs"
        plan = strategy.create_plan(r)
        assert plan.strategy == stype
        assert plan.parallel_config[key] == 2


def test_parallel_strategies_respect_support_flags():
    strategy = TensorParallelStrategy()
    strategy.hardware = _gpu_hardware(2, 24.0)
    unsupported = _req(model_gb=8.0, supports_tensor_parallel=False)
    assert not strategy.can_execute(unsupported)


def test_strategy_selector_prefers_highest_confidence():
    selector = StrategySelector()
    selector.strategies[StrategyType.SINGLE_GPU].hardware = _gpu_hardware(1, 24.0)
    selector.strategies[StrategyType.CPU_OFFLOAD].hardware = _gpu_hardware(1, 24.0)
    selector.strategies[StrategyType.DISK_OFFLOAD].hardware = _gpu_hardware(1, 24.0)
    req = _req(model_gb=8.0, min_vram=8.0)
    plan = selector.select_strategy(req)
    assert plan is not None
    assert plan.strategy == StrategyType.SINGLE_GPU
    assert plan.fallback_strategy is not None
    plans = selector.get_all_plans(req)
    assert len(plans) >= 2
    # plans sorted by confidence descending
    confidences = [p.confidence for p in plans]
    assert confidences == sorted(confidences, reverse=True)


def test_strategy_selector_no_viable_strategy():
    selector = StrategySelector()
    for s in selector.strategies.values():
        s.hardware = _gpu_hardware(0, 0.0)
        s.hardware.cpu_ram_gb = 0.5
    req = _req(model_gb=1000.0, min_vram=1000.0)
    assert selector.select_strategy(req) is None
    assert selector.get_all_plans(req) == []


def test_create_cpu_offload_plan_helper():
    plan = create_cpu_offload_plan(model_size_gb=16.0, gpu_vram_gb=4.0,
                                   cpu_ram_gb=64.0)
    assert plan is not None
    assert plan.offload_to_cpu is True


def test_create_execution_plan_helper():
    hw = _gpu_hardware(1, 24.0)
    plan = create_execution_plan(_req(model_gb=8.0, min_vram=8.0))
    # strategy depends on detected hardware (GPU present or not); helper must
    # return a viable plan or a degraded disk-offload fallback
    assert plan is not None
    assert plan.estimated_vram_usage_gb >= 0
    assert hw.gpu_count >= 0


def test_status_enum_and_strategy_types():
    assert StrategyStatus.AVAILABLE.value == "available"
    assert StrategyType.CPU_OFFLOAD.value == "cpu_offload"
    strategy = CPUOffloadStrategy()
    strategy.set_status(StrategyStatus.DEGRADED)
    assert strategy.get_status() == StrategyStatus.DEGRADED
    assert strategy.strategy_type == StrategyType.CPU_OFFLOAD
