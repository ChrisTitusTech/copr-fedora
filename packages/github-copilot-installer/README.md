# github-copilot-installer

This COPR recipe builds the MIT-licensed installer helper from upstream commit
`a1e6bfb096425712cb1958ea21739a4b388fcdfd` in
[`ChrisTitusTech/fedora-copilot`](https://github.com/ChrisTitusTech/fedora-copilot).
The helper remains version 0.1.1. RPM release 3 includes upstream's updated
application update instructions and validation documentation for GitHub
Copilot 1.1.34; the upstream installer code is unchanged from v0.1.1.
The local spec applies `fedora-45.patch` so the helper accepts Fedora 43, 44,
and 45 on x86_64. The upstream helper accepts only Fedora 43 and 44, which causes
its installer tests to fail when built on Fedora 45 without this patch.

The helper downloads GitHub's official GitHub Copilot RPM directly from GitHub
only when a user explicitly runs it. GitHub's proprietary application,
AppImage, RPM, and extracted files are not committed here and are not submitted
to or redistributed by COPR.

Application updates are separate from helper RPM updates. The helper resolves
the latest official application release whenever the user runs:

```bash
sudo github-copilot-installer update
```

To publish a helper update:

1. Validate, tag, and push a new `fedora-copilot` release.
2. Update `upstream_commit` in `github-copilot-installer.spec` to the release's
   full Git commit SHA. Update `Version` to the upstream helper version and
   reset `Release` to `1` for a new helper version; otherwise increment
   `Release`. Remove the compatibility patch when the upstream release
   includes Fedora 45 support.
3. Run the repository validation and merge the change.
4. Verify all configured COPR chroots: Fedora 43, 44, and 45 x86_64.
