# COPR Automation Tasks

This checklist tracks the initial repository implementation. A task is complete only after its listed validation succeeds.

- [x] Define the public `copr-fedora` project and package directory contract.
  - Acceptance: project TOML loads and an empty `packages/` directory validates.
- [x] Add reusable SRPM creation and package validation.
  - Acceptance: the fixture spec produces exactly one source RPM.
- [x] Add idempotent COPR project, package, and build management.
  - Acceptance: unit tests cover create/update, preservation, and build failure behavior.
- [x] Add pull-request validation and main/manual publishing workflows.
  - Acceptance: workflow syntax is valid and secrets are used only by the publish job.
- [x] Document maintainer setup, package onboarding, token rotation, and consumer installation.
  - Acceptance: README contains every required GitHub and COPR setup step.
- [x] Run local validation.
  - Acceptance: unit tests, package validation, Python compilation, and repository diff checks pass.

## Operator activation

- [ ] Add the `COPR_OWNER` Actions variable and `COPR_CONFIG` Actions secret.
- [ ] Push the repository to `main` and confirm the workflow creates or verifies the public project.
- [ ] Add the first real package and confirm both configured Fedora builds succeed.

Remote acceptance remains intentionally separate because it requires the repository owner's COPR credentials. The repository implementation was validated with 15 unit/integration tests, a real fixture SRPM build, Python bytecode compilation, and `actionlint` with ShellCheck integration.
