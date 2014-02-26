#!/usr/bin/python

__author__ = 'mccance'

try:
    import simplejson as json
except ImportError:
    import json
import yaml
import os
import sys
import urllib2
import iso8601
import datetime
import pytz
import humanize
import teigi.rogerclient
import prettytable
import argcomplete
import textwrap

from argparse import ArgumentParser
from aitools.pdb import PdbClient
from aitools.roger import RogerClient
from aitools.common import fqdnify
from aitools.config import ForemanConfig, RogerConfig, PdbConfig, AiConfig
from aitools.completer import ForemanCompleter
from aitools.errors import AiToolsPdbNotFoundError

def sanity_check_for_alarms(old_name):
    roger = RogerClient()
    state = roger.get_state(old_name)
    hwa = state['hw_alarmed']
    nca = state['nc_alarmed']
    osa = state['os_alarmed']
    appa = state['app_alarmed']
    appstate = state['appstate']
    if (hwa == "True" or nca=="True" or osa == "True" or appa == True or appstate=="production"):
        sys.stderr.write("Renaming host is a destructive operation for the host. Please ensure that\n")
        sys.stderr.write("all alarms have been disabled in Roger and the application state of the nodes\n")
        sys.stderr.write("is not production. To ignore this check, run this command with the --jfdi flag.")
        sys.exit(3)

def sanity_check_for_virtual_machine(oldhost):
    pdb = PdbClient()
    try:
        facts = pdb.get_facts(oldhost)
        if facts["is_virtual"]:
            sys.stderr.write("The host %s is a virtual machine and cannot be renamed with this tool.\n" % oldhost)
            sys.exit(4)
    except AiToolsPdbNotFoundError:
        pass # assume it's a new host which has not run Puppet yet


def host_renane(pargs):

    config = AiConfig()
    config.read_config_and_override_with_pargs(pargs)

    oldhost = fqdnify(pargs.oldhostname)
    if oldhost == False:
        sys.stderr.write("Error: the current host (%s) is not registered in DNS." % pargs.oldhostname)
        sys.exit(1)

    newhost = fqdnify(pargs.newhostname)
    if newhost:
        sys.stderr.write("Error: the new host name (%s) is already registered in DNS.")
        sys.exit(2)

    sanity_check_for_virtual_machine(oldhost)

    if not pargs.jfdi:
        sanity_check_for_alarms(oldhost)

    print "sane"


if __name__ == "__main__":
    # needs landb
    # needs foreman
    # relies on foreman to drop from puppetdb ? or explicit?
    # needs roger
    # refuse to do it if roger says alarms are on
    # refuse to do it if host is running puppet- how?

    parser = ArgumentParser(description="Rename a host (destructively)")

    ForemanConfig.add_standard_args(parser)
    PdbConfig.add_standard_args(parser)
    RogerConfig.add_standard_args(parser)

    parser.add_argument("oldhostname", metavar="HOST", help="host to rename").completer = ForemanCompleter()
    parser.add_argument("newhostname", metavar="HOST", help="the new name for the host")
    parser.add_argument("--jfdi", default=False, help="Just do it - don't check for alarmed states")

    argcomplete.autocomplete(parser)
    parser.set_defaults(func=host_renane)

    pargs = parser.parse_args()
    pargs.func(pargs)

    sys.exit()