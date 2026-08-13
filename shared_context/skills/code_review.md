# Skill Directive: Automated Code Review Standards

This document establishes code review criteria for automated agent reviews, quality gates, and code audits.

## 1. Security & Safety Compliance
- **Secrets Audit**: Ensure no API credentials, access tokens, DB passwords, or private keys are hardcoded in source files or configuration samples.
- **Injection & Input Hazards**: Verify safe query construction (parameterized SQL), safe command execution, and sanitized file path operations.
- **Dependency Vulnerabilities**: Verify that dependencies are declared cleanly and free of known high-severity vulnerabilities.

## 2. Readability, Maintainability & Style
- **Code Cleanliness**: Verify adherence to project formatting guidelines (e.g., PEP 8 for Python).
- **Single Responsibility & Complexity**: Ensure functions are concise and single-purpose. High cyclomatic complexity or deeply nested control structures must be refactored.
- **DRY & Reusability**: Ensure code is non-repetitive; repeated patterns should be consolidated into shared helper modules.

## 3. Performance & Resource Management
- **Resource Cleanup**: Confirm files, connections, and external handles use explicit context managers (`with` statements) or explicit cleanup blocks.
- **Algorithm Efficiency**: Check for unnecessary full-table scans, redundant loops, or unindexed database operations.

## 4. Test Coverage & Quality Verification
- **Automated Test Validation**: Confirm that new or modified functionality is accompanied by automated tests covering normal operations, boundary conditions, and error paths.
- **Test Independence**: Ensure test suites run deterministically without reliance on execution order or persistent state.
- **Assertive Assertions**: Verify that tests make explicit, meaningful assertions rather than dummy checks.
