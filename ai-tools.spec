%{!?dist: %define dist .ai6}                                                   
%define debug_package %{nil}

Summary: Tools for Agile Infrastructure project
Name: ai-tools
Version: 3.23
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
Requires: perl-YAML-Syck

%description
A collection of tools used by CERN/IT's Agile Infrastructure project

%prep
%setup -q

%build
pod2man ai-foreman-cli > ai-foreman-cli.1

%install
mkdir -p ${RPM_BUILD_ROOT}/usr/bin
install -m 755 ai-foreman-cli    ${RPM_BUILD_ROOT}/usr/bin
install -m 755 ai-gen-ssh-yaml    ${RPM_BUILD_ROOT}/usr/bin
install -m 755 ai-landb-bind-mac ${RPM_BUILD_ROOT}/usr/bin
install -m 755 ai-bs-vm ${RPM_BUILD_ROOT}/usr/bin
install -m 755 ai-kill-vm ${RPM_BUILD_ROOT}/usr/bin
ln -s /usr/bin/ai-kill-vm ${RPM_BUILD_ROOT}/usr/bin/ai-kill-pet
install -Dm 755 userdata/common ${RPM_BUILD_ROOT}/usr/share/ai-tools/userdata/common
mkdir -p $RPM_BUILD_ROOT/%{_mandir}/man1
install -m 644 ai-foreman-cli.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 ai-gen-ssh-yaml.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 ai-bs-vm.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 ai-kill-vm.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
ln -s %{_mandir}/man1/ai-kill-vm.1 $RPM_BUILD_ROOT/%{_mandir}/man1/ai-kill-pet.1

%clean
rm -rf ${RPM_BUILD_ROOT}

%files
%defattr (-, root, root)
%doc README.judy
/usr/bin/ai-foreman-cli
/usr/bin/ai-landb-bind-mac
/usr/bin/ai-bs-vm
/usr/bin/ai-kill-vm
/usr/bin/ai-kill-pet
/usr/bin/ai-gen-ssh-yaml
%{_mandir}/man1/ai-foreman-cli.1*
%{_mandir}/man1/ai-bs-vm.1*
%{_mandir}/man1/ai-kill-pet.1*
%{_mandir}/man1/ai-kill-vm.1*
%{_mandir}/man1/ai-gen-ssh-yaml.1*
/usr/share/ai-tools/userdata/*

%changelog
* Tue Apr 30 2013 Nacho Barrientos <nacho.barrientos@cern.ch> 3.23-0
- [ai-foreman-cli] Sanity check: do not try to configure AIMS for hosts that are registered as "unmanaged" in Foreman (AI-2142)
- [ai-foreman-cli] Minor updates to the values of the default parameters of the "disownhost" action
- [ai-bs-vm] Generate random hostname if none is specified in the command line
- [ai-bs-vm] Add parameter AIBS_VMNAME_PREFIX
- [ai-bs-vm] Limit hostname length to 60 characters
- [ai-bs-vm] Drop pet and cattle distinction
- [ai-bs-pet] Totally removed

* Wed Apr 03 2013 Nacho Barrientos <nacho.barrientos@cern.ch> 3.22-0
- [ai-bs-vm] Use FQDN when unstaging a host
- [ai-bs-vm] Add options AIBS_{PUPPETMASTER, CASERVER}_HOSTNAME
- [ai-bs-vm] Flush /etc/yum.repos.d/

* Fri Mar 22 2013 Jan van Eldik <Jan.van.Eldik@cern.ch> 3.21-0
- [ai-foreman-cli] Aims sync status now simply "Y" when successfull (AI-2014)
- [ai-foreman-cli] Don't print misleading error messages when adding a new host (AI-1574)

* Wed Mar 20 2013 Jan van Eldik <Jan.van.Eldik@cern.ch> 3.20-0
- [ai-foreman-cli] make "--ptable" option mandatory for "addhost" action (AI-1984)

* Mon Mar 18 2013 Nacho Barrientos <nacho.barrientos@cern.ch> 3.19-0
- [ai-bs-vm] Make AIBS_SSHKEY_NAME optional
- [ai-bs-vm] Minor changes to the documentation

* Mon Mar 11 2013 Nacho Barrientos <nacho.barrientos@cern.ch> 3.18-0
- [ai-bs-vm] More defensive userdata.
- [ai-bs-vm] Add option AIBS_METAPARAMETERS_LIST. Patch by Tom K.
- [ai-bs-vm] Manpage reformatting.
- [ai-bs-pet] Deprecated.

* Tue Mar 05 2013 Nacho Barrientos <nacho.barrientos@cern.ch> 3.17-0
- [ai-bs-vm] Allow dashes and underscores in the hostgroup name

* Fri Mar 01 2013 Nacho Barrientos <nacho.barrientos@cern.H> 3.16-0
- [ai-bs-vm] Add option AIBS_SECURITYGROUPS_LIST
- [ai-bs-*] Change default VM flavor to m1.small
- [ai-bs-vm] Customizable Susie URL via AIBS_SUSIE_{HOSTNAME,PORT}
- [ai-foreman-cli] add handling of "alarmed" parameter (AI-1789)

* Tue Feb 26 2013 Nacho Barrientos <nacho.barrientos@cern.ch> 3.15-0
- [ai-bs-*] Make them Ibex's-Nova-client-friendly

* Thu Feb 21 2013 Nacho Barrientos <nacho.barrientos@cern.ch> 3.14-0
- [ai-bs-pet] Fix JSON payload when creating a host
- [ai-bs-vm] More friendly output in case of cmdline errors

* Mon Feb 11 2013 Nacho Barrientos <nacho.barrientos@cern.H> 3.13-0
- [ai-bs-vm] Use cern-get-keytab instead of cern-config-keytab
- [ai-bs-vm] Show tenant name
- [ai-bs-vm] Add prerequisites to manpage

* Wed Feb 06 2013 Steve Traylen <steve.traylen@cern.ch> - 3.12-0
- [ai-gen-ssh-yaml] Addition of new script.

* Wed Feb 06 2013 Nacho Barrientos <nacho.barrientos@cern.ch> - 3.11-0
- [ai-bs-vm] Retry VM registration only once
- [ai-bs-vm] Fix nova exit code evaluation (AI-1618)
- [ai-kill-vm] Validate SSO cookie before deleting anything (AI-1610)

* Thu Jan 31 2013 Nacho Barrientos <nacho.barrientos@cern.ch> - 3.10-0
- [ai-bs-vm] Released
- [ai-kill-pet] Renambed to ai-kill-vm.

* Thu Jan 31 2013 Nacho Barrientos <nacho.barrientos@cern.ch> - 3.9-0
- [ai-foreman-cli] Stop sending sp_* when creating a host (AI-1566)
- [ai-foreman-cli] support medium "RedHat", + minor fixes
- [ai-foreman-cli] remove references to recently removed "base" hostgroup

* Thu Jan 17 2013 Jan van Eldik <Jan.van.Eldik@cern.ch> - 3.8-0
- [ai-foreman-cli] add "--reset" option for the addhost case (AI-1475)

* Tue Jan 08 2013 Jan Iven <jan.iven@cern.ch> - 3.7-0
- [ai-foreman-cli] add "ksopts" argument for "installhost"; clean up man page
- [ai-bs-pet] Print out HTTP status code in case of failure [NB]
- [ai-bs-pet] Rename openssl-CERN-CA-certs on SLC5 (patch by TK) [NB]

* Tue Nov 20 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 3.6-0
- [ai-foreman-cli] add action "disownhost"
- [ai-foreman-cli] addhost: introduce default h/w model "undefined"
- Minor updates

* Mon Nov 19 2012 Jan van Eldik <Jan.van.Eldik@cern.ch> - 3.5-0
- [ai-foreman-cli] prepare installation of Windows hosts
- Minor updates

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
