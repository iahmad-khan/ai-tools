__author__ = 'bejones'

import unittest
import sys
import os
import re
import string
from argparse import ArgumentParser
from aitools.config import ForemanConfig
from aitools.foreman import ForemanClient
from aitools.errors import AiToolsForemanError
from aitools.errors import AiToolsForemanNotAllowedError
from aitools.errors import AiToolsForemanNotFoundError


class TestForeman(unittest.TestCase):

    def setUp(self):
        self.foreman_config = ForemanConfig(configfile=os.path.abspath("ai.conf"))
        parser = ArgumentParser()
        self.foreman_config.add_standard_args(parser)

    def test_config_obj(self):
        self.assertTrue((isinstance(self.foreman_config.parser, ArgumentParser)))

    def test_default_args(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        self.assertEqual(self.foreman_config.foreman_hostname, "foreman-test.cern.ch")
        self.assertEqual(self.foreman_config.foreman_port, "8443")

    def test_foreman_obj(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        self.assertEqual(foreman_client.host, self.foreman_config.foreman_hostname)
        self.assertEqual(foreman_client.port, int(self.foreman_config.foreman_port))

    def test_foreman_get_media(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.get_media()
        self.assertTrue(res)
        self.assertTrue((isinstance(res, list)))
        self.assertTrue(("id" in res[0].keys()))

    def test_foreman_get_ptable(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.get_ptables()
        self.assertTrue(res)
        self.assertTrue((isinstance(res, list)))
        self.assertTrue(("id" in res[0].keys()))

    def test_foreman_get_operatinsystem(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.get_operatingsystems()
        self.assertTrue(res)
        self.assertTrue((isinstance(res, list)))
        self.assertTrue(("id" in res[0].keys()))

    def test_foreman_operatingsystem_property(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.operatingsystems
        self.assertTrue(res)
        self.assertTrue((isinstance(res, dict)))

    def test_foreman_get_architectures(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.get_architectures()
        self.assertTrue(res)
        self.assertTrue(("id" in res[0].keys()))

    def test_foreman_architectures_property(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.architectures
        self.assertTrue(res)
        self.assertTrue((isinstance(res, dict)))

    def test_foreman_get_models(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.get_models()
        self.assertTrue(res)
        self.assertTrue(("id" in res[0].keys()))

    def test_foreman_models_property(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.models
        self.assertTrue(res)
        self.assertTrue((isinstance(res, dict)))

    def test_foreman_get_hostgroups(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.get_hostgroups()
        self.assertTrue(res)
        self.assertTrue(("id" in res[0].keys()))

    def test_foreman_hostgroups_property(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.hostgroups
        self.assertTrue(res)
        self.assertTrue((isinstance(res, dict)))

    def test_foreman_get_environments(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.get_environments()
        self.assertTrue(res)
        self.assertTrue(("id" in res[0].keys()))

    def test_foreman_environments_property(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.environments
        self.assertTrue(res)
        self.assertTrue((isinstance(res, dict)))

    def test_foreman_get_users(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.get_users()
        self.assertTrue(res)
        self.assertTrue(("id" in res[0].keys()))

    def test_foreman_users_property(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.users
        self.assertTrue(res)
        self.assertTrue((isinstance(res, dict)))

    def test_foreman_get_usergroups(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.get_usergroups()
        self.assertTrue(res)
        self.assertTrue(("id" in res[0].keys()))

    def test_foreman_usergroups_property(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.usergroups
        self.assertTrue(res)
        self.assertTrue((isinstance(res, dict)))

    def test_foreman_get_domains(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.get_domains()
        self.assertTrue(res)
        self.assertTrue(("id" in res[0].keys()))

    def test_foreman_domains_property(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.domains
        self.assertTrue(res)
        self.assertTrue((isinstance(res, dict)))

    def test_foreman_get_subnets(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.get_subnets()
        self.assertTrue(res)
        self.assertTrue(("id" in res[0].keys()))

    def test_foreman_subnets_property(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        res = foreman_client.subnets
        self.assertTrue(res)
        self.assertTrue((isinstance(res, dict)))

    def test_resolve_hostgroup_id(self):
        (pargs, _) = self.foreman_config.parser.parse_known_args()
        self.foreman_config.read_config_and_override_with_pargs(pargs)
        foreman_client = ForemanClient()
        hid = foreman_client.resolve_hostgroup_id("punch/puppet/master/batch")
        self.assertEqual(int(hid), 764)
