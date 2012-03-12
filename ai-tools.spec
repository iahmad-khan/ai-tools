%{!?dist: %define dist .slc6}                                                   
%define debug_package %{nil}

Summary: Tools for Agile Infrastructure project
Name: ai-tools
Version: 1.3
Release: 0%{?dist}
BuildArch: noarch
Source: ai-tools-%{version}.tgz
Group: CERN/Utilities
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Packager: ai-admins@cern.ch
Vendor: CERN 
License: GPL+
URL: https://twiki.cern.ch/twiki/bin/view/AgileInfrastructure/WebHome

%description
A collection of tools used by CERN/IT's Agile Infrastructure project

%prep
%setup -q

%build
pod2man ai-foreman-cli > ai-foreman-cli.1

%install
mkdir -p ${RPM_BUILD_ROOT}/usr/bin
install -m 755 ai-foreman-cli ${RPM_BUILD_ROOT}/usr/bin
mkdir -p $RPM_BUILD_ROOT/%{_mandir}/man1
install -m 644 ai-foreman-cli.1 $RPM_BUILD_ROOT/%{_mandir}/man1/

%clean
rm -rf ${RPM_BUILD_ROOT}

%files
%defattr (-, root, root)
/usr/bin/ai-foreman-cli
%{_mandir}/man1/ai-foreman-cli.1*

%changelog
* Fri Mar 9 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 1.3-0
- [ai-foreman-cli][bug] console parameter syntax problem
- [ai-foreman-cli][bug] verify that Foreman and DNS agree on the IP address when install machines
- [specfile] fix rpmlint warnings

* Tue Mar  6 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 1.2-0
- new action "createvm": create CVI VM
- bug fix for ac_11_30 installs

* Mon Feb 27 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 1.1-0
- support usergroups
- add man page
- additional hardware support
- minor fixes

* Wed Feb  8 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 1.0-0
- initial build
