Name:           hello
Version:        1.0
Release:        1%{?dist}
Summary:        COPR automation test fixture
License:        MIT
Source0:        hello-1.0.tar.gz
BuildArch:      noarch

%description
Minimal package used to validate the shared SRPM target.

%prep
%autosetup

%build

%install
install -Dpm0644 README %{buildroot}%{_datadir}/hello/README

%files
%{_datadir}/hello/README

%changelog
* Thu Jan 01 2026 Test Maintainer <test@example.com> - 1.0-1
- Initial test fixture

