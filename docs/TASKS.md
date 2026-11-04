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

- [x] Publish the managed packages for Fedora 45 x86_64.
  - Validation on 2026-11-04: Fedora 45 builds succeeded for
    `gamescope` ([11261156](https://copr.fedorainfracloud.org/coprs/build/11261156/)),
    `github-copilot-installer` ([11261199](https://copr.fedorainfracloud.org/coprs/build/11261199/)),
    `linutil` ([11261158](https://copr.fedorainfracloud.org/coprs/build/11261158/)),
    `path` ([11261159](https://copr.fedorainfracloud.org/coprs/build/11261159/)), and
    `plazmic-legends` ([11261160](https://copr.fedorainfracloud.org/coprs/build/11261160/)).
  - The Copilot helper initially rejected Fedora 45. The local compatibility
    patch passed 13 offline installer tests for each of Fedora 43, 44, and 45,
    rejected unsupported platforms, and produced clean source and binary RPMs.
    Its corrected COPR build passed on all three releases.
  - The [corrected publishing run](https://github.com/ChrisTitusTech/copr-fedora/actions/runs/41924517045)
    passed all 27 automation tests, full package validation, and publication.
    The helper recipe pins source commit `e2a09ae4d0cea4d929b7f559b36f09c7d795adbf`.
  - Fedora 45 repository metadata lists all five binary packages. A clean
    Fedora 45 container enabled the public COPR with signature checking and
    installed all five COPR RPMs with their dependencies. Package ownership
    and `rpm -V` checks passed, as did the Copilot helper version/help,
    Linutil help, and Path daemon help checks. Gamescope was selected by
    its exact COPR version because Fedora 45 carries a newer upstream build.
    No graphical application or proprietary Copilot application was launched.
