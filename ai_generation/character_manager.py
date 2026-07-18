"""
Character Consistency Engine — identity locking, reference images, facial consistency,
clothing/hairstyle/environment continuity, and prompt continuity across generations.
"""
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CharacterAppearance:
    hair_color: str = ""
    hair_style: str = ""
    eye_color: str = ""
    skin_tone: str = ""
    height: str = ""
    build: str = ""
    distinguishing_features: List[str] = field(default_factory=list)


@dataclass
class CharacterClothing:
    name: str = ""
    description: str = ""
    colors: List[str] = field(default_factory=list)
    style: str = ""
    season: str = ""


@dataclass
class CharacterProfile:
    character_id: str = ""
    name: str = ""
    description: str = ""
    personality: str = ""
    role: str = ""
    appearance: CharacterAppearance = field(default_factory=CharacterAppearance)
    clothing: List[CharacterClothing] = field(default_factory=list)
    reference_images: List[str] = field(default_factory=list)
    prompt_base: str = ""
    prompt_lock: str = ""
    negative_prompt: str = ""
    style_tokens: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1

    def __post_init__(self):
        if not self.character_id:
            self.character_id = "char-" + uuid.uuid4().hex[:8]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_id": self.character_id,
            "name": self.name,
            "description": self.description,
            "personality": self.personality,
            "role": self.role,
            "appearance": self.appearance.__dict__,
            "clothing": [c.__dict__ for c in self.clothing],
            "reference_images": self.reference_images,
            "prompt_base": self.prompt_base,
            "prompt_lock": self.prompt_lock,
            "negative_prompt": self.negative_prompt,
            "style_tokens": self.style_tokens,
            "version": self.version,
            "created_at": self.created_at,
        }

    def generate_consistent_prompt(self, scene_description: str = "", outfit: str = "") -> str:
        """Generate a prompt that maintains character consistency."""
        parts = [self.prompt_base] if self.prompt_base else []

        if self.appearance.hair_color:
            parts.append(f"{self.appearance.hair_color} hair")
        if self.appearance.hair_style:
            parts.append(self.appearance.hair_style)
        if self.appearance.eye_color:
            parts.append(f"{self.appearance.eye_color} eyes")
        if self.appearance.skin_tone:
            parts.append(f"{self.appearance.skin_tone} skin")
        if self.appearance.distinguishing_features:
            parts.append(", ".join(self.appearance.distinguishing_features))

        if outfit:
            for c in self.clothing:
                if c.name.lower() == outfit.lower():
                    parts.append(c.description or c.name)
                    break
        elif self.clothing:
            parts.append(self.clothing[0].description or self.clothing[0].name)

        if scene_description:
            parts.append(scene_description)

        if self.style_tokens:
            parts.append(", ".join(self.style_tokens))

        return ", ".join(parts) if parts else self.description


@dataclass
class ContinuityCheck:
    character_id: str = ""
    aspect: str = ""
    expected: str = ""
    actual: str = ""
    consistent: bool = False
    confidence: float = 0.0
    notes: str = ""


class CharacterManager:
    """Manage character profiles and ensure consistency across generations."""

    def __init__(self, storage_dir: str = "./data/characters"):
        self._storage = Path(storage_dir)
        self._storage.mkdir(parents=True, exist_ok=True)
        self._characters: Dict[str, CharacterProfile] = {}
        self._index_file = self._storage / "characters.json"
        self._load()

    def _load(self):
        if self._index_file.exists():
            try:
                data = json.loads(self._index_file.read_text())
                for item in data:
                    char = CharacterProfile(**{k: v for k, v in item.items() if hasattr(CharacterProfile, k)})
                    self._characters[char.character_id] = char
            except Exception as e:
                logger.warning(f"Failed to load characters: {e}")

    def _save(self):
        data = [c.to_dict() for c in self._characters.values()]
        self._index_file.write_text(json.dumps(data, indent=2))

    def create_character(self, name: str, description: str = "", **kwargs) -> CharacterProfile:
        char = CharacterProfile(name=name, description=description, **kwargs)
        self._characters[char.character_id] = char
        self._save()
        return char

    def get_character(self, character_id: str) -> Optional[CharacterProfile]:
        return self._characters.get(character_id)

    def find_character(self, name: str) -> Optional[CharacterProfile]:
        for char in self._characters.values():
            if char.name.lower() == name.lower():
                return char
        return None

    def list_characters(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self._characters.values()]

    def update_character(self, character_id: str, **updates) -> Optional[CharacterProfile]:
        char = self._characters.get(character_id)
        if not char:
            return None
        for key, value in updates.items():
            if hasattr(char, key):
                setattr(char, key, value)
        char.version += 1
        self._save()
        return char

    def add_clothing(self, character_id: str, name: str, description: str = "", **kwargs) -> bool:
        char = self._characters.get(character_id)
        if not char:
            return False
        char.clothing.append(CharacterClothing(name=name, description=description, **kwargs))
        char.version += 1
        self._save()
        return True

    def add_reference_image(self, character_id: str, image_path: str) -> bool:
        char = self._characters.get(character_id)
        if not char:
            return False
        char.reference_images.append(image_path)
        self._save()
        return True

    def delete_character(self, character_id: str) -> bool:
        if character_id in self._characters:
            del self._characters[character_id]
            self._save()
            return True
        return False

    def get_consistency_prompt(self, character_id: str, scene: str = "", outfit: str = "") -> str:
        char = self._characters.get(character_id)
        if not char:
            return ""
        return char.generate_consistent_prompt(scene, outfit)

    def check_continuity(self, character_id: str, generated_metadata: Dict[str, Any]) -> List[ContinuityCheck]:
        char = self._characters.get(character_id)
        if not char:
            return []
        checks = []
        if char.appearance.hair_color:
            checks.append(ContinuityCheck(
                character_id=character_id, aspect="hair_color",
                expected=char.appearance.hair_color,
                actual=generated_metadata.get("hair_color", "unknown"),
                consistent=char.appearance.hair_color.lower() in generated_metadata.get("hair_color", "").lower(),
            ))
        if char.appearance.eye_color:
            checks.append(ContinuityCheck(
                character_id=character_id, aspect="eye_color",
                expected=char.appearance.eye_color,
                actual=generated_metadata.get("eye_color", "unknown"),
                consistent=char.appearance.eye_color.lower() in generated_metadata.get("eye_color", "").lower(),
            ))
        return checks

    def get_stats(self) -> Dict[str, Any]:
        total_clothing = sum(len(c.clothing) for c in self._characters.values())
        total_refs = sum(len(c.reference_images) for c in self._characters.values())
        return {
            "total_characters": len(self._characters),
            "total_clothing_items": total_clothing,
            "total_reference_images": total_refs,
        }
