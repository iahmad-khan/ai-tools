#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import os
import logging
import subprocess

from aitools.errors import AiToolsHieraError

DEFAULT_HIERA_CONF_PATH="/etc/puppet/hiera.yaml"
HIERA_BINARY_PATH = "/usr/bin/hiera"
HIERA_HOSTGROUP_DEPTH = 5

class HieraClient():
    def __init__(self, config, trace=False, hash=False, array=False):
        """
        Tool for looking up hiera keys

        :param config: location of the Hiera config file
        :param trace: trace how the keys were looked up and print the trace to sys.stdout
        :param hash: look up in hash mode
        :param array: look up in array mode
        """
        self.config = config
        self.trace = trace
        self.hash = hash
        self.array = array


    def lookupkey(self, key, fqdn, environment, hostgroup, facts, module=None):
        """
        Lookup a hiera key and returns its value.

        :param key: the Hiera key to look up
        :param fqdn: the hostname to look it up for
        :param environment: the environment to do the lookup for
        :param hostgroup: the hostgroup to do the lookup for
        :param facts: dictionary of the 'operatingsystemmajorrelease', 'osfamily', 'cern_hwvendor' facts
        :param module: search also for this module
        :return: a (possibly empty) list of values
        :raise AiToolsHieraError: in the case the Hiera call failed
        """
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
            self.__append_fact(factname, facts, hiera_cmd)
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

    def __append_fact(self, name, facts, hiera_cmd):
        value = facts.get(name)
        if value:
            logging.debug("Fact '%s': %s" % (name, value))
            hiera_cmd.append("::%s=%s" % (name, value))
        else:
            logging.info("Fact '%s' not found, won't be used" % name)
