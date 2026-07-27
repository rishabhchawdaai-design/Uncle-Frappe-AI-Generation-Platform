"""
Automated Refactoring Engine — patterns from claude-code-agents (alf-refactoring-advisor, alf-code-smell-detector).

Provides: RefactoringEngine with smell detection, technique mapping, suggestion generation.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ── Code Smells ────────────────────────────────────────────────

class SmellCategory(str, Enum):
    BLOATER = "blocator"
    CHANGE_PREVENTER = "change_preventer"
    COUPLER = "coupler"
    DISPENSABLE = "dispensable"
    OO_ABUSER = "oo_abuser"
    OBJECT_ORIENTED = "object_oriented"


class SmellType(str, Enum):
    LONG_METHOD = "long_method"
    LARGE_CLASS = "large_class"
    LONG_PARAMETER_LIST = "long_parameter_list"
    DUPLICATE_CODE = "duplicate_code"
    GOD_CLASS = "god_class"
    FEATURE_ENVY = "feature_envy"
    DATA_CLUMPS = "data_clumps"
    PRIMITIVE_OBSESSION = "primitive_obsession"
    SWITCH_STATEMENTS = "switch_statements"
    SPECULATIVE_GENERALITY = "speculative_generality"
    DEAD_CODE = "dead_code"
    MAGIC_NUMBERS = "magic_numbers"
    DEEP_NESTING = "deep_nesting"
    MISLEADING_NAMES = "misleading_names"
    INCONSISTENT_NAMING = "inconsistent_naming"
    MISSING_ABSTRACTION = "missing_abstraction"
    TIGHT_COUPLING = "tight_coupling"
    LOW_COHESION = "low_cohesion"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    FEATURE_BRANCH = "feature_branch"


@dataclass
class CodeSmell:
    smell_type: str
    category: str
    file_path: str
    line: int
    name: str
    description: str
    severity: str = "medium"
    confidence: float = 0.8
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "smell_type": self.smell_type,
            "category": self.category,
            "file_path": self.file_path,
            "line": self.line,
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
            "confidence": self.confidence,
            "context": self.context,
        }


# ── Refactoring Techniques ─────────────────────────────────────

class RefactoringTechnique(str, Enum):
    EXTRACT_METHOD = "extract_method"
    EXTRACT_CLASS = "extract_class"
    INLINE_METHOD = "inline_method"
    MOVE_METHOD = "move_method"
    RENAME_METHOD = "rename_method"
    RENAME_VARIABLE = "rename_variable"
    REMOVE_PARAMETER = "remove_parameter"
    INTRODUCE_PARAMETER_OBJECT = "introduce_parameter_object"
    REPLACE_TEMP_WITH_QUERY = "replace_temp_with_query"
    REPLACE_CONDITIONAL_WITH_POLYMORPHISM = "replace_conditional_with_polymorphism"
    INTRODUCE_NULL_OBJECT = "introduce_null_object"
    CONSOLIDATE_DUPLICATE = "consolidate_duplicate"
    SPLIT_LARGE_CLASS = "split_large_class"
    REDUCE_NESTING = "reduce_nesting"
    EXTRACT_CONSTANT = "extract_constant"
    ENCAPSULATE_FIELD = "encapsulate_field"
    REPLACE_MAGIC_NUMBER = "replace_magic_number"
    USE_GUARD_CLAUSES = "use_guard_clauses"
    INTRODUCE_ABSTRACTION = "introduce_abstraction"
    DECOUPLE_MODULES = "decouple_modules"


@dataclass
class RefactoringSuggestion:
    smell: CodeSmell
    technique: str
    description: str
    effort: str = "medium"
    risk: str = "low"
    priority: int = 0
    steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "smell": self.smell.to_dict(),
            "technique": self.technique,
            "description": self.description,
            "effort": self.effort,
            "risk": self.risk,
            "priority": self.priority,
            "steps": self.steps,
        }


# ── Smell Detector ─────────────────────────────────────────────

class SmellDetector:
    """Detect code smells in Python code — patterns from alf-code-smell-detector."""

    def detect(self, code: str, file_path: str = "<input>") -> List[CodeSmell]:
        smells: List[CodeSmell] = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return smells

        smells.extend(self._detect_long_methods(tree, file_path))
        smells.extend(self._detect_large_classes(tree, file_path))
        smells.extend(self._detect_long_params(tree, file_path))
        smells.extend(self._detect_deep_nesting(code, file_path))
        smells.extend(self._detect_magic_numbers(code, file_path))
        smells.extend(self._detect_dead_code(tree, file_path))
        smells.extend(self._detect_feature_envy(tree, file_path))
        smells.extend(self._detect_switch_statements(tree, file_path))
        return smells

    def _detect_long_methods(self, tree: ast.AST, file_path: str) -> List[CodeSmell]:
        smells = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, "end_lineno", None)
                if end and (end - node.lineno + 1) > 50:
                    smells.append(CodeSmell(
                        smell_type=SmellType.LONG_METHOD.value,
                        category=SmellCategory.BLOATER.value,
                        file_path=file_path, line=node.lineno,
                        name=node.name,
                        description=f"Method '{node.name}' is {end - node.lineno + 1} lines (threshold: 50)",
                        severity="medium",
                        context={"line_count": end - node.lineno + 1},
                    ))
        return smells

    def _detect_large_classes(self, tree: ast.AST, file_path: str) -> List[CodeSmell]:
        smells = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = sum(1 for n in ast.iter_child_nodes(node)
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
                if methods > 15:
                    smells.append(CodeSmell(
                        smell_type=SmellType.LARGE_CLASS.value,
                        category=SmellCategory.BLOATER.value,
                        file_path=file_path, line=node.lineno,
                        name=node.name,
                        description=f"Class '{node.name}' has {methods} methods (threshold: 15)",
                        severity="high",
                        context={"method_count": methods},
                    ))
        return smells

    def _detect_long_params(self, tree: ast.AST, file_path: str) -> List[CodeSmell]:
        smells = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = node.args
                total = len(args.args) + len(args.posonlyargs) + len(args.kwonlyargs)
                if total > 5:
                    smells.append(CodeSmell(
                        smell_type=SmellType.LONG_PARAMETER_LIST.value,
                        category=SmellCategory.BLOATER.value,
                        file_path=file_path, line=node.lineno,
                        name=node.name,
                        description=f"Function '{node.name}' has {total} parameters (threshold: 5)",
                        severity="medium",
                        context={"param_count": total},
                    ))
        return smells

    def _detect_deep_nesting(self, code: str, file_path: str) -> List[CodeSmell]:
        smells = []
        lines = code.splitlines()
        nesting = 0
        max_nesting = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if any(stripped.startswith(kw) for kw in ("if ", "elif ", "else:", "for ", "while ", "try:", "except", "with ")):
                nesting += 1
                if nesting > 4:
                    smells.append(CodeSmell(
                        smell_type=SmellType.DEEP_NESTING.value,
                        category=SmellCategory.CHANGE_PREVENTER.value,
                        file_path=file_path, line=i,
                        name="deep_nesting",
                        description=f"Deep nesting level {nesting} at line {i}",
                        severity="medium",
                        context={"nesting_level": nesting},
                    ))
            elif stripped == "" or not stripped.startswith((" ", "\t")):
                nesting = 0
        return smells

    def _detect_magic_numbers(self, code: str, file_path: str) -> List[CodeSmell]:
        smells = []
        lines = code.splitlines()
        pattern = re.compile(r'(?<![a-zA-Z_0-9])([2-9]\d{2,}|[1-9]\d{3,})(?![a-zA-Z_0-9])')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or "import" in stripped:
                continue
            matches = pattern.findall(line)
            for m in matches:
                num = int(m)
                if num not in (0, 1, 100, 1000):
                    smells.append(CodeSmell(
                        smell_type=SmellType.MAGIC_NUMBERS.value,
                        category=SmellCategory.BLOATER.value,
                        file_path=file_path, line=i,
                        name="magic_number",
                        description=f"Magic number {num} at line {i}",
                        severity="low",
                        context={"number": num},
                    ))
        return smells

    def _detect_dead_code(self, tree: ast.AST, file_path: str) -> List[CodeSmell]:
        smells = []
        defined: Dict[str, int] = {}
        used: set = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined[node.name] = node.lineno
            elif isinstance(node, ast.ClassDef):
                defined[node.name] = node.lineno
            elif isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                used.add(node.attr)
        for name, lineno in defined.items():
            if name.startswith("_") or name in ("__init__", "main", "setup", "teardown"):
                continue
            if name not in used:
                smells.append(CodeSmell(
                    smell_type=SmellType.DEAD_CODE.value,
                    category=SmellCategory.DISPENSABLE.value,
                    file_path=file_path, line=lineno,
                    name=name,
                    description=f"'{name}' appears unused",
                    severity="low",
                ))
        return smells

    def _detect_feature_envy(self, tree: ast.AST, file_path: str) -> List[CodeSmell]:
        """Detect methods that use more external attributes than their own class."""
        smells = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self_refs = 0
                other_refs = 0
                for child in ast.walk(node):
                    if isinstance(child, ast.Attribute):
                        if isinstance(child.value, ast.Name):
                            if child.value.id == "self":
                                self_refs += 1
                            else:
                                other_refs += 1
                if other_refs > 3 and other_refs > self_refs * 2:
                    smells.append(CodeSmell(
                        smell_type=SmellType.FEATURE_ENVY.value,
                        category=SmellCategory.COUPLER.value,
                        file_path=file_path, line=node.lineno,
                        name=node.name,
                        description=f"Method '{node.name}' envies other objects ({other_refs} external vs {self_refs} self refs)",
                        severity="medium",
                        context={"self_refs": self_refs, "other_refs": other_refs},
                    ))
        return smells

    def _detect_switch_statements(self, tree: ast.AST, file_path: str) -> List[CodeSmell]:
        """Detect long if/elif chains that should use polymorphism."""
        smells = []
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                chain_length = 1
                current = node
                while hasattr(current, "orelse") and current.orelse:
                    if len(current.orelse) == 1 and isinstance(current.orelse[0], ast.If):
                        chain_length += 1
                        current = current.orelse[0]
                    else:
                        break
                if chain_length > 4:
                    smells.append(CodeSmell(
                        smell_type=SmellType.SWITCH_STATEMENTS.value,
                        category=SmellCategory.OO_ABUSER.value,
                        file_path=file_path, line=node.lineno,
                        name="long_if_chain",
                        description=f"If/elif chain of length {chain_length} (threshold: 4)",
                        severity="medium",
                        context={"chain_length": chain_length},
                    ))
        return smells


# ── Refactoring Engine ─────────────────────────────────────────

SMELL_TO_TECHNIQUE: Dict[str, Dict[str, Any]] = {
    SmellType.LONG_METHOD.value: {
        "technique": RefactoringTechnique.EXTRACT_METHOD.value,
        "effort": "medium",
        "risk": "low",
        "steps": [
            "Identify logical blocks within the method",
            "Extract each block into a separate method with a descriptive name",
            "Replace the original block with a call to the new method",
            "Verify tests still pass after each extraction",
        ],
    },
    SmellType.LARGE_CLASS.value: {
        "technique": RefactoringTechnique.SPLIT_LARGE_CLASS.value,
        "effort": "high",
        "risk": "medium",
        "steps": [
            "Identify cohesive groups of methods",
            "Extract each group into a new class",
            "Update references to use the new classes",
            "Consider using composition or delegation",
        ],
    },
    SmellType.LONG_PARAMETER_LIST.value: {
        "technique": RefactoringTechnique.INTRODUCE_PARAMETER_OBJECT.value,
        "effort": "medium",
        "risk": "low",
        "steps": [
            "Group related parameters into a data class",
            "Replace individual parameters with the parameter object",
            "Update all call sites",
        ],
    },
    SmellType.DEEP_NESTING.value: {
        "technique": RefactoringTechnique.USE_GUARD_CLAUSES.value,
        "effort": "low",
        "risk": "low",
        "steps": [
            "Invert conditional checks to early returns",
            "Extract nested logic into helper methods",
            "Reduce nesting by flattening conditionals",
        ],
    },
    SmellType.MAGIC_NUMBERS.value: {
        "technique": RefactoringTechnique.EXTRACT_CONSTANT.value,
        "effort": "low",
        "risk": "low",
        "steps": [
            "Define a named constant for the magic number",
            "Replace all occurrences with the constant name",
            "Add a comment explaining the constant's meaning",
        ],
    },
    SmellType.DEAD_CODE.value: {
        "technique": RefactoringTechnique.INLINE_METHOD.value,
        "effort": "low",
        "risk": "low",
        "steps": [
            "Verify the code is truly unreachable",
            "Remove the dead code",
            "Run tests to confirm no impact",
        ],
    },
    SmellType.FEATURE_ENVY.value: {
        "technique": RefactoringTechnique.MOVE_METHOD.value,
        "effort": "medium",
        "risk": "medium",
        "steps": [
            "Identify the object the method envies",
            "Move the method to that object",
            "Update all callers to use the new location",
        ],
    },
    SmellType.SWITCH_STATEMENTS.value: {
        "technique": RefactoringTechnique.REPLACE_CONDITIONAL_WITH_POLYMORPHISM.value,
        "effort": "high",
        "risk": "medium",
        "steps": [
            "Identify the varying behavior in each branch",
            "Create a base class/interface with the common method",
            "Create subclasses for each branch",
            "Replace conditionals with polymorphic dispatch",
        ],
    },
    SmellType.GOD_CLASS.value: {
        "technique": RefactoringTechnique.EXTRACT_CLASS.value,
        "effort": "high",
        "risk": "medium",
        "steps": [
            "Identify distinct responsibilities in the class",
            "Extract each responsibility into a separate class",
            "Use composition or delegation to connect them",
            "Update all references",
        ],
    },
    SmellType.DUPLICATE_CODE.value: {
        "technique": RefactoringTechnique.CONSOLIDATE_DUPLICATE.value,
        "effort": "medium",
        "risk": "low",
        "steps": [
            "Identify the duplicate code blocks",
            "Extract into a shared method",
            "Replace all duplicates with calls to the shared method",
        ],
    },
    SmellType.LOW_COHESION.value: {
        "technique": RefactoringTechnique.EXTRACT_CLASS.value,
        "effort": "medium",
        "risk": "low",
        "steps": [
            "Identify cohesive groups of methods and fields",
            "Extract each group into a separate class",
            "Update references to use the new classes",
        ],
    },
    SmellType.SPECULATIVE_GENERALITY.value: {
        "technique": RefactoringTechnique.REMOVE_PARAMETER.value,
        "effort": "low",
        "risk": "low",
        "steps": [
            "Identify unused abstractions or parameters",
            "Remove them if no callers depend on them",
            "Run tests to confirm no impact",
        ],
    },
    SmellType.PRIMITIVE_OBSESSION.value: {
        "technique": RefactoringTechnique.EXTRACT_CLASS.value,
        "effort": "medium",
        "risk": "low",
        "steps": [
            "Group related primitive values into a value object",
            "Replace scattered primitives with the value object",
            "Update all references",
        ],
    },
    SmellType.DATA_CLUMPS.value: {
        "technique": RefactoringTechnique.INTRODUCE_PARAMETER_OBJECT.value,
        "effort": "medium",
        "risk": "low",
        "steps": [
            "Identify groups of parameters that always travel together",
            "Create a class to hold them",
            "Replace the parameter groups with the new class",
        ],
    },
    SmellType.TIGHT_COUPLING.value: {
        "technique": RefactoringTechnique.DECOUPLE_MODULES.value,
        "effort": "high",
        "risk": "medium",
        "steps": [
            "Identify direct dependencies between modules",
            "Introduce interfaces or abstractions",
            "Use dependency injection to decouple",
        ],
    },
    SmellType.INCONSISTENT_NAMING.value: {
        "technique": RefactoringTechnique.RENAME_METHOD.value,
        "effort": "low",
        "risk": "low",
        "steps": [
            "Establish a consistent naming convention",
            "Rename inconsistent names to match the convention",
            "Update all references",
        ],
    },
    SmellType.MISSING_ABSTRACTION.value: {
        "technique": RefactoringTechnique.INTRODUCE_ABSTRACTION.value,
        "effort": "medium",
        "risk": "low",
        "steps": [
            "Identify common behavior across implementations",
            "Create an abstract base class or interface",
            "Refactor implementations to use the abstraction",
        ],
    },
    SmellType.CIRCULAR_DEPENDENCY.value: {
        "technique": RefactoringTechnique.DECOUPLE_MODULES.value,
        "effort": "high",
        "risk": "medium",
        "steps": [
            "Identify the circular dependency chain",
            "Introduce an interface to break the cycle",
            "Move shared code to a third module",
        ],
    },
    SmellType.FEATURE_BRANCH.value: {
        "technique": RefactoringTechnique.EXTRACT_CLASS.value,
        "effort": "medium",
        "risk": "low",
        "steps": [
            "Identify the feature-specific behavior",
            "Extract it into a separate class or module",
            "Use composition or strategy pattern",
        ],
    },
    SmellType.MISLEADING_NAMES.value: {
        "technique": RefactoringTechnique.RENAME_METHOD.value,
        "effort": "low",
        "risk": "low",
        "steps": [
            "Choose a name that accurately describes the behavior",
            "Rename the method/variable",
            "Update all references",
        ],
    },
}


class RefactoringEngine:
    """Automated refactoring suggestion engine — patterns from alf-refactoring-advisor."""

    def __init__(self):
        self._detector = SmellDetector()

    def analyze(self, code: str, file_path: str = "<input>") -> List[RefactoringSuggestion]:
        """Analyze code and generate refactoring suggestions."""
        smells = self._detector.detect(code, file_path)
        suggestions = []
        for smell in smells:
            mapping = SMELL_TO_TECHNIQUE.get(smell.smell_type, {})
            if mapping:
                suggestion = RefactoringSuggestion(
                    smell=smell,
                    technique=mapping.get("technique", "manual_review"),
                    description=f"Apply {mapping.get('technique', 'manual review')} to fix {smell.smell_type}: {smell.description}",
                    effort=mapping.get("effort", "medium"),
                    risk=mapping.get("risk", "low"),
                    priority=self._calc_priority(smell),
                    steps=mapping.get("steps", []),
                )
                suggestions.append(suggestion)
        suggestions.sort(key=lambda s: s.priority, reverse=True)
        return suggestions

    def analyze_files(self, files: Dict[str, str]) -> List[RefactoringSuggestion]:
        """Analyze multiple files and generate refactoring suggestions."""
        all_suggestions: List[RefactoringSuggestion] = []
        for filepath, content in files.items():
            all_suggestions.extend(self.analyze(content, filepath))
        all_suggestions.sort(key=lambda s: s.priority, reverse=True)
        return all_suggestions

    def _calc_priority(self, smell: CodeSmell) -> int:
        severity_map = {"high": 3, "medium": 2, "low": 1}
        return severity_map.get(smell.severity, 1)

    def get_stats(self, suggestions: List[RefactoringSuggestion]) -> Dict[str, Any]:
        by_technique: Dict[str, int] = {}
        by_effort: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        for s in suggestions:
            by_technique[s.technique] = by_technique.get(s.technique, 0) + 1
            by_effort[s.effort] = by_effort.get(s.effort, 0) + 1
            by_severity[s.smell.severity] = by_severity.get(s.smell.severity, 0) + 1
        return {
            "total_suggestions": len(suggestions),
            "by_technique": by_technique,
            "by_effort": by_effort,
            "by_severity": by_severity,
        }
