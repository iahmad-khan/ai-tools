#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import os
import re
import logging
import hashlib
import socket
import time
import getpass
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from uuid import UUID
from urlparse import urlparse
import random

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
    res = url._replace(netloc="%s:%s" % (deref_name, str(url.port)))
    return res.geturl()


def get_openstack_environment():
    """
    Verify the user has provided the needed environment for Openstack and returns
    a dictionary containing this environment with the following entries:
       username, password, tenant_name, tenant_id, auth_url and cacert
    The returned values are filled from the **OS_** environement variables when
    present or asks the user. This function does not validate the correctness
    of the returned values.
    :raise AiToolsInitError: User doesn't have the basic environments set.
    """
    res = {}

    from_openrc = ["OS_USERNAME", "OS_TENANT_NAME",
        "OS_TENANT_ID", "OS_AUTH_URL"]
    for variable in from_openrc:
        if variable not in os.environ:
            raise AiToolsInitError("%s is not set (did you source openrc?)"
                % variable)
        else:
            res[re.sub(r'^OS_', '', variable).lower()] = os.environ[variable]

    # The password is a special case, we give the user a chance to
    # avoid storing it in an environment variable (this should disappear
    # once Kerberos support arrives)
    from_userinput = ["OS_PASSWORD"]
    for variable in from_userinput:
        name = re.sub(r'^OS_', '', variable).lower()
        if variable not in os.environ or len(os.environ[variable]) == 0:
            res[name] = getpass.getpass("Please, type your Openstack %s: " % name)
        else:
            res[name] = os.environ[variable]
        if len(res[name]) == 0:
            raise AiToolsInitError("%s is not set or empty" % variable)

    # We can continue if OS_CACERT is not defined
    res["cacert"] = os.environ.get('OS_CACERT', None)

    return res

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
