## START: Set by rpmautospec
## (rpmautospec version 0.8.4)
## RPMAUTOSPEC: autorelease, autochangelog
%define autorelease(e:s:pb:n) %{?-p:0.}%{lua:
    release_number = 1;
    base_release_number = tonumber(rpm.expand("%{?-b*}%{!?-b:1}"));
    print(release_number + base_release_number - 1);
}%{?-e:.%{-e*}}%{?-s:.%{-s*}}%{!?-n:%{?dist}}
## END: Set by rpmautospec

%global libliftoff_minver 0.5.0
%global reshade_commit 696b14cd6006ae9ca174e6164450619ace043283
%global reshade_shortcommit %(c=%{reshade_commit}; echo ${c:0:7})
%global vkroots_commit 5106d8a0df95de66cc58dc1ea37e69c99afc9540
%global vkroots_shortcommit %(c=%{vkroots_commit}; echo ${c:0:7})

Name:           gamescope
Version:        3.16.23
Release:        3.dwm_titus%{?dist}
Summary:        Micro-compositor for video games on Wayland
# Automatically converted from old format: BSD - review is highly recommended.
License:        LicenseRef-Callaway-BSD
URL:            https://github.com/ValveSoftware/gamescope
# luajit is not available on ppc64le:
# https://bugzilla.redhat.com/show_bug.cgi?id=2339416
ExcludeArch:    ppc64le

Source0:        %{url}/archive/%{version}/%{name}-%{version}.tar.gz
# Create stb.pc to satisfy dependency('stb')
Source1:        stb.pc
Source2:        https://github.com/misyltoad/reshade/archive/%{reshade_commit}/reshade-%{reshade_shortcommit}.tar.gz
Source3:        https://github.com/misyltoad/vkroots/archive/%{vkroots_commit}/vkroots-%{vkroots_shortcommit}.tar.gz

# https://github.com/misyltoad/reshade/pull/1:
Patch:          0001-cstdint.patch
# Allow to use system wlroots
# We use/package rest from the forks, I've tried to verify that wlroots match relevant commits
# We'll hold on rebases of gamescope if tags diverge in the future
Patch:          Allow-to-use-system-wlroots.patch
Patch:          Use-system-stb-glm.patch
# Backport the SDL backend shutdown fix from upstream pull request #2246.
Patch:          2246.patch

BuildRequires:  cmake
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  git-core
BuildRequires:  glm-devel
BuildRequires:  google-benchmark-devel
BuildRequires:  libXcursor-devel
BuildRequires:  libXmu-devel
BuildRequires:  meson >= 0.54.0
BuildRequires:  ninja-build
BuildRequires:  pkgconfig(hwdata)
BuildRequires:  pkgconfig(libavif)
BuildRequires:  pkgconfig(libcap)
BuildRequires:  pkgconfig(libdecor-0)
BuildRequires:  pkgconfig(libdisplay-info)
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(libeis-1.0)
BuildRequires:  (pkgconfig(libliftoff) >= %{libliftoff_minver} with pkgconfig(libliftoff) < 0.6)
BuildRequires:  pkgconfig(libpipewire-0.3)
BuildRequires:  pkgconfig(libudev)
BuildRequires:  pkgconfig(luajit)
%if 0%{?fedora} >= 44
BuildRequires:  pkgconfig(openvr) >= 2.12
%endif
BuildRequires:  pkgconfig(sdl2)
BuildRequires:  pkgconfig(vulkan)
BuildRequires:  pkgconfig(wayland-protocols) >= 1.17
BuildRequires:  pkgconfig(wayland-scanner)
BuildRequires:  pkgconfig(wayland-server)
BuildRequires:  pkgconfig(wlroots-0.18)
BuildRequires:  pkgconfig(x11)
BuildRequires:  pkgconfig(xcomposite)
BuildRequires:  pkgconfig(xdamage)
BuildRequires:  pkgconfig(xext)
BuildRequires:  pkgconfig(xfixes)
BuildRequires:  pkgconfig(xkbcommon)
BuildRequires:  pkgconfig(xrender)
BuildRequires:  pkgconfig(xres)
BuildRequires:  pkgconfig(xtst)
BuildRequires:  pkgconfig(xxf86vm)
BuildRequires:  spirv-headers-devel
# Enforce the the minimum EVR to contain fixes for all of:
# CVE-2021-28021 CVE-2021-42715 CVE-2021-42716 CVE-2022-28041 CVE-2023-43898
# CVE-2023-45661 CVE-2023-45662 CVE-2023-45663 CVE-2023-45664 CVE-2023-45666
# CVE-2023-45667, upstream issues #1860, #1861
BuildRequires:  stb_image-devel >= 2.30^20251025gitf1c79c0-2
# Header-only library: -static is for tracking per guidelines
BuildRequires:  stb_image-static
BuildRequires:  stb_image_resize-devel
BuildRequires:  stb_image_resize-static
BuildRequires:  stb_image_write-devel
BuildRequires:  stb_image_write-static
BuildRequires:  /usr/bin/glslangValidator

Provides:       bundled(vkroots) = 0^20240429git5106d8a

# libliftoff hasn't bumped soname, but API/ABI has changed for 0.2.0 release
Requires:       libliftoff%{?_isa} >= %{libliftoff_minver}
Requires:       xorg-x11-server-Xwayland
Recommends:     mesa-dri-drivers
Recommends:     mesa-vulkan-drivers

%description
%{name} is the micro-compositor optimized for running video games on Wayland.

%prep
%autosetup -p1 -N
# Install stub pkgconfig file
mkdir -p pkgconfig
cp %{SOURCE1} pkgconfig/stb.pc

# Replace spirv-headers include with the system directory
sed -i 's^../thirdparty/SPIRV-Headers/include/spirv/^/usr/include/spirv/^' src/meson.build

# Push in reshade and vkroots from sources instead of submodule
tar -xzf %{SOURCE2} --strip-components=1 -C src/reshade
tar -xzf %{SOURCE3} --strip-components=1 -C subprojects/vkroots

%autopatch -p1

%build
export PKG_CONFIG_PATH=pkgconfig
%meson \
    -Davif_screenshots=enabled \
    -Dbenchmark=enabled \
    -Ddrm_backend=enabled \
    -Denable_gamescope=true \
    -Denable_gamescope_wsi_layer=true \
%if 0%{?fedora} >= 44
    -Denable_openvr_support=true \
%else
    -Denable_openvr_support=false \
%endif
    -Dforce_fallback_for=[] \
    -Dinput_emulation=enabled \
    -Dpipewire=enabled \
    -Drt_cap=enabled \
    -Dsdl2_backend=enabled
%meson_build

%install
%meson_install --skip-subprojects

%files
%license LICENSE
%doc README.md
%{_bindir}/gamescope
%{_bindir}/gamescopectl
%{_bindir}/gamescopereaper
%{_bindir}/gamescopestream
%{_bindir}/gamescope-type
%{_datadir}/gamescope
%{_libdir}/libVkLayer_FROG_gamescope_wsi_*.so
%{_datadir}/vulkan/implicit_layer.d/VkLayer_FROG_gamescope_wsi.*.json

%changelog
* Sun Jul 12 2026 Chris Titus Tech <contact@christitus.com> - 3.16.23-3.dwm_titus
- Disable OpenVR integration on Fedora 43, where openvr-devel is unavailable

* Sun Jul 12 2026 Chris Titus Tech <contact@christitus.com> - 3.16.23-2.dwm_titus
- Backport upstream SDL backend thread shutdown fix (PR #2246)

## START: Generated by rpmautospec
* Sun Apr 19 2026 Steve Cossette <farchord@gmail.com> - 3.16.23-1
- 3.16.23

* Sun Mar 15 2026 František Zatloukal <fzatlouk@redhat.com> - 3.16.22-2
- Enable openvr

* Sun Mar 15 2026 František Zatloukal <fzatlouk@redhat.com> - 3.16.22-1
- Update to 3.16.22 (RHBZ#2447226)

* Sun Feb 15 2026 Neal Gompa <ngompa@fedoraproject.org> - 3.16.20-2
- Rebuild for libdisplay-info 0.3.0

* Sat Feb 07 2026 František Zatloukal <fzatlouk@redhat.com> - 3.16.20-1
- Update to 3.16.20 (RHBZ#2437421)

* Wed Jan 28 2026 Aleksei Bavshin <alebastr@fedoraproject.org> - 3.16.19-4
- Switch to bundled vkroots

* Sun Jan 25 2026 Aleksei Bavshin <alebastr@fedoraproject.org> - 3.16.19-3
- Rebuild for libdisplay-info 0.3.0

* Fri Jan 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 3.16.19-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Thu Dec 25 2025 František Zatloukal <fzatlouk@redhat.com> - 3.16.19-1
- Update to 3.16.19 (RHBZ#2423776)

* Sun Dec 14 2025 František Zatloukal <fzatlouk@redhat.com> - 3.16.18-1
- Update to 3.16.18 (RHBZ#2420901)

* Tue Nov 25 2025 Benjamin A. Beasley <code@musicinmybrain.net> - 3.16.17-3
- Rebuilt with latest patched stb_image: memory-safety fixes

* Sat Nov 08 2025 František Zatloukal <fzatlouk@redhat.com> - 3.16.17-2
- Backport HDR fix for KDE Plasma (RHBZ#2412031)

* Thu Oct 30 2025 František Zatloukal <fzatlouk@redhat.com> - 3.16.17-1
- Update to 3.16.17 (RHBZ#2392954)

* Sun Aug 31 2025 František Zatloukal <fzatlouk@redhat.com> - 3.16.15-1
- Update to 3.16.15 (RHBZ#2372596)

* Wed Jul 23 2025 Fedora Release Engineering <releng@fedoraproject.org> - 3.16.11-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Wed May 28 2025 František Zatloukal <fzatlouk@redhat.com> - 3.16.11-1
- Update to 3.16.11 (RHBZ#2356815)

* Tue Apr 22 2025 Simone Caronni <negativo17@gmail.com> - 3.16.4-2
- Drop duplicate line

* Thu Apr 17 2025 Simone Caronni <negativo17@gmail.com> - 3.16.4-1
- Update to 3.16.4

* Mon Apr 14 2025 Simone Caronni <negativo17@gmail.com> - 3.16.3-1
- Update to 3.16.3

* Mon Mar 17 2025 Simone Caronni <negativo17@gmail.com> - 3.16.2-1
- Update to 3.16.2

* Wed Jan 22 2025 Simone Caronni <negativo17@gmail.com> - 3.16.1-3
- luajit is not available on ppc64le

* Wed Jan 22 2025 Simone Caronni <negativo17@gmail.com> - 3.16.1-2
- Add missing patch

* Tue Jan 21 2025 Simone Caronni <negativo17@gmail.com> - 3.16.1-1
- Update to 3.16.1

* Thu Jan 16 2025 Fedora Release Engineering <releng@fedoraproject.org> - 3.15.15-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Mon Dec 09 2024 František Zatloukal <fzatlouk@redhat.com> - 3.15.15-1
- Rebase to 3.15.15 (RHBZ#2331143)

* Fri Nov 01 2024 František Zatloukal <fzatlouk@redhat.com> - 3.15.14-1
- Rebase to 3.15.14 (RHBZ#2322906)

* Sat Oct 12 2024 Steve Cossette <farchord@gmail.com> - 3.15.13-1
- Update to 3.15.13

* Mon Sep 30 2024 František Zatloukal <fzatlouk@redhat.com> - 3.15.11-1
- Rebase to 3.15.11 (RHBZ#2313953)

* Fri Sep 13 2024 František Zatloukal <fzatlouk@redhat.com> - 3.15.9-1
- Rebase to 3.15.9 (RHBZ#2309055)

* Sat Sep 07 2024 Steve Cossette <farchord@gmail.com> - 3.15.5-1
- 3.15.5

* Wed Aug 28 2024 Miroslav Suchý <msuchy@redhat.com> - 3.15.1-2
- convert license to SPDX

* Thu Aug 22 2024 František Zatloukal <fzatlouk@redhat.com> - 3.15.1-1
- Rebase to 3.15.1 (RHBZ#2307144)

* Tue Aug 20 2024 František Zatloukal <fzatlouk@redhat.com> - 3.15.0-1
- Rebase to 3.15.0

* Sun Aug 11 2024 František Zatloukal <fzatlouk@redhat.com> - 3.14.29-2
- Bump release

* Sun Aug 11 2024 František Zatloukal <fzatlouk@redhat.com> - 3.14.29-1
- Rebase to 3.14.29 (RHBZ#2274483)

* Wed Jul 17 2024 Fedora Release Engineering <releng@fedoraproject.org> - 3.14.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Mon Jul 01 2024 Aleksei Bavshin <alebastr@fedoraproject.org> - 3.14.2-2
- Rebuild for libdisplay-info 0.2 and libliftoff 0.5

* Thu Feb 22 2024 František Zatloukal <fzatlouk@redhat.com> - 3.14.2-1
- Rebase to 3.14.2 (Fixes RHBZ#2265459)

* Thu Feb 15 2024 František Zatloukal <fzatlouk@redhat.com> - 3.14.1-1
- Rebase to 3.14.1

* Thu Feb 01 2024 František Zatloukal <fzatlouk@redhat.com> - 3.14.0-1
- Rebase to 3.14.0 (Fixes RHBZ#2259316)

* Wed Jan 24 2024 Fedora Release Engineering <releng@fedoraproject.org> - 3.13.19-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Fri Jan 19 2024 Fedora Release Engineering <releng@fedoraproject.org> - 3.13.19-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Wed Dec 13 2023 František Zatloukal <fzatlouk@redhat.com> - 3.13.19-1
- Rebase to 3.13.19

* Tue Dec 12 2023 František Zatloukal <fzatlouk@redhat.com> - 3.13.18-1
- Rebase to 3.13.18 (Fixes RHBZ#2249222)

* Fri Oct 27 2023 Benjamin A. Beasley <code@musicinmybrain.net> - 3.12.7-3
- Add -static BR’s for header-only stb libraries per guidelines

* Fri Oct 27 2023 Benjamin A. Beasley <code@musicinmybrain.net> - 3.12.7-2
- Ensure stb_image contains the latest CVE patches

* Tue Oct 10 2023 František Zatloukal <fzatlouk@redhat.com> - 3.12.7-1
- Rebase to 3.12.7 (Fixes RHBZ#2242995)

* Sun Oct 08 2023 František Zatloukal <fzatlouk@redhat.com> - 3.12.6-1
- Rebase to 3.12.6 (Fixes RHBZ#2242699)

* Mon Sep 04 2023 František Zatloukal <fzatlouk@redhat.com> - 3.12.5-1
- Rebase to 3.12.5 (Fixes RHBZ#2236963)

* Sun Aug 20 2023 František Zatloukal <fzatlouk@redhat.com> - 3.12.3-1
- Rebase to 3.12.3 (Fixes RHBZ#2232483)

* Wed Jul 26 2023 Frantisek Zatloukal <fzatlouk@redhat.com> - 3.12.0-2
- Bacport i686 build fix

* Wed Jul 26 2023 Frantisek Zatloukal <fzatlouk@redhat.com> - 3.12.0-1
- Rebase to 3.12.0 (fixes RHBZ#2152065,RHBZ#2225815)

* Wed Jul 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 3.11.49-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Thu Jan 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 3.11.49-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Wed Dec 07 2022 Frantisek Zatloukal <fzatlouk@redhat.com> - 3.11.51-1
- Rebase to 3.11.51

* Fri Nov 18 2022 Onuralp SEZER <thunderbirdtr@fedoraproject.org> - 3.11.49-1
- Rebase to 3.11.49 (fixes RHBZ#2143471 )

* Sat Nov 12 2022 Onuralp SEZER <thunderbirdtr@fedoraproject.org> - 3.11.48-1
- Rebase to 3.11.48 (fixes RHBZ#2138408 )

* Mon Oct 03 2022 Frantisek Zatloukal <fzatlouk@redhat.com> - 3.11.47-1
- Rebase to 3.11.47 (fixes RHBZ#2053802 )

* Mon Sep 05 2022 Frantisek Zatloukal <fzatlouk@redhat.com> - 3.11.43-1
- Rebase to 3.11.43

* Fri Aug 19 2022 Frantisek Zatloukal <fzatlouk@redhat.com> - 3.11.36-1
- Rebase to 3.11.36

* Thu Jul 21 2022 Fedora Release Engineering <releng@fedoraproject.org> - 3.11.9-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Thu Feb 10 2022 Neal Gompa <ngompa@fedoraproject.org> - 3.11.9-1
- Rebase to 3.11.9

* Thu Jan 20 2022 Fedora Release Engineering <releng@fedoraproject.org> - 3.8.4-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Wed Jul 21 2021 Fedora Release Engineering <releng@fedoraproject.org> - 3.8.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Wed Jul 07 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 3.8.4-2
- Pin wlroots dependency to 0.13

* Sun Jul 04 2021 Neal Gompa <ngompa13@gmail.com> - 3.8.4-1
- Rebase to version 3.8.4
- Drop merged wlroots patch
- Backport patch for libliftoff 0.1.0 support
- Add explicit dependency on libliftoff >= 0.1.0

* Wed Apr 07 2021 Aleksei Bavshin <alebastr@fedoraproject.org> - 3.7.1-1
- Update to 3.7.1
- Add patch for wlroots 0.13.0 API changes

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 3.7-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Wed Nov 18 2020 Aleksei Bavshin <alebastr@fedoraproject.org> - 3.7-2
- Rebuild for wlroots 0.12

* Sun Oct  4 15:56:25 EDT 2020 Neal Gompa <ngompa13@gmail.com> - 3.7-1
- Initial packaging

## END: Generated by rpmautospec
