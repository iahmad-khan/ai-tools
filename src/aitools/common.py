#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import os
import re
import logging
import krbV
import hashlib
import time

from aitools.errors import AiToolsInitError

DEFAULT_LOGGING_LEVEL=logging.INFO
CERN_CA_BUNDLE = "/etc/ssl/certs/CERN-bundle.pem"
FQDN_VALIDATION_RE = "^[a-zA-Z0-9][a-zA-Z0-9\-]{0,59}?\.cern\.ch$"

class HTTPClient():
    def __init__(self, host, port, timeout, dryrun=False):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.dryrun = dryrun
        self.cache = {}

def configure_logging(args):
    """Configures application log level based on cmdline arguments"""
    logging_level = DEFAULT_LOGGING_LEVEL
    if args.verbose:
        logging_level = logging.DEBUG
    logging.basicConfig(level=logging_level, format="%(message)s")

def verify_openstack_environment():
    for variable in ("OS_USERNAME", "OS_PASSWORD", \
           "OS_TENANT_NAME", "OS_AUTH_URL"):
        if variable not in os.environ:
            raise AiToolsInitError("%s not set (openrc not (or partially) sourced?)" % variable)

def verify_kerberos_environment():
    context = krbV.default_context()
    ccache = context.default_ccache()
    try:
        ccache.principal()
    except krbV.Krb5Error:
        raise AiToolsInitError("Kerberos principal not found")

def generate_random_fqdn(prefix):
    hash = hashlib.sha1()
    hash.update(str(time.time()))
    return "%s%s.cern.ch" % (prefix if prefix else "", hash.hexdigest()[:10])

def validate_fqdn(fqdn):
    return re.match(FQDN_VALIDATION_RE, fqdn)
