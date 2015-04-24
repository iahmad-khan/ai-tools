__author__ = "ahencz"

import os
import sys
sys.path.insert(0, os.path.abspath("../src"))
import unittest
from argparse import ArgumentParser
from aitools.config import AuthzConfig
from aitools.authz import AuthzClient
from aitools.errors import AiToolsAuthzNotAllowedError
from aitools.errors import AiToolsAuthzNotFoundError
from aitools.errors import AiToolsAuthzNotImplementedError

from nose.tools import set_trace

# Test cases were based on Tbag tests

class TestAuthz(unittest.TestCase):

    def setUp(self):
        self.authz_config = AuthzConfig(configfile=os.path.abspath("ai.conf"))
        parser = ArgumentParser()
        self.authz_config.add_standard_args(parser)
        (pargs, _) = self.authz_config.parser.parse_known_args()
        self.authz_config.read_config_and_override_with_pargs(pargs)
        self.test_entities = { "hostgroup": "punch/puppetdb", "hostname": "ahencz-dev" }
        self.test_user = 'ahencz'
        # self.test_ownership = [["ahencz@cerN.ch ", "ai-config-team"], ["ai-robots@CERN.CH"]]
        # self.test_options = { "hasPhysical": True }

# yes, explicit order is frowned upon, but add/show/delete so...
    def test_00_default_args(self):
        self.assertEqual(self.authz_config.authz_hostname, "teigitest.cern.ch")

    def test_01_authz_get_info(self):
        authz = AuthzClient()

        scope = 'hostgroup'
        entity = self.test_entities[scope]
        # set_trace()
        resp = authz.get_authz(entity, scope, self.test_user)
        self.assertTrue(resp['authorized'])

        scope = 'hostname'
        entity = self.test_entities[scope]
        resp = authz.get_authz(entity, scope, self.test_user)
        self.assertTrue(resp['authorized'])

    def test_02_authz_get_info_fail(self):
        authz = AuthzClient()
        scope = 'hostgroup'
        entity = self.test_entities[scope]
        requestor = self.test_user
        self.assertRaises(TypeError, authz.get_authz, entity, scope)
        self.assertRaises(AttributeError, authz.get_authz, entity, scope, None)
        set_trace()
        resp = authz.get_authz('afsserv', 'hostgroup', self.test_user)
        # self.assertRaises(AiToolsAuthzNotFoundError, authz.get_authz, 'idontexist', scope, requestor)


    # def test_02_pwn_get_hostgroup_ownership(self):
    #     pwn = PwnClient()
    #     scope = 'hostgroup'
    #     entity = self.test_entities[scope]
    #     expected_owners = pwn.clean_owners(self.test_ownership[0])
    #     expected_options = self.test_options
    #     result = pwn.get_ownership(entity, scope)
    #     self.assertEqual(expected_owners, result['owners'])
    #     self.assertEqual(expected_options, result['options'])
