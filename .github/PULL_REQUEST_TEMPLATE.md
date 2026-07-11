## What this changes

<!-- One or two sentences: what does this PR do, and why. -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactor (no behavior change)
- [ ] Other:

## Behavior changes

<!--
List any change in observable behavior, even small ones — schema field
changes, new required env vars, changed defaults, new error responses,
etc. Write "None" if this is a pure refactor/doc change.
-->

## Checklist

- [ ] `make test` passes (backend)
- [ ] `npm run lint && npx tsc --noEmit && npm run build` passes (frontend, if touched)
- [ ] Updated `frontend/types/*.ts` if I changed a backend Pydantic schema
- [ ] Updated relevant docs in `docs/` if I changed documented behavior
- [ ] No secrets, API keys, or credential files included in this diff

## Related issue

<!-- Closes #... , or "N/A" -->
