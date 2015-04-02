__author__ = "ahencz"

import os
import sys
sys.path.insert(0, os.path.abspath("../src"))
import unittest
from argparse import ArgumentParser
from aitools.config import PwnConfig
from aitools.pwn import PwnClient
from aitools.errors import AiToolsPwnNotAllowedError
from aitools.errors import AiToolsPwnNotFoundError
from aitools.errors import AiToolsPwnNotImplementedError

# Test cases were based on Tbag tests

class TestPwn(unittest.TestCase):

    def setUp(self):
        self.pwn_config = PwnConfig(configfile=os.path.abspath("ai.conf"))
        parser = ArgumentParser()
        self.pwn_config.add_standard_args(parser)
        (pargs, _) = self.pwn_config.parser.parse_known_args()
        self.pwn_config.read_config_and_override_with_pargs(pargs)
        self.test_entities = { "hostgroup": "punch/puppetdb", "module": "my_module" }
        self.test_ownership = [["ahencz@cerN.ch ", "ai-config-team"], ["ai-robots@CERN.CH"]]
        self.test_options = { "hasPhysical": True }

# yes, explicit order is frowned upon, but add/show/delete so...
    def test_00_default_args(self):
        self.assertEqual(self.pwn_config.pwn_hostname, "teigitest.cern.ch")

    def test_01_pwn_add_hostgroup_ownership(self):
        pwn = PwnClient()
        scope = 'hostgroup'
        entity = self.test_entities[scope]
        owners = self.test_ownership[0]
        options = self.test_options
        pwn.update_or_create_ownership(entity, scope, owners, options=options)

    def test_02_pwn_get_hostgroup_ownership(self):
        pwn = PwnClient()
        scope = 'hostgroup'
        entity = self.test_entities[scope]
        expected_owners = pwn.clean_owners(self.test_ownership[0])
        expected_options = self.test_options
        result = pwn.get_ownership(entity, scope)
        self.assertEqual(expected_owners, result['owners'])
        self.assertEqual(expected_options, result['options'])

    def test_03_pwn_update_hostgroup_ownership(self):
        pwn = PwnClient()
        scope = 'hostgroup'
        entity = self.test_entities[scope]
        owners = self.test_ownership[1]
        options = self.test_options
        pwn.update_or_create_ownership(entity, scope, owners)

    def test_04_pwn_get_hostgroup_ownership(self):
        pwn = PwnClient()
        scope = 'hostgroup'
        entity = self.test_entities[scope]
        expected_owners = pwn.clean_owners(self.test_ownership[1])
        expected_options = self.test_options
        result = pwn.get_ownership(entity, scope)
        self.assertEqual(expected_owners, result['owners'])
        self.assertEqual(expected_options, result['options'])

    def test_05_pwn_add_hostgroup_owners(self):
        pwn = PwnClient()
        scope = 'hostgroup'
        entity = self.test_entities[scope]
        owners_to_add = self.test_ownership[0]
        expected_owners = pwn.clean_owners(self.test_ownership[1] + self.test_ownership[0])
        expected_options = self.test_options
        pwn.add_owners(entity, scope, owners_to_add)
        result = pwn.get_ownership(entity, scope)
        self.assertEqual(expected_owners, result['owners'])
        self.assertEqual(expected_options, result['options'])

    def test_06_pwn_remove_hostgroup_owner(self):
        pwn = PwnClient()
        scope = 'hostgroup'
        entity = self.test_entities[scope]
        owners_to_remove = self.test_ownership[0][1]
        expected_owners  = pwn.clean_owners(self.test_ownership[1] + [self.test_ownership[0][0]])
        expected_options = self.test_options
        pwn.remove_owners(entity, scope, owners_to_remove)
        result = pwn.get_ownership(entity, scope)
        self.assertEqual(expected_owners, result['owners'])
        self.assertEqual(expected_options, result['options'])

    def test_07_pwn_del_hostgroup_ownership(self):
        pwn = PwnClient()
        scope = 'hostgroup'
        entity = self.test_entities[scope]
        result = pwn.delete_ownership(entity, scope)
        self.assertRaises(AiToolsPwnNotFoundError, pwn.get_ownership, entity, scope)

    def test_08_pwn_remove_owner_from_nonexistent_hostgroup(self):
        pwn = PwnClient()
        scope = 'hostgroup'
        entity = self.test_entities[scope]
        self.assertRaises(AiToolsPwnNotFoundError, pwn.remove_owners, entity, scope,
            self.test_ownership[0])
    # Now the sama with modules

    def test_11_pwn_add_module_ownership(self):
        pwn = PwnClient()
        scope = 'module'
        entity = self.test_entities[scope]
        owners = self.test_ownership[0]
        options = self.test_options
        pwn.update_or_create_ownership(entity, scope, owners, options=options)

    def test_12_pwn_get_module_ownership(self):
        pwn = PwnClient()
        scope = 'module'
        entity = self.test_entities[scope]
        expected_owners = pwn.clean_owners(self.test_ownership[0])
        expected_options = self.test_options
        result = pwn.get_ownership(entity, scope)
        self.assertEqual(expected_owners, result['owners'])
        self.assertEqual(expected_options, result['options'])

    def test_13_pwn_update_module_ownership(self):
        pwn = PwnClient()
        scope = 'module'
        entity = self.test_entities[scope]
        owners = self.test_ownership[1]
        options = self.test_options
        pwn.update_or_create_ownership(entity, scope, owners)

    def test_14_pwn_get_module_ownership(self):
        pwn = PwnClient()
        scope = 'module'
        entity = self.test_entities[scope]
        expected_owners = pwn.clean_owners(self.test_ownership[1])
        expected_options = self.test_options
        result = pwn.get_ownership(entity, scope)
        self.assertEqual(expected_owners, result['owners'])
        self.assertEqual(expected_options, result['options'])

    def test_15_pwn_add_module_owners(self):
        pwn = PwnClient()
        scope = 'module'
        entity = self.test_entities[scope]
        owners_to_add = self.test_ownership[0]
        expected_owners = pwn.clean_owners(self.test_ownership[1] + self.test_ownership[0])
        expected_options = self.test_options
        pwn.add_owners(entity, scope, owners_to_add)
        result = pwn.get_ownership(entity, scope)
        self.assertEqual(expected_owners, result['owners'])
        self.assertEqual(expected_options, result['options'])

    def test_16_pwn_remove_module_owner(self):
        pwn = PwnClient()
        scope = 'module'
        entity = self.test_entities[scope]
        owners_to_remove = self.test_ownership[0][1]
        expected_owners  = pwn.clean_owners(self.test_ownership[1] + [self.test_ownership[0][0]])
        expected_options = self.test_options
        pwn.remove_owners(entity, scope, owners_to_remove)
        result = pwn.get_ownership(entity, scope)
        self.assertEqual(expected_owners, result['owners'])
        self.assertEqual(expected_options, result['options'])

    def test_17_pwn_del_module_ownership(self):
        pwn = PwnClient()
        scope = 'module'
        entity = self.test_entities[scope]
        result = pwn.delete_ownership(entity, scope)
        self.assertRaises(AiToolsPwnNotFoundError, pwn.get_ownership, entity, scope)

    def test_18_pwn_remove_owner_from_nonexistent_module(self):
        pwn = PwnClient()
        scope = 'module'
        entity = self.test_entities[scope]
        self.assertRaises(AiToolsPwnNotFoundError, pwn.remove_owners, entity, scope,
            self.test_ownership[0])
