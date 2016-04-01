#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import os
import sys
import re
import logging
import hashlib
import socket
import time
import random
import krbV

from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from uuid import UUID
from urlparse import urlparse
from collections import namedtuple
from datetime import datetime

from aitools.params import FQDN_VALIDATION_RE
from aitools.params import HASHLEN, MAX_FQDN_LEN
from aitools.params import DEFAULT_LOGGING_LEVEL
from aitools.errors import AiToolsInitError
from aitools.config import CertmgrConfig

IMAGES_METADATA = {
    'slc5': ('SLC', '5', 'Server'),
    'slc6': ('SLC', '6', 'Base'),
    'cc7' : ('CC',  '7', 'Base'),
}

def configure_logging(args, default_lvl=DEFAULT_LOGGING_LEVEL):
    """Configures application log level based on cmdline arguments"""
    logging_level = default_lvl
    if args.verbose:
        logging_level = logging.DEBUG
    logging.basicConfig(level=logging_level, format="%(message)s")
    # Workaround to get rid of "Starting new HTTP connection..."
    # and "Resetting dropped connection..."
    if logging_level > logging.DEBUG:
        logging.getLogger("requests.packages.urllib3.connectionpool") \
            .setLevel(logging.WARNING)


def deref_url(url):
    """
    The host in a url will be dereferenced from a load balanced alias
    :param url: url for which the host will have any alias converted
    :return: a dereferenced url
    """
    url = urlparse(url)
    try:
        deref_name = socket.gethostbyaddr(random.choice(socket.gethostbyname_ex(url.hostname)[2]))[0]
    except socket.gaierror, e:
        logging.warn("Could not deference '%s' in '%s' received error: '%s' attempting connection to original url'" %
        (url.hostname, url, e))
        return url
    res = url._replace(netloc="%s:%s" % (deref_name, str(url.port)))
    return res.geturl()


def get_openstack_environment():
    """
    Verify the user has provided the needed environment for Openstack and
    returns a OpenstackEnvironmentVariables object containing this environment.
    The returned values are filled from the **OS_** environement variables
    when present. This function does not validate the correctness of the
    returned values.
    :raise AiToolsInitError: User doesn't have the basic environment set.
    """
    # We get all environment variables that start with 'OS_'
    res = dict((env.lower(), os.getenv(env))
        for env in os.environ.keys() if env.startswith('OS_'))

    # Removing tenant_name and tenant_id if they are present
    if res.get('os_tenant_name'):
        if not res.get('os_project_name'):
            res['os_project_name'] = res['os_tenant_name']
        del res['os_tenant_name']

    if res.get('os_tenant_id'):
        if not res.get('os_project_id'):
            res['os_project_id'] = res['os_tenant_id']
        del res['os_tenant_id']

    if not res:
        raise AiToolsInitError("There are no Openstack environment "
            " variables set")

    res['os_url'] = ''
    res['os_region_name'] = ''
    res['timing'] = ''

    return OpenstackEnvironmentVariables(**res)

class OpenstackEnvironmentVariables(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def get(self, key):
        return self.__dict__.get(key)

# Shamefully stolen from:
# https://github.com/tkdchen/python-krbcontext
# "Docs"
# https://git.fedorahosted.org/cgit/python-krbV.git/tree/krb5module.c
def get_tgt_time(ccache):
    ''' Get specified TGT's credential time tuple.

    Arguments:
    - ccache, a CCache object
    '''
    CredentialTime = namedtuple('CredentialTime',
        'authtime starttime endtime renew_till')
    tgt_princ_name = 'krbtgt/%(realm)s@%(realm)s' % \
        {'realm': ccache.principal().realm}
    tgt_princ = krbV.Principal(tgt_princ_name, context=ccache.context)
    creds = (ccache.principal(), tgt_princ,
             (0, None), (0, 0, 0, 0), None, None, None, None,
             None, None)
    tgt = ccache.get_credentials(creds, krbV.KRB5_GC_CACHED, 0)
    return CredentialTime._make([datetime.fromtimestamp(t) for t in tgt[3]])

def verify_kerberos_environment():
    """
    Verify the user has a valid Kerberos token and associated environment.

    :return: the Kerberos principal name
    :raise AiToolsInitError: if the user has no valid Kerberos token
    """
    context = krbV.default_context()
    ccache = context.default_ccache()
    try:
        # If the TGT is expired the next call will raise krbV.Krb5Error
        get_tgt_time(ccache)
        return ccache.principal().name
    except krbV.Krb5Error:
        raise AiToolsInitError("Kerberos ticket not available or expired")

def generate_random_fqdn(prefix):
    """
    Generate a random CERN hostname.

    :param prefix: prefix for the hostname
    :return: the generated hostname
    """
    hashname = hashlib.sha1()
    hashname.update(str(time.time()))
    return "%s%s.cern.ch" % (prefix.lower() if prefix else "",
        hashname.hexdigest()[:HASHLEN])

def validate_fqdn(fqdn):
    """
    Return whether the string is an FQDN or not
    :param fqdn: the string to test
    :return: tests True if the string is an FQDN otherwise tests False
    """
    return re.match(FQDN_VALIDATION_RE, fqdn) and len(fqdn) <= MAX_FQDN_LEN

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
    values = {'_CASERVER_HOSTNAME': certmgrconf.certmgr_hostname,
        '_CASERVER_PORT': certmgrconf.certmgr_port,
        '_PUPPETMASTER_HOSTNAME': args.puppetmaster_hostname,
        '_FOREMAN_ENVIRONMENT': args.foreman_environment,
        '_NO_GROW': 1 if args.nogrow else 0,
        '_GROWPART_VDA_PARTITION': args.grow_partition,
        '_NO_REBOOT': 1 if args.noreboot else 0}
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
    if hostname is not None and '.' not in hostname:
        logging.warning("Using default domain (cern.ch) as '%s' does not look "
            "like an FQDN" % hostname)
        return "%s.cern.ch" % hostname

    return hostname

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
    return bool(re.match(r'^[1-9][0-9]*(GB|TB)$', size, re.IGNORECASE)) if size else False

def generator_device_names():
    """
    Returns a generator of volume device names.

    :return: a different volume device name each time,
    starting with 'vdb' and following in alphabetical order
    e.g. 'vdb', 'vdc', 'vdd', etc. The limit is 'vdz'
    """
    # Starts with 'vdb' as 'vda' is used for booting
    value = 'b'
    while ord(value) <= ord('z'):
        yield 'vd' + value
        value = chr(ord(value) + 1)

def print_progress_meter(count, total, new_line=False):
    progress = int((float(count)/total)*100)
    term = "\n" if new_line else ""
    sys.stdout.write("\rIn progress... %d%% done%s" % (progress, term))
    sys.stdout.flush()
