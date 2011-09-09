#! /usr/bin/perl -w

# Todo:
#  - filesystem layout?
#       by default nova and glance uses:
#          "/var/lib/nova/"
#          "/var/lib/glance/" 
#  - root access
#  - configure SLC6 repo's? cern-config-users...

use strict;
use diagnostics;
use Text::Template;
use POSIX;
use Getopt::Long;
use Data::Dumper;

sub Packages($$$);

my $OS   = "rhel6";
my $ARCH = "x86_64";
my $rc = Getopt::Long::GetOptions("os=s"            => \$OS,
                                  "arch=s"          => \$ARCH,
                                 );
if (not $rc){
    print STDERR "Cannot parse options...\n";;
    exit 1;
}

my @os = qw(slc4 slc5 slc6 rhel4 rhel5 rhel6);
if (not grep {$_ eq $OS} @os){
    print "Unsupported OS \"$OS\"\n";
    exit 1;
}
my @arch = qw(i386 x86_64);
if (not grep {$_ eq $ARCH} @arch){
    print "Unsupported architecture \"$ARCH\"\n";
    exit 1;
}
my @host = @ARGV;
if (not @host){
    print STDERR "No hostname(s) given...\n";;
    exit 1;
}

my %data = (OS => $OS, ARCH => $ARCH, BOOTLOADER => "");
$data{USER} = (getpwuid($<))[0];

#print Dumper(\%data);exit;


my $tpl = new Text::Template(TYPE    => "FILEHANDLE",
                             UNTAINT => 1,
                             SOURCE  => *DATA) or die "Couldn't construct template: $Text::Template::ERROR";

for my $host (@host){
    $data{HOSTNAME} = $host;
    $data{"HOSTNAME_GE"} = "${host}-gigeth";
    $data{KSFILE}   = POSIX::tmpnam();
    my $result = $tpl->fill_in(HASH => \%data);
    if (not defined $result) {
        print STDERR "Couldn't fill in template: $Text::Template::ERROR\n";
        next;
    }
    
    open(F,"> $data{KSFILE}");
    print F $result;
#    print $result;
    close F;
    (my $aims) = $result =~ /(aims2client .*)\n/;
    print STDOUT "[INFO] Upload KS-file with \"$aims\"\n";
    system("$aims; aims2client showhost $data{HOSTNAME_GE}");
    #unlink $data{KSFILE};
}

__END__
##############################################################################
#
# KickStart file for {$HOSTNAME}
#
#   uploaded with : /usr/bin/aims2client addhost --hostname {$HOSTNAME_GE} --kickstart {$KSFILE} --kopts "text noipv6 network ks ksdevice=bootif latefcload" --pxe --name RHEL6_U1_{$ARCH}
#
##############################################################################

text

lang en_US

network --bootproto=dhcp
network --bootproto=dhcp --device=eth1 --onboot=no
network --bootproto=dhcp --device=eth2 --onboot=yes --hostname {$HOSTNAME}.cern.ch
#network --bootproto=dhcp --device=eth0 --hostname {$HOSTNAME_GE}.cern.ch
#network --bootproto dhcp --device=eth1 --hostname {$HOSTNAME}.cern.ch

# installation path
url --url http://linuxsoft.cern.ch/enterprise/6Server_U1/en/os/{$ARCH}
    
#xconfig --startxonboot

keyboard us

#mouse generic3ps/2

zerombr

clearpart --drives sda --all
zerombr
part /boot    --size 1024 --ondisk sda 
part pv.01    --size 1    --ondisk sda  --grow
volgroup vg1 pv.01 
logvol /             --vgname=vg1 --size=10000  --name=root --fstype=ext4
logvol /var/lib/nova --vgname=vg1 --size=10000  --name=nova --fstype=ext4 --grow
logvol swap          --vgname=vg1 --recommended --name=swap --fstype=swap

authconfig --useshadow --enablemd5 --enablekrb5

install

timezone --utc Europe/Zurich

skipx

rootpw --iscrypted $1$ks7kG0$RT27ln7QlojbaLCyGMcoa1

auth --enableshadow --enablemd5

firewall --enabled --ssh --port=7001:udp

selinux --enforcing

firstboot --disable

# FIXME logging host=<headnode> inneresting...

# services
key --skip
services --disabled=pcscd,nfslock,netfs,portmap,rpcgssd,rpcidmapd,irqbalance,bluetooth,autofs,rhnsd,rhsmcertd

# additional repositories
#repo --name="EPEL" --baseurl http://linuxsoft.cern.ch/epel/6/{$ARCH}

# bootloader
bootloader --location=mbr --driveorder=sda

vnc

reboot

##############################################################################
#
# packages part of the KickStart configuration file
#
##############################################################################

%packages
@ Server Platform
#nss-pam-ldapd

##############################################################################
#
# pre installation part of the KickStart configuration file
#
##############################################################################

%pre


##############################################################################
#
# post installation part of the KickStart configuration file
#
##############################################################################

%post

fail () \{
    #
    # we cannot assume that mail is properly configured at this stage...
    #

    /bin/cat /root/ks-post-anaconda.log | /bin/mail -s "Subject: install failed on {$HOSTNAME}: $1" {$USER}@mail.cern.ch

    exec 4<>/dev/tcp/cernmxlb.cern.ch/25
    /bin/sleep 2
    /bin/echo -e "EHLO {$HOSTNAME}.cern.ch\r" >&4
    /bin/sleep 5
    /bin/echo -e "MAIL From:<root@{$HOSTNAME}.cern.ch>\r" >&4
    /bin/sleep 2
    /bin/echo -e "RCPT To:<{$USER}@mail.cern.ch>\r" >&4
    /bin/sleep 2
    # and off we go
    /bin/echo -e "DATA\r" >&4
    /bin/sleep 1
    /bin/echo -e "Subject: install failed on {$HOSTNAME}: $1\r\n" >&4
    /bin/sleep 1
    /bin/cat /root/ks-post-anaconda.log >&4
    /bin/echo -e "\r" >&4
    /bin/sleep 1
    /bin/echo -e ".\r" >&4
    /bin/sleep 1
    /bin/echo -e "QUIT\r" >&4
    /bin/sleep 1
    /bin/cat <&4

    exit -1
\}

trap "fail unknown\ error" ERR

# redirect the output to the log file
exec >/root/ks-post-anaconda.log 2>&1

# show the output on the seventh console
tail -f /root/ks-post-anaconda.log >/dev/tty7 &

# try to save useful stuff
/bin/mkdir /root/install-logs || :
#/bin/cp /tmp/ks-script-*.log /root/ks-post-anaconda.log || :
/bin/cp /tmp/ks-script-* /root/install-logs/ || :
/bin/cp /tmp/anaconda.log /root/install-logs/ || :

set -x 

#
# Set the correct time
#
/usr/sbin/ntpdate -bus ip-time-1 ip-time-2 || :
/sbin/clock --systohc || :

#
# first thing in the postinstall script: deregister from PXE
#
/usr/bin/wget -O /root/aims2-deregistration.txt http://linuxsoft.cern.ch/aims2server/aims2reboot.cgi?pxetarget=localboot

#
# save the Kickstart file for future reference
#
/usr/bin/wget -O /root/{$HOSTNAME_GE}.ks --quiet http://linuxsoft.cern.ch/aims2server/aims2ks.cgi\?{$HOSTNAME_GE}.ks || :

#
# YUM repo's
#
/usr/bin/wget -O /etc/yum.repos.d/rhel6.repo --quiet http://cern.ch/linux/rhel6/rhel6.repo
/usr/bin/wget -O /etc/yum.repos.d/epel.repo  --quiet http://cern.ch/linux/rhel6/epel.repo

#
# Update the machine
#
/usr/bin/yum update --assumeyes --skip-broken || :

#
# Install & configure Puppet
#
/usr/bin/yum --enablerepo=epel-testing install puppet --assumeyes || :

/bin/cat <<EOFpuppet > /etc/puppet/puppet.conf
# Initial puppet.conf to bootstrap the initial contact
# of this client to puppet master. It will almost
# certainly overwritten at first puppet succesful puppet
# execution.

[main]
  server = punch.cern.ch
  logdir = /var/log/puppet
  rundir = /var/run/puppet
  ssldir = \$vardir/ssl

[agent]
  pluginsync = false
  report = true
  classfile = \$vardir/classes.txt
  localconfig = \$vardir/localconfig

EOFpuppet

/sbin/chkconfig --list puppet || :
/sbin/chkconfig puppet on || :

#
# Ownership
#
#/usr/sbin/cern-config-users
/bin/echo ai-admins@cern.ch > /root/.forward || :
/sbin/restorecon -v /root/.forward || :

#
# Enable some YUM repositories
#

#
# /boot/grub/grub.conf
#
/usr/bin/perl -ni -e "s/ rhgb quiet//;print" /boot/grub/grub.conf || :

#
# Misc fixes
#

#
# Done
#
exit 0

