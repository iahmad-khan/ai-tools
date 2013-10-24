#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import os
import logging
import krbV

from aitools.errors import AiToolsInitError

DEFAULT_LOGGING_LEVEL=logging.INFO
CERN_CA_BUNDLE = "/etc/ssl/certs/CERN-bundle.pem"

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
