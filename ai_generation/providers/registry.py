"""
Provider Registry — auto-discovery, registration, and lookup.
"""
import importlib
import logging
import pkgutil
from typing import Any, Dict, List, Optional, Type

from .base import (
    Provider, ImageProvider, VideoProvider, EditProvider,
    ProviderType, ProviderTier, ProviderStatus,
)

logger = logging.getLogger(__name__)

_registry: Optional["ProviderRegistry"] = None


class ProviderRegistry:
    """Central registry for all AI generation providers."""

    def __init__(self):
        self._providers: Dict[str, Provider] = {}
        self._provider_classes: Dict[str, Type[Provider]] = {}
        self._auto_discovered = False

    def register(self, provider: Provider):
        """Register a provider instance."""
        self._providers[provider.name] = provider
        logger.debug(f"Registered provider: {provider.name} ({provider.provider_type.value})")

    def register_class(self, name: str, cls: Type[Provider]):
        """Register a provider class for lazy instantiation."""
        self._provider_classes[name] = cls

    def get(self, name: str) -> Optional[Provider]:
        return self._providers.get(name)

    def get_provider(self, name: str) -> Optional[Provider]:
        return self._providers.get(name)

    def get_by_type(self, provider_type: ProviderType) -> List[Provider]:
        return [p for p in self._providers.values() if p.provider_type == provider_type]

    def get_available(self, provider_type: Optional[ProviderType] = None) -> List[Provider]:
        providers = self._providers.values()
        if provider_type:
            providers = [p for p in providers if p.provider_type == provider_type]
        return [p for p in providers if p.is_available]

    def get_best_provider(
        self,
        provider_type: ProviderType,
        prefer_free: bool = True,
        prefer_cloud: bool = True,
    ) -> Optional[Provider]:
        """Select the best available provider based on tier, latency, and success rate."""
        candidates = self.get_available(provider_type)
        if not candidates:
            return None

        tier_order = {
            ProviderTier.FREE: 0,
            ProviderTier.COMMUNITY: 1,
            ProviderTier.PAID: 2,
            ProviderTier.ENTERPRISE: 3,
        }

        def score(p: Provider) -> float:
            s = 100.0
            if prefer_free:
                s -= tier_order.get(p.tier, 2) * 10
            if prefer_cloud and p.cloud_first:
                s += 15
            if p.api_key:
                s += 5
            s += p.success_rate * 0.3
            s -= min(p.avg_latency_ms / 1000, 30)
            return s

        candidates.sort(key=score, reverse=True)
        return candidates[0]

    def get_all(self) -> List[Provider]:
        return list(self._providers.values())

    def get_all_stats(self) -> List[Dict[str, Any]]:
        return [p.get_stats() for p in self._providers.values()]

    def list_providers(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": p.name,
                "type": p.provider_type.value,
                "tier": p.tier.value,
                "status": p._status.value,
                "available": p.is_available,
                "models": p.supported_models,
                "cloud_first": p.cloud_first,
            }
            for p in self._providers.values()
        ]

    def auto_discover(self):
        """Auto-discover and register all providers in the providers package."""
        if self._auto_discovered:
            return
        import ai_generation.providers as _pkg
        package_path = _pkg.__path__
        for importer, modname, ispkg in pkgutil.iter_modules(package_path):
            if modname.startswith("_") or modname in ("base", "registry"):
                continue
            try:
                module = importlib.import_module(f"ai_generation.providers.{modname}")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, Provider)
                        and attr is not Provider
                        and attr is not ImageProvider
                        and attr is not VideoProvider
                        and attr is not EditProvider
                        and not getattr(attr, "_abstract", False)
                    ):
                        try:
                            instance = attr()
                            self.register(instance)
                            logger.info(f"Auto-discovered provider: {instance.name}")
                        except Exception as e:
                            logger.debug(f"Could not instantiate {attr_name}: {e}")
            except Exception as e:
                logger.debug(f"Could not import module {modname}: {e}")
        self._auto_discovered = True

    def summary(self) -> Dict[str, Any]:
        types = {}
        for p in self._providers.values():
            t = p.provider_type.value
            types[t] = types.get(t, 0) + 1
        return {
            "total_providers": len(self._providers),
            "by_type": types,
            "available": sum(1 for p in self._providers.values() if p.is_available),
            "free": sum(1 for p in self._providers.values() if p.tier == ProviderTier.FREE),
        }


def get_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
        _registry.auto_discover()
    return _registry
