# Path

The manifest pins Path 0.1.0 with packaging fixes at
`99aa825db8b7f35532ad139c1c3b81a0c013825c`. The source builder resolves its pin after installing Git on a clean COPR worker.
The `v0.1.0` tag remains at
`64d261ada0631798d7dbbdd27783a854f1912300`; it is not retagged.

Validate the generated sources and SRPM before submission:

```bash
python3 scripts/copr_automation.py validate --package path
```

Fedora 43 requires the separate Quickshell repository selected for this package.
After Path is approved and published, installation is:

```bash
sudo dnf copr enable errornointernet/quickshell
sudo dnf copr enable christitustech/copr-fedora
sudo dnf install path
```

On Fedora 44, Quickshell is available in the standard Fedora repositories; only
`christitustech/copr-fedora` needs enabling. Quickshell uses private Qt APIs, so
keep it updated with the Qt packages from the same Fedora release.

The dependency repository is a runtime prerequisite. It is not automatically
enabled by Path's RPM scripts, and is not needed to compile Path's RPM.
