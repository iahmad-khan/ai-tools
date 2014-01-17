#!/usr/bin/env python
# Steve Traylen <steve.traylen@cern.ch>

import glob
import os

from aitools.foreman import ForemanClient
from aitools.foreman import DEFAULT_FOREMAN_TIMEOUT
from aitools.foreman import DEFAULT_FOREMAN_HOSTNAME
from aitools.foreman import DEFAULT_FOREMAN_PORT
from argcomplete import warn

# Use as bash argcomplete to foreman
# e.g.
# parser.add_argument('hostname', nargs=1, default=None,
#       help="Hostname (qualified or not)").completer = ForemanCompleter('hosts')
# The default will expand hosts.

class ForemanCompleter(object):
    """Completes item from within forman"""
    def __init__(self,model='hosts',item='name'):
        self.model = model
        self.name = model[:-1]
        self.item = item

    def __call__(self, prefix, parsed_args, **kwargs):
        foreman = ForemanClient(parsed_args.foreman_hostname, parsed_args.foreman_port,
            parsed_args.foreman_timeout, parsed_args.dryrun)
        if prefix == '':
           query = ''
        else:
           query = "%s~%s" % (self.item, prefix)
        response = foreman.search_query(self.model,query)   
   
        return [item[self.name][self.item] for item in response if item[self.name][self.item].startswith(prefix) ]

class NovaCompleter(object):
    """Completes nova entities from nova cache in ~/.novaclient"""
    def __init__(self,cache='server'):
        self.cache = cache
        
    def __call__(self, prefix, parsed_args, **kwargs):
        files = (glob.glob("%s/.novaclient/*/%s-human-id-cache" % ( os.environ.get('HOME'), self.cache ))[0],
          glob.glob("%s/.novaclient/*/%s-uuid-cache"     % ( os.environ.get('HOME'), self.cache ))[0])

        data = []
        for name in files:
            data +=  [line.strip() for line in open(name, 'r')]
        return [e for e in data if e.startswith(prefix) ]

