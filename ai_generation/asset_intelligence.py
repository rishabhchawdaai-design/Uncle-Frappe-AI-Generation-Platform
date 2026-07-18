"""
Asset Intelligence — smart asset management, deduplication,
versioning, metadata indexing, and content organization.
"""
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AssetMetadata:
    asset_id: str = ""
    filename: str = ""
    filepath: str = ""
    asset_type: str = ""  # image, video
    prompt: str = ""
    provider: str = ""
    model: str = ""
    width: int = 0
    height: int = 0
    file_size: int = 0
    content_hash: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1
    parent_id: Optional[str] = None

    def to_dict(self):
        return {
            "asset_id": self.asset_id, "filename": self.filename,
            "filepath": self.filepath, "asset_type": self.asset_type,
            "prompt": self.prompt[:200], "provider": self.provider,
            "model": self.model, "width": self.width, "height": self.height,
            "file_size": self.file_size, "content_hash": self.content_hash,
            "tags": self.tags, "version": self.version,
            "created_at": self.created_at,
        }


class AssetIntelligence:
    """Smart asset management and organization."""

    def __init__(self, storage_dir="./output/assets"):
        self._storage = Path(storage_dir)
        self._storage.mkdir(parents=True, exist_ok=True)
        self._assets: Dict[str, AssetMetadata] = {}
        self._index_file = self._storage / "asset_index.json"
        self._load_index()

    def _load_index(self):
        if self._index_file.exists():
            try:
                data = json.loads(self._index_file.read_text())
                for item in data:
                    asset = AssetMetadata(**{k: v for k, v in item.items() if hasattr(AssetMetadata, k)})
                    self._assets[asset.asset_id] = asset
            except Exception as e:
                logger.warning(f"Failed to load asset index: {e}")

    def _save_index(self):
        data = [a.to_dict() for a in self._assets.values()]
        self._index_file.write_text(json.dumps(data, indent=2))

    def register_asset(self, filepath, prompt="", provider="", model="",
                       width=0, height=0, asset_type="image", tags=None) -> AssetMetadata:
        path = Path(filepath)
        if not path.exists():
            return AssetMetadata()

        content = path.read_bytes()
        content_hash = hashlib.sha256(content).hexdigest()[:16]
        import uuid
        asset_id = f"asset-{content_hash}-{uuid.uuid4().hex[:4]}"

        asset = AssetMetadata(
            asset_id=asset_id, filename=path.name, filepath=str(path),
            asset_type=asset_type, prompt=prompt, provider=provider,
            model=model, width=width, height=height,
            file_size=len(content), content_hash=content_hash,
            tags=tags or [],
        )
        self._assets[asset_id] = asset
        self._save_index()
        return asset

    def _find_by_hash(self, content_hash):
        for a in self._assets.values():
            if a.content_hash == content_hash:
                return a
        return None

    def find_duplicates(self) -> List[List[str]]:
        hash_groups: Dict[str, List[str]] = {}
        for a in self._assets.values():
            if a.content_hash:
                hash_groups.setdefault(a.content_hash, []).append(a.asset_id)
        return [ids for ids in hash_groups.values() if len(ids) > 1]

    def search(self, query="", tags=None, provider="", asset_type=""):
        results = list(self._assets.values())
        if query:
            q = query.lower()
            results = [a for a in results if q in a.prompt.lower() or q in a.filename.lower()]
        if tags:
            results = [a for a in results if any(t in a.tags for t in tags)]
        if provider:
            results = [a for a in results if a.provider == provider]
        if asset_type:
            results = [a for a in results if a.asset_type == asset_type]
        return [a.to_dict() for a in results]

    def get_asset(self, asset_id):
        asset = self._assets.get(asset_id)
        return asset.to_dict() if asset else None

    def delete_asset(self, asset_id):
        if asset_id in self._assets:
            del self._assets[asset_id]
            self._save_index()
            return True
        return False

    def get_stats(self):
        total_size = sum(a.file_size for a in self._assets.values())
        types = {}
        providers = {}
        for a in self._assets.values():
            types[a.asset_type] = types.get(a.asset_type, 0) + 1
            if a.provider:
                providers[a.provider] = providers.get(a.provider, 0) + 1
        duplicates = self.find_duplicates()
        return {
            "total_assets": len(self._assets),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1048576, 2),
            "by_type": types,
            "by_provider": providers,
            "duplicate_groups": len(duplicates),
        }
