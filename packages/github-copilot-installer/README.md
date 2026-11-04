# github-copilot-installer

This COPR recipe builds the MIT-licensed installer helper from the immutable
`v0.2.0` tag in
[`ChrisTitusTech/fedora-copilot`](https://github.com/ChrisTitusTech/fedora-copilot).

The helper installs and updates the latest stable GitHub Copilot desktop and
CLI releases by default, downloading each directly from GitHub only when a
user explicitly runs it. GitHub's proprietary applications, AppImage, RPM,
CLI archives, and extracted files are not committed here and are not submitted
to or redistributed by COPR.

To publish a helper update:

1. Validate, tag, and push a new `fedora-copilot` release.
2. Update `committish` in `package.toml` to that immutable tag.
3. Run the repository validation and merge the change.
4. Verify both configured COPR chroots.
