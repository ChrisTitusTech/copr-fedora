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

## Package operations

- [x] Configure `COPR_OWNER` and `COPR_CONFIG` and activate publication.
- [x] Publish real packages successfully on both configured Fedora chroots.
- [x] Publish `github-copilot-installer` from its immutable external SCM tag.
  - Acceptance: validation builds the external SRPM and both Fedora 43 and
    Fedora 44 x86_64 COPR builds succeed without proprietary application
    artifacts.
  - Validation: immutable tag `v0.1.1` produced COPR build 10781232; both
    configured chroots succeeded and the installed noarch helper contains
    only the MIT-licensed installer, documentation, and manual page.
