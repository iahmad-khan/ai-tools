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

def sanity_check_on_new_name(new_name):
    if fqdnify(new_name) is not None:
        sys.stderr.write("Error: the new host name (%s) is already registered in DNS")
        sys.exit(1)

def sanity_check_on_old_name(old_name):
    if fqdnify(old_name) is None:
        sys.stderr.write("Error: host %s is not registered in DNS")
        sys.exit(1)

def sanity_check_for_alarms(old_name):
    r = RogerClient()
    roger = r.get_state(old_name)
    print roger


def host_renane(pargs):

    config = AiConfig()
    config.read_config_and_override_with_pargs(pargs)

    oldhost = fqdnify(pargs.oldhostname)

    sanity_check_for_alarms(oldhost)
    pdb = PdbClient()
    #pdb.get



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

    argcomplete.autocomplete(parser)
    parser.set_defaults(func=host_renane)

    pargs = parser.parse_args()
    pargs.func(pargs)

    sys.exit()