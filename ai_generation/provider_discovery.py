"""
Provider Discovery — automated research from GitHub, HuggingFace, official docs,
release notes, and changelogs. Discovers new providers, models, hosted inference,
and capabilities. Generates implementation recommendations, never auto-integrates.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DiscoverySource(str, Enum):
    GITHUB = "github"
    HUGGINGFACE = "huggingface"
    OFFICIAL_DOCS = "official_docs"
    CHANGELOG = "changelog"
    ARXIV = "arxiv"
    COMMUNITY = "community"


class DiscoveryStatus(str, Enum):
    DISCOVERED = "discovered"
    RESEARCHING = "researching"
    VERIFIED = "verified"
    INTEGRATED = "integrated"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


@dataclass
class ProviderDiscovery:
    name: str = ""
    url: str = ""
    source: DiscoverySource = DiscoverySource.COMMUNITY
    status: DiscoveryStatus = DiscoveryStatus.DISCOVERED
    provider_type: str = ""  # image, video, audio, editing
    description: str = ""
    models: List[Dict[str, Any]] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    license_info: str = ""
    free_tier: bool = False
    api_key_required: bool = False
    requires_docker: bool = False
    requires_gpu: bool = False
    github_stars: int = 0
    documentation_url: str = ""
    api_url: str = ""
    health_check_url: str = ""
    benchmark_scores: Dict[str, float] = field(default_factory=dict)
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    verified_at: str = ""
    notes: str = ""
    implementation_priority: str = "low"  # low, medium, high

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "url": self.url, "source": self.source.value,
            "status": self.status.value, "provider_type": self.provider_type,
            "description": self.description[:200],
            "models_count": len(self.models),
            "capabilities": self.capabilities,
            "license": self.license_info, "free_tier": self.free_tier,
            "api_key_required": self.api_key_required,
            "requires_docker": self.requires_docker,
            "requires_gpu": self.requires_gpu,
            "github_stars": self.github_stars,
            "documentation_url": self.documentation_url,
            "api_url": self.api_url,
            "benchmark_scores": self.benchmark_scores,
            "implementation_priority": self.implementation_priority,
            "discovered_at": self.discovered_at,
        }


class ProviderDiscoveryEngine:
    """Automated provider discovery and research."""

    def __init__(self):
        self._discoveries: List[ProviderDiscovery] = []
        self._research_queries: List[Dict[str, Any]] = []
        self._seed_known()

    def _seed_known(self):
        """Seed with known providers as baseline."""
        known = [
            ProviderDiscovery(
                name="pollinations", url="https://pollinations.ai",
                source=DiscoverySource.OFFICIAL_DOCS, status=DiscoveryStatus.VERIFIED,
                provider_type="image",
                description="Free AI image generation via Pollinations.ai",
                models=[{"name": "flux", "type": "image"}],
                capabilities=["text_to_image"],
                license_info="Free, no API key", free_tier=True,
                documentation_url="https://pollinations.ai",
                api_url="https://image.pollinations.ai/prompt",
                benchmark_scores={"quality": 70, "speed": 60},
                implementation_priority="high",
            ),
            ProviderDiscovery(
                name="pollinations_text", url="https://text.pollinations.ai",
                source=DiscoverySource.OFFICIAL_DOCS, status=DiscoveryStatus.VERIFIED,
                provider_type="text",
                description="Free anonymous text generation via Pollinations.ai (live-verified 2026-08-01)",
                models=[
                    {"name": "openai-fast", "type": "text", "free": True},
                    {"name": "mistral", "type": "text", "free": True},
                ],
                capabilities=["chat"],
                license_info="Free, no API key", free_tier=True,
                documentation_url="https://pollinations.ai",
                api_url="https://text.pollinations.ai",
                health_check_url="https://text.pollinations.ai/models",
                benchmark_scores={"quality": 70, "speed": 80},
                implementation_priority="high",
            ),
            ProviderDiscovery(
                name="siliconflow", url="https://siliconflow.cn",
                source=DiscoverySource.OFFICIAL_DOCS, status=DiscoveryStatus.VERIFIED,
                provider_type="image",
                description="Free Flux and other image models",
                models=[
                    {"name": "FLUX.1-schnell", "type": "image", "free": True},
                    {"name": "FLUX.1-dev", "type": "image"},
                ],
                capabilities=["text_to_image"],
                license_info="Free tier available", free_tier=True, api_key_required=True,
                documentation_url="https://docs.siliconflow.cn",
                api_url="https://api.siliconflow.cn/v1/images/generations",
                benchmark_scores={"quality": 80, "speed": 85},
                implementation_priority="high",
            ),
            ProviderDiscovery(
                name="together", url="https://together.ai",
                source=DiscoverySource.OFFICIAL_DOCS, status=DiscoveryStatus.VERIFIED,
                provider_type="image",
                description="Together AI with free Flux tier",
                models=[{"name": "FLUX.1-schnell-Free", "type": "image", "free": True}],
                capabilities=["text_to_image"],
                license_info="Free credits for new accounts", free_tier=True, api_key_required=True,
                documentation_url="https://docs.together.ai",
                api_url="https://api.together.xyz/v1/images/generations",
                benchmark_scores={"quality": 80, "speed": 80},
                implementation_priority="high",
            ),
            ProviderDiscovery(
                name="stability", url="https://platform.stability.ai",
                source=DiscoverySource.OFFICIAL_DOCS, status=DiscoveryStatus.VERIFIED,
                provider_type="image+editing",
                description="Stability AI — SD3, SD3.5, image editing",
                models=[
                    {"name": "sd3-medium", "type": "image"},
                    {"name": "sd3-large", "type": "image"},
                    {"name": "sd3.5-large", "type": "image"},
                ],
                capabilities=["text_to_image", "img2img", "inpainting", "outpainting", "upscale", "style_transfer"],
                license_info="Commercial", free_tier=False, api_key_required=True,
                documentation_url="https://platform.stability.ai/docs",
                api_url="https://api.stability.ai/v2beta",
                benchmark_scores={"quality": 90, "speed": 75},
                implementation_priority="high",
            ),
            ProviderDiscovery(
                name="replicate", url="https://replicate.com",
                source=DiscoverySource.OFFICIAL_DOCS, status=DiscoveryStatus.VERIFIED,
                provider_type="image+video",
                description="Replicate — community models for image and video",
                models=[
                    {"name": "flux-schnell", "type": "image", "free": True},
                    {"name": "flux-dev", "type": "image"},
                    {"name": "sdxl", "type": "image"},
                    {"name": "stable-video-diffusion", "type": "video"},
                ],
                capabilities=["text_to_image", "img2img", "upscale", "text_to_video", "image_to_video"],
                license_info="Free tier for Flux-Schnell", free_tier=True, api_key_required=True,
                documentation_url="https://replicate.com/docs",
                api_url="https://api.replicate.com/v1/predictions",
                benchmark_scores={"quality": 85, "speed": 70},
                implementation_priority="high",
            ),
            ProviderDiscovery(
                name="fal", url="https://fal.ai",
                source=DiscoverySource.OFFICIAL_DOCS, status=DiscoveryStatus.VERIFIED,
                provider_type="image",
                description="FAL.ai — fast Flux inference",
                models=[
                    {"name": "flux-schnell", "type": "image"},
                    {"name": "flux-dev", "type": "image"},
                    {"name": "flux-pro", "type": "image"},
                ],
                capabilities=["text_to_image", "img2img", "inpainting"],
                license_info="Commercial", free_tier=False, api_key_required=True,
                documentation_url="https://fal.ai/docs",
                api_url="https://fal.run",
                benchmark_scores={"quality": 90, "speed": 95},
                implementation_priority="medium",
            ),
            ProviderDiscovery(
                name="hf_spaces_flux", url="https://huggingface.co/spaces/black-forest-labs/FLUX.1-schnell",
                source=DiscoverySource.HUGGINGFACE, status=DiscoveryStatus.VERIFIED,
                provider_type="image",
                description="FLUX.1-schnell on Hugging Face Spaces (free inference)",
                models=[{"name": "flux-schnell", "type": "image"}],
                capabilities=["text_to_image"],
                license_info="Apache 2.0", free_tier=True,
                documentation_url="https://huggingface.co/spaces/black-forest-labs/FLUX.1-schnell",
                benchmark_scores={"quality": 75, "speed": 50},
                implementation_priority="medium",
            ),
        ]
        self._discoveries.extend(known)

    def add_discovery(self, discovery: ProviderDiscovery):
        self._discoveries.append(discovery)

    def research_sources(self) -> List[Dict[str, Any]]:
        """Return list of research sources to check."""
        return [
            {"source": "github", "query": "text-to-image inference server", "url": "https://github.com/search?q=text-to-image+inference+server&type=repositories&s=stars&o=desc"},
            {"source": "huggingface", "query": "inference-api", "url": "https://huggingface.co/models?pipeline_tag=text-to-image&sort=downloads"},
            {"source": "huggingface_spaces", "query": "text-to-image spaces", "url": "https://huggingface.co/spaces?sort=likes&search=text-to-image"},
            {"source": "arxiv", "query": "diffusion model inference", "url": "https://arxiv.org/search/?query=diffusion+inference&searchtype=all&order=-announced_date_first"},
        ]

    def get_all(self, provider_type: Optional[str] = None, status: Optional[DiscoveryStatus] = None) -> List[Dict[str, Any]]:
        results = self._discoveries
        if provider_type:
            results = [d for d in results if provider_type in d.provider_type]
        if status:
            results = [d for d in results if d.status == status]
        return [d.to_dict() for d in results]

    def get_verified(self) -> List[Dict[str, Any]]:
        return [d.to_dict() for d in self._discoveries if d.status == DiscoveryStatus.VERIFIED]

    def get_free_providers(self) -> List[Dict[str, Any]]:
        return [d.to_dict() for d in self._discoveries if d.free_tier]

    def get_recommendations(self) -> List[Dict[str, Any]]:
        recs = []
        for d in self._discoveries:
            avg_score = sum(d.benchmark_scores.values()) / max(len(d.benchmark_scores), 1)
            priority_score = {"high": 30, "medium": 20, "low": 10}.get(d.implementation_priority, 0)
            recs.append({
                "name": d.name, "priority": d.implementation_priority,
                "avg_benchmark": round(avg_score, 1),
                "status": d.status.value, "free_tier": d.free_tier,
                "recommendation_score": round(priority_score + avg_score, 1),
            })
        recs.sort(key=lambda x: x["recommendation_score"], reverse=True)
        return recs

    def get_stats(self) -> Dict[str, Any]:
        by_status = {}
        by_type = {}
        for d in self._discoveries:
            by_status[d.status.value] = by_status.get(d.status.value, 0) + 1
            by_type[d.provider_type] = by_type.get(d.provider_type, 0) + 1
        return {
            "total_discoveries": len(self._discoveries),
            "by_status": by_status,
            "by_type": by_type,
            "verified": sum(1 for d in self._discoveries if d.status == DiscoveryStatus.VERIFIED),
            "free_providers": sum(1 for d in self._discoveries if d.free_tier),
            "high_priority": sum(1 for d in self._discoveries if d.implementation_priority == "high"),
        }
