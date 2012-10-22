%{!?dist: %define dist .ai6}                                                   
%define debug_package %{nil}

Summary: Tools for Agile Infrastructure project
Name: ai-tools
Version: 3.4
Release: 0%{?dist}
BuildArch: noarch
Source: %{name}-%{version}.tgz
Group: CERN/Utilities
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Packager: ai-admins@cern.ch
Vendor: CERN 
License: GPL+
URL: https://twiki.cern.ch/twiki/bin/view/AgileInfrastructure/WebHome

Requires: aims2-client, certmgr-client, python-novaclient
 
%description
A collection of tools used by CERN/IT's Agile Infrastructure project

%prep
%setup -q

%build
pod2man ai-foreman-cli > ai-foreman-cli.1

%install
mkdir -p ${RPM_BUILD_ROOT}/usr/bin
install -m 755 ai-foreman-cli    ${RPM_BUILD_ROOT}/usr/bin
install -m 755 ai-landb-bind-mac ${RPM_BUILD_ROOT}/usr/bin
install -m 755 ai-bs-pet ${RPM_BUILD_ROOT}/usr/bin
install -m 755 ai-kill-pet ${RPM_BUILD_ROOT}/usr/bin
install -Dm 755 userdata/pet ${RPM_BUILD_ROOT}/usr/share/ai-tools/userdata/pet
mkdir -p $RPM_BUILD_ROOT/%{_mandir}/man1
install -m 644 ai-foreman-cli.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 ai-bs-pet.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 ai-kill-pet.1 $RPM_BUILD_ROOT/%{_mandir}/man1/

%clean
rm -rf ${RPM_BUILD_ROOT}

%files
%defattr (-, root, root)
%doc README.judy
/usr/bin/ai-foreman-cli
/usr/bin/ai-landb-bind-mac
/usr/bin/ai-bs-pet
/usr/bin/ai-kill-pet
%{_mandir}/man1/ai-foreman-cli.1*
%{_mandir}/man1/ai-bs-pet.1*
%{_mandir}/man1/ai-kill-pet.1*
/usr/share/ai-tools/userdata/pet

%changelog
* Mon Oct 22 2012 Nacho Barrientos <nacho.barrientos@cern.ch> - 3.4-0
- Userdata support for SLC5
- Support for generic SLC images
- Change default image to "SLC6 Server"

* Thu Oct 11 2012 Nacho Barrientos <nacho.barrientos@cern.ch> - 3.3-0
- Restart syslog
- Wait for DNS before packages are installed
- Change default image to [AI] SLC6 Server
- Rename env var: AIBS_VMIMAGE_ID -> AIBS_VMIMAGE_NAME

* Wed Oct 10 2012 Nacho Barrientos <nacho.barrientos@cern.ch> - 3.2-0
- Add option AIBS_VMAVAILZONE_NAME to ai-bs-pet

* Mon Oct 08 2012 Nacho Barrientos <nacho.barrientos@cern.ch> - 3.1-0
- Add script ai-kill-pet
- Improve DNS logic in default userdata for pets
- Change boothook's default path
- Print out Foreman response if the registration fails

* Fri Oct 05 2012 Nacho Barrientos <nacho.barrientos@cern.ch> - 3.0-0
- Add script ai-bs-pet and userdata for pet usecase

* Mon Sep 17 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 2.4-0
- Ensure MAC-addresses use ":" as a separator

* Thu Sep 13 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 2.3-0
- Oops... [AI-933]

* Tue Sep 11 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 2.2-0
- Addhost: determine ("guess") MAC address in case the main interface is not bound in Landb
- remove references to CDB-style hardware models
- Showhost: Display owner if it's a group [AI-924]
- minor fixes

* Wed Aug 29 2012 Nacho Barrientos <nacho.barrientos@cern.ch> - 2.1-0
- Showhost: Fix --all
- Showhost: Replace --regexp by --filter

* Wed Aug 22 2012 Nacho Barrientos <nacho.barrientos@cern.ch> - 2.0-0
- First Judy era release.
- Judy API support.
- --foreman-host and --foreman-port options.
- SSO support (--foreman-cookie).
- CertMgr support.
- Drop admin privileges constraint.
- Better response status code handling.

* Thu Jul 19 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 1.11-0
- oops...

* Thu Jul 19 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 1.10-0
- [ai-foreman-cli] Add "nodmraid" kernel parameter to the options passed to AIMS (AI 738, SNOW INC147316)

* Mon Jul  9 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 1.9-0
- [ai-foreman-cli] fix issue in case of missing Landb data for IPMI interface

* Mon Jun 25 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 1.8-0
- added script "ai-landb-bind-mac"
- minor fixes

* Tue Jun  5 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 1.7-0
- bug fix for dl_11_20 installs

* Tue May 22 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 1.6-1
- small updates to build under Koji

* Mon May 21 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 1.6-0
- print helpful message when unknown "--owner" is specified (AI-336)
- on Hyper-V VMs, use Aims target w/ ICs for SLC 6.2
- [specfile] add "Requires: aims2-client"

* Wed Mar 21 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 1.5-0
- Support SLC + RedHat 5.8
- createvm: new option "--template"
- Improved handling of possible AIMS problems (AI-317)

* Thu Mar 15 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 1.4-0
- [ai-foreman-cli][bug] fixes for "createvm" mode (AI-286)

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
