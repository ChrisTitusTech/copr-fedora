# copr-fedora

This repository publishes community RPM packages to the public Fedora COPR project `<COPR_OWNER>/copr-fedora`. Pull requests validate package definitions without credentials. Merges to `main` create or verify the COPR project, synchronize changed package recipes, and build them for Fedora 43 and Fedora 44 on x86_64.

No example package is published. The repository starts with automation and a package template only.

## 1. Prepare Fedora COPR

1. Create a [Fedora Account System account](https://accounts.fedoraproject.org/) if needed.
2. Sign in to [Fedora COPR](https://copr.fedorainfracloud.org/).
3. Open the [COPR API page](https://copr.fedorainfracloud.org/api/) while signed in.
4. Copy the complete generated `[copr-cli]` configuration. Treat its `login` and `token` values as secrets.

The workflow creates `copr-fedora` automatically if it does not exist. If it already exists, the workflow makes it listed publicly, enables automatic repository metadata, ensures the configured Fedora chroots exist, and preserves additional chroots and packages.

## 2. Configure GitHub Actions

In `ChrisTitusTech/copr-fedora`, open **Settings > Secrets and variables > Actions**.

1. Under **Variables**, create `COPR_OWNER` with the Fedora username that owns the COPR project.
2. Under **Secrets**, create `COPR_CONFIG` and paste the complete configuration copied from the COPR API page.
3. Optionally protect `main` and require the **Validate packages** status check before merge.

COPR API tokens expire after 180 days. Replace `COPR_CONFIG` with a newly generated configuration before expiration. The workflow writes the value to a mode-restricted temporary file, never prints it, and removes it when publishing finishes.

## 3. Create a package

Package definitions use this layout:

```text
packages/
  example/
    example.spec
    optional-local-source-or-patch
```

The package directory, spec filename, and RPM `Name:` must all match. `Source` and `Patch` entries may point to public HTTPS URLs or files committed beside the spec.

To add a package:

1. Copy `templates/package/package.spec` to `packages/<name>/<name>.spec`.
2. Replace every placeholder and add any local sources or patches.
3. Use a release archive URL in `Source0` when upstream publishes one.
4. Validate locally on Fedora:

   ```bash
   sudo dnf install git make python3 rpm-build rpmdevtools rpmlint
   python3 scripts/copr.py validate --package <name>
   ```

5. Open a pull request. The credential-free validation job runs unit tests, parses every spec, downloads URL sources, and creates source RPMs.
6. Merge the pull request. The `main` workflow updates and builds only packages changed by that merge.

Changes to shared files under `.copr/`, `scripts/`, or the workflow rebuild every package. Removing a local package does not delete its COPR package or historical builds; remove those manually in COPR after confirming they are no longer needed.

## 4. Create or rebuild manually

Open **Actions > COPR > Run workflow**. Enter one package directory name or `all`.

The workflow verifies the project before every publishing run. It then adds missing COPR package recipes, updates existing recipes to match this repository, submits the requested builds concurrently, and fails if a build is unsuccessful. Build links and final states are added to the GitHub Actions job summary.

## 5. Install published packages

After at least one package builds successfully, Fedora users can enable the public repository and install it:

```bash
sudo dnf copr enable <COPR_OWNER>/copr-fedora
sudo dnf install <package-name>
```

Replace `<COPR_OWNER>` with the Fedora username configured in GitHub and `<package-name>` with the RPM name. COPR maintains downloadable RPM metadata automatically after successful builds.

## Behavior and safety

- Pull requests never receive COPR credentials and never mutate COPR.
- Publishing is limited to pushes to `main` and manually authorized workflow runs.
- Publishing runs are serialized so project and package updates cannot race.
- Binary build network access is disabled. URL sources are fetched while producing the source RPM.
- Native COPR webhook rebuilding is disabled because GitHub Actions owns the trigger.
- The automation never calls COPR deletion APIs. COPR's standard server-side build retention still applies.

Project settings live in `.copr/project.toml`. COPR uses `.copr/Makefile` with its documented `make_srpm` source method, so package specs remain ordinary RPM spec files rather than rpkg templates.
