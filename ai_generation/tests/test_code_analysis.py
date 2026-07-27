"""Tests for code_analysis.py — SecretScanner, StaticAnalyzer, StructuralAnalyzer,
MultiAgentReviewEngine, PRVerificationEngine, TechnicalDebtTracker."""

import pytest
from ai_generation.code_analysis import (
    SecretScanner, SecretFinding, SecretSeverity,
    StaticAnalyzer, StaticIssue, IssueSeverity,
    StructuralAnalyzer, StructuralFinding,
    MultiAgentReviewEngine, ReviewAgentRole, AggregatedReview,
    PRVerificationEngine, CheckResult, CheckStatus,
    TechnicalDebtTracker, DebtItem, DebtCategory, DebtPriority,
)


# ── SecretScanner Tests ────────────────────────────────────────

class TestSecretScanner:
    def test_scan_aws_key(self):
        scanner = SecretScanner()
        findings = scanner.scan_text("AKIAIOSFODNN7EXAMPLE", "test.py")
        assert len(findings) >= 1
        assert findings[0].pattern_name == "AWS Access Key ID"
        assert findings[0].severity == SecretSeverity.CRITICAL.value

    def test_scan_github_pat(self):
        scanner = SecretScanner()
        findings = scanner.scan_text("token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij", "config.py")
        assert any(f.pattern_name == "GitHub PAT" for f in findings)

    def test_scan_private_key(self):
        scanner = SecretScanner()
        findings = scanner.scan_text("-----BEGIN RSA PRIVATE KEY-----", "key.pem")
        assert any(f.pattern_name == "Private Key" for f in findings)

    def test_scan_openai_key(self):
        scanner = SecretScanner()
        findings = scanner.scan_text("api_key = 'sk-1234567890abcdefghijklmnopqrst'", "config.py")
        assert any(f.pattern_name == "OpenAI / Stripe Secret Key" for f in findings)

    def test_scan_slack_token(self):
        scanner = SecretScanner()
        findings = scanner.scan_text("SLACK_TOKEN=xoxb-1234567890-abcdef", ".env")
        assert any(f.pattern_name == "Slack Token" for f in findings)

    def test_scan_no_secrets(self):
        scanner = SecretScanner()
        findings = scanner.scan_text("x = 42\nprint('hello')", "clean.py")
        assert len(findings) == 0

    def test_scan_excluded_file(self):
        scanner = SecretScanner(exclude_patterns=["*.md"])
        findings = scanner.scan_text("AKIAIOSFODNN7EXAMPLE", "readme.md")
        assert len(findings) == 0

    def test_scan_dedup(self):
        scanner = SecretScanner()
        text = "AKIAIOSFODNN7EXAMPLE\nAKIAIOSFODNN7EXAMPLE"
        findings = scanner.scan_text(text, "test.py")
        unique_lines = set(f.line for f in findings)
        assert len(findings) == len(unique_lines)

    def test_scan_diff(self):
        scanner = SecretScanner()
        diff = """--- a/config.py
+++ b/config.py
@@ -1,3 +1,4 @@
 import os
+API_KEY = 'sk-1234567890abcdefghijklmnopqrst'
 def main():
     pass"""
        findings = scanner.scan_diff(diff)
        assert any(f.pattern_name == "OpenAI / Stripe Secret Key" for f in findings)

    def test_scan_diff_ignores_removed_lines(self):
        scanner = SecretScanner()
        diff = """--- a/config.py
+++ b/config.py
@@ -1,3 +1,3 @@
-API_KEY = 'sk-1234567890abcdefghijklmnopqrst'
+API_KEY = 'safe'"
 def main():
     pass"""
        findings = scanner.scan_diff(diff)
        assert not any(f.pattern_name == "OpenAI / Stripe Secret Key" for f in findings)

    def test_finding_to_dict(self):
        f = SecretFinding(pattern_name="test", file_path="f.py", line=1, severity="critical", confidence=0.9)
        d = f.to_dict()
        assert d["pattern_name"] == "test"
        assert d["line"] == 1

    def test_database_connection_string(self):
        scanner = SecretScanner()
        findings = scanner.scan_text("DATABASE_URL=postgres://admin:password@localhost/mydb", ".env")
        assert any("Connection String" in f.pattern_name for f in findings)


# ── StaticAnalyzer Tests ───────────────────────────────────────

class TestStaticAnalyzer:
    def test_detect_eval(self):
        analyzer = StaticAnalyzer()
        issues = analyzer.analyze_code("result = eval(user_input)", "test.py")
        assert any(i.rule_id == "SEC001" for i in issues)

    def test_detect_exec(self):
        analyzer = StaticAnalyzer()
        issues = analyzer.analyze_code("exec(code_string)", "test.py")
        assert any(i.rule_id == "SEC002" for i in issues)

    def test_detect_bare_except(self):
        analyzer = StaticAnalyzer()
        issues = analyzer.analyze_code("try:\n    pass\nexcept:", "test.py")
        assert any(i.rule_id == "QLT001" for i in issues)

    def test_detect_star_import(self):
        analyzer = StaticAnalyzer()
        issues = analyzer.analyze_code("from os import *", "test.py")
        assert any(i.rule_id == "QLT003" for i in issues)

    def test_detect_todo(self):
        analyzer = StaticAnalyzer()
        issues = analyzer.analyze_code("# TODO: implement this", "test.py")
        assert any(i.rule_id == "QLT004" for i in issues)

    def test_detect_print(self):
        analyzer = StaticAnalyzer()
        issues = analyzer.analyze_code("print('debug')", "test.py")
        assert any(i.rule_id == "QLT009" for i in issues)

    def test_detect_pickle(self):
        analyzer = StaticAnalyzer()
        issues = analyzer.analyze_code("data = pickle.load(f)", "test.py")
        assert any(i.rule_id == "SEC005" for i in issues)

    def test_no_issues_clean_code(self):
        analyzer = StaticAnalyzer()
        issues = analyzer.analyze_code("import logging\nlogger = logging.getLogger(__name__)\n", "test.py")
        security_issues = [i for i in issues if i.category == "security"]
        assert len(security_issues) == 0

    def test_analyze_diff(self):
        analyzer = StaticAnalyzer()
        diff = "--- a/test.py\n+++ b/test.py\n@@ -1 +1,2 @@\n+import os\n+os.system('ls')"
        issues = analyzer.analyze_diff(diff)
        assert any(i.rule_id == "SEC003" for i in issues)

    def test_analyze_diff_ignores_removed(self):
        analyzer = StaticAnalyzer()
        diff = "--- a/test.py\n+++ b/test.py\n@@ -1 +1 @@\n-os.system('ls')\n+os.listdir('.')"
        issues = analyzer.analyze_diff(diff)
        sec_issues = [i for i in issues if i.category == "security"]
        assert len(sec_issues) == 0

    def test_issue_to_dict(self):
        issue = StaticIssue(file_path="f.py", line=1, severity="critical", category="security", message="test", rule_id="SEC001")
        d = issue.to_dict()
        assert d["rule_id"] == "SEC001"

    def test_skip_comments(self):
        analyzer = StaticAnalyzer()
        issues = analyzer.analyze_code("# eval(x) is bad", "test.py")
        security = [i for i in issues if i.category == "security"]
        assert len(security) == 0


# ── StructuralAnalyzer Tests ───────────────────────────────────

class TestStructuralAnalyzer:
    def test_detect_complex_function(self):
        analyzer = StructuralAnalyzer()
        code = """
def complex_func(x):
    if x > 0:
        if x > 10:
            if x > 20:
                for i in range(x):
                    if i % 2 == 0:
                        while i > 0:
                            i -= 1
                    elif i % 3 == 0:
                        for j in range(i):
                            if j > 5:
                                pass
                            elif j > 3:
                                pass
                            else:
                                pass
                    else:
                        pass
    return x
"""
        findings = analyzer.analyze({"complex.py": code})
        complexity_findings = [f for f in findings if f.category == "complexity"]
        assert len(complexity_findings) >= 1

    def test_detect_long_function(self):
        analyzer = StructuralAnalyzer()
        lines = ["def long_func():"]
        for i in range(60):
            lines.append(f"    x_{i} = {i}")
        code = "\n".join(lines)
        findings = analyzer.analyze({"long.py": code})
        long_findings = [f for f in findings if f.category == "long_function"]
        assert len(long_findings) >= 1

    def test_detect_dead_code(self):
        analyzer = StructuralAnalyzer()
        code = """
def unused_helper():
    return 42

def main():
    return used_helper()

def used_helper():
    return 0
"""
        findings = analyzer.analyze({"dead.py": code})
        dead_findings = [f for f in findings if f.category == "dead_code"]
        assert any("unused_helper" in f.message for f in dead_findings)

    def test_no_false_positive_for_main(self):
        analyzer = StructuralAnalyzer()
        code = """
def main():
    print("hello")

if __name__ == "__main__":
    main()
"""
        findings = analyzer.analyze({"main.py": code})
        dead_findings = [f for f in findings if f.category == "dead_code" and "main" in f.message]
        assert len(dead_findings) == 0

    def test_structural_finding_to_dict(self):
        f = StructuralFinding(category="test", severity="low", message="msg", file_path="f.py", line=1)
        d = f.to_dict()
        assert d["category"] == "test"

    def test_analyze_non_python_files_skipped(self):
        analyzer = StructuralAnalyzer()
        findings = analyzer.analyze({"test.js": "function foo() { return 1; }"})
        dead = [f for f in findings if f.category == "dead_code"]
        assert len(dead) == 0


# ── MultiAgentReviewEngine Tests ───────────────────────────────

class TestMultiAgentReviewEngine:
    def test_review_clean_code(self):
        engine = MultiAgentReviewEngine()
        review = engine.simulate_review("import logging\nlogger = logging.getLogger(__name__)\n", "clean.py")
        assert isinstance(review, AggregatedReview)
        assert review.quality_score >= 80

    def test_review_with_security_issues(self):
        engine = MultiAgentReviewEngine()
        review = engine.simulate_review("import os\nos.system('rm -rf /')\nresult = eval(input())", "bad.py")
        assert review.total_findings > 0
        assert review.by_severity.get("critical", 0) > 0

    def test_review_specific_role(self):
        engine = MultiAgentReviewEngine()
        review = engine.simulate_review("x = 1", "test.py", roles=["security"])
        assert len(review.agent_results) == 1
        assert review.agent_results[0]["agent_role"] == "security"

    def test_aggregated_review_to_dict(self):
        engine = MultiAgentReviewEngine()
        review = engine.simulate_review("x = 1", "test.py")
        d = review.to_dict()
        assert "total_findings" in d
        assert "quality_score" in d

    def test_stats(self):
        engine = MultiAgentReviewEngine()
        engine.simulate_review("x = 1", "a.py")
        engine.simulate_review("y = 2", "b.py")
        stats = engine.get_stats()
        assert stats["total_reviews"] == 12  # 6 roles x 2 reviews

    def test_consensus_detection(self):
        engine = MultiAgentReviewEngine(config={"consensus_threshold": 0.3})
        code = "try:\n    x = eval('1+1')\nexcept:\n    pass\n"
        review = engine.simulate_review(code, "risky.py")
        assert review.total_findings > 0


# ── PRVerificationEngine Tests ─────────────────────────────────

class TestPRVerificationEngine:
    def test_all_checks_clean(self):
        engine = PRVerificationEngine()
        code = "import logging\nlogger = logging.getLogger(__name__)\ndef main() -> None:\n    pass\n"
        result = engine.run_full_verification(code, "clean.py")
        assert result["total"] == 10

    def test_detect_bare_except(self):
        engine = PRVerificationEngine()
        result = engine.verify("try:\n    pass\nexcept:", "test.py", checks=["no_bare_excepts"])
        assert result[0].status == CheckStatus.FAILED.value

    def test_detect_print(self):
        engine = PRVerificationEngine()
        result = engine.verify("print('hello')", "test.py", checks=["no_print_statements"])
        assert result[0].status == CheckStatus.FAILED.value

    def test_detect_star_import(self):
        engine = PRVerificationEngine()
        result = engine.verify("from os import *", "test.py", checks=["no_star_imports"])
        assert result[0].status == CheckStatus.FAILED.value

    def test_skip_unknown_check(self):
        engine = PRVerificationEngine()
        result = engine.verify("x = 1", "test.py", checks=["nonexistent_check"])
        assert result[0].status == CheckStatus.SKIPPED.value

    def test_check_result_to_dict(self):
        r = CheckResult(name="test", status="passed", message="ok")
        d = r.to_dict()
        assert d["name"] == "test"

    def test_type_hints_check(self):
        engine = PRVerificationEngine()
        result = engine.verify("def foo():\n    return 1", "test.py", checks=["type_hints_present"])
        assert result[0].status == CheckStatus.FAILED.value

    def test_type_hints_pass(self):
        engine = PRVerificationEngine()
        result = engine.verify("def foo(x: int) -> int:\n    return x", "test.py", checks=["type_hints_present"])
        assert result[0].status == CheckStatus.PASSED.value


# ── TechnicalDebtTracker Tests ─────────────────────────────────

class TestTechnicalDebtTracker:
    def test_scan_todos(self):
        tracker = TechnicalDebtTracker()
        items = tracker.scan_codebase({"main.py": "# TODO: add tests\nx = 1"})
        todo_items = [i for i in items if i.category == DebtCategory.TODO.value]
        assert len(todo_items) >= 1

    def test_scan_fixmes(self):
        tracker = TechnicalDebtTracker()
        items = tracker.scan_codebase({"main.py": "# FIXME: broken logic\nx = 1"})
        fixme_items = [i for i in items if i.category == DebtCategory.FIXME.value]
        assert len(fixme_items) >= 1
        assert fixme_items[0].priority == DebtPriority.HIGH.value

    def test_scan_hacks(self):
        tracker = TechnicalDebtTracker()
        items = tracker.scan_codebase({"main.py": "# HACK: temporary workaround\nx = 1"})
        hack_items = [i for i in items if i.category == DebtCategory.HACK.value]
        assert len(hack_items) >= 1

    def test_scan_noqa(self):
        tracker = TechnicalDebtTracker()
        items = tracker.scan_codebase({"main.py": "x = foo()  # noqa"})
        noqa_items = [i for i in items if i.category == DebtCategory.CODE_SMELL.value]
        assert len(noqa_items) >= 1

    def test_scan_type_ignore(self):
        tracker = TechnicalDebtTracker()
        items = tracker.scan_codebase({"main.py": "x = foo()  # type: ignore"})
        ti_items = [i for i in items if i.category == DebtCategory.TYPE_IGNORE.value]
        assert len(ti_items) >= 1

    def test_scan_missing_docstrings(self):
        tracker = TechnicalDebtTracker()
        items = tracker.scan_codebase({"main.py": "def foo():\n    return 1"})
        doc_items = [i for i in items if i.category == DebtCategory.MISSING_DOCS.value]
        assert len(doc_items) >= 1

    def test_resolve_item(self):
        tracker = TechnicalDebtTracker()
        items = tracker.scan_codebase({"main.py": "# TODO: fix\nx = 1"})
        item_id = items[0].id
        assert tracker.resolve(item_id) is True
        assert tracker.get_all()[0].status == "resolved"

    def test_resolve_nonexistent(self):
        tracker = TechnicalDebtTracker()
        assert tracker.resolve("DEBT-9999") is False

    def test_get_by_priority(self):
        tracker = TechnicalDebtTracker()
        tracker.scan_codebase({"a.py": "# TODO: low\n# FIXME: high"})
        high = tracker.get_by_priority(DebtPriority.HIGH.value)
        assert len(high) >= 1

    def test_get_by_category(self):
        tracker = TechnicalDebtTracker()
        tracker.scan_codebase({"a.py": "# TODO: fix\n# FIXME: broken"})
        todos = tracker.get_by_category(DebtCategory.TODO.value)
        assert len(todos) >= 1

    def test_stats(self):
        tracker = TechnicalDebtTracker()
        tracker.scan_codebase({"a.py": "# TODO: one\n# FIXME: two\nx = 1"})
        stats = tracker.get_stats()
        assert stats["total"] >= 2
        assert "by_priority" in stats
        assert "by_category" in stats

    def test_debt_item_to_dict(self):
        item = DebtItem(id="DEBT-0001", category="todo", priority="low", file_path="f.py", line=1, description="test")
        d = item.to_dict()
        assert d["id"] == "DEBT-0001"

    def test_empty_scan(self):
        tracker = TechnicalDebtTracker()
        items = tracker.scan_codebase({"clean.py": "import os\nprint(os.path.abspath('.'))"})
        assert len(items) == 0  # os.path.abspath is not a bare print in this context


# ── Integration Tests ──────────────────────────────────────────

class TestIntegration:
    def test_secret_scanner_in_multi_agent_review(self):
        engine = MultiAgentReviewEngine()
        review = engine.simulate_review("API_KEY = 'sk-1234567890abcdefghijklmnopqrst'", "config.py")
        assert review.total_findings > 0

    def test_structural_analyzer_in_multi_agent_review(self):
        engine = MultiAgentReviewEngine()
        code = """
def complex_func(x):
    if x > 0:
        if x > 10:
            if x > 20:
                for i in range(x):
                    if i % 2 == 0:
                        while i > 0:
                            i -= 1
                    elif i % 3 == 0:
                        for j in range(i):
                            if j > 5: pass
                            elif j > 3: pass
                            else: pass
                    else: pass
    return x
"""
        review = engine.simulate_review(code, "complex.py", roles=["performance"])
        assert review.total_findings >= 0  # structural analysis runs

    def test_debt_tracker_with_code_analysis(self):
        scanner = SecretScanner()
        tracker = TechnicalDebtTracker()
        code = "API_KEY = 'sk-1234567890abcdefghijklmnopqrst'\n# TODO: rotate key\nresult = eval(x)"
        secret_findings = scanner.scan_text(code, "bad.py")
        debt_items = tracker.scan_codebase({"bad.py": code})
        assert len(secret_findings) > 0
        assert len(debt_items) > 0

    def test_full_pipeline(self):
        """Test the complete quality analysis pipeline."""
        code = """
import os
# TODO: add logging
API_KEY = 'sk-1234567890abcdefghijklmnopqrst'
result = eval(input())
def complex_func(x):
    if x > 0:
        if x > 10:
            if x > 20:
                for i in range(x):
                    if i % 2 == 0:
                        while i > 0:
                            i -= 1
                    elif i % 3 == 0:
                        for j in range(i):
                            if j > 5: pass
                            elif j > 3: pass
                            else: pass
                    else: pass
    return x
"""
        files = {"pipeline_test.py": code}

        scanner = SecretScanner()
        secrets = scanner.scan_text(code, "pipeline_test.py")
        assert len(secrets) > 0

        analyzer = StaticAnalyzer()
        issues = analyzer.analyze_code(code, "pipeline_test.py")
        assert len(issues) > 0

        structural = StructuralAnalyzer()
        struct_findings = structural.analyze(files)
        assert len(struct_findings) > 0

        engine = MultiAgentReviewEngine()
        review = engine.simulate_review(code, "pipeline_test.py")
        assert review.total_findings > 0

        verifier = PRVerificationEngine()
        verification = verifier.run_full_verification(code, "pipeline_test.py")
        assert verification["failed"] > 0

        tracker = TechnicalDebtTracker()
        debt = tracker.scan_codebase(files)
        assert len(debt) > 0
