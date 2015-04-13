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

    def test_01_tbag_add_host_key(self):
        tbag = TrustedBagClient()
        hostname = "aiadm053.cern.ch"
        key = "testsecret"
        value = "sooperseekrit"
        tbag.add_key(hostname, "host", key, value)

    def test_02_tbag_get_host_key(self):
        tbag = TrustedBagClient()
        hostname = "aiadm053.cern.ch"
        key = "testsecret"
        expected_value = "sooperseekrit"
        result = tbag.get_key(hostname, "host", key)
        self.assertEqual(expected_value, result['secret'])

    def test_03_tbag_list_host_keys(self):
        tbag = TrustedBagClient()
        hostname = "aiadm053.cern.ch"
        key = "testsecret"
        res = tbag.get_keys(hostname, "host")
        self.assertEqual(hostname, res["hostname"])
        self.assertTrue(key in res["secrets"])

    def test_04_tbag_del_host_key(self):
        tbag = TrustedBagClient()
        hostname = "aiadm053.cern.ch"
        key = "testsecret"
        result = tbag.delete_key(hostname, "host", key)
        self.assertRaises(AiToolsTrustedBagNotFoundError, tbag.get_key, hostname, "host", key)

    def test_05_tbag_add_hg_key(self):
        tbag = TrustedBagClient()
        hg = "punch/puppet/master/panic"
        key = "testsecret"
        value = "hgsecretstring"
        tbag.add_key(hg, "hostgroup", key, value)

    def test_06_tbag_get_hg_key(self):
        tbag = TrustedBagClient()
        hg = "punch/puppet/master/panic"
        key = "testsecret"
        expected_value = "hgsecretstring"
        result = tbag.get_key(hg, "hostgroup", key)
        self.assertEqual(expected_value, result['secret'])

    def test_07_tbag_list_hg_keys(self):
        tbag = TrustedBagClient()
        hg = "punch/puppet/master/panic"
        key = "testsecret"
        res = tbag.get_keys(hg, "hostgroup")
        self.assertEqual(hg, res["hostgroup"])
        self.assertTrue(key in res["secrets"])

    def test_08_tbag_del_hg_key(self):
        tbag = TrustedBagClient()
        hg = "punch/puppet/master/panic"
        key = "testsecret"
        tbag.delete_key(hg, "hostgroup", key)
        self.assertRaises(AiToolsTrustedBagNotFoundError, tbag.get_key, hg, "hostgroup", key)

    def test_09_tbag_host_tree(self):
        tbag = TrustedBagClient()
        hg = "punch/puppet/master/panic"
        host = "lxbsp2702.cern.ch"
        key = "treesecret"
        hostvalue = "host_treesecretstring"
        upper_hg = "punch"
        upper_hg_value = "upperg_treesecretstring"
        hgvalue = "hg_treesecretstring"
        # delete if they exist already
        try:
            tbag.delete_key(host, "host", key)
        except AiToolsTrustedBagNotFoundError:
            pass
        try:
            tbag.delete_key(hg, "hostgroup", key)
        except AiToolsTrustedBagNotFoundError:
            pass
        try:
            tbag.delete_key(upper_hg, "hostgroup", key)
        except AiToolsTrustedBagNotFoundError:
            pass
        tbag.add_key(upper_hg, "hostgroup", key, upper_hg_value)
        uhg_result = tbag.get_from_tree(host, key)
        self.assertEqual(upper_hg_value, uhg_result["secret"])
        tbag.add_key(hg, "hostgroup", key, hgvalue)
        hg_result = tbag.get_from_tree(host, key)
        self.assertEqual(hgvalue, hg_result["secret"])
        tbag.add_key(host, "host", key, hostvalue)
        host_result = tbag.get_from_tree(host, key)
        self.assertEqual(hostvalue, host_result["secret"])
        tbag.delete_key(host, "host", key)
        result = tbag.get_from_tree(host, key)
        self.assertEqual(hgvalue, result["secret"])
        tbag.delete_key(hg, "hostgroup", key)
        result = tbag.get_from_tree(host, key)
        self.assertEqual(upper_hg_value, result["secret"])
        tbag.delete_key(upper_hg, "hostgroup", key)
        self.assertRaises(AiToolsTrustedBagNotFoundError, tbag.get_from_tree, host, key)



