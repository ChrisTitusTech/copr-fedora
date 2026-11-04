# github-copilot-installer

This COPR recipe builds the MIT-licensed installer helper from the immutable
`v0.1.1` tag in
[`ChrisTitusTech/fedora-copilot`](https://github.com/ChrisTitusTech/fedora-copilot).
The local spec applies `fedora-45.patch` so the helper accepts Fedora 43, 44,
and 45 on x86_64. Upstream v0.1.1 accepts only Fedora 43 and 44, which causes
its installer tests to fail when built on Fedora 45 without this patch.

The helper downloads GitHub's official GitHub Copilot RPM directly from GitHub
only when a user explicitly runs it. GitHub's proprietary application,
AppImage, RPM, and extracted files are not committed here and are not submitted
to or redistributed by COPR.

To publish a helper update:

1. Validate, tag, and push a new `fedora-copilot` release.
2. Update `Version` in `github-copilot-installer.spec` to that immutable tag's
   version and reset `Release` to `1`. Remove the compatibility patch when
   the upstream release includes Fedora 45 support.
3. Run the repository validation and merge the change.
4. Verify all configured COPR chroots: Fedora 43, 44, and 45 x86_64.
