%global upstream_version 2026.05.21

Name:           linutil
Version:        26.5.21
Release:        1%{?dist}
Summary:        Distribution-independent toolbox for everyday Linux tasks

License:        Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND ISC AND MIT AND NCSA AND Unicode-3.0 AND Zlib
URL:            https://github.com/ChrisTitusTech/linutil
Source0:        %{url}/archive/%{upstream_version}/%{name}-%{upstream_version}.tar.gz
# Generated from the release Cargo.lock; see README.md for the exact command.
Source1:        %{name}-vendor-%{version}.tar.zst

ExclusiveArch:  x86_64

BuildRequires:  cargo
BuildRequires:  desktop-file-utils
BuildRequires:  gcc
BuildRequires:  rust
BuildRequires:  rust-packaging
Requires:       bash

%description
Linutil is a distribution-independent terminal toolbox that helps users set up
applications and optimize Linux systems for specific use cases.

%prep
%autosetup -n %{name}-%{upstream_version} -a 1
# The upstream launcher falls back to Cargo and shell PATH installations. This
# package always provides the binary at the standard system path.
sed -i 's|^Exec=.*|Exec=%{_bindir}/%{name}|' %{name}.desktop
%cargo_prep -v vendor

%build
%cargo_build
%cargo_license_summary
{
%cargo_license
} > LICENSE.dependencies

%install
install -Dpm0755 target/rpm/%{name} %{buildroot}%{_bindir}/%{name}
install -Dpm0644 %{name}.desktop \
    %{buildroot}%{_datadir}/applications/%{name}.desktop
install -Dpm0644 man/%{name}.1 %{buildroot}%{_mandir}/man1/%{name}.1

%check
%cargo_test
desktop-file-validate %{name}.desktop
target/rpm/%{name} --help >/dev/null

%files
%license LICENSE LICENSE.dependencies
%doc README.md
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_mandir}/man1/%{name}.1*

%changelog
* Mon Jul 13 2026 Chris Titus Tech <contact@christitus.com> - 26.5.21-1
- Package the 2026.05.21 upstream release
- Build from source with locked, vendored Rust dependencies
