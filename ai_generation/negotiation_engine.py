"""
Negotiation Engine — ACOS decision-making core.

Implements multi-criteria scoring for optimal execution path selection.
Based on ACOS Research: NEGOTIATION_ENGINE_SPECIFICATION.md

Every routing decision is evidence-based, documented, and reversible.
Never assume one model, provider, or backend is best.
"""
import logging
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Enums ──────────────────────────────────────────────────────

class TaskType(str, Enum):
    TEXT_GENERATION = "text_generation"
    TEXT_EMBEDDING = "text_embedding"
    IMAGE_GENERATION = "image_generation"
    IMAGE_EDITING = "image_editing"
    IMAGE_UPSCALING = "image_upscaling"
    VIDEO_GENERATION = "video_generation"
    VIDEO_EDITING = "video_editing"
    VIDEO_UPSCALING = "video_upscaling"
    AUDIO_GENERATION = "audio_generation"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    AUDIO_TTS = "audio_tts"
    DOCUMENT_PROCESSING = "document_processing"
    OCR = "ocr"
    FACE_RESTORE = "face_restore"
    BACKGROUND_REMOVAL = "background_removal"
    STYLE_TRANSFER = "style_transfer"
    INPAINTING = "inpainting"
    OUTPAINTING = "outpainting"
    FACE_IDENTITY = "face_identity"
    AVATAR_GENERATION = "avatar_generation"
    THREE_D_GENERATION = "3d_generation"
    GAUSSIAN_SPLATTING = "gaussian_splatting"
    WORLD_MODEL = "world_model"


class Modality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"
    DOCUMENT = "document"
    THREE_D = "3d"


class QualityPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


class PrivacyLevel(str, Enum):
    LOCAL_ONLY = "local_only"
    ENCRYPTED = "encrypted"
    CLOUD_OK = "cloud_ok"


class ExecutionLayer(int, Enum):
    PUBLIC_API = 1
    HOSTED_OPENSOURCE = 2
    USER_CONFIGURED = 3
    LOCAL_GPU = 4
    LOCAL_CPU = 5
    BROWSER = 6


# ── Data Structures ────────────────────────────────────────────

@dataclass
class NegotiationRequest:
    """Complete negotiation request from the master pipeline."""
    task_id: str = ""
    task_type: TaskType = TaskType.IMAGE_GENERATION
    modality: Modality = Modality.IMAGE
    prompt: str = ""
    input_data: Optional[bytes] = None
    reference_images: Optional[List[bytes]] = None

    min_model_size: Optional[int] = None
    max_model_size: Optional[int] = None
    required_capabilities: List[str] = field(default_factory=list)
    preferred_models: Optional[List[str]] = None
    excluded_models: Optional[List[str]] = None

    min_quality_score: Optional[float] = None
    quality_priority: QualityPriority = QualityPriority.HIGH

    latency_target_ms: Optional[float] = None
    throughput_target: Optional[float] = None
    streaming_required: bool = False

    max_cost_usd: Optional[float] = None
    max_energy_wh: Optional[float] = None
    privacy_level: PrivacyLevel = PrivacyLevel.CLOUD_OK
    max_nodes: Optional[int] = None

    preferred_hardware: Optional[List[str]] = None
    excluded_hardware: Optional[List[str]] = None
    preferred_region: Optional[str] = None
    preferred_runtimes: Optional[List[str]] = None
    excluded_runtimes: Optional[List[str]] = None

    prefer_free: bool = True
    prefer_cloud: bool = True
    width: int = 1024
    height: int = 1024
    duration_secs: float = 4.0
    negative_prompt: str = ""
    seed: Optional[int] = None
    model: str = ""
    style: str = ""

    def __post_init__(self):
        if not self.task_id:
            h = hashlib.sha256(
                f"{self.task_type.value}:{self.prompt}:{time.time()}".encode()
            ).hexdigest()[:10]
            self.task_id = f"neg-{h}"


@dataclass
class ExecutionCandidate:
    """A potential execution path for a task."""
    candidate_id: str = ""
    provider_name: str = ""
    model_id: str = ""
    model_name: str = ""
    layer: ExecutionLayer = ExecutionLayer.PUBLIC_API
    layer_name: str = "public_api"

    task_type: str = ""
    media_type: str = ""
    supported_tasks: List[str] = field(default_factory=list)
    supported_resolutions: List[str] = field(default_factory=list)
    free_tier: bool = False
    api_key_required: bool = False
    api_key_available: bool = False

    expected_latency_ms: float = 5000.0
    expected_cost_usd: float = 0.0
    expected_quality_score: float = 0.5
    expected_throughput: float = 1.0
    expected_energy_wh: float = 0.0

    success_rate: float = 0.8
    benchmark_count: int = 0
    last_benchmark_time: Optional[str] = None
    verified: bool = False
    healthy: bool = True

    requires_image_input: bool = False
    max_duration_secs: float = 0.0
    max_resolution: str = ""
    streaming: bool = False
    batching: bool = False

    score: float = 0.0
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "provider": self.provider_name,
            "model": self.model_id,
            "model_name": self.model_name,
            "layer": self.layer_name,
            "score": round(self.score, 3),
            "confidence": round(self.confidence, 3),
            "expected_latency_ms": round(self.expected_latency_ms, 1),
            "expected_cost_usd": round(self.expected_cost_usd, 6),
            "expected_quality": round(self.expected_quality_score, 3),
            "success_rate": round(self.success_rate, 3),
            "free_tier": self.free_tier,
            "verified": self.verified,
            "healthy": self.healthy,
            "benchmark_count": self.benchmark_count,
        }


@dataclass
class FallbackPlan:
    """A fallback execution plan when primary fails."""
    level: int = 1
    reason: str = ""
    candidate: Optional[ExecutionCandidate] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "reason": self.reason,
            "provider": self.candidate.provider_name if self.candidate else "",
            "model": self.candidate.model_id if self.candidate else "",
            "score": round(self.candidate.score, 3) if self.candidate else 0.0,
        }


@dataclass
class TradeOff:
    """Documents a trade-off made during negotiation."""
    dimension: str = ""
    chosen_value: Any = None
    alternative_value: Any = None
    impact: str = ""
    reasoning: str = ""
    user_notification: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "chosen": str(self.chosen_value),
            "alternative": str(self.alternative_value),
            "impact": self.impact,
            "reasoning": self.reasoning,
            "notification": self.user_notification,
        }


@dataclass
class NegotiationResult:
    """Complete result of a negotiation."""
    task_id: str = ""
    status: str = "success"  # success, no_compatible_path, constraints_relaxed
    suggestion: str = ""

    selected_candidate: Optional[ExecutionCandidate] = None
    fallback_chain: List[FallbackPlan] = field(default_factory=list)
    all_candidates: List[ExecutionCandidate] = field(default_factory=list)

    expected_quality_score: float = 0.0
    expected_latency_ms: float = 0.0
    expected_cost_usd: float = 0.0
    expected_energy_wh: float = 0.0

    confidence_score: float = 0.0
    reasoning: str = ""
    trade_offs: List[TradeOff] = field(default_factory=list)

    negotiation_time_ms: float = 0.0
    total_candidates_evaluated: int = 0
    candidates_before_filter: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "suggestion": self.suggestion,
            "selected": self.selected_candidate.to_dict() if self.selected_candidate else None,
            "fallback_chain": [f.to_dict() for f in self.fallback_chain],
            "expected_quality": round(self.expected_quality_score, 3),
            "expected_latency_ms": round(self.expected_latency_ms, 1),
            "expected_cost_usd": round(self.expected_cost_usd, 6),
            "confidence_score": round(self.confidence_score, 3),
            "reasoning": self.reasoning,
            "trade_offs": [t.to_dict() for t in self.trade_offs],
            "negotiation_time_ms": round(self.negotiation_time_ms, 1),
            "total_evaluated": self.total_candidates_evaluated,
            "candidates_before_filter": self.candidates_before_filter,
        }


# ── Scoring Weights by Task Category ──────────────────────────

SCORING_WEIGHTS = {
    "default": {"quality": 0.30, "speed": 0.25, "cost": 0.15, "reliability": 0.15, "energy": 0.15},
    "image_generation": {"quality": 0.35, "speed": 0.20, "cost": 0.15, "reliability": 0.15, "energy": 0.15},
    "video_generation": {"quality": 0.30, "speed": 0.20, "cost": 0.20, "reliability": 0.15, "energy": 0.15},
    "audio_generation": {"quality": 0.30, "speed": 0.25, "cost": 0.15, "reliability": 0.15, "energy": "0.15"},
    "image_editing": {"quality": 0.35, "speed": 0.20, "cost": 0.15, "reliability": 0.15, "energy": 0.15},
    "inpainting": {"quality": 0.35, "speed": 0.20, "cost": 0.15, "reliability": 0.15, "energy": 0.15},
    "style_transfer": {"quality": 0.35, "speed": 0.20, "cost": 0.15, "reliability": 0.15, "energy": 0.15},
    "upscale": {"quality": 0.40, "speed": 0.20, "cost": 0.10, "reliability": 0.15, "energy": 0.15},
    "background_removal": {"quality": 0.30, "speed": 0.30, "cost": 0.10, "reliability": 0.20, "energy": 0.10},
    "text_generation": {"quality": 0.35, "speed": 0.25, "cost": 0.15, "reliability": 0.15, "energy": 0.10},
    "document_processing": {"quality": 0.40, "speed": 0.20, "cost": 0.10, "reliability": 0.20, "energy": 0.10},
    "face_restore": {"quality": 0.40, "speed": 0.15, "cost": 0.15, "reliability": 0.20, "energy": 0.10},
    "3d_generation": {"quality": 0.35, "speed": 0.15, "cost": 0.20, "reliability": 0.15, "energy": 0.15},
}

# Quality priority multipliers
QUALITY_MULTIPLIERS = {
    QualityPriority.LOW: 0.6,
    QualityPriority.MEDIUM: 0.8,
    QualityPriority.HIGH: 1.0,
    QualityPriority.MAXIMUM: 1.3,
}

# Max throughput for normalization (images/sec)
MAX_THROUGHPUT = 10.0
MAX_COST = 0.10  # $0.10 per generation
MAX_ENERGY = 100.0  # Wh per generation


# ── Negotiation Engine ────────────────────────────────────────

class NegotiationEngine:
    """
    ACOS Negotiation Engine — selects optimal execution path.

    Given a request and constraints, queries available candidates,
    scores them on multiple criteria, generates fallback chains,
    and documents trade-offs. Every decision is evidence-based.
    """

    def __init__(self):
        self._history: List[NegotiationResult] = []
        self._benchmark_cache: Dict[str, Dict[str, Any]] = {}
        self._health_cache: Dict[str, bool] = {}
        self._scoring_weights = dict(SCORING_WEIGHTS)

    def negotiate(self, request: NegotiationRequest,
                  candidates: List[ExecutionCandidate]) -> NegotiationResult:
        """
        Full negotiation pipeline:
        1. Filter candidates by constraints
        2. Score each candidate
        3. Rank by composite score
        4. Select top candidate
        5. Generate fallback chain
        6. Validate against constraints
        7. Document trade-offs
        """
        start = time.time()
        result = NegotiationResult(task_id=request.task_id)

        if not candidates:
            result.status = "no_compatible_path"
            result.suggestion = self._suggest_relaxation(request)
            result.reasoning = (
                f"No candidates provided for negotiation. "
                f"Suggestion: {result.suggestion}"
            )
            result.negotiation_time_ms = (time.time() - start) * 1000
            self._history.append(result)
            return result

        result.candidates_before_filter = len(candidates)

        # Step 1: Filter by constraints
        filtered = self._filter_candidates(candidates, request)

        if not filtered:
            result.status = "no_compatible_path"
            result.suggestion = self._suggest_relaxation(request)
            result.reasoning = (
                f"All {len(candidates)} candidates filtered out by constraints. "
                f"Suggestion: {result.suggestion}"
            )
            result.negotiation_time_ms = (time.time() - start) * 1000
            self._history.append(result)
            return result

        # Step 2: Score each candidate
        for candidate in filtered:
            benchmark = self._get_benchmark(
                candidate.provider_name, candidate.model_id, request.task_type.value
            )
            candidate.score = self._compute_composite_score(
                candidate, benchmark, request
            )
            candidate.confidence = self._compute_confidence(
                candidate, request
            )

        # Step 3: Rank by composite score
        filtered.sort(key=lambda c: c.score, reverse=True)

        # Step 4: Select top candidate
        primary = filtered[0]
        result.selected_candidate = primary
        result.all_candidates = filtered

        # Step 5: Generate fallback chain
        result.fallback_chain = self._generate_fallback_chain(
            primary, filtered[1:], request
        )

        # Step 6: Validate and document
        result.expected_quality_score = primary.expected_quality_score
        result.expected_latency_ms = primary.expected_latency_ms
        result.expected_cost_usd = primary.expected_cost_usd
        result.expected_energy_wh = primary.expected_energy_wh
        result.confidence_score = primary.confidence
        result.total_candidates_evaluated = len(filtered)
        result.status = "success"

        # Step 7: Document trade-offs
        result.trade_offs = self._document_trade_offs(
            primary, filtered[1:] if len(filtered) > 1 else [], request
        )

        result.reasoning = self._generate_reasoning(primary, request)
        result.negotiation_time_ms = (time.time() - start) * 1000

        self._history.append(result)
        logger.info(
            f"Negotiation complete: {result.task_id} → "
            f"{primary.provider_name}/{primary.model_id} "
            f"(score={primary.score:.3f}, confidence={primary.confidence:.3f}, "
            f"{len(result.fallback_chain)} fallbacks, "
            f"{result.negotiation_time_ms:.1f}ms)"
        )
        return result

    def _filter_candidates(
        self, candidates: List[ExecutionCandidate], request: NegotiationRequest
    ) -> List[ExecutionCandidate]:
        """Apply all constraint filters. Returns surviving candidates."""
        filtered = list(candidates)

        # Filter by task type support
        task_val = request.task_type.value
        filtered = [c for c in filtered if task_val in c.supported_tasks or not c.supported_tasks]

        # Filter by privacy level
        if request.privacy_level == PrivacyLevel.LOCAL_ONLY:
            local_layers = {ExecutionLayer.LOCAL_GPU, ExecutionLayer.LOCAL_CPU, ExecutionLayer.BROWSER}
            filtered = [c for c in filtered if c.layer in local_layers]

        # Filter by excluded models
        if request.excluded_models:
            filtered = [c for c in filtered if c.model_id not in request.excluded_models]

        # Filter by excluded hardware
        if request.excluded_hardware:
            filtered = [c for c in filtered if c.provider_name not in request.excluded_hardware]

        # Filter by excluded runtimes
        if request.excluded_runtimes:
            filtered = [c for c in filtered if c.model_id not in request.excluded_runtimes]

        # Filter by required capabilities
        if request.required_capabilities:
            filtered = [
                c for c in filtered
                if all(cap in c.metadata.get("capabilities", []) for cap in request.required_capabilities)
            ]

        # Filter by cost constraint
        if request.max_cost_usd is not None:
            filtered = [c for c in filtered if c.expected_cost_usd <= request.max_cost_usd]

        # Filter by latency constraint
        if request.latency_target_ms is not None:
            filtered = [
                c for c in filtered
                if c.expected_latency_ms <= request.latency_target_ms * 1.5
            ]

        # Filter by model size constraints
        if request.min_model_size is not None:
            filtered = [
                c for c in filtered
                if c.metadata.get("parameters", 0) >= request.min_model_size
            ]
        if request.max_model_size is not None:
            filtered = [
                c for c in filtered
                if c.metadata.get("parameters", 0) <= request.max_model_size
            ]

        # Filter by preferred models (boost but don't exclude)
        if request.preferred_models:
            for c in filtered:
                if c.model_id in request.preferred_models:
                    c.score += 0.1  # Boost preferred models

        # Filter unhealthy candidates (keep but penalize)
        for c in filtered:
            if not c.healthy:
                c.score *= 0.5
            if not c.verified and c.api_key_required:
                c.score *= 0.7

        # Apply free tier preference
        if request.prefer_free:
            for c in filtered:
                if c.free_tier and not c.api_key_required:
                    c.score += 0.05

        # Apply cloud preference
        if request.prefer_cloud:
            cloud_layers = {ExecutionLayer.PUBLIC_API, ExecutionLayer.HOSTED_OPENSOURCE}
            for c in filtered:
                if c.layer in cloud_layers:
                    c.score += 0.03

        return filtered

    def _compute_composite_score(
        self, candidate: ExecutionCandidate,
        benchmark: Optional[Dict[str, Any]],
        request: NegotiationRequest,
    ) -> float:
        """
        Multi-criteria composite score.
        Score = w_q * quality + w_s * speed + w_c * cost + w_r * reliability + w_e * energy
        Each dimension 0.0-1.0, higher is better.
        """
        weights = self._get_weights(request.task_type.value)
        quality_mult = QUALITY_MULTIPLIERS.get(request.quality_priority, 1.0)

        q_score = self._quality_score(candidate, benchmark)
        s_score = self._speed_score(candidate, request)
        c_score = self._cost_score(candidate, request)
        r_score = self._reliability_score(candidate, benchmark)
        e_score = self._energy_score(candidate, request)

        composite = (
            weights["quality"] * q_score * quality_mult +
            weights["speed"] * s_score +
            weights["cost"] * c_score +
            weights["reliability"] * r_score +
            weights["energy"] * e_score
        )

        # Clamp to [0, 1]
        return max(0.0, min(1.0, composite))

    def _quality_score(
        self, candidate: ExecutionCandidate,
        benchmark: Optional[Dict[str, Any]]
    ) -> float:
        """Quality dimension: benchmark-based or default."""
        if benchmark:
            base = benchmark.get("quality_score", 0.5)
            # Recency weight: recent benchmarks count more
            ts = benchmark.get("timestamp", "")
            if ts:
                try:
                    bench_time = datetime.fromisoformat(ts)
                    age_days = (datetime.now() - bench_time).days
                    recency = max(0.5, 1.0 - (age_days / 30.0))
                    base *= recency
                except (ValueError, TypeError):
                    pass
            return min(1.0, base)

        # Default: use verified status and free tier as proxies
        score = 0.5
        if candidate.verified:
            score += 0.1
        if candidate.benchmark_count > 0:
            score += 0.1
        return min(1.0, score)

    def _speed_score(
        self, candidate: ExecutionCandidate,
        request: NegotiationRequest
    ) -> float:
        """Speed dimension: latency relative to target, or throughput."""
        if request.latency_target_ms and request.latency_target_ms > 0:
            ratio = candidate.expected_latency_ms / request.latency_target_ms
            return max(0.0, 1.0 - ratio)
        return min(1.0, candidate.expected_throughput / MAX_THROUGHPUT)

    def _cost_score(
        self, candidate: ExecutionCandidate,
        request: NegotiationRequest
    ) -> float:
        """Cost dimension: lower cost is better."""
        if request.max_cost_usd and request.max_cost_usd > 0:
            return max(0.0, 1.0 - (candidate.expected_cost_usd / request.max_cost_usd))
        return max(0.0, 1.0 - (candidate.expected_cost_usd / MAX_COST))

    def _reliability_score(
        self, candidate: ExecutionCandidate,
        benchmark: Optional[Dict[str, Any]]
    ) -> float:
        """Reliability dimension: success rate from benchmarks or history."""
        if benchmark:
            return benchmark.get("success_rate", candidate.success_rate)
        return candidate.success_rate

    def _energy_score(
        self, candidate: ExecutionCandidate,
        request: NegotiationRequest
    ) -> float:
        """Energy dimension: lower energy is better."""
        if request.max_energy_wh and request.max_energy_wh > 0:
            return max(0.0, 1.0 - (candidate.expected_energy_wh / request.max_energy_wh))
        return max(0.0, 1.0 - (candidate.expected_energy_wh / MAX_ENERGY))

    def _compute_confidence(
        self, candidate: ExecutionCandidate,
        request: NegotiationRequest
    ) -> float:
        """
        Confidence = benchmark_quality * 0.35 + constraint_match * 0.25
                   + resource_availability * 0.20 + fallback_availability * 0.10
                   + data_freshness * 0.10
        """
        # Benchmark quality
        if candidate.benchmark_count >= 10:
            bq = 1.0
        elif candidate.benchmark_count >= 3:
            bq = 0.7
        elif candidate.benchmark_count >= 1:
            bq = 0.4
        else:
            bq = 0.1

        # Constraint match (all constraints met = 1.0)
        cm = 1.0
        if request.latency_target_ms and candidate.expected_latency_ms > request.latency_target_ms:
            cm *= 0.7
        if request.max_cost_usd and candidate.expected_cost_usd > request.max_cost_usd * 0.8:
            cm *= 0.8

        # Resource availability
        ra = 1.0 if candidate.healthy else 0.3

        # Fallback availability (placeholder — actual count from chain)
        fa = 0.7  # Assume moderate fallback availability

        # Data freshness
        df = 0.7  # Default moderate freshness
        if candidate.last_benchmark_time:
            try:
                bench_time = datetime.fromisoformat(candidate.last_benchmark_time)
                age_days = (datetime.now() - bench_time).days
                if age_days < 1:
                    df = 1.0
                elif age_days < 7:
                    df = 0.7
                elif age_days < 30:
                    df = 0.4
                else:
                    df = 0.1
            except (ValueError, TypeError):
                pass

        confidence = bq * 0.35 + cm * 0.25 + ra * 0.20 + fa * 0.10 + df * 0.10
        return max(0.0, min(1.0, confidence))

    def _generate_fallback_chain(
        self, primary: ExecutionCandidate,
        remaining: List[ExecutionCandidate],
        request: NegotiationRequest
    ) -> List[FallbackPlan]:
        """
        Generate up to 5 fallback plans in priority order:
        Level 1: Same model, different runtime/provider
        Level 2: Same runtime/provider, different model
        Level 3: Different everything (degraded quality)
        Level 4: Cloud API (if local-only was requested)
        Level 5: Free tier alternatives
        """
        chain: List[FallbackPlan] = []

        # Level 1: Same model, different provider
        for c in remaining:
            if c.model_name == primary.model_name and c.provider_name != primary.provider_name:
                chain.append(FallbackPlan(level=1, reason="Same model, different provider", candidate=c))
                if len(chain) >= 5:
                    return chain

        # Level 2: Same provider, different model
        for c in remaining:
            if c.provider_name == primary.provider_name and c.model_id != primary.model_id:
                chain.append(FallbackPlan(level=2, reason="Same provider, different model", candidate=c))
                if len(chain) >= 5:
                    return chain

        # Level 3: Different everything
        for c in remaining:
            if c.model_id != primary.model_id and c.provider_name != primary.provider_name:
                chain.append(FallbackPlan(level=3, reason="Full fallback", candidate=c))
                if len(chain) >= 5:
                    return chain

        # Level 4: Cloud fallback if local was preferred
        if request.privacy_level == PrivacyLevel.LOCAL_ONLY:
            cloud_layers = {ExecutionLayer.PUBLIC_API, ExecutionLayer.HOSTED_OPENSOURCE}
            for c in remaining:
                if c.layer in cloud_layers:
                    chain.append(FallbackPlan(level=4, reason="Cloud fallback", candidate=c))
                    if len(chain) >= 5:
                        return chain

        # Level 5: Free tier alternatives
        for c in remaining:
            if c.free_tier and not c.api_key_required:
                chain.append(FallbackPlan(level=5, reason="Free tier alternative", candidate=c))
                if len(chain) >= 5:
                    return chain

        # Fill remaining with any unranked candidates
        for c in remaining:
            already = any(f.candidate and f.candidate.candidate_id == c.candidate_id for f in chain)
            if not already:
                chain.append(FallbackPlan(level=6, reason="Other alternative", candidate=c))
                if len(chain) >= 5:
                    return chain

        return chain[:5]

    def _document_trade_offs(
        self, primary: ExecutionCandidate,
        alternatives: List[ExecutionCandidate],
        request: NegotiationRequest
    ) -> List[TradeOff]:
        """Document what was traded off in the selection."""
        trade_offs: List[TradeOff] = []

        if not alternatives:
            return trade_offs

        best_alt = alternatives[0]

        # Quality trade-off
        if primary.expected_quality_score < best_alt.expected_quality_score:
            diff = (best_alt.expected_quality_score - primary.expected_quality_score) * 100
            trade_offs.append(TradeOff(
                dimension="quality",
                chosen_value=f"{primary.provider_name}/{primary.model_id}",
                alternative_value=f"{best_alt.provider_name}/{best_alt.model_id}",
                impact=f"{diff:.0f}% lower quality",
                reasoning=f"Selected for better {self._dominant_dimension(primary, best_alt, request)}",
                user_notification=f"Using {primary.provider_name} for better {self._dominant_dimension(primary, best_alt, request)}",
            ))

        # Cost trade-off
        if primary.expected_cost_usd > best_alt.expected_cost_usd:
            diff = primary.expected_cost_usd - best_alt.expected_cost_usd
            trade_offs.append(TradeOff(
                dimension="cost",
                chosen_value=f"${primary.expected_cost_usd:.6f}",
                alternative_value=f"${best_alt.expected_cost_usd:.6f}",
                impact=f"${diff:.6f} higher cost",
                reasoning="Higher cost accepted for better quality/speed",
                user_notification=f"Using {primary.provider_name} (${primary.expected_cost_usd:.4f}/gen)",
            ))

        # Latency trade-off
        if primary.expected_latency_ms > best_alt.expected_latency_ms:
            diff = primary.expected_latency_ms - best_alt.expected_latency_ms
            trade_offs.append(TradeOff(
                dimension="speed",
                chosen_value=f"{primary.expected_latency_ms:.0f}ms",
                alternative_value=f"{best_alt.expected_latency_ms:.0f}ms",
                impact=f"{diff:.0f}ms slower",
                reasoning="Higher latency accepted for better quality",
                user_notification=f"Estimated latency: {primary.expected_latency_ms:.0f}ms",
            ))

        return trade_offs

    def _dominant_dimension(
        self, primary: ExecutionCandidate,
        alternative: ExecutionCandidate,
        request: NegotiationRequest
    ) -> str:
        """Determine which dimension made the primary win."""
        weights = self._get_weights(request.task_type.value)
        dims = {
            "quality": weights["quality"] * (primary.expected_quality_score - alternative.expected_quality_score),
            "speed": weights["speed"] * (1.0 - primary.expected_latency_ms / max(alternative.expected_latency_ms, 1)),
            "cost": weights["cost"] * (alternative.expected_cost_usd - primary.expected_cost_usd),
            "reliability": weights["reliability"] * (primary.success_rate - alternative.success_rate),
        }
        best = max(dims, key=dims.get)
        return best if dims[best] > 0 else "overall balance"

    def _generate_reasoning(
        self, primary: ExecutionCandidate,
        request: NegotiationRequest
    ) -> str:
        """Generate human-readable reasoning for the selection."""
        parts = [
            f"Selected {primary.provider_name}/{primary.model_id}",
            f"layer={primary.layer_name}",
            f"score={primary.score:.3f}",
            f"confidence={primary.confidence:.3f}",
        ]
        if primary.free_tier:
            parts.append("free_tier=true")
        if primary.verified:
            parts.append("verified=true")
        parts.append(f"quality={primary.expected_quality_score:.2f}")
        parts.append(f"latency={primary.expected_latency_ms:.0f}ms")
        parts.append(f"cost=${primary.expected_cost_usd:.6f}")
        return " | ".join(parts)

    def _suggest_relaxation(self, request: NegotiationRequest) -> str:
        """Suggest how to relax constraints to find a path."""
        suggestions = []
        if request.privacy_level == PrivacyLevel.LOCAL_ONLY:
            suggestions.append("Set privacy_level to CLOUD_OK to use cloud providers")
        if request.max_cost_usd is not None and request.max_cost_usd < 0.001:
            suggestions.append("Increase max_cost_usd to allow paid providers")
        if request.latency_target_ms is not None and request.latency_target_ms < 1000:
            suggestions.append("Increase latency_target_ms to allow slower but higher-quality providers")
        if request.required_capabilities:
            suggestions.append(f"Remove required_capabilities: {request.required_capabilities}")
        if request.excluded_models:
            suggestions.append("Clear excluded_models list")
        return "; ".join(suggestions) if suggestions else "Check available resources and API keys"

    def _get_weights(self, task_type: str) -> Dict[str, float]:
        """Get scoring weights for a task type."""
        return self._scoring_weights.get(task_type, self._scoring_weights["default"])

    def _get_benchmark(
        self, provider: str, model: str, task_type: str
    ) -> Optional[Dict[str, Any]]:
        """Look up benchmark data for a provider/model combination."""
        key = f"{provider}:{model}:{task_type}"
        return self._benchmark_cache.get(key)

    def update_benchmark(
        self, provider: str, model: str, task_type: str,
        quality_score: float, success_rate: float, latency_ms: float
    ):
        """Update benchmark data for a provider/model combination."""
        key = f"{provider}:{model}:{task_type}"
        self._benchmark_cache[key] = {
            "provider": provider,
            "model": model,
            "task_type": task_type,
            "quality_score": quality_score,
            "success_rate": success_rate,
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat(),
        }

    def update_health(self, provider: str, healthy: bool):
        """Update health status for a provider."""
        self._health_cache[provider] = healthy

    def get_stats(self) -> Dict[str, Any]:
        """Get negotiation statistics."""
        total = len(self._history)
        success = sum(1 for r in self._history if r.status == "success")
        no_path = sum(1 for r in self._history if r.status == "no_compatible_path")
        avg_time = (
            sum(r.negotiation_time_ms for r in self._history) / max(total, 1)
        )
        avg_confidence = (
            sum(r.confidence_score for r in self._history if r.selected_candidate)
            / max(success, 1)
        )
        return {
            "total_negotiations": total,
            "successful": success,
            "no_compatible_path": no_path,
            "avg_negotiation_time_ms": round(avg_time, 1),
            "avg_confidence_score": round(avg_confidence, 3),
            "benchmark_entries": len(self._benchmark_cache),
            "health_tracked": len(self._health_cache),
        }

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent negotiation history."""
        return [r.to_dict() for r in self._history[-limit:]]

    def set_weights(self, task_type: str, weights: Dict[str, float]):
        """Override scoring weights for a task type."""
        self._scoring_weights[task_type] = weights
        logger.info(f"Updated scoring weights for {task_type}: {weights}")


# ── Candidate Builder ──────────────────────────────────────────

class CandidateBuilder:
    """
    Builds ExecutionCandidate objects from the CapabilityRegistry
    and provider state. Bridges the existing registry to the
    negotiation engine.
    """

    def __init__(self, capability_registry=None, provider_registry=None,
                 health_monitor=None, benchmark_engine=None):
        self._cr = capability_registry
        self._pr = provider_registry
        self._hm = health_monitor
        self._be = benchmark_engine

    # Map NegotiationEngine TaskType values to CapabilityRegistry task names
    _TASK_TYPE_ALIASES = {
        "image_generation": "text_to_image",
        "image_editing": "img2img",
        "image_upscaling": "upscale",
        "background_removal": "background_removal",
        "style_transfer": "style_transfer",
        "inpainting": "inpainting",
        "outpainting": "outpainting",
        "face_restore": "face_restore",
        "face_identity": "face_identity",
        "video_generation": "text_to_video",
        "audio_generation": "text_to_audio",
        "text_to_speech": "text_to_speech",
        "3d_generation": "3d_generation",
    }

    def build_candidates(self, task_type: TaskType) -> List[ExecutionCandidate]:
        """Build candidates from the capability registry and provider state."""
        candidates: List[ExecutionCandidate] = []

        if self._cr:
            registry_task = self._TASK_TYPE_ALIASES.get(task_type.value, task_type.value)
            models = self._cr.find_models(task=registry_task, free_only=False)
            for m in models:
                candidate = ExecutionCandidate(
                    candidate_id=f"cr-{m['model_id']}",
                    provider_name=m.get("provider", ""),
                    model_id=m.get("model_id", ""),
                    model_name=m.get("model_name", ""),
                    layer=self._determine_layer(m),
                    layer_name=m.get("provider", "unknown"),
                    task_type=task_type.value,
                    media_type=m.get("media_type", ""),
                    supported_tasks=m.get("tasks", []),
                    supported_resolutions=m.get("resolutions", []),
                    free_tier=m.get("free_tier", False),
                    api_key_required=m.get("api_key_required", False),
                    api_key_available=self._check_api_key(m.get("provider", "")),
                    expected_latency_ms=self._estimate_latency(m),
                    expected_cost_usd=self._estimate_cost(m),
                    expected_quality_score=self._estimate_quality(m),
                    success_rate=0.85,
                    healthy=self._is_healthy(m.get("provider", "")),
                    verified=self._is_verified(m.get("provider", "")),
                    metadata=m,
                )
                candidates.append(candidate)

        # Add provider-level candidates from provider registry
        if self._pr:
            for provider in self._pr.get_all():
                if hasattr(provider, 'name') and hasattr(provider, 'provider_type'):
                    provider_type_val = provider.provider_type.value if hasattr(provider.provider_type, 'value') else str(provider.provider_type)
                    if task_type.value.replace("_", "") in provider_type_val.replace("_", "") or \
                       self._is_compatible_task(provider_type_val, task_type.value):
                        stats = provider.get_stats()
                        candidate = ExecutionCandidate(
                            candidate_id=f"pr-{provider.name}",
                            provider_name=provider.name,
                            model_id=provider.default_model,
                            model_name=provider.default_model,
                            layer=ExecutionLayer.PUBLIC_API,
                            layer_name="public_api",
                            task_type=task_type.value,
                            media_type=provider_type_val,
                            supported_tasks=[provider_type_val],
                            free_tier=stats.get("tier", "") == "free",
                            api_key_required=stats.get("requires_api_key", True),
                            api_key_available=stats.get("has_api_key", False),
                            expected_latency_ms=stats.get("avg_latency_ms", 5000),
                            expected_cost_usd=0.0 if stats.get("tier") == "free" else 0.005,
                            expected_quality_score=stats.get("success_rate", 80) / 100.0,
                            success_rate=stats.get("success_rate", 80) / 100.0,
                            healthy=provider.is_available,
                            verified=stats.get("has_api_key", False),
                            metadata=stats,
                        )
                        # Avoid duplicates
                        if not any(c.provider_name == provider.name for c in candidates):
                            candidates.append(candidate)

        return candidates

    def _determine_layer(self, model: Dict[str, Any]) -> ExecutionLayer:
        """Determine execution layer from model metadata."""
        if model.get("requires_docker"):
            return ExecutionLayer.USER_CONFIGURED
        return ExecutionLayer.PUBLIC_API

    def _check_api_key(self, provider: str) -> bool:
        """Check if API key is available for a provider."""
        import os
        key_map = {
            "huggingface_inference": "HUGGINGFACE_API_KEY",
            "siliconflow": "SILICONFLOW_API_KEY",
            "together": "TOGETHER_API_KEY",
            "stability": "STABILITY_API_KEY",
            "replicate": "REPLICATE_API_TOKEN",
            "replicate_video": "REPLICATE_API_TOKEN",
            "fal": "FAL_KEY",
        }
        env_var = key_map.get(provider, f"{provider.upper().replace('-', '_')}_API_KEY")
        return bool(os.environ.get(env_var, ""))

    def _is_healthy(self, provider: str) -> bool:
        """Check provider health from monitor."""
        if self._hm:
            return self._hm.is_healthy(provider)
        return True  # Default to healthy if no monitor

    def _is_verified(self, provider: str) -> bool:
        """Check if provider has been verified."""
        return self._check_api_key(provider)

    def _estimate_latency(self, model: Dict[str, Any]) -> float:
        """Estimate latency for a model/provider."""
        latency_map = {
            "pollinations": 8000,
            "craiyon": 15000,
            "siliconflow": 3000,
            "together": 3000,
            "huggingface_inference": 10000,
            "replicate": 12000,
            "replicate_video": 30000,
            "stability": 5000,
            "fal": 4000,
        }
        return latency_map.get(model.get("provider", ""), 5000)

    def _estimate_cost(self, model: Dict[str, Any]) -> float:
        """Estimate cost per generation."""
        if model.get("free_tier"):
            return 0.0
        cost_map = {
            "replicate": 0.003,
            "replicate_video": 0.05,
            "stability": 0.01,
            "fal": 0.005,
        }
        return cost_map.get(model.get("provider", ""), 0.0)

    def _estimate_quality(self, model: Dict[str, Any]) -> float:
        """Estimate quality score from benchmark score or defaults."""
        bench = model.get("benchmark_score", 0)
        if bench > 0:
            return min(1.0, bench / 100.0)
        quality_map = {
            "pollinations": 0.65,
            "craiyon": 0.45,
            "siliconflow": 0.75,
            "together": 0.80,
            "huggingface_inference": 0.70,
            "replicate": 0.80,
            "stability": 0.85,
            "fal": 0.80,
        }
        return quality_map.get(model.get("provider", ""), 0.6)

    def _is_compatible_task(self, provider_type: str, task_type: str) -> bool:
        """Check if a provider type is compatible with a task type."""
        compat = {
            "image": {"image_generation", "image_editing", "image_upscaling",
                      "background_removal", "style_transfer", "inpainting",
                      "outpainting", "face_restore", "face_identity"},
            "video": {"video_generation", "video_editing", "video_upscaling"},
            "audio": {"audio_generation", "audio_transcription", "audio_tts"},
            "text": {"text_generation", "text_embedding"},
        }
        for ptype, tasks in compat.items():
            if ptype in provider_type.lower() and task_type in tasks:
                return True
        return False
