"""
Skill Registry — unified registry of skills for the platform.

Single source of truth: ``configs/skills.json`` (canonical — no parallel
skill registry). Platform-native skills map to verified modules; external
skill packs are catalogued references (verified=false) or blocked with a
reason. This module is a read-only view over the configuration so SDK,
CLI, and MCP surfaces expose the same registry without duplicating data.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parent.parent / "configs" / "skills.json"


class SkillRegistry:
    """Unified skill registry (read-only view over the canonical config)."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = Path(config_path) if config_path else CONFIG_PATH
        self._skills: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if not self.config_path.exists():
            logger.warning("Skill registry config missing: %s", self.config_path)
            return
        try:
            with open(self.config_path) as f:
                data = json.load(f)
            skills = data.get("skills", data)
            self._skills = {k: dict(v) for k, v in skills.items()}
        except Exception as e:
            logger.warning("Failed to load skill registry config: %s", e)

    def list_skills(self, category: str = "", status: str = "",
                    search: str = "") -> List[Dict[str, Any]]:
        """List skills, optionally filtered by category, status, or text search."""
        results = []
        q = search.lower().strip()
        for skill in self._skills.values():
            if category and skill.get("category", "") != category:
                continue
            if status and skill.get("status", "ready") != status:
                continue
            if q:
                haystack = " ".join(str(skill.get(k, "")) for k in
                                    ("id", "name", "description", "category", "source"))
                if q not in haystack.lower():
                    continue
            results.append(dict(skill))
        return sorted(results, key=lambda s: s.get("id", ""))

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        skill = self._skills.get(skill_id)
        return dict(skill) if skill else None

    def categories(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for skill in self._skills.values():
            cat = skill.get("category", "other")
            counts[cat] = counts.get(cat, 0) + 1
        return dict(sorted(counts.items()))

    def stats(self) -> Dict[str, Any]:
        total = len(self._skills)
        ready = sum(1 for s in self._skills.values() if s.get("status") == "ready")
        blocked = total - ready
        verified = sum(1 for s in self._skills.values() if s.get("verified"))
        return {
            "total_skills": total,
            "ready": ready,
            "blocked": blocked,
            "verified": verified,
            "categories": self.categories(),
            "sources": sorted({
                str(s.get("source", "unknown")) for s in self._skills.values()
            }),
        }

    def ready_skills(self) -> List[Dict[str, Any]]:
        return self.list_skills(status="ready")


_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """Return the process-wide singleton skill registry."""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry
