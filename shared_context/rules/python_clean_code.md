# Directives: Python Clean Code Standards

This document specifies the technical and coding standards required for all Python code developed within the Titan platform pipelines.

## 1. Code Style & Formatting (PEP 8)
- **Naming Conventions**:
  - `snake_case` for module names, function names, and variable names.
  - `PascalCase` for classes, exceptions, and Pydantic models.
  - `UPPER_SNAKE_CASE` for constants.
- **Formatting & Line Length**:
  - Limit lines to a maximum of 100 characters where practical.
  - Use 4 spaces per indentation level. Do not mix tabs and spaces.
  - Separate top-level classes and functions with two blank lines.
- **Imports**:
  - Group imports in order: Standard Library, Third-party packages, Local application modules.
  - Separate import groups with a single blank line.

## 2. Type Hints & Annotations
- **Mandatory Type Annotations**:
  - All public function and method signatures must explicitly annotate parameter types and return types using standard Python `typing` or modern type syntax (`list[str]`, `dict[str, Any]`, `str | None`).
- **Data Structures**:
  - Prefer Pydantic `BaseModel` or standard `@dataclass` over unstructured dictionaries when passing internal domain structures or contract models.

## 3. Exception Handling & Robustness
- **Specific Exception Handling**:
  - Avoid catching generic `Exception` or using bare `except:` blocks without re-raising.
  - Catch explicit exceptions (`FileNotFoundError`, `ValueError`, `ValidationError`, `KeyError`).
- **Exception Context**:
  - Use exception chaining (`raise CustomError(...) from err`) to retain tracebacks and error context.
- **Input Validation**:
  - Perform defensive input validation at boundary interfaces (CLI commands, API endpoints, module entry points).

## 4. Documentation & Docstrings
- **Google Docstring Format**:
  - Provide descriptive docstrings for modules, classes, and public functions detailing `Args:`, `Returns:`, and `Raises:`.
- **Inline Comments**:
  - Use inline comments strictly to clarify non-obvious business logic, technical constraints, or edge-case handling.
