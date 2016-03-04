%{!?dist: %define dist .ai6}
%define debug_package %{nil}

Summary: Tools for Agile Infrastructure project
Name: ai-tools
Version: 9.8
Release: 1%{?dist}
BuildArch: noarch
Source: %{name}-%{version}.tgz
Group: CERN/Utilities
BuildRoot: %{_tmppath}/%{name}-%{version}-root
Packager: ai-config-team@cern.ch
Vendor: CERN 
License: GPL+
URL: https://twiki.cern.ch/twiki/bin/view/AgileInfrastructure/WebHome

BuildRequires: python-devel
Requires: aims2-client >= 2.13.1, certmgr-client, python-krbV, python-urllib2_kerberos
Requires: perl-YAML-Syck, python-requests, python-requests-kerberos
Requires: python-argcomplete, python-humanize, teigi-client, python-dateutil
Requires: python-openstackclient, python-cinderclient
Requires: python-keystoneclient, python-novaclient
%if 0%{?el5} || 0%{?el6}
Requires: python-argparse
%endif
Obsoletes: qai

%description
A collection of tools used by CERN/IT's Agile Infrastructure project

%prep
%setup -q

%build
pod2man scripts/ai-foreman-cli > man/ai-foreman-cli.1
CFLAGS="%{optflags}" %{__python} setup.py build


%install
%{__rm} -rf %{buildroot}
%{__python} setup.py install --skip-build --root %{buildroot}
#mkdir -p ${RPM_BUILD_ROOT}/usr/bin
install -m 755 scripts/ai-foreman-cli    ${RPM_BUILD_ROOT}/usr/bin
install -m 755 scripts/ai-create-environment-metadata ${RPM_BUILD_ROOT}/usr/bin
install -m 755 scripts/ai-gen-ssh-yaml    ${RPM_BUILD_ROOT}/usr/bin
install -m 755 scripts/ai-landb-bind-mac ${RPM_BUILD_ROOT}/usr/bin
install -m 755 scripts/ai-pdb ${RPM_BUILD_ROOT}/usr/bin
install -m 755 scripts/ai-dump ${RPM_BUILD_ROOT}/usr/bin
install -m 755 scripts/ai-module-type ${RPM_BUILD_ROOT}/usr/bin
install -Dm 755 userdata/puppetinit ${RPM_BUILD_ROOT}/usr/share/ai-tools/userdata/puppetinit
mkdir -p $RPM_BUILD_ROOT/%{_mandir}/man1
install -m 644 man/ai-foreman-cli.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-create-environment-metadata.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-gen-ssh-yaml.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-bs-vm.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-kill-vm.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-rebuild-vm.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-pdb.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-dump.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-qai.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-whatfe.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-rename-host.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-set-fe.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-hiera.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-ipmi.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-remote-power-control.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/tbag.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-installhost.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-foreman.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-rc.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-disownhost.1 $RPM_BUILD_ROOT/%{_mandir}/man1/
install -m 644 man/ai-pwn.1 $RPM_BUILD_ROOT/%{_mandir}/man1/

mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/bash_completion.d
install -m 0644 -p addons/bash_completion.d/ai-tools $RPM_BUILD_ROOT/%{_sysconfdir}/bash_completion.d


%clean
rm -rf ${RPM_BUILD_ROOT}

%files
%defattr (-, root, root)
%{_bindir}/ai-*
%{_bindir}/tbag
%{python_sitelib}/*
%{_mandir}/man1/*
/usr/share/ai-tools/userdata/*
%config(noreplace) %{_sysconfdir}/bash_completion.d

%changelog
* Tue Feb 16 2016 Nacho Barrientos <nacho.barrientos@cern.ch> 9.8-1
- [ai-disownhost] Handle AiToolsRogerNotFoundError.
- [ai-rebuild-vm] Support --cc7 and friends a-la-ai-bs-vm.
- [ai-dump] Fix a crash when there was no catalog yet in PDB.

* Fri Jan 08 2016 Nacho Barrientos <nacho.barrientos@cern.ch> 9.7-1
- [ai-bs-vm] stringify_facts to false during the first run.
- [ai-installhost] Add option to override the e-mail addr.
- [ai-rc] Don't crash if $SHELL is not set.
- [ai-set-fe] Allow overriding the FE cache path via a parameter.
- [ai-foreman] Add IPMI FQDN to the list of fields when doing addhost.
- [ai-ipmi] Support IPMI interface renaming.
- [ai-foreman-cli] Add support for CC71, RHEL7 and RHEL67 targets.
- [ai-bs-vm] Allow dashes in volume types.
- [libs] Add createhostgroup function to ForemanClient.
- [libs] Handle strings properly if passed to clean_owners()
- Add support for Gitlab CI.

* Mon Nov 09 2015 Nacho Barrientos <nacho.barrientos@cern.ch> 9.6-1
- [ai-hiera] Add support for $::datacentre.
- [ai-hiera] Don't leave the output behind if --trace.
- [all] Prevent a crash from happening if the TGT is expired.
- [ai-disownhost] Add --landb-pass for non-inter sessions.
- [ai-installhost] Add --console to override the def. console redirection.
- [ai-dump] Fix crash when the object was a PDU.
- [ai-foreman-cli] Add SLC 6.7.

* Wed Sep 23 2015 Nacho Barrientos <nacho.barrientos@cern.ch> 9.5-1
- [ai-bs-vm] Add --slc5, --slc6 and --cc7 options.
- [ai-kill-vm] Swap Foreman and Openstack calls.
- Documentation fixes.

* Fri Aug 28 2015 Nacho Barrientos <nacho.barrientos@cern.ch> 9.4-1
- [ai-rc] Add support for C-shell.
- [ai-pdb] Pass deref_alias to all PdbClients.
- [ai-hiera] Pass deref_alias to PdbClient.

* Mon Jul 06 2015 Nacho Barrientos <nacho.barrientos@cern.ch> 9.3-1
- [ai-bs-vm, ai-kill-vm] Add support for Juno clients.
- [ai-bs-vm] Add support for volume types
- [ai-installhost] Allow setting a custom Roger message.
- [ai-pwn] Add console output for show operation.
- [ai-hiera] Print some hints if the key was not found.
- [all] Mask INFO messages genearated by urllib3.connectionpool.
- [all] Small documentation fixes.

* Mon Jul 06 2015 Nacho Barrientos <nacho.barrientos@cern.ch> 9.2-1
- [ai-disownhost] Released.
- [ai-rc] Released.
- [ai-pwn] Released.
- [ai-dump] Exception handling improved.
- [ai-bs-vm] Inject tenant id via the VM metadata.
- [ai-bs-vm] Ensure Facter is installed from AI.
- [ai-foreman] Minor corrections to the manpage.
- [ai-foreman-cli] Support new RHEL AIMS targets.
- Add Authz library.

* Tue Apr 21 2015 Nacho Barrientos <nacho.barrientos@cern.ch> 9.1-1
- [ai-bs-vm] Add support for deleting volumes upon instance termination.
- [ai-bs-vm] Name created volumes after the instance using them.
- [ai-bs-vm] Add option to dump the generated userdata to a file.
- [ai-kill-vm] Add --disable-* options.
- [ai-hiera] Get facts from PDB instead of Foreman.
- [ai-installhost] Add support for new RHEL AIMS targets.
- [ai-installhost] Drop support for Ferora AIMS targets.
- [ai-installhost] Differentiate between minor CentOS versions.
- [ai-foreman] Fix a couple of typos in the manpage.

* Wed Apr 01 2015 Nacho Barrientos <nacho.barrientos@cern.ch> 9.0-1
- [ai-foreman] New!
- [ai-add-param] New!
- [ai-bs-vm] Use /etc/sysconfig/puppet no matter what OS is being installed
- [ai-dump] Check if there's a Krb ticket

* Tue Mar 03 2015 Nacho Barrientos <nacho.barrientos@cern.ch> 8.13-1
- [ai-bs-vm] Make sure background runs use batch on CC7.

* Tue Feb 24 2015 Nacho Barrientos <nacho.barrientos@cern.ch> 8.12-1
- [tbag] Unescape secret string for printing
- [ai-rename-host, ai-ipmi] Fix for API change in Foreman
- [ai-rebuild-vm] First release.
- [ai-foreman-cli] Add the centos media path for CentOS machines.

* Tue Jan 06 2015 Alberto Rodriguez Peon <alberto.rodriguez.peon@cern.ch> 8.11-1
- [ai-{bs,kill}-vm] Use Openstack client manager to authenticate, which supports Kerberos

* Tue Dec 16 2014 Nacho Barrientos <nacho.barrientos@cern.ch> 8.10-1
- [foreman] Parse error messages correctly

* Mon Dec 15 2014 Steve Traylen <steve.traylen@cern.ch> 8.9-1
- [ai-foreman-cli] - display hostgroup correctley.
- [*] - update man pages to use snow for support always.

* Thu Dec 11 2014 Nacho Barrientos <nacho.barrientos@cern.ch> 8.8-1
- Several fixes adding Foreman 1.6 compatibility

* Mon Nov 17 2014 Nacho Barrientos <nacho.barrientos@cern.ch> 8.7-1
- [ai-foreman-cli] Add support for SLC/RH 5.11 and 6.6.
- [ai-bs-vm] Fix bug when attaching a new volume if dryrun is enabled.
- [ai-bs-vm] Use certmgr-getcert instead of -installack.
- [ai-bs-vm] Install LANDB gems before running Puppet for the first time.
- [ai-rename-host] Fix JFDI flag.
- [tbag] Add friendly update time in show output
- [ai-qai] [ai-whatfe] "shhh... don't look."
- [libs] EncClient: Handle 412

* Wed Oct 21 2014 Ben Jones <ben.dylan.jones@cern.ch> 8.6-1
- [tbag] Fixes for --all and --tree printing
- [common] error handling for url dereferencing
- [ai-bs-vm] support newest cc7 image
- [ai-set-fe] 'Ignore' as valid FE
- Disable all alarms by default when preparing host for install

* Tue Sep 09 2014 Steve Traylen <steve.traylen@cern.ch> 8.5-1
- [roger] - fix bool test for roger state update 
- [ai-*] - deref alias in kerberos
- [ai-{bs,kill}-vm] - improve msg on nova fail.
- [ai-dump] - add tennant name.
- [ai-installhost] - Disable alarms before insalling host.

* Tue Sep 09 2014 Gavin McCance <gavin.mccance@cern.ch> 8.4-2
- [ai-rename-host] fixes to correctl handle Foreman IPMI interface
- [ai-ipmi] tool added, allowing direct manipulation of the Foreman IPMI interface

* Mon Sep 01 2014 Nacho Barrientos <nacho.barrientos@cern.ch> 8.3-1
- [ai-bs-vm] Add support to attach volumes at boot time.
- [ai-{bs,kill}-vm] Read OS_PASSWORD from STDIN if not defined.
- [ai-bs-vm] Add support for bootstrapping CentOS7 virtual machines.
- [ai-installhost] Add support to install CentOS7 boxes.
- [ai-rename-host] Unregister the old name from AIMS.

* Tue Aug 19 2014 Alberto Rodriguez Peon <alberto.rodriguez.peon@cern.ch> 8.2-1
- [ai-installhost] Released
- [ai-bs-vm] Fix puppetinit to allow instantiation of RHEL guests

* Wed Aug 07 2014 Ben Jones <ben.dylan.jones@cern.ch> 8.1-1
- fixes for tbag binary encoding

* Thu Jul 17 2014 Ben Jones <ben.dylan.jones@cern.ch> 8.0-1
- support to boot from cinder volumes

* Wed Jul 09 2014 Ben Jones <ben.dylan.jones@cern.ch> 7.9-1
- fix binary file regression

* Wed Jul 09 2014 Ben Jones <ben.dylan.jones@cern.ch> 7.8-1
- echo secret to cmdline (still hides from ps)

* Tue Jul 08 2014 Ben Jones <ben.dylan.jones@cern.ch> 7.7-1
- tbag hides secrets on command line
- tbag allows dash and dot in secret key name
- tbag fixes behaviour when host lookup fails

* Wed Jul 02 2014 Gavin McCance <gavin.mccance@cern.ch> - 7.6-3
- ...and actually package the new qai tools in the RPM

* Wed Jul 02 2014 Gavin McCance <gavin.mccance@cern.ch> - 7.6-2
- correctly Obsoletes the qai package it replaces

* Wed Jul 02 2014 Gavin McCance <gavin.mccance@cern.ch> - 7.6-1
- ai-qai and ai-whatfe was merge into ai-tools (was separate before). Now they use the ai-tools PdbClient. Man pages included

* Mon Jun 16 2014 Gavin McCance <gavin.mccance@cern.ch> - 7.5-1
- Allow again to specify an image using the env AIBS_VMIMAGE_NAME

* Mon Jun 16 2014 Nacho Barrientos <nacho.barrientos@cern.ch> - 7.4-2
- Tweak ai-environments-reminder's email template
- [ai-bs-vm] Add support to boot from an existing volume
- [ai-bs-wm] Add tenant name to the VM metadata
- [tbag] New tree option
- [tbag] add validation on key name

* Mon Jun 16 2014 Ben Jones <ben.dylan.jones@cern.ch> - 7.4-1
- Undeployed tag, please ignore

* Mon May 19 2014 Ben Jones <ben.dylan.jones@cern.ch> - 7.3-1
- tbag binary file support

* Mon Apr 07 2014 Ben Jones <ben.dylan.jones@cern.ch> - 6.6-1
- initial tbag client
- roger fixes

* Thu Mar 27 2014 Ben Jones <ben.dylan.jones@cern.ch> - 6.5-1
- roger updates

* Thu Mar 27 2014 Nacho Barrientos <nacho.barrientos@cern.ch> - 6.4-1
- Add support for configuration snapshots

* Mon Mar 24 2014 Gavin McCance <gavin.mccance@cern.ch> - 6.3-1
- packaging bug, missing ai-set-fe, ai-rename-host

* Fri Mar 21 2014 Gavin McCance <gavin.mccance@cern.ch> - 6.3-0
- [ai-*] All tools integrate better with Roger now
- [ai-rename-host] new tool to rename physical hosts
- [ai-set-fe] new tool to set FE name for hosts
- [ai-pdb] new facts subcommand and --llan option for hostgroups
- Better unit test coverage
- AITools library easier to configure

* Thu Feb 06 2014 Nacho Barrientos <nacho.barrientos@cern.ch> - 6.2-0
- [ai-bs-vm] Light Puppet run at init time to configure Yum repositories.
- [ai-bs-vm] Run distro_sync if available.
- [ai-bs-vm] Grow /dev/vdaX.
- [ai-bs-vm] Reboot the VM to get a fresh kernel.
- [ai-dump] Add manpage
- [ai-dump] Add options --enc and --facts.

* Fri Jan 31 2014 Gavin McCance <gavin.mccance@cern.ch> - 6.1-0
- Fix command completion

* Fri Jan 31 2014 Gavin McCance <gavin.mccance@cern.ch> - 6.0-0
- Regularise options on all clients and use common config file

* Fri Jan 31 2014 Gavin McCance <gavin.mccance@cern.ch> - 5.17-0
- Added CNAME, servicename, environemnt to ai-dump

* Mon Jan 27 2014 Gavin McCance <gavin.mccance@cern.ch> - 5.16-0
- (Added comment and env, added command completion) to ai-dump

* Fri Jan 24 2014 Gavin McCance <gavin.mccance@cern.ch> - 5.15-0
- Added JSON formatter, cleaned up formatting

* Thu Jan 23 2014 Gavin McCance <gavin.mccance@cern.ch> - 5.14-0
- Initial version of ai-dump

* Mon Jan 20 2014 Nacho Barrientos <nacho.barrientos@cern.ch> - 5.13-0
- [ai-bs-vm] Use aiX-qa if --foreman-environment qa

* Fri Jan 17 2014 Nacho Barrientos <nacho.barrientos@cern.ch> - 5.12-0
- [ai-hiera] First release.

* Thu Jan 16 2014 Steve Traylen <steve.traylen@cern.ch> - 5.11-0
- Add bash completion for ai-bs-vm.

* Thu Jan 16 2014 Ben Jones <ben.dylan.jones@cern.ch> - 5.10-0
- ai-pdb fixes for hostgroup and detailed queries

* Thu Jan 16 2014 Steve Traylen <steve.traylen@cern.ch> - 5.9-0
- Add bash completion for ai-remote-power-control

* Tue Jan 14 2014 Steve Traylen <steve.traylen@cern.ch> - 5.8-0
- Add bash completion for ai-kill-vm

* Thu Dec 05 2013 Nacho Barrientos <nacho.barrientos@cern.ch> - 5.7-0
- [ai-kill-vm] Get CA cert path from the shell environment

* Wed Dec 04 2013 Nacho Barrientos <nacho.barrientos@cern.ch> - 5.6-0
- [ai-bs-vm] Get CA cert path from the shell environment

* Tue Dec 03 2013 Nacho Barrientos <nacho.barrientos@cern.ch> - 5.5-0
- [ai-bs-vm] Set owner of hosts explicitly.

* Mon Nov 25 2013 Gavin McCance <gavin.mccance@cern.ch> - 5.4-0
- bump version

* Mon Nov 25 2013 Gavin McCance <gavin.mccance@cern.ch> - 5.3-3
- bump version

* Mon Nov 25 2013 Gavin McCance <gavin.mccance@cern.ch> - 5.3-2
- AI-3287: SLC5.10/6.5, AI-3287: better messages

* Thu Nov 14 2013 Gavin McCance <gavin.mccance@cern.ch> - 5.3-1
- Fix ENC url for ksopts

* Mon Nov 11 2013 Nacho Barrientos <nacho.barrientos@cern.ch> - 5.3-0
- Install ai-remote-power-control.

* Fri Nov 08 2013 Nacho Barrientos <nacho.barrientos@cern.ch> - 5.2-0
- Set default prefix to "vm".

* Fri Nov 08 2013 Gavin McCance <gavin.mccance@cern.ch> - 5.1-0
- Misc URL and paging fixes for compatibility with Foreman 1.3. AI-3273

* Fri Oct 25 2013 Nacho Barrientos <nacho.barrientos@cern.ch> - 5.0-0
- New common API for ai-bs-vm, ai-kill-vm and ai-remote-power-control
- Reorganization of the whole source tree
- Change package's maintainer email to ai-config-team@cern.ch
- [ai-bs-vm] Rewritten in Python from scratch
- [ai-bs-vm] Foreman registration (Susie not needed anymore)
- [ai-bs-vm] Add --foreman-parameter option
- [ai-bs-vm] Add support for custom userdata fragments
- [ai-bs-vm] Use userdata script instead of boothook
- [ai-bs-vm] Drop support for security groups (not supported in Grizzly)
- [ai-kill-vm] Connected to the new API
- [ai-environments-reminder] Connected to the new API
- [ai-remote-power-control] Connected to the new API
- [ai-rmt-module-type] Installed

* Mon Oct 07 2013 Ben Jones <ben.dylan.jones@cern.ch> - 4.6-1A
- [ai-pdb] initial addition of script

* Wed Oct 02 2013 Nacho Barrientos <nacho.barrientos@cern.ch> - 4.5-0
- [ai-bs-vm] Don't allow hostgroups with dashes.

* Tue Sep 24 2013 Nacho Barrientos <nacho.barrientos@cern.ch> - 4.4-0
- [ai-bs-vm] AI-2711 Use new Linuxsoft replicas.
- [ai-create-environment-metadata] Improve user messages.

* Fri Sep 13 2013 Gavin McCance <gavin.mccance@cern.ch> - 4.3-0
- Fixed AI-2932 - bad credentials with new Foreman version

* Thu Aug 29 2013 Nacho Barrientos <nacho.barrientos@cern.ch> 4.2-0
- [ai-create-environment-metadata] Released

* Thu Aug 15 2013 Nacho Barrientos <nacho.barrientos@cern.ch> 4.1-0
- [ai-kill-vm] Typos manual page.
- [ai-kill-vm] Return 1 if some operations failed

* Thu Aug 15 2013 Nacho Barrientos <nacho.barrientos@cern.ch> 4.0-0
- Bump major version: "Kerberos era"
- Remove link ai-kill-pet
- ai-kill-vm completely rewritten with Kerberos support and Nova API

* Thu Jul 25 2013 Nacho Barrientos <nacho.barrientos@cern.ch> 3.29-0
- [ai-bs-vm] Fix manpage examples

* Thu Jul 25 2013 Nacho Barrientos <nacho.barrientos@cern.ch> 3.28-0
- [ai-foreman-cli][installhost] Bug fix for PXE target for SCL 6.1 [AI-2680]
- [ai-bs-vm] Boothook: redirect outputs to $LOGFILE avoiding file descriptor voodoo.
- [ai-bs-vm] Boothook: embed initial krb5.conf
- [ai-bs-vm] Add options to set LANDB's responsible and main user
- [ai-kill-vm] Always create a new cookie

* Tue Jul 02 2013 Jan van Eldik <Jan.van.Eldik@cern.ch> 3.27-0
- [ai-foreman-cli][installhost] Bug fix for e-mail address in KS file [AI-2579]
- [ai-foreman-cli][installhost] Bug fix for upper-case model name
- [ai-foreman-cli][installhost] Append host[params][hwdbkopts] to --kopts
- [ai-foreman-cli][installhost] Improve documentation for "--ksopts" option [AI-2637]
- [ai-foreman-cli][installhost] Bug fix for undefined model name [AI-2630]

* Fri Jun 21 2013 Nacho Barrientos <nacho.barrientos@cern.ch> 3.26-0
- [ai-bs-vm] Point initial run to the batch cluster
- [ai-bs-vm] Fill initial environment with %FOREMAN_ENVIRONMENT%
- [ai-bs-vm] Modify /etc/yum.conf with an augeas call

* Tue Jun 04 2013 Nacho Barrientos <nacho.barrientos@cern.ch> 3.25-0
- [ai-git-cherry-pick] Install
- [ai-bs-vm] Change initial Puppet interval to 1800

* Fri May 03 2013 Nacho Barrientos <nacho.barrientos@cern.ch> 3.24-0
- [ai-foreman-cli] Drop createvm subcommand
- [ai-bs-vm] Stop installing virt-what, it's included in new images.
- [ai-bs-vm] Create /etc/yum-puppet.repos.d

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
