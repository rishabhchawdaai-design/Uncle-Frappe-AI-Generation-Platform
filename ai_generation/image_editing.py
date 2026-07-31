"""
Image Editing Engine — unified interface for all image editing operations.
Supports: img2img, inpainting, outpainting, background removal/replacement,
relighting, object removal/insertion, style transfer, face/identity preservation,
upscaling, and restoration.
"""
import hashlib
import logging
import time
import base64
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class EditOperation(str, Enum):
    IMG2IMG = "img2img"
    INPAINTING = "inpainting"
    OUTPAINTING = "outpainting"
    BACKGROUND_REMOVAL = "background_removal"
    BACKGROUND_REPLACEMENT = "background_replacement"
    RELIGHTING = "relighting"
    OBJECT_REMOVAL = "object_removal"
    OBJECT_INSERTION = "object_insertion"
    STYLE_TRANSFER = "style_transfer"
    FACE_PRESERVATION = "face_preservation"
    FACE_RESTORATION = "face_restoration"
    IDENTITY_PRESERVATION = "identity_preservation"
    UPSCALE = "upscale"
    RESTORATION = "restoration"


class EditStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


@dataclass
class EditResult:
    operation: EditOperation = EditOperation.IMG2IMG
    provider: str = ""
    status: EditStatus = EditStatus.PENDING
    request_id: str = ""
    input_path: str = ""
    output_path: str = ""
    output_url: str = ""
    output_bytes: Optional[bytes] = None
    output_format: str = "png"
    width: int = 0
    height: int = 0
    latency_ms: float = 0.0
    cost_estimate: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the edit result to a dictionary."""
        return {
            "operation": self.operation.value,
            "provider": self.provider,
            "status": self.status.value,
            "request_id": self.request_id,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "output_url": self.output_url,
            "output_format": self.output_format,
            "width": self.width,
            "height": self.height,
            "latency_ms": self.latency_ms,
            "cost_estimate": self.cost_estimate,
            "error": self.error,
            "created_at": self.created_at,
        }


# Provider capability mapping for editing operations
PROVIDER_EDIT_CAPABILITIES = {
    "stability": {
        EditOperation.IMG2IMG: {"supported": True, "model": "sd3-medium"},
        EditOperation.INPAINTING: {"supported": True, "model": "sd3-medium"},
        EditOperation.OUTPAINTING: {"supported": True, "model": "sd3-medium"},
        EditOperation.STYLE_TRANSFER: {"supported": True, "model": "sd3-medium"},
        EditOperation.UPSCALE: {"supported": True, "model": "sd3-medium"},
        EditOperation.BACKGROUND_REMOVAL: {"supported": False},
        EditOperation.RELIGHTING: {"supported": False},
        EditOperation.OBJECT_REMOVAL: {"supported": True, "model": "sd3-medium"},
        EditOperation.OBJECT_INSERTION: {"supported": True, "model": "sd3-medium"},
        EditOperation.FACE_PRESERVATION: {"supported": False},
        EditOperation.IDENTITY_PRESERVATION: {"supported": False},
        EditOperation.RESTORATION: {"supported": False},
        EditOperation.BACKGROUND_REPLACEMENT: {"supported": True, "model": "sd3-medium"},
        EditOperation.FACE_RESTORATION: {"supported": True, "model": "gfpgan"},
    },
    "replicate": {
        EditOperation.IMG2IMG: {"supported": True, "model": "stability-ai/sdxl"},
        EditOperation.INPAINTING: {"supported": True, "model": "stability-ai/sdxl"},
        EditOperation.STYLE_TRANSFER: {"supported": True, "model": "tencentarc/photomaker"},
        EditOperation.UPSCALE: {"supported": True, "model": "nightmareai/real-esrgan"},
        EditOperation.BACKGROUND_REMOVAL: {"supported": True, "model": "cjwbw/rembg"},
        EditOperation.FACE_PRESERVATION: {"supported": True, "model": "tencentarc/photomaker"},
        EditOperation.IDENTITY_PRESERVATION: {"supported": True, "model": "tencentarc/photomaker"},
        EditOperation.RESTORATION: {"supported": True, "model": "nightmareai/real-esrgan"},
        EditOperation.FACE_RESTORATION: {"supported": True, "model": "tencentarc/gfpgan"},
    },
    "fal": {
        EditOperation.IMG2IMG: {"supported": True, "model": "fal-ai/flux/dev/image-to-image"},
        EditOperation.INPAINTING: {"supported": True, "model": "fal-ai/flux/dev/inpainting"},
        EditOperation.UPSCALE: {"supported": True, "model": "fal-ai/real-esrgan"},
        EditOperation.FACE_RESTORATION: {"supported": True, "model": "fal-ai/gfpgan"},
    },
    "pollinations": {
        EditOperation.IMG2IMG: {"supported": False},
        EditOperation.STYLE_TRANSFER: {"supported": False},
    },
}


class EditProvider:
    """Base class for image editing providers."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the provider with its name and configuration."""
        self.name = name
        self.config = config or {}
        self._capabilities = PROVIDER_EDIT_CAPABILITIES.get(name, {})
        self._success_count = 0
        self._error_count = 0
        self._total_latency_ms = 0.0

    def supports(self, operation: EditOperation) -> bool:
        """Return whether this provider supports the given edit operation."""
        cap = self._capabilities.get(operation, {})
        return cap.get("supported", False)

    def get_model(self, operation: EditOperation) -> str:
        """Return the model name used by this provider for an operation."""
        cap = self._capabilities.get(operation, {})
        return cap.get("model", "")

    def record_success(self, latency_ms: float):
        """Record a successful edit for statistics."""
        self._success_count += 1
        self._total_latency_ms += latency_ms

    def record_error(self):
        """Record a failed edit for statistics."""
        self._error_count += 1

    async def execute_edit(
        self,
        operation: EditOperation,
        input_path: str,
        prompt: str = "",
        strength: float = 0.75,
        mask_path: str = "",
        width: int = 1024,
        height: int = 1024,
        **kwargs,
    ) -> EditResult:
        """Execute an edit operation. Override in subclasses for real API calls."""
        request_id = f"edit-{int(time.time() * 1000)}-{hashlib.sha256(operation.value.encode()).hexdigest()[:6]}"
        return EditResult(
            operation=operation,
            provider=self.name,
            status=EditStatus.UNSUPPORTED,
            request_id=request_id,
            input_path=input_path,
            error=f"Provider {self.name} does not support {operation.value}",
        )


class StabilityEditProvider(EditProvider):
    """Stability AI image editing via their API."""

    def __init__(self, config=None):
        """Initialize the Stability provider with its API key."""
        super().__init__("stability", config)
        import os
        self._api_key = self.config.get("api_key") or os.environ.get("STABILITY_API_KEY", "")

    async def execute_edit(self, operation, input_path, prompt="", strength=0.75,
                           mask_path="", width=1024, height=1024, **kwargs) -> EditResult:
        request_id = f"edit-{int(time.time() * 1000)}-{hashlib.sha256(operation.value.encode()).hexdigest()[:6]}"
        start = time.time()

        if not self._api_key:
            return EditResult(
                operation=operation, provider=self.name, status=EditStatus.FAILED,
                request_id=request_id, input_path=input_path,
                error="No STABILITY_API_KEY set",
            )

        if not self.supports(operation):
            return EditResult(
                operation=operation, provider=self.name, status=EditStatus.UNSUPPORTED,
                request_id=request_id, input_path=input_path,
                error=f"Stability does not support {operation.value}",
            )

        model = self.get_model(operation)
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                path = Path(input_path)
                if path.exists():
                    files = {"image": (path.name, path.read_bytes(), "image/png")}
                else:
                    return EditResult(
                        operation=operation, provider=self.name, status=EditStatus.FAILED,
                        request_id=request_id, input_path=input_path,
                        error=f"File not found: {input_path}",
                    )

                data = {"output_format": "png"}
                if prompt:
                    data["prompt"] = prompt
                if strength != 0.75:
                    data["strength"] = str(strength)
                if mask_path and Path(mask_path).exists():
                    files["mask"] = ("mask.png", Path(mask_path).read_bytes(), "image/png")

                url = f"https://api.stability.ai/v2beta/stable-image/edit/{operation.value}"
                response = await client.post(
                    url, files=files, data=data,
                    headers={"Authorization": f"Bearer {self._api_key}", "Accept": "image/*"},
                )
                latency_ms = round((time.time() - start) * 1000, 1)

                if response.status_code == 200:
                    self.record_success(latency_ms)
                    return EditResult(
                        operation=operation, provider=self.name, status=EditStatus.COMPLETED,
                        request_id=request_id, input_path=input_path,
                        output_bytes=response.content, output_format="png",
                        width=width, height=height, latency_ms=latency_ms,
                    )
                else:
                    self.record_error()
                    return EditResult(
                        operation=operation, provider=self.name, status=EditStatus.FAILED,
                        request_id=request_id, input_path=input_path,
                        error=f"HTTP {response.status_code}: {response.text[:200]}",
                        latency_ms=latency_ms,
                    )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            self.record_error()
            return EditResult(
                operation=operation, provider=self.name, status=EditStatus.FAILED,
                request_id=request_id, input_path=input_path, error=str(e)[:200],
                latency_ms=latency_ms,
            )


class ReplicateEditProvider(EditProvider):
    """Replicate-based image editing."""

    def __init__(self, config=None):
        """Initialize the Replicate provider with its API token."""
        super().__init__("replicate", config)
        import os
        self._api_key = self.config.get("api_key") or os.environ.get("REPLICATE_API_TOKEN", "")

    async def execute_edit(self, operation, input_path, prompt="", strength=0.75,
                           mask_path="", width=1024, height=1024, **kwargs) -> EditResult:
        request_id = f"edit-{int(time.time() * 1000)}-{hashlib.sha256(operation.value.encode()).hexdigest()[:6]}"
        start = time.time()

        if not self._api_key:
            return EditResult(
                operation=operation, provider=self.name, status=EditStatus.FAILED,
                request_id=request_id, input_path=input_path,
                error="No REPLICATE_API_TOKEN set",
            )

        if not self.supports(operation):
            return EditResult(
                operation=operation, provider=self.name, status=EditStatus.UNSUPPORTED,
                request_id=request_id, input_path=input_path,
                error=f"Replicate does not support {operation.value}",
            )

        model = self.get_model(operation)
        input_data = {}
        if prompt:
            input_data["prompt"] = prompt
        if input_path and Path(input_path).exists():
            input_data["image"] = input_path
        if mask_path and Path(mask_path).exists():
            input_data["mask"] = mask_path

        try:
            async with httpx.AsyncClient(timeout=180) as client:
                response = await client.post(
                    "https://api.replicate.com/v1/predictions",
                    json={"version": model, "input": input_data},
                    headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
                )
                latency_ms = round((time.time() - start) * 1000, 1)

                if response.status_code in (200, 201):
                    data = response.json()
                    if data.get("status") == "succeeded":
                        output = data.get("output", [])
                        output_url = output if isinstance(output, str) else (output[0] if output else "")
                        self.record_success(latency_ms)
                        return EditResult(
                            operation=operation, provider=self.name, status=EditStatus.COMPLETED,
                            request_id=request_id, input_path=input_path, output_url=output_url,
                            latency_ms=latency_ms,
                        )
                    else:
                        self.record_error()
                        return EditResult(
                            operation=operation, provider=self.name, status=EditStatus.FAILED,
                            request_id=request_id, input_path=input_path,
                            error=f"Prediction status: {data.get('status')}",
                            latency_ms=latency_ms,
                        )
                else:
                    self.record_error()
                    return EditResult(
                        operation=operation, provider=self.name, status=EditStatus.FAILED,
                        request_id=request_id, input_path=input_path,
                        error=f"HTTP {response.status_code}: {response.text[:200]}",
                        latency_ms=latency_ms,
                    )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 1)
            self.record_error()
            return EditResult(
                operation=operation, provider=self.name, status=EditStatus.FAILED,
                request_id=request_id, input_path=input_path, error=str(e)[:200],
                latency_ms=latency_ms,
            )


class ImageEditingEngine:
    """Unified image editing engine with provider failover."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the engine and register all configured providers."""
        self.config = config or {}
        self._providers: Dict[str, EditProvider] = {}
        self._history: List[EditResult] = []
        self._init_providers()

    def _init_providers(self):
        """Register the built-in stability and replicate providers."""
        self._providers["stability"] = StabilityEditProvider(self.config.get("stability", {}))
        self._providers["replicate"] = ReplicateEditProvider(self.config.get("replicate", {}))

    def get_providers_for_operation(self, operation: EditOperation) -> List[str]:
        """Get providers that support a given operation, ordered by preference."""
        supported = []
        for name, provider in self._providers.items():
            if provider.supports(operation):
                supported.append(name)
        return supported

    def get_all_operations(self) -> List[Dict[str, Any]]:
        """List all supported operations and which providers support them."""
        operations = []
        for op in EditOperation:
            providers = self.get_providers_for_operation(op)
            operations.append({
                "operation": op.value,
                "supported_providers": providers,
                "supported": len(providers) > 0,
            })
        return operations

    async def edit(
        self,
        operation: EditOperation,
        input_path: str,
        prompt: str = "",
        strength: float = 0.75,
        mask_path: str = "",
        width: int = 1024,
        height: int = 1024,
        preferred_provider: Optional[str] = None,
        **kwargs,
    ) -> EditResult:
        """Execute an image edit with automatic provider failover."""
        providers_to_try = []
        if preferred_provider and preferred_provider in self._providers:
            if self._providers[preferred_provider].supports(operation):
                providers_to_try.append(preferred_provider)

        for name in self.get_providers_for_operation(operation):
            if name not in providers_to_try:
                providers_to_try.append(name)

        if not providers_to_try:
            return EditResult(
                operation=operation, status=EditStatus.UNSUPPORTED,
                input_path=input_path,
                error=f"No provider supports {operation.value}",
            )

        for provider_name in providers_to_try:
            provider = self._providers[provider_name]
            result = await provider.execute_edit(
                operation=operation, input_path=input_path, prompt=prompt,
                strength=strength, mask_path=mask_path, width=width, height=height, **kwargs,
            )
            if result.status in (EditStatus.COMPLETED,):
                self._history.append(result)
                return result
            if result.status == EditStatus.UNSUPPORTED:
                continue
            logger.warning(f"Provider {provider_name} failed for {operation.value}: {result.error}")

        self._history.append(result)
        return result

    async def img2img(self, input_path, prompt, strength=0.75, **kwargs):
        """Run an image-to-image edit on the input file."""
        return await self.edit(EditOperation.IMG2IMG, input_path, prompt, strength, **kwargs)

    async def inpaint(self, input_path, mask_path, prompt, **kwargs):
        """Run an inpainting edit masked to the given region."""
        return await self.edit(EditOperation.INPAINTING, input_path, prompt, mask_path=mask_path, **kwargs)

    async def outpaint(self, input_path, prompt, **kwargs):
        """Run an outpainting edit beyond the input boundaries."""
        return await self.edit(EditOperation.OUTPAINTING, input_path, prompt, **kwargs)

    async def remove_background(self, input_path, **kwargs):
        """Remove the background from the input image."""
        return await self.edit(EditOperation.BACKGROUND_REMOVAL, input_path, **kwargs)

    async def replace_background(self, input_path, prompt, **kwargs):
        """Replace the background of the input image."""
        return await self.edit(EditOperation.BACKGROUND_REPLACEMENT, input_path, prompt, **kwargs)

    async def style_transfer(self, input_path, prompt, **kwargs):
        """Transfer the prompted style onto the input image."""
        return await self.edit(EditOperation.STYLE_TRANSFER, input_path, prompt, **kwargs)

    async def upscale(self, input_path, **kwargs):
        """Upscale the input image."""
        return await self.edit(EditOperation.UPSCALE, input_path, **kwargs)

    async def remove_object(self, input_path, prompt, **kwargs):
        """Remove the prompted object from the input image."""
        return await self.edit(EditOperation.OBJECT_REMOVAL, input_path, prompt, **kwargs)

    async def insert_object(self, input_path, prompt, **kwargs):
        """Insert the prompted object into the input image."""
        return await self.edit(EditOperation.OBJECT_INSERTION, input_path, prompt, **kwargs)

    async def relight(self, input_path, prompt, **kwargs):
        """Relight the input image according to the prompt."""
        return await self.edit(EditOperation.RELIGHTING, input_path, prompt, **kwargs)

    async def preserve_face(self, input_path, prompt, **kwargs):
        """Run a face preservation edit on the input image."""
        return await self.edit(EditOperation.FACE_PRESERVATION, input_path, prompt, **kwargs)

    async def restore(self, input_path, **kwargs):
        """Restore the input image."""
        return await self.edit(EditOperation.RESTORATION, input_path, **kwargs)

    async def restore_face(self, input_path, **kwargs):
        """Restore faces in the input image."""
        return await self.edit(EditOperation.FACE_RESTORATION, input_path, **kwargs)

    def get_stats(self) -> Dict[str, Any]:
        """Return aggregate statistics over the edit history."""
        ops = {}
        for r in self._history:
            ops[r.operation.value] = ops.get(r.operation.value, 0) + 1
        return {
            "total_edits": len(self._history),
            "by_operation": ops,
            "providers": list(self._providers.keys()),
        }
