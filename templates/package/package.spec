# Copy this file to packages/<name>/<name>.spec and replace every placeholder.
Name:           PACKAGE_NAME
Version:        PACKAGE_VERSION
Release:        1%{?dist}
Summary:        PACKAGE_SUMMARY

License:        PACKAGE_LICENSE
URL:            https://github.com/OWNER/PROJECT
Source0:        https://github.com/OWNER/PROJECT/archive/refs/tags/v%{version}.tar.gz

BuildArch:      noarch

%description
PACKAGE_DESCRIPTION

%prep
%autosetup -n PROJECT-%{version}

%build

%install
install -Dpm0755 PACKAGE_BINARY %{buildroot}%{_bindir}/PACKAGE_NAME

%files
%license LICENSE
%{_bindir}/PACKAGE_NAME

%changelog
* Thu Jan 01 2026 PACKAGE_MAINTAINER <maintainer@example.com> - PACKAGE_VERSION-1
- Initial COPR package

