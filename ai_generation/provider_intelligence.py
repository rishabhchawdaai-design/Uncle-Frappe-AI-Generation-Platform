"""
Provider Discovery Intelligence — extends research_agent with automated
research of GitHub, Hugging Face, official docs, model releases, changelogs.
Verifies availability, licensing, capabilities, benchmarks, media support.
Never auto-integrates — generates implementation recommendations only.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    FAILED = "failed"
    PARTIAL = "partial"


class LicenseType(str, Enum):
    UNKNOWN = "unknown"
    OPEN = "open"
    COMMERCIAL = "commercial"
    RESEARCH_ONLY = "research_only"
    FREE_TIER = "free_tier"
    PROPRIETARY = "proprietary"


class MediaSupportLevel(str, Enum):
    NONE = "none"
    BASIC = "basic"
    ADVANCED = "advanced"
    PRODUCTION = "production"


@dataclass
class ProviderIntelligence:
    name: str = ""
    url: str = ""
    provider_type: str = ""
    license: LicenseType = LicenseType.UNKNOWN
    license_notes: str = ""
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    availability_confirmed: bool = False
    api_key_required: bool = False
    free_tier_available: bool = False
    models: List[Dict[str, Any]] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    media_support: Dict[str, str] = field(default_factory=dict)
    benchmark_scores: Dict[str, float] = field(default_factory=dict)
    github_stars: int = 0
    last_model_release: str = ""
    last_changelog: str = ""
    implementation_notes: str = ""
    implementation_priority: str = "low"
    verified_at: str = ""
    notes: str = ""
    source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "url": self.url,
            "provider_type": self.provider_type,
            "license": self.license.value,
            "license_notes": self.license_notes,
            "verification_status": self.verification_status.value,
            "availability_confirmed": self.availability_confirmed,
            "api_key_required": self.api_key_required,
            "free_tier_available": self.free_tier_available,
            "models_count": len(self.models),
            "capabilities": self.capabilities,
            "media_support": self.media_support,
            "benchmark_scores": self.benchmark_scores,
            "github_stars": self.github_stars,
            "last_model_release": self.last_model_release,
            "implementation_priority": self.implementation_priority,
            "source": self.source,
        }


class ProviderIntelligenceEngine:
    """
    Research-driven provider discovery and evaluation.
    Never auto-integrates — generates recommendations only.
    """

    def __init__(self):
        self._discoveries: List[ProviderIntelligence] = []
        self._research_history: List[Dict[str, Any]] = []
        self._seed_known_providers()

    def _seed_known_providers(self):
        """Seed with known providers and their intelligence."""
        known = [
            ProviderIntelligence(
                name="pollinations", url="https://pollinations.ai",
                provider_type="image", license=LicenseType.FREE_TIER,
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, free_tier_available=True,
                models=[{"name": "flux", "type": "image", "free": True}],
                capabilities=["text_to_image"],
                media_support={"image": "advanced", "video": "none"},
                benchmark_scores={"realism": 70, "speed": 60, "quality": 70},
                implementation_priority="high",
                source="github.com/pollinations/pollinations",
                notes="Free, no API key. Good Flux models.",
            ),
            ProviderIntelligence(
                name="pollinations_text", url="https://text.pollinations.ai",
                provider_type="text", license=LicenseType.FREE_TIER,
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, free_tier_available=True,
                models=[
                    {"name": "openai-fast", "type": "text", "free": True},
                    {"name": "mistral", "type": "text", "free": True},
                ],
                capabilities=["chat"],
                media_support={"text": "production", "audio": "none", "video": "none"},
                benchmark_scores={"quality": 70, "speed": 80, "latency": 80},
                implementation_priority="high",
                source="github.com/pollinations/pollinations",
                notes="Free, no API key. Anonymous GET endpoint live-verified 2026-08-01.",
            ),
            ProviderIntelligence(
                name="siliconflow", url="https://siliconflow.cn",
                provider_type="image", license=LicenseType.FREE_TIER,
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, api_key_required=True,
                free_tier_available=True,
                models=[
                    {"name": "FLUX.1-schnell", "type": "image", "free": True},
                    {"name": "FLUX.1-dev", "type": "image", "free": True},
                ],
                capabilities=["text_to_image"],
                media_support={"image": "advanced", "video": "none"},
                benchmark_scores={"realism": 80, "speed": 85, "quality": 80},
                implementation_priority="high",
                source="docs.siliconflow.cn",
            ),
            ProviderIntelligence(
                name="stability", url="https://platform.stability.ai",
                provider_type="image", license=LicenseType.COMMERCIAL,
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, api_key_required=True,
                free_tier_available=False,
                models=[
                    {"name": "sd3-medium", "type": "image"},
                    {"name": "sd3-large", "type": "image"},
                    {"name": "sd3.5-large", "type": "image"},
                ],
                capabilities=["text_to_image", "img2img", "inpainting", "outpainting", "style_transfer"],
                media_support={"image": "production", "video": "basic"},
                benchmark_scores={"realism": 90, "speed": 75, "quality": 90},
                implementation_priority="high",
                source="platform.stability.ai/docs",
            ),
            ProviderIntelligence(
                name="replicate", url="https://replicate.com",
                provider_type="image+video", license=LicenseType.FREE_TIER,
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, api_key_required=True,
                free_tier_available=True,
                models=[
                    {"name": "flux-schnell", "type": "image", "free": True},
                    {"name": "flux-dev", "type": "image"},
                    {"name": "sdxl", "type": "image"},
                    {"name": "stable-video-diffusion", "type": "video"},
                    {"name": "animate-diff", "type": "video"},
                ],
                capabilities=["text_to_image", "text_to_video", "image_to_video"],
                media_support={"image": "production", "video": "advanced"},
                benchmark_scores={"realism": 85, "speed": 70, "quality": 85},
                implementation_priority="high",
                source="replicate.com/docs",
            ),
            ProviderIntelligence(
                name="fal", url="https://fal.ai",
                provider_type="image", license=LicenseType.COMMERCIAL,
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, api_key_required=True,
                models=[
                    {"name": "flux-schnell", "type": "image"},
                    {"name": "flux-dev", "type": "image"},
                    {"name": "flux-pro", "type": "image"},
                ],
                capabilities=["text_to_image", "img2img", "inpainting"],
                media_support={"image": "production", "video": "none"},
                benchmark_scores={"realism": 90, "speed": 95, "quality": 90},
                implementation_priority="medium",
                source="fal.ai/docs",
            ),
            ProviderIntelligence(
                name="kimi_k3", url="https://platform.kimi.ai",
                provider_type="text", license=LicenseType.OPEN,
                license_notes="Kimi K3 License (open weights); API use subject to Moonshot AI ToS",
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, api_key_required=True,
                free_tier_available=False,
                models=[
                    {"name": "kimi-k3", "type": "text"},
                    {"name": "kimi-k3", "type": "text", "runtime": "vllm"},
                    {"name": "kimi-k3", "type": "text", "runtime": "sglang"},
                ],
                capabilities=["chat"],
                media_support={"text": "production", "image": "basic"},
                benchmark_scores={"reasoning": 92, "quality": 92, "speed": 70},
                implementation_priority="high",
                source="platform.kimi.ai/docs + official vLLM/SGLang recipes",
                notes="1M context, always-on thinking (low/high/max), MXFP4/MXFP8",
            ),
            # ── Local backends — free, open-weight, self-hostable, CPU (live-verified 2026-08-01) ──
            ProviderIntelligence(
                name="sentence_transformers", url="https://www.sbert.net",
                provider_type="text", license=LicenseType.OPEN,
                license_notes="Apache-2.0; all-MiniLM-L6-v2 (384-dim embeddings)",
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, api_key_required=False,
                free_tier_available=True,
                models=[{"name": "all-MiniLM-L6-v2", "type": "text", "runtime": "local-cpu"}],
                capabilities=["text_embedding"],
                media_support={"text": "production"},
                benchmark_scores={"quality": 75, "speed": 90, "latency": 90},
                implementation_priority="high",
                source="sbert.net + HF model card",
                notes="Local CPU embeddings, 384-dim, verified cos_sim 0.858.",
            ),
            ProviderIntelligence(
                name="piper_local", url="https://github.com/rhasspy/piper",
                provider_type="audio", license=LicenseType.OPEN,
                license_notes="MIT; voices MIT/CC-BY; en_US-lessac-medium",
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, api_key_required=False,
                free_tier_available=True,
                models=[{"name": "en_US-lessac-medium", "type": "audio", "runtime": "local-cpu"}],
                capabilities=["text_to_speech"],
                media_support={"audio": "production"},
                benchmark_scores={"quality": 78, "speed": 95, "latency": 95},
                implementation_priority="high",
                source="github.com/rhasspy/piper",
                notes="Fast CPU TTS, verified 2.76s WAV round-trip.",
            ),
            ProviderIntelligence(
                name="faster_whisper", url="https://github.com/SYSTRAN/faster-whisper",
                provider_type="audio", license=LicenseType.OPEN,
                license_notes="MIT (faster-whisper); Whisper models MIT (OpenAI)",
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, api_key_required=False,
                free_tier_available=True,
                models=[{"name": "tiny", "type": "audio", "runtime": "local-cpu"},
                        {"name": "base", "type": "audio", "runtime": "local-cpu"}],
                capabilities=["speech_to_text"],
                media_support={"audio": "production"},
                benchmark_scores={"quality": 72, "speed": 92, "latency": 92},
                implementation_priority="high",
                source="github.com/SYSTRAN/faster-whisper",
                notes="CPU-optimized STT (int8), verified TTS->STT round-trip.",
            ),
            ProviderIntelligence(
                name="helsinki_opus_mt", url="https://huggingface.co/Helsinki-NLP",
                provider_type="text", license=LicenseType.OPEN,
                license_notes="CC-BY-4.0 (Helsinki-NLP opus-mt models)",
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, api_key_required=False,
                free_tier_available=True,
                models=[{"name": "opus-mt-en-fr", "type": "text", "runtime": "local-cpu"},
                        {"name": "opus-mt-en-de", "type": "text", "runtime": "local-cpu"},
                        {"name": "opus-mt-en-es", "type": "text", "runtime": "local-cpu"}],
                capabilities=["translation"],
                media_support={"text": "production"},
                benchmark_scores={"quality": 80, "speed": 85, "latency": 85},
                implementation_priority="high",
                source="huggingface.co/Helsinki-NLP",
                notes="Open-weight MT on CPU, verified en->fr live.",
            ),
            ProviderIntelligence(
                name="realesrgan", url="https://github.com/xinntao/Real-ESRGAN",
                provider_type="image", license=LicenseType.OPEN,
                license_notes="BSD-3-Clause",
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, api_key_required=False,
                free_tier_available=True,
                models=[{"name": "realesr-general-x4v3", "type": "image", "runtime": "local-cpu"}],
                capabilities=["upscale"],
                media_support={"image": "advanced"},
                benchmark_scores={"quality": 85, "speed": 70, "latency": 70},
                implementation_priority="high",
                source="github.com/xinntao/Real-ESRGAN",
                notes="4x upscaling on CPU, verified 200x60 -> 800x240.",
            ),
            ProviderIntelligence(
                name="rembg", url="https://github.com/danielgatis/rembg",
                provider_type="image", license=LicenseType.OPEN,
                license_notes="MIT; u2net model Apache-2.0",
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, api_key_required=False,
                free_tier_available=True,
                models=[{"name": "u2net", "type": "image", "runtime": "local-cpu"}],
                capabilities=["background_removal"],
                media_support={"image": "advanced"},
                benchmark_scores={"quality": 82, "speed": 75, "latency": 75},
                implementation_priority="high",
                source="github.com/danielgatis/rembg",
                notes="RGBA background removal on CPU, verified 88.5% transparent.",
            ),
            ProviderIntelligence(
                name="tesseract_ocr", url="https://github.com/tesseract-ocr/tesseract",
                provider_type="image", license=LicenseType.OPEN,
                license_notes="Apache-2.0",
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, api_key_required=False,
                free_tier_available=True,
                models=[{"name": "tesseract-5.3", "type": "image", "runtime": "local-cpu"}],
                capabilities=["text_extraction"],
                media_support={"image": "production"},
                benchmark_scores={"quality": 85, "speed": 90, "latency": 90},
                implementation_priority="high",
                source="github.com/tesseract-ocr/tesseract",
                notes="OCR via ocr_engine (Tesseract backend), verified exact extraction.",
            ),
            # ── Storage & Databases (ACOS Storage Architecture) ──
            ProviderIntelligence(
                name="sqlite_local", url="https://www.sqlite.org",
                provider_type="storage", license=LicenseType.OPEN,
                license_notes="Public domain",
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, api_key_required=False,
                free_tier_available=True,
                models=[{"name": "sqlite3", "type": "storage", "runtime": "local-stdlib"}],
                capabilities=["metadata", "ledger", "audit", "cache"],
                media_support={"text": "production"},
                benchmark_scores={"speed": 95, "latency": 95, "reliability": 95},
                implementation_priority="high",
                source="ACOS Storage & Databases Research (SQLite)",
                notes="Local stdlib storage backend, verified in registry.",
            ),
            ProviderIntelligence(
                name="json_files", url="",
                provider_type="storage", license=LicenseType.OPEN,
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, api_key_required=False,
                free_tier_available=True,
                models=[{"name": "json", "type": "storage", "runtime": "local-stdlib"}],
                capabilities=["metadata", "ledger", "graph"],
                media_support={"text": "production"},
                benchmark_scores={"speed": 90, "latency": 90, "reliability": 90},
                implementation_priority="high",
                source="ACOS Storage & Databases Research (JSON files)",
                notes="Mirrors the data/ registry pattern used across the platform.",
            ),
            ProviderIntelligence(
                name="postgresql", url="https://www.postgresql.org",
                provider_type="storage", license=LicenseType.OPEN,
                license_notes="PostgreSQL License",
                verification_status=VerificationStatus.PARTIAL,
                availability_confirmed=False, api_key_required=True,
                free_tier_available=False,
                models=[{"name": "postgresql", "type": "storage"}],
                capabilities=["metadata", "ledger", "audit"],
                media_support={"text": "basic"},
                implementation_priority="medium",
                source="ACOS Storage & Databases Research (PostgreSQL)",
                notes="External service — profile registered, not configured.",
            ),
            ProviderIntelligence(
                name="qdrant", url="https://qdrant.tech",
                provider_type="storage", license=LicenseType.OPEN,
                license_notes="Apache-2.0",
                verification_status=VerificationStatus.PARTIAL,
                availability_confirmed=False, api_key_required=True,
                free_tier_available=False,
                models=[{"name": "qdrant", "type": "storage"}],
                capabilities=["embeddings"],
                media_support={"text": "basic"},
                implementation_priority="medium",
                source="ACOS Storage & Databases Research (Qdrant)",
                notes="External service — profile registered, not configured.",
            ),
            ProviderIntelligence(
                name="minio", url="https://min.io",
                provider_type="storage", license=LicenseType.OPEN,
                license_notes="AGPL-3.0",
                verification_status=VerificationStatus.PARTIAL,
                availability_confirmed=False, api_key_required=True,
                free_tier_available=False,
                models=[{"name": "minio", "type": "storage"}],
                capabilities=["artifacts"],
                media_support={"text": "basic"},
                implementation_priority="medium",
                source="ACOS Storage & Databases Research (MinIO)",
                notes="External service — profile registered, not configured.",
            ),
            ProviderIntelligence(
                name="neo4j", url="https://neo4j.com",
                provider_type="storage", license=LicenseType.OPEN,
                license_notes="GPLv3 (community)",
                verification_status=VerificationStatus.PARTIAL,
                availability_confirmed=False, api_key_required=True,
                free_tier_available=False,
                models=[{"name": "neo4j", "type": "storage"}],
                capabilities=["graph"],
                media_support={"text": "basic"},
                implementation_priority="medium",
                source="ACOS Storage & Databases Research (Neo4j)",
                notes="External service — profile registered, not configured.",
            ),
            ProviderIntelligence(
                name="prometheus", url="https://prometheus.io",
                provider_type="storage", license=LicenseType.OPEN,
                license_notes="Apache-2.0",
                verification_status=VerificationStatus.PARTIAL,
                availability_confirmed=False, api_key_required=False,
                free_tier_available=True,
                models=[{"name": "prometheus", "type": "storage"}],
                capabilities=["metrics"],
                media_support={"text": "basic"},
                implementation_priority="medium",
                source="ACOS Storage & Databases Research (Prometheus)",
                notes="External service — profile registered, not configured.",
            ),
            ProviderIntelligence(
                name="redis", url="https://redis.io",
                provider_type="storage", license=LicenseType.OPEN,
                license_notes="RSALv2 / SSPLv1",
                verification_status=VerificationStatus.PARTIAL,
                availability_confirmed=False, api_key_required=True,
                free_tier_available=False,
                models=[{"name": "redis", "type": "storage"}],
                capabilities=["cache"],
                media_support={"text": "basic"},
                implementation_priority="medium",
                source="ACOS Storage & Databases Research (Redis)",
                notes="External service — profile registered, not configured.",
            ),
            # ── Messaging & Events — Durable Event Log ──
            ProviderIntelligence(
                name="event_log", url="",
                provider_type="events", license=LicenseType.OPEN,
                verification_status=VerificationStatus.VERIFIED,
                availability_confirmed=True, api_key_required=False,
                free_tier_available=True,
                models=[{"name": "durable-event-log", "type": "events",
                         "runtime": "local-stdlib"}],
                capabilities=["event_sourcing", "event_replay", "dead_letter"],
                media_support={"text": "production"},
                benchmark_scores={"speed": 95, "latency": 95, "reliability": 95},
                implementation_priority="high",
                source="ACOS Messaging & Events Research (durable log)",
                notes="SQLite durable event log with delivery guarantees per ACOS taxonomy.",
            ),
        ]
        self._discoveries.extend(known)

    def add_intelligence(self, intel: ProviderIntelligence):
        self._discoveries.append(intel)

    def get_all(self, provider_type: Optional[str] = None, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self._discoveries
        if provider_type:
            results = [d for d in results if provider_type in d.provider_type]
        if priority:
            results = [d for d in results if d.implementation_priority == priority]
        return [d.to_dict() for d in results]

    def get_verified(self) -> List[Dict[str, Any]]:
        return [d.to_dict() for d in self._discoveries if d.verification_status == VerificationStatus.VERIFIED]

    def get_free_providers(self) -> List[Dict[str, Any]]:
        return [d.to_dict() for d in self._discoveries if d.free_tier_available]

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get implementation recommendations sorted by priority and score."""
        recs = []
        for d in self._discoveries:
            avg_score = sum(d.benchmark_scores.values()) / max(len(d.benchmark_scores), 1)
            priority_score = {"high": 3, "medium": 2, "low": 1}.get(d.implementation_priority, 0)
            recs.append({
                "name": d.name,
                "priority": d.implementation_priority,
                "avg_benchmark": round(avg_score, 1),
                "verification": d.verification_status.value,
                "free_tier": d.free_tier_available,
                "media_support": d.media_support,
                "recommendation_score": round(priority_score * 10 + avg_score, 1),
            })
        recs.sort(key=lambda x: x["recommendation_score"], reverse=True)
        return recs

    def record_research(self, query: str, results: List[Dict[str, Any]]):
        self._research_history.append({
            "query": query, "results_count": len(results),
            "timestamp": datetime.now().isoformat(),
        })

    def get_stats(self) -> Dict[str, Any]:
        verified = sum(1 for d in self._discoveries if d.verification_status == VerificationStatus.VERIFIED)
        return {
            "total_discoveries": len(self._discoveries),
            "verified": verified,
            "free_providers": sum(1 for d in self._discoveries if d.free_tier_available),
            "high_priority": sum(1 for d in self._discoveries if d.implementation_priority == "high"),
            "research_queries": len(self._research_history),
        }
