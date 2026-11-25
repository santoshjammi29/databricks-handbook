## Description

<!-- Provide a concise summary of the change, motivation, and target module/component. -->

## Type of Change

- [ ] 🐛 Bug fix (content correction or tool fix)
- [ ] ✨ New recipe / drill (authored in `src/handbook/generators/`)
- [ ] 📝 Documentation update (guides, whiteboards, runbooks)
- [ ] ⚙️ Tooling / CI/CD enhancement

## Code-Test-Doc Triad Checklist

In accordance with [`CONTRIBUTING.md`](../CONTRIBUTING.md), verify the following invariants:

- [ ] **1. Deterministic Generator Rule**: If modifying notebooks, changes were made in `src/handbook/generators/` (NOT directly in `notebooks/`), and regenerated via `make build`.
- [ ] **2. Triad Compliance**: Does the change provide theoretical mental model, runnable code, and automated test assertions?
- [ ] **3. Automated Test Assertions**: Does the recipe/module include automated tests or asserts verifying behavior?
- [ ] **4. Anti-Pattern Demonstrated**: Is there a side-by-side `Bad` vs `Good` comparison with operational consequences?
- [ ] **5. Zero Drift Verified**: Ran `make check` (or `handbook build --check`) and verified zero notebook drift.
- [ ] **6. Tests & Lint Passing**: `make test` and `make lint` pass with 100% success.
- [ ] **7. Link & Anchor Integrity**: `uv run handbook validate --target links` reports 0 broken links and 0 broken anchors.
- [ ] **8. Secret Sanitization**: No credentials, tokens, or live cloud resource identifiers are committed.
