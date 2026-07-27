"""Tests for refactoring_engine.py — SmellDetector, RefactoringEngine."""

import pytest
from ai_generation.refactoring_engine import (
    SmellCategory, SmellType, CodeSmell,
    RefactoringTechnique, RefactoringSuggestion,
    SmellDetector, RefactoringEngine, SMELL_TO_TECHNIQUE,
)


# ── SmellDetector Tests ────────────────────────────────────────

class TestSmellDetector:
    def test_detect_long_method(self):
        detector = SmellDetector()
        lines = ["def long_func():"]
        for i in range(60):
            lines.append(f"    x_{i} = {i}")
        code = "\n".join(lines)
        smells = detector.detect(code, "test.py")
        long_methods = [s for s in smells if s.smell_type == SmellType.LONG_METHOD.value]
        assert len(long_methods) >= 1

    def test_detect_large_class(self):
        detector = SmellDetector()
        methods = "\n".join([f"    def method_{i}(self): pass" for i in range(20)])
        code = f"class BigClass:\n{methods}"
        smells = detector.detect(code, "test.py")
        large = [s for s in smells if s.smell_type == SmellType.LARGE_CLASS.value]
        assert len(large) >= 1

    def test_detect_long_params(self):
        detector = SmellDetector()
        code = "def func(a, b, c, d, e, f, g): pass"
        smells = detector.detect(code, "test.py")
        long_params = [s for s in smells if s.smell_type == SmellType.LONG_PARAMETER_LIST.value]
        assert len(long_params) >= 1

    def test_detect_magic_numbers(self):
        detector = SmellDetector()
        code = "x = 9999\ny = 5000\nz = 10000"
        smells = detector.detect(code, "test.py")
        magic = [s for s in smells if s.smell_type == SmellType.MAGIC_NUMBERS.value]
        assert len(magic) >= 1

    def test_detect_dead_code(self):
        detector = SmellDetector()
        code = "def unused():\n    return 42\ndef main():\n    return 0"
        smells = detector.detect(code, "test.py")
        dead = [s for s in smells if s.smell_type == SmellType.DEAD_CODE.value]
        assert any("unused" in s.name for s in dead)

    def test_no_false_positive_main(self):
        detector = SmellDetector()
        code = "def main():\n    return 0"
        smells = detector.detect(code, "test.py")
        dead = [s for s in smells if s.smell_type == SmellType.DEAD_CODE.value and "main" in s.name]
        assert len(dead) == 0

    def test_no_smells_clean_code(self):
        detector = SmellDetector()
        code = "def clean(x: int) -> int:\n    return x * 2\nclean(1)"
        smells = detector.detect(code, "test.py")
        assert len(smells) == 0

    def test_syntax_error_returns_empty(self):
        detector = SmellDetector()
        smells = detector.detect("def func(:\n  pass", "bad.py")
        assert len(smells) == 0

    def test_smell_to_dict(self):
        smell = CodeSmell(
            smell_type="long_method", category="blocator",
            file_path="f.py", line=1, name="func",
            description="too long", severity="medium",
        )
        d = smell.to_dict()
        assert d["smell_type"] == "long_method"
        assert d["severity"] == "medium"


# ── RefactoringEngine Tests ────────────────────────────────────

class TestRefactoringEngine:
    def test_analyze_long_method(self):
        engine = RefactoringEngine()
        lines = ["def long_func():"]
        for i in range(60):
            lines.append(f"    x_{i} = {i}")
        code = "\n".join(lines)
        suggestions = engine.analyze(code, "test.py")
        assert len(suggestions) >= 1
        assert suggestions[0].technique == RefactoringTechnique.EXTRACT_METHOD.value

    def test_analyze_large_class(self):
        engine = RefactoringEngine()
        methods = "\n".join([f"    def method_{i}(self): pass" for i in range(20)])
        code = f"class BigClass:\n{methods}"
        suggestions = engine.analyze(code, "test.py")
        assert any(s.technique == RefactoringTechnique.SPLIT_LARGE_CLASS.value for s in suggestions)

    def test_analyze_long_params(self):
        engine = RefactoringEngine()
        code = "def func(a, b, c, d, e, f, g): pass"
        suggestions = engine.analyze(code, "test.py")
        assert any(s.technique == RefactoringTechnique.INTRODUCE_PARAMETER_OBJECT.value for s in suggestions)

    def test_analyze_deep_nesting(self):
        engine = RefactoringEngine()
        code = """def deep(x):
    if x > 0:
        if x > 10:
            if x > 20:
                if x > 30:
                    if x > 40:
                        return x"""
        suggestions = engine.analyze(code, "test.py")
        assert any(s.technique == RefactoringTechnique.USE_GUARD_CLAUSES.value for s in suggestions)

    def test_analyze_magic_numbers(self):
        engine = RefactoringEngine()
        code = "x = 9999"
        suggestions = engine.analyze(code, "test.py")
        assert any(s.technique == RefactoringTechnique.EXTRACT_CONSTANT.value for s in suggestions)

    def test_analyze_files(self):
        engine = RefactoringEngine()
        files = {
            "a.py": "def func(a, b, c, d, e, f, g): pass",
            "b.py": "x = 9999",
        }
        suggestions = engine.analyze_files(files)
        assert len(suggestions) >= 2

    def test_suggestion_priority_ordering(self):
        engine = RefactoringEngine()
        code = "def func(a, b, c, d, e, f, g): pass"
        suggestions = engine.analyze(code, "test.py")
        if len(suggestions) > 1:
            for i in range(len(suggestions) - 1):
                assert suggestions[i].priority >= suggestions[i + 1].priority

    def test_suggestion_has_steps(self):
        engine = RefactoringEngine()
        code = "def func(a, b, c, d, e, f, g): pass"
        suggestions = engine.analyze(code, "test.py")
        assert len(suggestions) >= 1
        assert len(suggestions[0].steps) > 0

    def test_suggestion_to_dict(self):
        engine = RefactoringEngine()
        code = "x = 9999"
        suggestions = engine.analyze(code, "test.py")
        assert len(suggestions) >= 1
        d = suggestions[0].to_dict()
        assert "smell" in d
        assert "technique" in d
        assert "steps" in d

    def test_get_stats(self):
        engine = RefactoringEngine()
        code = "def func(a, b, c, d, e, f, g): pass\nx = 9999"
        suggestions = engine.analyze(code, "test.py")
        stats = engine.get_stats(suggestions)
        assert "total_suggestions" in stats
        assert "by_technique" in stats

    def test_smell_to_technique_mapping_coverage(self):
        """Verify all smell types have a technique mapping."""
        for smell_type in SmellType:
            assert smell_type.value in SMELL_TO_TECHNIQUE, f"Missing technique for {smell_type.value}"


# ── Integration Tests ──────────────────────────────────────────

class TestRefactoringIntegration:
    def test_analyze_realistic_code(self):
        engine = RefactoringEngine()
        code = """
class UserManager:
    def __init__(self, db, cache, logger, mailer, notifier, validator, transformer):
        self.db = db
        self.cache = cache
        self.logger = logger
        self.mailer = mailer
        self.notifier = notifier
        self.validator = validator
        self.transformer = transformer

    def process_user(self, user_id, action, flag1, flag2, flag3, flag4, flag5, flag6):
        if action == "create":
            if flag1:
                if flag2:
                    if flag3:
                        if flag4:
                            x = 9999
                            return self.db.create(user_id)
        elif action == "update":
            pass
        elif action == "delete":
            pass
        elif action == "archive":
            pass
        elif action == "restore":
            pass

    def method_0(self): pass
    def method_1(self): pass
    def method_2(self): pass
    def method_3(self): pass
    def method_4(self): pass
    def method_5(self): pass
    def method_6(self): pass
    def method_7(self): pass
    def method_8(self): pass
    def method_9(self): pass
    def method_10(self): pass
    def method_11(self): pass
    def method_12(self): pass
    def method_13(self): pass
    def method_14(self): pass
    def method_15(self): pass
    def method_16(self): pass
"""
        suggestions = engine.analyze(code, "user_manager.py")
        assert len(suggestions) >= 3
        techniques = set(s.technique for s in suggestions)
        assert RefactoringTechnique.SPLIT_LARGE_CLASS.value in techniques
        assert RefactoringTechnique.INTRODUCE_PARAMETER_OBJECT.value in techniques

    def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline from smell detection to suggestions."""
        detector = SmellDetector()
        engine = RefactoringEngine()
        code = """
def complex_func(a, b, c, d, e, f, g):
    if a > 0:
        if b > 0:
            if c > 0:
                x = 7777
                return a + b + c + x
    return 0
"""
        smells = detector.detect(code, "test.py")
        suggestions = engine.analyze(code, "test.py")
        assert len(smells) >= 2
        assert len(suggestions) >= 2
        stats = engine.get_stats(suggestions)
        assert stats["total_suggestions"] >= 2
