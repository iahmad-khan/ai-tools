%{!?dist: %define dist .slc6}                                                   
%define debug_package %{nil}

Summary: Tools for Agile Infrastructure project
Name: ai-tools
Version: 1.0
Release: 0%{?dist}
BuildArch: noarch
Source: ai-tools-%{version}.tgz
Group: CERN/Utilities
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Packager: ai-admins@cern.ch
Vendor: CERN 
License: GPL

%description
A collection of tools used by CERN/IT's Agile Infrastructure project

%prep
%setup -q

%install
mkdir -p ${RPM_BUILD_ROOT}/usr/bin
install -m 755 ai-foreman-cli ${RPM_BUILD_ROOT}/usr/bin

%clean
rm -rf ${RPM_BUILD_ROOT}

%files
%defattr (-, root, root)
/usr/bin/ai-foreman-cli

%changelog
* Wed Feb  8 2012  Jan van Eldik <Jan.van.Eldik@cern.ch> - 1.0-0.slc6
- initial build
