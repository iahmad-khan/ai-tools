#! /usr/bin/perl -w

# Todo:

# - note: unregistering from PXE does not work


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
use SOAP::Lite;# +trace => 'debug';
use Net::Netrc;
use File::Basename;

sub Packages($$$);
sub LandbHostInfo($);
sub SetupAims($);
sub HelpMessage();

my %data = ();
my $debug = my $verbose = my $dryrun = 0;
my %opts = (debug   => \$debug,
            dryrun  => \$dryrun,
            verbose => \$verbose);

my %landb_credentials = ();

my $rc = Getopt::Long::GetOptions(\%opts,
				  "debug","dryrun","verbose",
				  "os=s"            => \$data{OS},
                                  "arch=s"          => \$data{ARCH},
                                  "user=s"          => \$data{USER},
                                  "help" => sub { HelpMessage() },
                                 );
#print Dumper(\%opts);
if (not $rc){
    HelpMessage();
    exit 1;
}

$data{OS}     ||= "rhel6";
$data{ARCH}   ||= "x86_64";
$data{USER}   ||= (getpwuid($<))[0];
$data{PASSWD} = '$1$ks7kG0$RT27ln7QlojbaLCyGMcoa1';

my @os = qw(slc4 slc5 slc6 rhel4 rhel5 rhel6);
if (not grep {$_ eq $data{OS}} @os){
    print "Unsupported OS \"$data{OS}\"\n";
    exit 1;
}
my @arch = qw(i386 x86_64);
if (not grep {$_ eq $data{ARCH}} @arch){
    print "Unsupported architecture \"$data{ARCH}\"\n";
    exit 1;
}
my @host = @ARGV;
if (not @host){
    print STDERR "No hostname(s) given...\n";;
    exit 1;
}

my %AimsImg = (
    rhel6 => "RHEL6_U1",
    slc6  => "SLC6X",
    rhel5 => "RHES_5_U7",
    slc5  => "SLC5X",
    );

#print Dumper(\%data);exit;


my $tpl = new Text::Template(TYPE    => "FILEHANDLE",
                             UNTAINT => 1,
                             SOURCE  => *DATA) or die "Couldn't construct template: $Text::Template::ERROR";

my %todo = ();

for my $host (@host){
    $data{HOSTNAME} = $host;
    if (gethostbyname("${host}-gigeth")){
	print "[INFO] Getting LANdb info for host \"$host\", patience please...\n";
	$data{"HOSTNAME_GE"} = "${host}-gigeth";
	my @landb = LandbHostInfo($host);
	if (not @landb){
	    print "[WARNING] Could not get Landb info for \$host\", skipping it...\n";
	    next;
	}
	$data{NETWORK}  = "\n#\n# - onboot=yes for the 10GB interface, specify hostname";
	$data{NETWORK} .= "\n# - onboot=no  for the  1GB interface, do *not* specify a hostname!\n#\n\n";
	for (@landb){
	    my ($name,$mac) = @$_;
	    if ($name eq $host){
		$data{NETWORK} .= "network --bootproto=dhcp --noipv6 --device=$mac --onboot=yes --hostname $host.cern.ch\n";
	    }elsif ($name eq "${host}-gigeth"){
		$data{NETWORK} .= "network --bootproto=dhcp --noipv6 --device=$mac --onboot=no\n";
	    }
	    #print ">>> $name,$mac\n";
	}
    }else{
	$data{"HOSTNAME_GE"} = $host;
	$data{NETWORK} = "network --bootproto=dhcp --device=eth0 --hostname $host.cern.ch";
    }  
#print $data{NETWORK}."\n";
#exit;

    $data{KSFILE} = POSIX::tmpnam();

    my $image = $AimsImg{$data{OS}} . "_" . $data{ARCH};
    $data{AIMSCMD} = "/usr/bin/aims2client addhost --hostname " . $data{"HOSTNAME_GE"} . " --kickstart $data{KSFILE} --kopts \"text noipv6 network ks ksdevice=bootif latefcload console=tty0 console=ttyS2,9600n8\" --pxe --name $image";

    my $result = $tpl->fill_in(HASH => \%data);
    if (not defined $result) {
        print STDERR "Couldn't fill in template: $Text::Template::ERROR\n";
        next;
    }
    
    if (not open(F,"> $data{KSFILE}")){
        print STDERR "[ERROR] Could not open \"$data{KSFILE}\" for writing: $!\n";
	next;
    }
    print F $result;
    print $result if $debug;
    close F;

    %{$todo{$host}} = ( ksfile  => $data{KSFILE},
			aimscmd => $data{AIMSCMD},
                        gigeth  => $data{"HOSTNAME_GE"},
    );
}

if (SetupAims(\%todo)){
    print STDERR "[ERROR] Upload to AIMS failed, exiting...\n";
    exit 1;
}


print <<EOMESS;

Right. So you think this is it? Think again...

At the moment of writing this (Sept 22, 2011), there are quite some 
problems to be/being investigated. Without going into the technical
details, this is what you should do next to reinstall the machine:

-- Remove the host from the puppetmaster CA to get puppet to configure
   the host in the post-installation:

      ssh root\@punch puppetca --clean <hostname>

-- Reboot the host to start the installation:

      ssh root\@<hostname> shutdown -r now
 
   or

      ssh lxadm remote-power-control reset <hostname>

-- To see installation in progress:

      ssh lxadm connect2console.sh <hostname>

-- For "*-gigeth" machines: once the installation is underway, run 

      aims2 pxeoff <hostname>-gigeth

    to break out on an install loop

This should become simpler over time. Or not.


EOMESS

exit 0;

sub HelpMessage(){

    my $script = basename $0;
    my $user = (getpwuid($<))[0];

    print <<EOH;


Usage: $script [options] hostname [hostname]

       where options are

           --os   [rhel6|slc6]    : operating system to install
                                    default: "rhel6"
           --arch [x86_64|i386]   : architecture to install
                                    default: "x86_64"
           --user <username>      : username to be used for LANdb lookups, e-mail sending, etc
                                    default "$user" :)

           --help     : print this help
           --verbose  : print more output
           --debug    : print even more output
           --dryrun   : do not upload to AIMS

EOH

exit 0;

}

sub SetupAims($){
    my $href = shift @_;
    my %todo = %$href;
    my $rc = 0;
    #print Dumper(\%todo);
    for my $host (sort keys %todo){
	my $aims = $todo{$host}{aimscmd};
	$aims = "/bin/echo $aims" if $dryrun;
        print STDOUT "[INFO] Upload KS-file with \"$aims\"\n";
        if (system("$aims") != 0){
	    print STDERR "[ERROR] Upload to AIMS failed.\n";
	    $rc++;
	}
        unlink $todo{$host}{ksfile};
    }
    return 1 if $rc;

    print "[INFO] Verifying that AIMS is properly set up, patience please...\n";
    return 0 if $dryrun;
    $rc = 0;
    for my $host (sort keys %todo){
	my $cnt = 0;
	while (1){
	    #print "\$cnt = $cnt\n";
	    my $aims = "aims2client showhost $todo{$host}{gigeth} --full";
	    print "[VERB] Running \"$aims\"\n" if $verbose;
	    open(F,"$aims |") or die "aargh...";
	    my @out = grep /PXE boot synced:/, <F>;
	    close F;
	    my $out = "@out";
	    if ($out =~ /PXE boot synced:\s+(\S+)\n/){
		my $status = $1;
		#print ">>> $status\n";
		if (grep {$_ eq $status} qw(YYY YYN YNY NYY)){
		    print "Machine \"$host\" is ready to be reinstalled.\n";
		    $cnt = 0;
		    last;
		}
	    }
	    if ($cnt++ == 20){
		print "Machine \"$host\" still not properly configured in AIMS, giving up...\n";
		last;
	    }
	    print "Sleeping 5 seconds...\n";
	    sleep 5;
	}
	$rc += $cnt;
    }
    
    return ($rc ? 1 : 0);
}

sub LandbHostInfo($){
    my $device = shift @_;

    if (not %landb_credentials){
	print "[VERB] Getting LANdb credentials\n" if $verbose;
	my $mach = Net::Netrc->lookup("network.cern.ch");
	if ($mach){
	    $landb_credentials{user} = $mach->login;
	    $landb_credentials{passwd} = $mach->password;
	}else{
	    use Term::ReadKey;
	    print STDOUT "Please give the username/password combination to query LANdb: \n";
	    print STDOUT "   - username : ";
	    chomp($landb_credentials{user} = <STDIN>);
	    if (not defined $landb_credentials{user}){
		print STDERR "Failed to read a username, exiting\n";
		exit 1;
	    }
	    print STDOUT "   - password : ";
	    ReadMode("noecho",);
	    chomp($landb_credentials{passwd} = <STDIN>);
	    ReadMode("normal");
	    print "\n";
	    if (not defined $landb_credentials{passwd}){
		print STDERR "failed to read a passwd, exiting\n";
		exit 1;
	    }

	}
    }
    
    my $client = SOAP::Lite
	->uri('http://network.cern.ch/NetworkService')
	->xmlschema('http://www.w3.org/2001/XMLSchema')
	->proxy('https://network.cern.ch/sc/soap/soap.fcgi?v=4', keep_alive=>1);

    # Get Auth token
    my $call = $client->getAuthToken($landb_credentials{user},$landb_credentials{passwd},'NICE');
    
    my ($auth) = $call->result;
    if ($call->fault){
        print "ERROR: failed to authenticate to LANdb.\n";
        exit 1;
    }

    my $authHeader = SOAP::Header->name('Auth' => { "token" => $auth });

    $call = $client->getDeviceInfo($authHeader,$device);
	
    my $bu = $call->result;
    if ($call->fault) {
	print "[WARNING] Device \"$device\" not found in Landb, ignoring it...\n";
	return ();
    }
    #print Dumper($bu);
    my @landb = ();
    for (@{$bu->{Interfaces}}) {
	my $Name = lc($_->{Name});
	my $HardwareAddress = $_->{BoundInterfaceCard}->{HardwareAddress};
	$HardwareAddress =~ s/\-/:/g;
	push(@landb,[$Name,$HardwareAddress]);
    }
    #print Dumper(\@landb);
    #exit;
    return @landb;
}

__END__
##############################################################################
#
# KickStart file for {$HOSTNAME}
#
#   uploaded with : {$AIMSCMD}
#
##############################################################################

text

lang en_US

{$NETWORK}

# installation path
{
    if     ($OS eq  "slc4"){ $OUT .= "url --url http://linuxsoft.cern.ch/cern/slc4X/$ARCH";
    }elsif ($OS eq  "slc5"){ $OUT .= "url --url http://linuxsoft.cern.ch/cern/slc5X/$ARCH";
    }elsif ($OS eq  "slc6"){ $OUT .= "url --url http://linuxsoft.cern.ch/cern/slc6X/$ARCH";
    }elsif ($OS eq "rhel4"){ $OUT .= "url --url http://linuxsoft.cern.ch/enterprise/4ES_U8/en/os/$ARCH";
    }elsif ($OS eq "rhel5"){ $OUT .= "url --url http://linuxsoft.cern.ch/enterprise/5Server_U7/en/os/$ARCH";
    }elsif ($OS eq "rhel6"){ $OUT .= "url --url http://linuxsoft.cern.ch/enterprise/6Server_U1/en/os/$ARCH";
    }
}

keyboard us

#mouse generic3ps/2

zerombr

# XXX Hardware specific!
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

rootpw --iscrypted {$PASSWD}

auth --enableshadow --enablemd5

firewall --enabled --ssh --port=7001:udp

selinux --enforcing

firstboot --disable

# FIXME logging host=<headnode> inneresting...
logging --level=debug

# services
key --skip
services --disabled=pcscd,nfslock,netfs,portmap,rpcgssd,rpcidmapd,irqbalance,bluetooth,autofs,rhnsd,rhsmcertd

# additional repositories
#repo --name="EPEL" --baseurl http://linuxsoft.cern.ch/epel/6/{$ARCH}

# bootloader
bootloader --location=mbr --driveorder=sda

#vnc
#sshpw --username={$USER} {$PASSWD} --iscrypted

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

    /bin/cat /root/ks-post-anaconda.log | /bin/mail -s "Subject: install failed on {$HOSTNAME}: $1" {$USER}@mail.cern.ch

    exit -1
\}

trap "fail unknown\ error" ERR

# redirect the output to the log file
exec >/root/ks-post-anaconda.log 2>&1
#escript -f /root/ks-post-anaconda.log

# show the output on the seventh console
tail -f /root/ks-post-anaconda.log >/dev/tty7 &

# try to save useful stuff
/bin/mkdir /root/install-logs || :
ls -l /tmp
#/bin/cp /tmp/ks-script-*.log /root/ks-post-anaconda.log || :
/bin/cp /tmp/ks-script-* /root/install-logs/ || :
/bin/cp /tmp/*.log /root/install-logs/ || :

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

{
    if ($OS eq "rhel6"){ $OUT .= <<EOOUT
#
# YUM repo's
#
/usr/bin/wget -O /etc/yum.repos.d/rhel6.repo --quiet http://cern.ch/linux/rhel6/rhel6.repo
/usr/bin/wget -O /etc/yum.repos.d/epel.repo  --quiet http://cern.ch/linux/rhel6/epel.repo
EOOUT
    }
}

#
# Update the machine
#
/usr/bin/yum update --assumeyes --skip-broken || :

#
# Install & configure Puppet
#
/usr/bin/yum --enablerepo=epel-testing install puppet ruby-rdoc --assumeyes || :

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
# Bootstrap puppet
#
/usr/bin/puppet agent --no-daemonize --verbose --onetime --waitforcert 30 || :

#
# Ownership
#
#/usr/sbin/cern-config-users
/bin/echo {$USER}@mail.cern.ch > /root/.forward || :
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
/bin/cat /root/ks-post-anaconda.log | /bin/mail -s "Subject: installation of {$HOSTNAME} successfully completed" {$USER}@mail.cern.ch

exit 0

