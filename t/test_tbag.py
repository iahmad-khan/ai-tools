import os
import sys
sys.path.insert(0, os.path.abspath("../src"))
import unittest
from argparse import ArgumentParser
from aitools.config import TrustedBagConfig
from aitools.trustedbag import TrustedBagClient
from aitools.errors import AiToolsTrustedBagNotAllowedError
from aitools.errors import AiToolsTrustedBagNotFoundError
from aitools.errors import AiToolsTrustedBagNotImplementedError


class TestTrustedBag(unittest.TestCase):

    def setUp(self):
        self.tbag_config = TrustedBagConfig(configfile=os.path.abspath("ai.conf"))
        parser = ArgumentParser()
        self.tbag_config.add_standard_args(parser)
        (pargs, _) = self.tbag_config.parser.parse_known_args()
        self.tbag_config.read_config_and_override_with_pargs(pargs)

# yes, explicit order is frowned upon, but add/show/delete so...
    def test_00_default_args(self):
        self.assertEqual(self.tbag_config.tbag_hostname, "teigitest.cern.ch")

    def test_01_tbag_add_host_key(self):
        tbag = TrustedBagClient()
        hostname = "aiadm047.cern.ch"
        key = "testsecret"
        value = "sooperseekrit"
        tbag.add_key(hostname, "host", key, value)

    def test_02_tbag_get_host_key(self):
        tbag = TrustedBagClient()
        hostname = "aiadm047.cern.ch"
        key = "testsecret"
        expected_value = "sooperseekrit"
        result = tbag.get_key(hostname, "host", key)
        self.assertEqual(expected_value, result['secret'])

    def test_03_tbag_del_host_key(self):
        tbag = TrustedBagClient()
        hostname = "aiadm047.cern.ch"
        key = "testsecret"
        result = tbag.delete_key(hostname, "host", key)
        self.assertRaises(AiToolsTrustedBagNotFoundError, tbag.get_key, hostname, "host", key)

    def test_04_tbag_add_hg_key(self):
        tbag = TrustedBagClient()
        hg = "punch/puppet/master/panic"
        key = "testsecret"
        value = "hgsecretstring"
        tbag.add_key(hg, "hostgroup", key, value)

    def test_05_tbag_get_hg_key(self):
        tbag = TrustedBagClient()
        hg = "punch/puppet/master/panic"
        key = "testsecret"
        expected_value = "hgsecretstring"
        result = tbag.get_key(hg, "hostgroup", key)
        self.assertEqual(expected_value, result['secret'])

    def test_06_tbag_del_hg_key(self):
        tbag = TrustedBagClient()
        hg = "punch/puppet/master/panic"
        key = "testsecret"
        tbag.delete_key(hg, "hostgroup", key)
        self.assertRaises(AiToolsTrustedBagNotFoundError, tbag.get_key, hg, "hostgroup", key)

