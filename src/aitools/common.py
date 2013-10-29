#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import os
import re
import logging
import krbV
import hashlib
import time
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from aitools.errors import AiToolsInitError

DEFAULT_LOGGING_LEVEL=logging.INFO
CERN_CA_BUNDLE = "/etc/ssl/certs/CERN-bundle.pem"
FQDN_VALIDATION_RE = "^[a-zA-Z0-9][a-zA-Z0-9\-]{0,59}?\.cern\.ch$"
HASHLEN = 10

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
    for variable in ("OS_USERNAME", "OS_PASSWORD", \
           "OS_TENANT_NAME", "OS_AUTH_URL"):
        if variable not in os.environ:
            raise AiToolsInitError("%s not set (openrc not (or partially) sourced?)" % variable)

def verify_kerberos_environment():
    context = krbV.default_context()
    ccache = context.default_ccache()
    try:
        return ccache.principal().name
    except krbV.Krb5Error:
        raise AiToolsInitError("Kerberos principal not found")

def generate_random_fqdn(prefix):
    hash = hashlib.sha1()
    hash.update(str(time.time()))
    return "%s%s.cern.ch" % (prefix if prefix else "",
        hash.hexdigest()[:HASHLEN])

def validate_fqdn(fqdn):
    return re.match(FQDN_VALIDATION_RE, fqdn)

def generate_userdata(args):
    logging.info("Preparing dynamic user data...")
    logging.info("Using '%s' as userdata script template to init Puppet" % \
        args.puppetinit_path)
    try:
        script = Template(open(args.puppetinit_path).read())
    except IOError, error:
        raise AiToolsInitError(error)
    values = {'CASERVER_HOSTNAME': args.caserver_hostname,
        'CASERVER_PORT': args.caserver_port,
        'PUPPETMASTER_HOSTNAME': args.puppetmaster_hostname,
        'FOREMAN_ENVIRONMENT': args.foreman_environment}
    userdata = MIMEMultipart()
    userdata.attach(MIMEText(script.substitute(values), 'x-shellscript'))
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

def append_domain(hostname):
    if hostname is not None:
        hostname = "%s.cern.ch" % hostname.split('.')[0]
    return hostname
