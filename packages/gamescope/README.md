# Patched Gamescope

This package carries the Gamescope build previously published on the
`gamescope-x11-display-fixes` branch of `ChrisTitusTech/dwm-titus`.

## Provenance

- Base package: Fedora `gamescope-3.16.23-1.fc44.src.rpm`
- Custom release: `3.16.23-2.dwm_titus`
- Original packaging commit: `d9ef9cb0ceee602ed810e57bdef4a4151e267c9a`
- Custom backport: ValveSoftware/gamescope pull request 2246, upstream commit
  `191c7920ff04f7a92011cc2259b1a5c3e291839b`

The custom patch stops and joins the SDL backend thread during shutdown. It
prevents the `std::terminate` crash that occurred when an SDL-backed Gamescope
session exited. The remaining patches and source configuration come unchanged
from the Fedora source RPM used for the original local build.

The COPR release is bumped to `3.16.23-3.dwm_titus` to support both project
chroots. Fedora 44 retains the original OpenVR integration. Fedora 43 builds
without OpenVR because that release does not provide `openvr-devel`; the SDL,
DRM, PipeWire, Vulkan, X11, and Wayland functionality remains enabled.

Source archives are downloaded from their upstream HTTPS URLs during SRPM
creation. The package directory keeps the Fedora patches, the custom backport,
and the local `stb.pc` source file needed to reproduce the package.
