#!/usr/bin/env python
# Steve Traylen <steve.traylen@cern.ch>

from aitools.foreman import ForemanClient
from aitools.foreman import DEFAULT_FOREMAN_TIMEOUT
from aitools.foreman import DEFAULT_FOREMAN_HOSTNAME
from aitools.foreman import DEFAULT_FOREMAN_PORT


# Use as bash argcomplete to foreman
# e.g.
# parser.add_argument('hostname', nargs=1, default=None,
#       help="Hostname (qualified or not)").completer = ForemanCompleter('hosts')
# The default will expand hosts.

class ForemanCompleter(object):
    """Completes item from within forman"""
    def __init__(self,expand='hosts'):
        self.expand = expand
        self.name = expand[:-1]

    def __call__(self, prefix, parsed_args, **kwargs):
        foreman = ForemanClient(parsed_args.foreman_hostname, parsed_args.foreman_port,
            parsed_args.foreman_timeout, parsed_args.dryrun)
        response = foreman.search_query(self.expand,"name~%s" % prefix)   
        return [item[self.name]['name'] for item in response if item[self.name]['name'].startswith(prefix) ]


