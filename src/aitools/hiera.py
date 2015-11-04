#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import os
import logging
import subprocess

from aitools.config import HieraConfig
from aitools.errors import AiToolsHieraError
from aitools.errors import AiToolsHieraKeyNotFoundError

class HieraClient():
    def __init__(self, config_path=None, binary_path=None, hostgroup_depth=None,
                 fact_list=None, trace=False, hash=False, array=False):
        """
        Tool for looking up hiera keys

        :param config: location of the Hiera config file
        :param trace: trace how the keys were looked up and print the trace to sys.stdout
        :param hash: look up in hash mode
        :param array: look up in array mode
        """
        config = HieraConfig()
        self.config_path = config_path or config.hiera_config_path
        self.binary_path = binary_path or config.hiera_binary_path
        self.hostgroup_depth = int(hostgroup_depth or config.hiera_hostgroup_depth)
        self.fact_list = (fact_list or config.hiera_fact_list).split(',')
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
        :param facts: dictionary containing fqdn's facts
        :param module: search also for this module
        :return: a (possibly empty) list of values
        :raise AiToolsHieraError: in the case the Hiera call failed
        """
        hiera_cmd = [self.binary_path, "-c", self.config_path, key]
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
        if len(hostgroup) > self.hostgroup_depth:
            logging.warn("The lookup depth for hostgroup keys is limited to %d levels"
                % self.hostgroup_depth)
            logging.warn("You might be leaving behind some data")
        hiera_cmd.extend(["::encgroup_%d=%s" % (i,x) 
            for i,x in enumerate(hostgroup)])
        for factname in self.fact_list:
            self.__append_fact(factname, facts, hiera_cmd)
        logging.debug("About to execute: %s" % hiera_cmd)
        try:
            process = subprocess.Popen(hiera_cmd, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            stdout = process.communicate()[0]
        except OSError, error:
            raise AiToolsHieraError("Hiera call failed (%s)" % error)
        if process.returncode == os.EX_OK:
            chopped = stdout.splitlines()
            if chopped and chopped[-1] == 'nil': # Jeez...
                raise AiToolsHieraKeyNotFoundError(stdout if self.trace else "")
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
