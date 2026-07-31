"""
Tests for the unified SDK package-level exports.
"""


def test_package_exports_uncle_frappe_ai():
    from ai_generation import UncleFrappeAI
    assert UncleFrappeAI is not None


def test_sdk_initialize_and_stats():
    from ai_generation import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_stats()
    assert "generation" in stats
    assert stats["generation"]["provider_summary"]["total_providers"] > 0


def test_sdk_quality_gates_available():
    from ai_generation import UncleFrappeAI
    ai = UncleFrappeAI()
    gates = ai.quality_gates.list_gates()
    assert len(gates) > 0
