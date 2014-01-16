#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import os
import logging
import subprocess

from aitools.common import extract_fact
from aitools.errors import AiToolsHieraError

DEFAULT_HIERA_CONF_PATH="/etc/puppet/hiera.yaml"
HIERA_BINARY_PATH = "/usr/bin/hiera"
HIERA_HOSTGROUP_DEPTH = 5

class HieraClient():
    def __init__(self, config, trace=False, hash=False, array=False):
        self.config = config
        self.trace = trace
        self.hash = hash
        self.array = array

    def lookupkey(self, key, fqdn, environment, hostgroup, facts, module=None):
        hiera_cmd = [HIERA_BINARY_PATH, "-c", self.config, key]
        if self.trace:
            hiera_cmd.append("-d")
        if self.array:
            hiera_cmd.append("-a")
        if self.hash:
            hiera_cmd.append("-h")
        if module:
            hiera_cmd.append("module_name=%s" % module)
        hiera_cmd.append("::foreman_env=%s" % environment)
        hiera_cmd.append("::fqdn=%s" % fqdn)
        hostgroup = hostgroup.split("/")
        if len(hostgroup) > HIERA_HOSTGROUP_DEPTH:
            logging.warn("The lookup depth for hostgroup keys is limited to %d levels"
                % HIERA_HOSTGROUP_DEPTH)
            logging.warn("You might be leaving behind some data")
        hiera_cmd.extend(["::encgroup_%d=%s" % (i,x) 
            for i,x in enumerate(hostgroup)])
        for factname in ['operatingsystemmajorrelease', 'osfamily', 'cern_hwvendor']:
            self.__append_fact(factname, facts, fqdn, hiera_cmd)
        logging.debug("About to execute: %s" % hiera_cmd)
        try:
            process = subprocess.Popen(hiera_cmd, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            stdout = process.communicate()[0]
        except OSError, error:
            raise AiToolsHieraError("Hiera call failed (%s)" % error)
        if process.returncode == os.EX_OK:
            return stdout
        else:
            raise AiToolsHieraError("Hiera returned non-zero exit code (%d)" %
                process.returncode)

    def __append_fact(self, name, facts, fqdn, hiera_cmd):
        value = extract_fact(name, facts, fqdn)
        if value:
            logging.info("Fact '%s': %s" % (name, value))
            hiera_cmd.append("::%s=%s" % (name, value))
        else:
            logging.info("Fact '%s' not found, won't be used" % name)
