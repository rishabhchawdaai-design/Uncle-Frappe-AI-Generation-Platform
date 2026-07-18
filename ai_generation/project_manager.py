"""
Project Management Layer — projects contain characters, locations, props,
style guides, prompt history, generated assets, versions, workflows, benchmarks.
"""
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class StyleGuide:
    name: str = ""
    color_palette: List[str] = field(default_factory=list)
    typography: str = ""
    mood: str = ""
    reference_images: List[str] = field(default_factory=list)
    prompt_prefix: str = ""
    prompt_suffix: str = ""
    negative_prompt: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectAsset:
    asset_id: str = ""
    name: str = ""
    asset_type: str = ""
    filepath: str = ""
    prompt: str = ""
    provider: str = ""
    generation_params: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Project:
    project_id: str = ""
    name: str = ""
    description: str = ""
    characters: List[Dict[str, Any]] = field(default_factory=list)
    locations: List[Dict[str, Any]] = field(default_factory=list)
    props: List[Dict[str, Any]] = field(default_factory=list)
    style_guide: Optional[StyleGuide] = None
    prompt_history: List[Dict[str, Any]] = field(default_factory=list)
    assets: List[ProjectAsset] = field(default_factory=list)
    workflows: List[Dict[str, Any]] = field(default_factory=list)
    benchmark_history: List[Dict[str, Any]] = field(default_factory=list)
    versions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if not self.project_id:
            self.project_id = "proj-" + uuid.uuid4().hex[:8]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "characters_count": len(self.characters),
            "locations_count": len(self.locations),
            "props_count": len(self.props),
            "assets_count": len(self.assets),
            "workflows_count": len(self.workflows),
            "prompt_history_count": len(self.prompt_history),
            "benchmark_count": len(self.benchmark_history),
            "versions_count": len(self.versions),
            "has_style_guide": self.style_guide is not None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ProjectManager:
    """Manage creative projects with all associated data."""

    def __init__(self, storage_dir: str = "./data/projects"):
        self._storage = Path(storage_dir)
        self._storage.mkdir(parents=True, exist_ok=True)
        self._projects: Dict[str, Project] = {}
        self._index_file = self._storage / "projects.json"
        self._load()

    def _load(self):
        if self._index_file.exists():
            try:
                data = json.loads(self._index_file.read_text())
                for item in data:
                    p = Project(**{k: v for k, v in item.items() if hasattr(Project, k)})
                    self._projects[p.project_id] = p
            except Exception as e:
                logger.warning(f"Failed to load projects: {e}")

    def _save(self):
        data = [p.to_dict() for p in self._projects.values()]
        self._index_file.write_text(json.dumps(data, indent=2))

    def create_project(self, name: str, description: str = "", **kwargs) -> Project:
        project = Project(name=name, description=description, **kwargs)
        self._projects[project.project_id] = project
        self._save()
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        return self._projects.get(project_id)

    def find_project(self, name: str) -> Optional[Project]:
        for p in self._projects.values():
            if p.name.lower() == name.lower():
                return p
        return None

    def list_projects(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._projects.values()]

    def delete_project(self, project_id: str) -> bool:
        if project_id in self._projects:
            del self._projects[project_id]
            self._save()
            return True
        return False

    def add_character(self, project_id: str, character: Dict[str, Any]) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False
        project.characters.append(character)
        project.updated_at = datetime.now().isoformat()
        self._save()
        return True

    def add_location(self, project_id: str, location: Dict[str, Any]) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False
        project.locations.append(location)
        project.updated_at = datetime.now().isoformat()
        self._save()
        return True

    def add_prop(self, project_id: str, prop: Dict[str, Any]) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False
        project.props.append(prop)
        project.updated_at = datetime.now().isoformat()
        self._save()
        return True

    def set_style_guide(self, project_id: str, style_guide: StyleGuide) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False
        project.style_guide = style_guide
        project.updated_at = datetime.now().isoformat()
        self._save()
        return True

    def add_asset(self, project_id: str, asset: ProjectAsset) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False
        project.assets.append(asset)
        project.updated_at = datetime.now().isoformat()
        self._save()
        return True

    def add_prompt_history(self, project_id: str, entry: Dict[str, Any]) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False
        project.prompt_history.append(entry)
        project.updated_at = datetime.now().isoformat()
        self._save()
        return True

    def add_workflow(self, project_id: str, workflow: Dict[str, Any]) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False
        project.workflows.append(workflow)
        project.updated_at = datetime.now().isoformat()
        self._save()
        return True

    def add_benchmark(self, project_id: str, benchmark: Dict[str, Any]) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False
        project.benchmark_history.append(benchmark)
        project.updated_at = datetime.now().isoformat()
        self._save()
        return True

    def create_version(self, project_id: str, label: str = "", notes: str = "") -> Optional[Dict[str, Any]]:
        project = self._projects.get(project_id)
        if not project:
            return None
        version = {
            "version_id": f"v{len(project.versions) + 1}",
            "label": label or f"Version {len(project.versions) + 1}",
            "notes": notes,
            "snapshot": project.to_dict(),
            "created_at": datetime.now().isoformat(),
        }
        project.versions.append(version)
        project.updated_at = datetime.now().isoformat()
        self._save()
        return version

    def get_project_context(self, project_id: str) -> Dict[str, Any]:
        """Get full project context for generation."""
        project = self._projects.get(project_id)
        if not project:
            return {}
        return {
            "project_name": project.name,
            "characters": [c.get("name", "") for c in project.characters],
            "locations": [l.get("name", "") for l in project.locations],
            "style_guide": project.style_guide.__dict__ if project.style_guide else None,
            "recent_prompts": [p.get("prompt", "") for p in project.prompt_history[-5:]],
        }

    def get_stats(self) -> Dict[str, Any]:
        total_assets = sum(len(p.assets) for p in self._projects.values())
        total_chars = sum(len(p.characters) for p in self._projects.values())
        return {
            "total_projects": len(self._projects),
            "total_assets": total_assets,
            "total_characters": total_chars,
        }
