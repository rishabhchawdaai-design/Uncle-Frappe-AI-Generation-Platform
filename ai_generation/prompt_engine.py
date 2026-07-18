"""
Prompt Engine — intelligent prompt enhancement, templates, optimization,
negative prompt generation, style injection.
"""
import re
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    name: str
    template: str
    variables: List[str] = field(default_factory=list)
    category: str = "general"
    tags: List[str] = field(default_factory=list)


@dataclass
class PromptEnhancement:
    original: str
    enhanced: str
    negative_prompt: str = ""
    style: str = ""
    techniques_applied: List[str] = field(default_factory=list)
    confidence: float = 0.0


STYLE_PRESETS = {
    "photorealistic": {
        "suffix": ", photorealistic, high detail, 8k uhd, DSLR, film grain, sharp focus",
        "negative": "cartoon, anime, drawing, painting, sketch, illustration, low quality, blurry",
    },
    "cinematic": {
        "suffix": ", cinematic lighting, dramatic shadows, movie still, anamorphic lens, bokeh",
        "negative": "flat lighting, overexposed, underexposed, cartoon, anime",
    },
    "anime": {
        "suffix": ", anime style, vibrant colors, detailed, studio ghibli, makoto shinkai",
        "negative": "photorealistic, 3d render, ugly, deformed, blurry, low quality",
    },
    "digital_art": {
        "suffix": ", digital art, concept art, artstation, trending, highly detailed",
        "negative": "photo, real life, blurry, low quality, watermark, text",
    },
    "oil_painting": {
        "suffix": ", oil painting, masterpiece, classical art, thick brushstrokes, rich colors",
        "negative": "digital, photo, modern, low quality, blurry",
    },
    "watercolor": {
        "suffix": ", watercolor painting, soft edges, flowing colors, artistic, delicate",
        "negative": "sharp edges, digital, photo, harsh colors, low quality",
    },
    "3d_render": {
        "suffix": ", 3d render, octane render, unreal engine 5, ray tracing, volumetric lighting",
        "negative": "2d, flat, cartoon, low poly, low quality, blurry",
    },
    "minimalist": {
        "suffix": ", minimalist, clean design, simple, elegant, white space",
        "negative": "cluttered, busy, complex, noisy, low quality",
    },
    "product_photo": {
        "suffix": ", product photography, studio lighting, white background, professional, high detail",
        "negative": "cluttered background, blurry, low quality, watermark",
    },
    "food_photo": {
        "suffix": ", food photography, appetizing, warm lighting, shallow depth of field, top-down",
        "negative": "unappetizing, cold lighting, blurry, low quality",
    },
    "architectural": {
        "suffix": ", architectural photography, wide angle, detailed, grand, symmetrical",
        "negative": "tilted, blurry, low quality, distorted",
    },
    "portrait": {
        "suffix": ", portrait photography, soft lighting, bokeh, sharp focus on eyes, natural skin",
        "negative": "unflattering lighting, harsh shadows, blurry, low quality, deformed face",
    },
}

QUALITY_MODIFIERS = {
    "high": "masterpiece, best quality, highly detailed, sharp, high resolution",
    "medium": "good quality, detailed, clear",
    "fast": "simple, clean, basic detail",
}


class PromptEngine:
    """Intelligent prompt enhancement and optimization engine."""

    def __init__(self, config=None):
        self.config = config or {}
        self._templates: Dict[str, PromptTemplate] = {}
        self._history: List[Dict[str, Any]] = []
        self._register_defaults()

    def _register_defaults(self):
        self.register_template(PromptTemplate(
            name="product_showcase",
            template="{subject} on {surface}, {lighting} lighting, {style} style, product photography, high detail",
            variables=["subject", "surface", "lighting", "style"],
            category="product", tags=["product", "e-commerce"],
        ))
        self.register_template(PromptTemplate(
            name="restaurant_menu",
            template="{dish_name}, {cuisine} cuisine, {presentation}, food photography, appetizing, warm lighting",
            variables=["dish_name", "cuisine", "presentation", "style"],
            category="food", tags=["food", "restaurant", "menu"],
        ))
        self.register_template(PromptTemplate(
            name="brand_visual",
            template="{brand_name} brand identity, {color_palette}, {visual_style}, professional design, clean",
            variables=["brand_name", "color_palette", "visual_style"],
            category="branding", tags=["brand", "logo", "identity"],
        ))
        self.register_template(PromptTemplate(
            name="social_media",
            template="{topic}, eye-catching design, vibrant colors, {platform} style, engaging, trending",
            variables=["topic", "platform"],
            category="social", tags=["social", "instagram", "marketing"],
        ))
        self.register_template(PromptTemplate(
            name="scene_description",
            template="{scene}, {time_of_day} lighting, {weather}, {mood} atmosphere, detailed environment, cinematic",
            variables=["scene", "time_of_day", "weather", "mood"],
            category="scene", tags=["scene", "environment"],
        ))
        self.register_template(PromptTemplate(
            name="character_concept",
            template="{character}, {age} {gender}, {expression}, {clothing}, concept art, detailed, {style}",
            variables=["character", "age", "gender", "expression", "clothing", "style"],
            category="character", tags=["character", "concept"],
        ))

    def register_template(self, template: PromptTemplate):
        self._templates[template.name] = template

    def get_template(self, name: str):
        return self._templates.get(name)

    def list_templates(self):
        return [
            {"name": t.name, "category": t.category, "tags": t.tags, "variables": t.variables}
            for t in self._templates.values()
        ]

    def render_template(self, name: str, **variables) -> str:
        template = self._templates.get(name)
        if not template:
            return ""
        result = template.template
        for key, value in variables.items():
            result = result.replace("{" + key + "}", str(value))
        return result

    def enhance(self, prompt, style="", quality="high", enhance_negative=True, add_quality_modifiers=True):
        enhanced = prompt.strip()
        techniques = []
        negative = ""

        if add_quality_modifiers and quality in QUALITY_MODIFIERS:
            enhanced = enhanced + ", " + QUALITY_MODIFIERS[quality]
            techniques.append("quality:" + quality)

        if style and style in STYLE_PRESETS:
            preset = STYLE_PRESETS[style]
            enhanced = enhanced + preset["suffix"]
            negative = preset["negative"]
            techniques.append("style:" + style)
        elif style:
            enhanced = enhanced + ", " + style + " style"
            techniques.append("style_custom:" + style)

        enhanced = self._fix_prompt_structure(enhanced)
        techniques.append("structure_fix")

        if enhance_negative:
            base_negative = "low quality, blurry, watermark, text, logo, bad anatomy, deformed"
            negative = (base_negative + ", " + negative) if negative else base_negative
            techniques.append("negative_prompt")

        return PromptEnhancement(
            original=prompt, enhanced=enhanced, negative_prompt=negative,
            style=style, techniques_applied=techniques,
            confidence=min(len(techniques) * 0.2, 1.0),
        )

    def _fix_prompt_structure(self, prompt):
        prompt = re.sub(r'\s+', ' ', prompt).strip()
        prompt = prompt.rstrip(', ')
        parts = [p.strip() for p in prompt.split(',')]
        seen = set()
        deduped = []
        for part in parts:
            key = part.lower().strip()
            if key and key not in seen:
                seen.add(key)
                deduped.append(part)
        return ', '.join(deduped)

    def generate_negative(self, prompt, style="", extra_avoid=None):
        base = "low quality, blurry, watermark, text, logo, bad anatomy, deformed, disfigured"
        style_neg = ""
        if style and style in STYLE_PRESETS:
            style_neg = STYLE_PRESETS[style].get("negative", "")
        parts = [base]
        if style_neg:
            parts.append(style_neg)
        if extra_avoid:
            parts.append(", ".join(extra_avoid))
        return ", ".join(parts)

    def analyze_prompt(self, prompt):
        word_count = len(prompt.split())
        has_quality = any(w in prompt.lower() for w in ["masterpiece", "high quality", "detailed", "sharp"])
        suggests_style = any(s in prompt.lower() for s in STYLE_PRESETS.keys())
        matched = [s for s in STYLE_PRESETS if s in prompt.lower()] if suggests_style else []

        suggestions = []
        if word_count < 5:
            suggestions.append("Prompt is very short - add details about composition, lighting, style")
        if not has_quality:
            suggestions.append("Add quality modifiers like 'highly detailed', 'sharp', '8k'")
        if matched:
            suggestions.append("Detected style keywords: " + str(matched) + ". Use style parameter")

        return {
            "word_count": word_count,
            "has_quality_modifiers": has_quality,
            "suggested_style": matched[0] if matched else None,
            "suggestions": suggestions,
            "complexity": "simple" if word_count < 8 else "moderate" if word_count < 20 else "complex",
        }

    def get_stats(self):
        return {
            "total_enhancements": len(self._history),
            "templates_count": len(self._templates),
            "style_presets": list(STYLE_PRESETS.keys()),
        }
