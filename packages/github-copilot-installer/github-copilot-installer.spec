%global upstream_commit a1e6bfb096425712cb1958ea21739a4b388fcdfd

Name:           github-copilot-installer
Version:        0.1.1
Release:        3%{?dist}
Summary:        Verified installer for the GitHub Copilot app on Fedora
License:        MIT
URL:            https://github.com/ChrisTitusTech/fedora-copilot
Source0:        %{url}/archive/%{upstream_commit}/fedora-copilot-%{upstream_commit}.tar.gz
# Keep the Fedora 45 compatibility change in COPR until an upstream release includes it.
Patch0:         fedora-45.patch

BuildArch:      noarch
BuildRequires:  bash
BuildRequires:  coreutils
BuildRequires:  jq
BuildRequires:  make
Requires:       bash
Requires:       coreutils
Requires:       curl
Requires:       dnf
Requires:       jq
Requires:       rpm

%description
An open-source helper that downloads GitHub's official GitHub Copilot RPM,
verifies its published SHA-256 digest and package identity, and delegates the
transaction to DNF. The proprietary GitHub Copilot application is not included.

%prep
%autosetup -n fedora-copilot-%{upstream_commit} -p1

%build

%install
install -Dpm0755 scripts/github-copilot-installer \
    %{buildroot}%{_bindir}/github-copilot-installer
install -Dpm0644 packaging/github-copilot-installer.1 \
    %{buildroot}%{_mandir}/man1/github-copilot-installer.1

%check
bash tests/test-installer.sh

%files
%license LICENSE
%doc README.md SPEC.md ROADMAP.md
%{_bindir}/github-copilot-installer
%{_mandir}/man1/github-copilot-installer.1*

%changelog
* Wed Nov 04 2026 Chris Titus Tech <contact@christitus.com> - 0.1.1-3
- Refresh sources to upstream commit a1e6bfb with updated application update documentation
- Retain Fedora 45 compatibility

* Wed Nov 04 2026 Chris Titus Tech <contact@christitus.com> - 0.1.1-2
- Allow Fedora 45 alongside Fedora 43 and 44

* Mon Jul 27 2026 Chris Titus Tech <contact@christitus.com> - 0.1.1-1
- Accept absolute spec paths from COPR source builds

* Mon Jul 27 2026 Chris Titus Tech <contact@christitus.com> - 0.1.0-1
- Initial Fedora installer helper release
