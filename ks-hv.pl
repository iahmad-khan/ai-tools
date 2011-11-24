#! /usr/bin/perl -w

# Todo:

# - note: unregistering from PXE does not work


#  - filesystem layout?
#       by default nova and glance uses:
#          "/var/lib/nova/"
#          "/var/lib/glance/" 

use strict;
use diagnostics;
use Text::Template;
use POSIX;
use Getopt::Long;
use Data::Dumper;
use SOAP::Lite;# +trace => 'debug';
use Net::Netrc;
use Term::ReadKey;
use File::Basename;
use LWP;
use JSON;
use Socket;

sub LandbHostInfo($);
sub SetupAims($);
sub SetupForeman($);
sub HelpMessage();
sub getId($$$$$);

HelpMessage() if not @ARGV;

my %data = ();
my $debug = my $verbose = my $dryrun = 0;
my %opts = (debug   => \$debug,
            dryrun  => \$dryrun,
            verbose => \$verbose);

my $rc = Getopt::Long::GetOptions(\%opts,
				  "debug","dryrun","verbose",
				  "os=s"            => \$data{OS},
                                  "arch=s"          => \$data{ARCH},
                                  "cern-user=s"     => \$data{USER},
                                  "help" => sub { HelpMessage() },
                                 );
#print Dumper(\%opts);

HelpMessage() if not $rc;

$data{OS}     ||= "slc6";
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

map {s/.cern.ch//;$_ = lc} @host;  # strip domain name, change to lower case

# XXX todo: verify if user has a cern account.

# Get user credentials

my %user_credentials = ();
my $mach = Net::Netrc->lookup("network.cern.ch",$data{USER});
if ($mach){
    $user_credentials{username} = $mach->login;
    $user_credentials{password} = $mach->password;
}else{
    print STDOUT "Please give the CERN username/password combination to query LANdb, talk to Foreman, etc: \n";
    print STDOUT "   - username : ";
    chomp($user_credentials{username} = <STDIN>);
    if (not defined $user_credentials{username}){
	print STDERR "Failed to read a username, exiting\n";
	exit 1;
    }
    print STDOUT "   - password : ";
    ReadMode("noecho",);
    chomp($user_credentials{password} = <STDIN>);
    ReadMode("normal");
    print "\n";
    if (not defined $user_credentials{password}){
	print STDERR "failed to read a password, exiting\n";
	exit 1;
    }
}

my %AimsImg = (
    rhel6 => "RHEL6_U1_$data{ARCH}",
    slc6  => "SLC6X_$data{ARCH}",
    rhel5 => "RHES_5_U7_$data{ARCH}",
    slc5  => "SLC5X_$data{ARCH}",
    );

#print Dumper(\%data);exit;


my $tpl = new Text::Template(TYPE    => "FILEHANDLE",
                             UNTAINT => 1,
                             SOURCE  => *DATA) or die "Couldn't construct template: $Text::Template::ERROR";

my %todo = ();

for my $host (@host){
    $data{HOSTNAME} = $host;
    print "[INFO] Getting LANdb info for host \"$host\", patience please...\n";
    my %landb = LandbHostInfo($host);
    if (not %landb){
	print "[WARNING] Could not get Landb info for \$host\", skipping it...\n";
	next;
    }
    my @mac = ();
    map {push(@mac,$$_[1])} @{$landb{Interfaces}};
    #print "MAC @mac\n";exit;

    if (gethostbyname("${host}-gigeth")){
	$data{"HOSTNAME_GE"} = "${host}-gigeth";
	$data{NETWORK}  = "\n#\n# - onboot=yes for the 10GB interface, specify hostname";
	$data{NETWORK} .= "\n# - onboot=no  for the  1GB interface, do *not* specify a hostname!\n#\n\n";
	for (@{$landb{Interfaces}}){
	    my ($name,$mac) = @$_;
	    if ($name eq $host){
		$data{NETWORK} .= "network --bootproto=dhcp --device=$mac --onboot=yes --hostname $host.cern.ch\n";
	    } elsif ($name eq "${host}-gigeth"){
		$data{NETWORK} .= "network --bootproto=dhcp --device=$mac --onboot=no\n";
	    }
	    #print ">>> $name,$mac\n";
	}
    }else{
	$data{"HOSTNAME_GE"} = $host;
	$data{NETWORK} = "network --bootproto=dhcp --device=eth0 --hostname $host.cern.ch";
    }
    $data{HWMODEL} = $landb{Model};

    $data{KSFILE} = POSIX::tmpnam();

    my $console = uc($data{HWMODEL}) ne "HYPER-V VIRTUAL MACHINE" ? "console=tty0 console=ttyS2,9600n8" : "";

    $data{AIMSCMD} = "/usr/bin/aims2client addhost --hostname " . $data{"HOSTNAME_GE"} . " --kickstart $data{KSFILE} --kopts \"text network ks ksdevice=bootif latefcload $console\" --pxe --name $AimsImg{$data{OS}}";

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
			mac     => [@mac],                # to be used in Foreman
    );
}

#
# Add to AIMS
#
@host = SetupAims(\%todo);
if (not @host){
    print STDERR "[ERROR] Upload to AIMS failed, exiting...\n";
    exit 1;
}

#
# Add to Foreman
#
SetupForeman(\%todo);


map {print "[INFO] Machine \"$_\" is ready to be reinstalled.\n"} sort @host;


#my $mess1 = join("\n",map {"      ssh root\@punch puppetca --clean $_.cern.ch"} @host);
my $mess2 = join("\n",map {"      ssh root\@$_ shutdown -r now"} @host);
my $mess3 = join("\n",map {"      ssh lxadm remote-power-control reset $_"} @host);
my $mess4 = join("\n",map {"      ssh lxadm connect2console.sh $_"} @host);
my $mess5 = join("\n",map {"      aims2 pxeoff $_-gigeth"} @host);

print <<EOMESS;

Right. So you think this is it? Think again...

At the moment of writing this (Sept 22, 2011), there are quite some 
problems to be/being investigated. Without going into the technical
details, this is what you should do next to reinstall the machine:

-- Reboot the host to start the installation:

$mess2

   or

$mess3

-- To see installation in progress:

$mess4

-- For "*-gigeth" machines: once the installation is underway, run 

$mess5

    to break out on an install loop

This should become simpler over time. Or not.


EOMESS

exit 0;

sub SetupForeman($){
    my $href = shift @_;
    my %todo = %$href;
    my $rc = 0;
#    print Dumper(\%todo);exit;


    my $group    = "base";
    my $environ  = "devel";
    my $domain   = "cern.ch";
    my $ptable   = "RedHat default";

    my %OS = (
	"SLC6" => "SLC 6.1",
	"RHEL6" => "RedHat 6.1",
	);
    die if not exists $OS{uc($data{OS})};

    my $url         = "https://punch.cern.ch";
    my $netlocation = "punch.cern.ch:443";
    my $realm       = "Application";

    my $browser  = LWP::UserAgent->new;
    $browser->credentials($netlocation,$realm,$user_credentials{username} => $user_credentials{password});

    my %tmp = (comment => "Machine Provisioned by Kickstart");
    
    $tmp{operatingsystem_id} = &getId(\$browser->get("$url/operatingsystems?format=json"),"operatingsystem","name", $OS{uc($data{OS})},         "id");
    $tmp{hostgroup_id}       = &getId(\$browser->get("$url/hostgroups?format=json"),      "hostgroup",      "label",$group,                     "id");
    $tmp{environment_id}     = &getId(\$browser->get("$url/environments?format=json"),    "environment",    "name", $environ,                   "id");
    $tmp{architecture_id}    = &getId(\$browser->get("$url/architectures?format=json"),   "architecture",   "name", $data{ARCH},                "id");
    $tmp{domain_id}          = &getId(\$browser->get("$url/domains?format=json"),         "domain",         "name", $domain,                    "id");
    $tmp{ptable_id}          = &getId(\$browser->get("$url/ptables?format=json"),         "ptable",         "name", $ptable,                    "id");
    $tmp{owner_id}           = &getId(\$browser->get("$url/users?format=json"),           "user",           "login",$user_credentials{username},"id");

    for my $host (sort keys %todo){
	$tmp{name} = $host;

	# IP address
	my $iaddr = gethostbyname($host);
	die "aargh..." if not defined $iaddr;
	$tmp{ip} = inet_ntoa($iaddr);
	die "aaargh..." if not defined $tmp{ip};

	# MAC address.
	$tmp{mac} = [@{$todo{$host}{mac}}];
	$tmp{mac} = ${$todo{$host}{mac}}[0]; # JvE, Nov 2011: Foreman does not handle multiple MAC addresses?

	# First, delete the entry from Foreman
	my $request = HTTP::Request->new("DELETE","$url/hosts/$host.$domain");
	$request->header("Content-Type" => "application/json");
	my $response = $browser->request($request);
	#if (not $response->is_success){
	#    print "[ERROR] Cannot remove \"$host\" from Foreman: " . $response->status_line . " :: " . $response->content ."\n";
	#    #next;
	#}

	# Then, add it back to Foreman
	for my $key (sort keys %tmp){
	    #print "$key :: \"".ref($tmp{$key})."\"";
	    if (ref($tmp{$key}) eq "ARRAY"){
		$tmp{$key} = "[\"" . join("\",\"",@{$tmp{$key}}) . "\"]";
	    }else{
		$tmp{$key} = "\"$tmp{$key}\"";
	    }
	    #print " $tmp{$key}\n";
	}
	my $json = "{host:{".(join ",", map {"\"$_\":$tmp{$_}"} sort keys %tmp )."}}";
	#print "$json\n";#next;

	$request = HTTP::Request->new("POST","$url/hosts");
	$request->header("Content-Type" => "application/json");
	$request->content($json);
	
	$response = $browser->request($request);
	
	if (not $response->is_success){
	    print "[ERROR] Cannot add \"$host\" to Foreman: " . $response->status_line . " :: " . $response->content ."\n";
	    #print Dumper(\$response);
	    #next;
	}

    }

}

sub getId($$$$$) {
    my ($sref,$name,$search,$field,$value) = @_;

    my $response = $$sref;

    my $id = -1;

    for my $element (@{from_json($response->content)}) {
        if ($element->{$name}->{$search} eq $field) {
            $id = $element->{$name}->{$value};
	    last;
        }
    }
    return $id;
}


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
           --cern-user <username> : CERN account to be used for LANdb lookups, e-mail sending, etc
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
	my $cnt = 0;
	while (1){
	    my $aims = $todo{$host}{aimscmd};
	    if ($dryrun){
		print "[DRYRUN] *Not* uploading Kickstart file  for $host to AIMS\n";
		last;
	    }
	    print STDOUT "[INFO] Uploading Kickstart file for $host to AIMS\n";
	    print STDOUT "[VERB] Running \"$aims\"\n" if $verbose;
	    if (system("$aims 2>/dev/null 1>/dev/null") != 0){
		print STDERR "[ERROR] Upload to AIMS failed: $!\n";
		$rc++;
	    }
	    #
	    $aims = "aims2client showhost $todo{$host}{gigeth} --full";
	    print "[VERB] Running \"$aims\"\n" if $verbose;
	    open(F,"$aims |") or die "aargh...";
	    my @output = <F>;
	    close F;
	    print "[DEBUG] \@output:\n @output\n" if $debug;
	    my $status = join(" ",grep /PXE status:/, @output);
	    print "[DEBUG] \$status $status\n" if $debug;
	    if ($status =~ /PXE status:\s+ON\s*\n/){
		last;
	    }else{
		if (++$cnt == 5){
		    print STDERR "[ERROR] Machine \"$host\" still not properly configured in AIMS, giving up...\n";
                    $rc++;
		    unlink $todo{$host}{ksfile} unless $debug;
		    delete $todo{$host};
		    last;
		}
		print "[WARN] AIMS did not do its job for host $host, let's try again...\n";
		sleep 5;
	    }
	}
        #unlink $todo{$host}{ksfile} unless $debug;
    }
    map {unlink $todo{$_}{ksfile}} keys %todo unless $debug;
    return () unless %todo;

    print "[INFO] Verifying that AIMS is properly set up, patience please...\n";
    return 0 if $dryrun;
    $rc = 0;
    my @done = ();
    for my $host (sort keys %todo){
	my $cnt = 0;
	while (1){
	    #print "\$cnt = $cnt\n";
	    my $aims = "aims2client showhost $todo{$host}{gigeth} --full";
	    print "[VERB] Running \"$aims\"\n" if $verbose;
	    open(F,"$aims |") or die "aargh...";
	    my @output = <F>;
	    close F;
	    print "[DEBUG] \@output:\n @output\n" if $debug;
	    #my $status = join(" ",grep /PXE status:/, @output);
	    #print "[DEBUG] \$status $status\n" if $debug;
	    #if ($status !~ /PXE status:\s+ON\s*\n/){
	    #    print "AARGH! AIMS did not do its job for host $host! Complain && try again...!";
	    #    $cnt++;
	    #    last;
	    #}
	    my $sync = join(" ",grep /PXE boot synced:/, @output);
	    print "[DEBUG] \$sync    $sync\n" if $debug;
	    if ($sync =~ /PXE boot synced:\s+(\S+)\n/){
		my $status = $1;
		#print ">>> $status\n";
		if (grep {$_ eq $status} qw(YYY YYN YNY NYY)){
		    $cnt = 0;
		    push(@done,$host);
		    last;
		}
	    }
	    if ($cnt++ == 20){
		print "Machine \"$host\" still not properly configured in AIMS, giving up...\n";
		last;
	    }
	    print "[INFO] Sleeping 5 seconds...\n";
	    sleep 5;
	}
	$rc += $cnt;
    }
    
    return @done;
}

sub LandbHostInfo($){
    my $device = shift @_;

    my $client = SOAP::Lite
	->uri('http://network.cern.ch/NetworkService')
	->xmlschema('http://www.w3.org/2001/XMLSchema')
	->proxy('https://network.cern.ch/sc/soap/soap.fcgi?v=4', keep_alive=>1);

    # Get Auth token
    my $call = $client->getAuthToken($user_credentials{username},$user_credentials{password},'NICE');
    
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
    my %landb = ();
    $landb{Model} = $bu->{Model};
    for (@{$bu->{Interfaces}}) {
	my $Name = lc($_->{Name});
	my $HardwareAddress = $_->{BoundInterfaceCard}->{HardwareAddress};
	if (defined $HardwareAddress){
	    $HardwareAddress =~ s/\-/:/g;
	    push(@{$landb{Interfaces}},[$Name,$HardwareAddress]);
	}
    }
    if (not exists $landb{Interfaces}){
	my $Name = lc($bu->{DeviceName});
	for (@{$bu->{NetworkInterfaceCards}}) {
	    my $HardwareAddress = $_->{HardwareAddress};
	    if (defined $HardwareAddress){
		$HardwareAddress =~ s/\-/:/g;
		push(@{$landb{Interfaces}},[$Name,$HardwareAddress]);
	    }
	}
    }

    #print Dumper(\%landb);
    #exit;

    return %landb;
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

# 7001 AFS
# 4241 ARC
# 8139 Puppet
firewall --enabled --ssh --port=7001:udp --port=4241:tcp --port=8139:tcp

selinux --enforcing

firstboot --disable

# FIXME logging host=<headnode> inneresting...
logging --level=debug

# services
key --skip
services --disabled=pcscd,nfslock,netfs,portmap,rpcgssd,rpcidmapd,irqbalance,bluetooth,autofs,rhnsd,rhsmcertd

# additional repositories
{
    if ($OS eq "rhel6"){ $OUT .= <<EOOUT
repo --name="puppet-bootstrap" --baseurl http://cern.ch/agileinf/yum/puppet-bootstrap/6/$ARCH
repo --name="EPEL"             --baseurl http://linuxsoft.cern.ch/epel/6/$ARCH
repo --name="RHEL - optional"  --baseurl http://linuxsoft.cern.ch/rhel/rhel6server-$ARCH/RPMS.optional/
repo --name="RHEL - updates"   --baseurl http://linuxsoft.cern.ch/rhel/rhel6server-$ARCH/RPMS.updates/
repo --name="RHEL - fastrack"  --baseurl http://linuxsoft.cern.ch/rhel/rhel6server-$ARCH/RPMS.fastrack/
EOOUT
    } elsif ($OS eq "slc6"){ $OUT .= <<EOOUT
repo --name="puppet-bootstrap" --baseurl http://cern.ch/agileinf/yum/puppet-bootstrap/6/$ARCH
repo --name="EPEL"             --baseurl http://linuxsoft.cern.ch/epel/6/$ARCH
repo --name="SLC6 - updates"   --baseurl http://linuxsoft.cern.ch/cern/slc6X/$ARCH/yum/updates/
EOOUT
    }
}

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
agileinf-puppet-bootstrap
-fprintd

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

    /bin/sed 's/\r//' /root/ks-post-anaconda.log | /bin/mail -s "install failed on {$HOSTNAME}: $1" {$USER}@mail.cern.ch

    exit -1
\}

trap "fail unknown\ error" ERR

# redirect the output to the log file
exec >/root/ks-post-anaconda.log 2>&1
#script -f /root/ks-post-anaconda.log

# show the output on the seventh console
tail -f /root/ks-post-anaconda.log >/dev/tty7 &

# changing to VT 7 that we can see what's going on....
/usr/bin/chvt 7

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
# Bootstrap puppet first, then do a full run
#
/sbin/service agileinf-puppet-bootstrap start

/usr/bin/puppet agent --color=false --no-daemonize --verbose --onetime || :

#
# Ownership
#
#/usr/sbin/cern-config-users
/bin/echo {$USER}@mail.cern.ch > /root/.forward || :
/sbin/restorecon -v /root/.forward || :

#
# Misc fixes
#
/usr/bin/yum clean all || :

# Make sure the boot sequence is verbose
/usr/bin/perl -ni -e "s/ rhgb quiet//;print" /boot/grub/grub.conf || :

# The net.bridge.* entries in /etc/sysctl.conf make "sysctl -p" fail if "bridge" module is not loaded...
/usr/bin/perl -ni -e '$_ = "### Commented out by CERN... $_" if /^net\.bridge/;print' /etc/sysctl.conf || :

#
# Done
#
/bin/sed 's/\r//' /root/ks-post-anaconda.log | /bin/mail -s "installation of {$HOSTNAME} successfully completed" {$USER}@mail.cern.ch

exit 0

