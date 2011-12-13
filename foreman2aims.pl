#! /usr/bin/perl -w



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

$Data::Dumper::Sortkeys = 1;

sub LandbHostInfo($);
sub SetupAims($);
sub HelpMessage();
sub getId($$$$$);

HelpMessage() if not @ARGV;

my %data = ();
my $debug = my $verbose = my $dryrun = 0;
my $noaims = 0;
my %opts = (debug   => \$debug,
            dryrun  => \$dryrun,
            verbose => \$verbose);

my $rc = Getopt::Long::GetOptions(\%opts,
				  "debug","dryrun","verbose",
				  "noaims"            => \$noaims,
                                  "cern-user=s"       => \$data{USER},
                                  "help"              => sub { HelpMessage() },
                                 );
#print Dumper(\%opts);

HelpMessage() if not $rc;

$data{USER} ||= (getpwuid($<))[0];
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


#print Dumper(\%data);exit;

my %todo = ();
my %fmdata = (); # Host data from Foreman

my $url         = "https://punch.cern.ch";
my $netlocation = "punch.cern.ch:443";
my $realm       = "Application";
my $browser  = LWP::UserAgent->new;
$browser->credentials($netlocation,$realm,$user_credentials{username} => $user_credentials{password});

#
# Are the hosts known to Foreman?
#
my @err = ();
for my $host (@host){
    my $request = HTTP::Request->new("GET","$url/hosts/$host.cern.ch");
    $request->header("Content-Type" => "application/json");
    my $response = $browser->request($request);
    push(@err,$host) unless $response->is_success;
    my %data = %{from_json($response->content)};
    #print Dumper(\%data);exit;
    $fmdata{$host}{operatingsystem_id} = $data{host}{operatingsystem_id};
    $fmdata{$host}{architecture_id} = $data{host}{architecture_id};
    $fmdata{$host}{model_id} = $data{host}{model_id};
    #print Dumper(\%fmdata);#exit;
}
if (@err){
    print STDERR "[ERROR] Host(s) \"".join("\" - \"",@err). "\" unknown to Foreman, exiting...\n";
    exit 1;
}

#
# Resolve Foreman ID's, update host data.
#
my %fmos = my %fmarch = my %fmmodel = ();
my @fmos    = @{from_json($browser->get("$url/operatingsystems?format=json")->content)};
my @fmarch  = @{from_json($browser->get("$url/architectures?format=json")->content)};
my @fmmodel = @{from_json($browser->get("$url/models?format=json")->content)};
map {$fmos  {$$_{operatingsystem}{id}} = $$_{operatingsystem}{name}} @fmos;
map {$fmarch{$$_{architecture}{id}}    = $$_{architecture}   {name}} @fmarch;
map {$fmmodel{$$_{model}{id}}          = $$_{model}          {name}} @fmmodel;
for my $host (keys %fmdata){
    $fmdata{$host}{operatingsystem} = $fmos   {$fmdata{$host}{operatingsystem_id}};
    $fmdata{$host}{architecture}    = $fmarch {$fmdata{$host}{architecture_id}};
    $fmdata{$host}{model}           = $fmmodel{$fmdata{$host}{model_id}};
    delete $fmdata{$host}{operatingsystem_id};
    delete $fmdata{$host}{architecture_id};
    delete $fmdata{$host}{model_id};
}
#print Dumper(\%fmdata);exit;

#
# Delete certs
#
@err = ();
for my $host (keys %fmdata){
    my $request = HTTP::Request->new("DELETE","$url/smart_proxies/2-punch-cern-ch/puppetca/$host.cern.ch"); # XXX to-do: replace hardcoded URL by sthg smart :)
    $request->header("Content-Type" => "application/json");
    my $response = $browser->request($request);
    if (not $response->is_success){
        push(@err,$host);
	print "[ERROR] ".$response->status_line."\n" if $debug;
    }
}
if (@err){
    print STDERR "[ERROR] Could not revoke certificate for host(s) \"".join("\" - \"",@err). "\" from Puppet Certificate Authority, exiting...\n";
    #exit 1;
}

#
# Do the real work
#
for my $host (@host){
    my $os      = $fmdata{$host}{operatingsystem};
    my $arch    = $fmdata{$host}{architecture};
    my $hwmodel = $fmdata{$host}{model};

    if (gethostbyname("${host}-gigeth")){
	print "[INFO] Getting LANdb info for host \"$host\", patience please...\n";
	my %landb = LandbHostInfo($host);
	if (not %landb){
	    print "[WARNING] Could not get Landb info for \$host\", skipping it...\n";
	    next;
	}
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
	$data{NETWORK} = "network --bootproto=dhcp --device=eth0 --hostname $host.cern.ch";
    }

    $data{HWMODEL} = $hwmodel;

    if (uc($hwmodel) eq "HYPER-V VIRTUAL MACHINE" and $os =~ /^(SLC|RedHat) 5\./){
	$data{FIRST_DRIVE} = "hda";
    } else {
	$data{FIRST_DRIVE} = "sda";
    }

    my $ksfile = POSIX::tmpnam();


    # IP address
    my $iaddr = gethostbyname($host);
    die "aargh..." if not defined $iaddr;
    $iaddr = inet_ntoa($iaddr);
    my $request = HTTP::Request->new("GET","$url/unattended/provision?spoof=$iaddr");
    $request->header("Content-Type" => "application/json");
    my $response = $browser->request($request);
    if (not $response->is_success){
        print STDERR Dumper($response)."AARGH! $url/unattended/provision?spoof=$iaddr\n";
	exit;
    }
    my $template = $response->content;

    my $tpl = new Text::Template(TYPE    => "STRING",
				 UNTAINT => 1,
				 SOURCE  => $template) or die "Couldn't construct template: $Text::Template::ERROR";

    my $console = uc($hwmodel) ne "HYPER-V VIRTUAL MACHINE" ? "console=tty0 console=ttyS2,9600n8" : "";

    my $result = $tpl->fill_in(HASH => \%data);
    if (not defined $result) {
        print STDERR "Couldn't fill in template: $Text::Template::ERROR\n";
        next;
    }
    
    if (not open(F,"> $ksfile")){
        print STDERR "[ERROR] Could not open \"$ksfile\" for writing: $!\n";
	next;
    }
    print F $result;
    print $result if $debug;
    close F;
    
    %{$todo{$host}} = ( ksfile          => $ksfile,
                        hostname        => ( gethostbyname("${host}-gigeth") ? "${host}-gigeth" : $host),
			operatingsystem => $os,
			architecture    => $arch,
			console         => $console,

    );
}

#
# Add to AIMS
#
if ($noaims){
    print "[INFO] Option \"--noaims\" specified, exiting now.\n";
    exit 0;
}

@host = SetupAims(\%todo);
if (not @host){
    print STDERR "[ERROR] Upload to AIMS failed, exiting...\n";
    exit 1;
}

map {print "[INFO] Machine \"$_\" is ready to be reinstalled.\n"} sort @host;

#my $mess1 = join("\n",map {"      ssh root\@punch puppetca --clean $_.cern.ch"} @host);
my $mess2 = join("\n",map {"      ssh root\@$_ shutdown -r now"} @host);
my $mess3 = join("\n",map {"      ssh lxadm remote-power-control reset $_"} @host);
my $mess4 = join("\n",map {"      ssh lxadm connect2console.sh $_"} @host);
my $mess5 = join("\n",map {"      aims2 pxeoff $_-gigeth"} @host);

print <<EOMESS;

Right. So you think this is it? Think again...

At the moment of writing this (Nov 30, 2011), there are quite some 
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


sub HelpMessage(){

    my $script = basename $0;
    my $user = (getpwuid($<))[0];

    print <<EOH;


Usage: $script [options] hostname [hostname]

       where options are

           --cern-user <username>          : CERN account to be used for LANdb lookups, Foreman access, e-mail sending, etc
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
    my %AimsImg = (
        "RedHat 6"   => "RHEL6_U2",
        "RedHat 6.2" => "RHEL6_U2",
        "RedHat 6.1" => "RHEL6_U1",
        "SLC 6"      => "SLC6X",
        "SLC 6.1"    => "SLC6X",
        "RedHat 5.7" => "RHES_5_U7",
        "SLC 5.7"    => "SLC5X",
        );


    for my $host (sort keys %todo){
	my $cnt = 0;
	my $kopts = "text network ks ksdevice=bootif latefcload";
	$kopts .= " $todo{$host}{console}" if $todo{$host}{console};
	if (not exists $AimsImg{$todo{$host}{operatingsystem}}){
	    print STDERR "[ERROR] No suitable AIMS target for Operating System \"$todo{$host}{operatingsystem}\" available. Probably a bug in the script you are running :)\n";
	    exit 1;
	}
	my $imgname = $AimsImg{$todo{$host}{operatingsystem}} . "_" . $todo{$host}{architecture};
	my $aims = "/usr/bin/aims2client addhost --hostname $todo{$host}{hostname} --kickstart $todo{$host}{ksfile} --kopts \"$kopts\" --pxe --name $imgname";
	while (1){
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
	    $aims = "aims2client showhost $todo{$host}{hostname} --full";
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
        unlink $todo{$host}{ksfile} unless $debug;
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
	    my $aims = "aims2client showhost $todo{$host}{hostname} --full";
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

Dec  5 14:12:02 lxsoft04 httpd: lxfssm4004.cern.ch - - [05/Dec/2011:14:12:02 +0100] "GET /aims2server/aims2reboot.cgi?pxetarget=localboot HTTP/1.0" 200 57 "-" "Wget/1.12 (linux-gnu)"

