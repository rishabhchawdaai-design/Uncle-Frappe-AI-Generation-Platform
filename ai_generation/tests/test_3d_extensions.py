"""Tests for 3D-06/07/08 — Gaussian Splatting, Mesh Processing, 3D Editing."""
import pytest


def test_gaussian_splat_backend_enum():
    from ai_generation.generation_3d_extensions import GaussianSplatBackend
    assert GaussianSplatBackend.SPLATFACTO.value == "splatfacto"
    assert GaussianSplatBackend.NERFSTUDIO.value == "nerfstudio"
    assert GaussianSplatBackend.GAUSSTUDIO.value == "gausstudio"


def test_mesh_operation_enum():
    from ai_generation.generation_3d_extensions import MeshOperation
    assert MeshOperation.SIMPLIFY.value == "simplify"
    assert MeshOperation.SMOOTH.value == "smooth"
    assert MeshOperation.REMESH.value == "remesh"
    assert MeshOperation.TRIANGULATE.value == "triangulate"
    assert MeshOperation.DECIMATE.value == "decimate"
    assert MeshOperation.UV_UNWRAP.value == "uv_unwrap"
    assert MeshOperation.NORMAL_MAP.value == "normal_map"
    assert MeshOperation.SCALE.value == "scale"
    assert MeshOperation.MERGE.value == "merge"


def test_edit_3d_operation_enum():
    from ai_generation.generation_3d_extensions import Edit3DOperation
    assert Edit3DOperation.TRANSFORM.value == "transform"
    assert Edit3DOperation.CLIP.value == "clip"
    assert Edit3DOperation.RECONSTRUCT.value == "reconstruct"
    assert Edit3DOperation.EXPORT.value == "export"


def test_three_d_status_enum():
    from ai_generation.generation_3d_extensions import ThreeDStatus
    assert ThreeDStatus.COMPLETED.value == "completed"
    assert ThreeDStatus.FAILED.value == "failed"
    assert ThreeDStatus.DEPENDENCY_MISSING.value == "dependency_missing"


def test_gaussian_splat_profiles():
    from ai_generation.generation_3d_extensions import GAUSSIAN_SPLAT_PROFILES
    assert len(GAUSSIAN_SPLAT_PROFILES) == 2
    for p in GAUSSIAN_SPLAT_PROFILES:
        assert p.requires_gpu is True
        assert len(p.output_formats) > 0


def test_mesh_profiles():
    from ai_generation.generation_3d_extensions import MESH_PROFILES
    assert len(MESH_PROFILES) >= 8


def test_edit_3d_profiles():
    from ai_generation.generation_3d_extensions import EDIT_3D_PROFILES
    assert len(EDIT_3D_PROFILES) == 4


def test_three_d_result_serialization():
    from ai_generation.generation_3d_extensions import ThreeDResult, ThreeDStatus
    r = ThreeDResult(operation="simplify", backend="trimesh", status=ThreeDStatus.COMPLETED, request_id="test-123")
    d = r.to_dict()
    assert d["operation"] == "simplify"
    assert d["status"] == "completed"


def test_gaussian_splatting_engine_import():
    from ai_generation.generation_3d_extensions import GaussianSplattingEngine
    e = GaussianSplattingEngine()
    assert e is not None
    assert len(e.get_profiles()) == 2


def test_mesh_processing_engine_import():
    from ai_generation.generation_3d_extensions import MeshProcessingEngine
    e = MeshProcessingEngine()
    assert e is not None
    assert len(e.get_profiles()) >= 8


def test_edit_3d_engine_import():
    from ai_generation.generation_3d_extensions import Edit3DEngine
    e = Edit3DEngine()
    assert e is not None
    assert len(e.get_profiles()) == 4


@pytest.mark.asyncio
async def test_gaussian_splat_train_no_gpu():
    from ai_generation.generation_3d_extensions import GaussianSplattingEngine, ThreeDStatus
    e = GaussianSplattingEngine()
    result = await e.train("images/")
    assert result.status == ThreeDStatus.DEPENDENCY_MISSING


@pytest.mark.asyncio
async def test_mesh_process_no_backend():
    from ai_generation.generation_3d_extensions import MeshProcessingEngine, MeshOperation, ThreeDStatus
    e = MeshProcessingEngine()
    result = await e.process(MeshOperation.SIMPLIFY, "model.obj")
    assert result.status == ThreeDStatus.DEPENDENCY_MISSING


@pytest.mark.asyncio
async def test_edit_3d_no_backend():
    from ai_generation.generation_3d_extensions import Edit3DEngine, Edit3DOperation, ThreeDStatus
    e = Edit3DEngine()
    result = await e.edit(Edit3DOperation.TRANSFORM, "model.obj")
    assert result.status == ThreeDStatus.DEPENDENCY_MISSING


# ── SDK Integration ──

def test_sdk_3d_extensions_import():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    assert ai.gaussian_splatting is not None
    assert ai.mesh_processing is not None
    assert ai.edit_3d is not None


def test_sdk_3d_extensions_in_stats():
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_stats()
    assert "gaussian_splatting" in stats
    assert "mesh_processing" in stats
    assert "edit_3d" in stats


# ── MCP Tools ──

def test_mcp_3d_tools_exist():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    assert "train_gaussian_splat" in MCP_GENERATION_TOOLS
    assert "render_gaussian_splat" in MCP_GENERATION_TOOLS
    assert "process_mesh" in MCP_GENERATION_TOOLS
    assert "edit_3d_model" in MCP_GENERATION_TOOLS
    assert "get_gaussian_splat_profiles" in MCP_GENERATION_TOOLS
    assert "get_mesh_profiles" in MCP_GENERATION_TOOLS
    assert "get_3d_edit_profiles" in MCP_GENERATION_TOOLS


def test_mcp_process_mesh_schema():
    from ai_generation.mcp_tools import MCP_GENERATION_TOOLS
    tool = MCP_GENERATION_TOOLS["process_mesh"]
    schema = tool["inputSchema"]
    assert "operation" in schema["properties"]
    assert "input_path" in schema["properties"]


@pytest.mark.asyncio
async def test_mcp_process_mesh_handler():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    assert hasattr(mcp, "_handle_process_mesh")


@pytest.mark.asyncio
async def test_mcp_gaussian_splat_profiles():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("get_gaussian_splat_profiles", {})
    assert "profiles" in result
    assert len(result["profiles"]) == 2


@pytest.mark.asyncio
async def test_mcp_mesh_profiles():
    from ai_generation.mcp_tools import MCPGenerationTools
    mcp = MCPGenerationTools()
    result = await mcp.handle("get_mesh_profiles", {})
    assert "profiles" in result
    assert len(result["profiles"]) >= 8
