#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import os
import re
import logging
import hashlib
import socket
import time
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from uuid import UUID

import krbV
from aitools.params import FQDN_VALIDATION_RE
from aitools.params import HASHLEN
from aitools.params import DEFAULT_LOGGING_LEVEL
from aitools.errors import AiToolsInitError
from aitools.config import CertmgrConfig


def configure_logging(args, default_lvl=DEFAULT_LOGGING_LEVEL):
    """Configures application log level based on cmdline arguments"""
    logging_level = default_lvl
    if args.verbose:
        logging_level = logging.DEBUG
    logging.basicConfig(level=logging_level, format="%(message)s")
    # Workaround to get rid of "Starting new HTTP connection..."
    if logging_level > logging.DEBUG:
        logging.getLogger("urllib3").setLevel(logging.WARNING)


def verify_openstack_environment():
    """
    Verify the user has the basic **OS_** environment variables set for Openstack.
    Returns nothing but raises an exception if these are not defined. It does not
    validate the correctness of these environment variables.

    :raise AiToolsInitError: User doesn't have the basic environments set.
    """
    for variable in ("OS_USERNAME", "OS_PASSWORD", \
           "OS_TENANT_NAME", "OS_AUTH_URL"):
        if variable not in os.environ:
            raise AiToolsInitError("%s not set (openrc not (or partially) sourced?)" % variable)

def verify_kerberos_environment():
    """
    Verify the user has a valid Kerberos token and associated environment.

    :return: the Kerberos principal name
    :raise AiToolsInitError: if the user has no valid Kerberos token
    """
    context = krbV.default_context()
    ccache = context.default_ccache()
    try:
        return ccache.principal().name
    except krbV.Krb5Error:
        raise AiToolsInitError("Kerberos principal not found")

def generate_random_fqdn(prefix):
    """
    Generate a random CERN hostname.

    :param prefix: prefix for the hostname
    :return: the generated hostname
    """
    hash = hashlib.sha1()
    hash.update(str(time.time()))
    return "%s%s.cern.ch" % (prefix.lower() if prefix else "",
        hash.hexdigest()[:HASHLEN])

def validate_fqdn(fqdn):
    """
    Return whether the string is an FQDN or not
    :param fqdn: the string to test
    :return: tests True if the string is an FQDN otherwise tests False
    """
    return re.match(FQDN_VALIDATION_RE, fqdn)

def fqdnify(h):
    """
    Return the FQDN for the given host. Validates the host and returns None if the host is not found in DNS.
    Aliases are resolved to first valid A record.

    :param h: short or otherwise name fo host to return FQDN for
    :return: the FQDN or None if host fails DNS lookup
    """
    try:
        ip = socket.gethostbyname(h)
    except socket.gaierror:
        return False
    return socket.getfqdn(h)

def shortify(h):
    """
    Return the shortname for the given host. Validates the host and returns None if the host is not found in DNS.

    :param h: hostname of host to return the short name for
    :return: the short name or None if host fails DNS lookup
    """
    fqdn = fqdnify(h)
    return fqdn.split('.')[0] if fqdn else None

def generate_userdata(args):
    certmgrconf = CertmgrConfig()
    logging.info("Preparing dynamic user data...")
    logging.info("Using '%s' as userdata script template to init Puppet" % \
        args.puppetinit_path)
    try:
        script = Template(open(args.puppetinit_path).read())
    except IOError, error:
        raise AiToolsInitError(error)
    values = {'CASERVER_HOSTNAME': certmgrconf.certmgr_hostname,
        'CASERVER_PORT': certmgrconf.certmgr_port,
        'PUPPETMASTER_HOSTNAME': args.puppetmaster_hostname,
        'FOREMAN_ENVIRONMENT': args.foreman_environment,
        'NO_GROW': 1 if args.nogrow else 0,
        'GROWPART_VDA_PARTITION': args.grow_partition,
        'NO_REBOOT': 1 if args.noreboot else 0}
    userdata = MIMEMultipart()
    puppetinit = MIMEText(script.safe_substitute(values), 'x-shellscript')
    puppetinit.add_header('Content-Disposition', 'attachment',
        filename=os.path.basename(args.puppetinit_path))
    userdata.attach(puppetinit)
    if args.userdata_dir:
        try:
            for snippet_name in os.listdir(args.userdata_dir):
                snippet_path = os.path.join(args.userdata_dir, snippet_name)
                if os.path.isfile(snippet_path):
                    logging.info("Adding snippet '%s'" % snippet_name)
                    userdata.attach(MIMEText(open(snippet_path).read(),
                                        snippet_name))
        except (IOError, OSError), error:
            raise AiToolsInitError(error)
    return userdata.as_string()

def append_domain(hostname):  # todo: replace by fqndify
    if hostname is not None:
        hostname = "%s.cern.ch" % hostname.split('.')[0].lower()
    return hostname


def extract_fact(name, facts, fqdn):
    if fqdn in facts and name in facts[fqdn]:
        return facts[fqdn][name]
    return None

def is_valid_UUID(value):
    try:
        UUID(value, version=4)
        return True
    except ValueError:
        return False

def is_valid_size_format(size):
    """
    Returns true if size has a human readable size format
    specified in GB or TB i.e. '10GB' or '10TB'
    """
    return bool(re.match(r'^[1-9][0-9]*(GB|TB)$', size)) if size else False

def generator_device_names():
    """
    Returns a generator of volume device names.

    :return: a different volume device name each time,
    starting with 'vdb' and following in alphabetical order
    e.g. 'vdb', 'vdc', 'vdd', etc. When it reaches 'vdz' it
    continues with 'vdaa'
    """
    # Starts with 'vdb' as 'vda' is used for booting
    value ='b'
    while True:
        yield 'vd' + value

        # All letters are 'z'
        if value == 'z' * len(value):
            value = 'a' * (len(value) + 1)
        # At least ends with a 'z' but contains some other
        # letters as well
        elif re.search(r'z+$', value):
            l_value = list(value)
            for pos, char in reversed(list(enumerate(l_value))):
                if char == 'z':
                    l_value[pos] = 'a'
                else:
                    l_value[pos] = chr(ord(char) + 1)
                    value = ''.join(l_value)
                    break
        # General case
        else:
            value = value[:-1] + chr(ord(value[-1]) + 1)
