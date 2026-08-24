## Summary

Describe the problem and the smallest cohesive solution.

## Verification

- [ ] A focused test failed before the implementation and now passes.
- [ ] `uv run ruff check .` passes.
- [ ] `uv run ruff format --check .` passes.
- [ ] `uv run mypy src tests` passes.
- [ ] `uv run pytest` passes.
- [ ] Documentation and changelog are updated when user-facing behavior changes.

## Risk review

- [ ] No credentials, `.env` files, private procurement records, or supplier data are included.
- [ ] Core behavior still works without an API key or external AI service.
- [ ] New dependencies and workflow permissions are necessary and narrowly scoped.
- [ ] Compatibility, privacy, and security impacts are described below.

## Additional context

Link related issues and include only synthetic or safely redistributable reproduction data.
