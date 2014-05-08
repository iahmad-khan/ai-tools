import unittest
import sys
import os
import re
import string
import random
sys.path.insert(0, os.path.abspath("../src"))
from aitools.config import RogerConfig
from aitools.roger import RogerClient
from aitools.errors import AiToolsRogerNotFoundError
from argparse import ArgumentParser


def teststring_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class TestRoger(unittest.TestCase):

    def setUp(self):
        self.roger_config = RogerConfig(configfile=os.path.abspath("ai.conf"))
        parser = ArgumentParser()
        self.roger_config.add_standard_args(parser)

    def test_config_obj(self):
        self.assertTrue((isinstance(self.roger_config.parser, ArgumentParser)))

    def test_default_args(self):
        (pargs, _) = self.roger_config.parser.parse_known_args()
        self.roger_config.read_config_and_override_with_pargs(pargs)
        self.assertEqual(self.roger_config.roger_hostname, "teigitest.cern.ch")
        self.assertEqual(self.roger_config.roger_port, "8201")
        self.assertEqual(self.roger_config.roger_timeout, "15")

    def test_roger_obj(self):
        (pargs, _) = self.roger_config.parser.parse_known_args()
        self.roger_config.read_config_and_override_with_pargs(pargs)
        rogerclient = RogerClient()
        self.assertEqual(rogerclient.host, self.roger_config.roger_hostname)
        self.assertEqual(rogerclient.host, "teigitest.cern.ch")
        self.assertEqual(rogerclient.port, int(self.roger_config.roger_port))
        self.assertEqual(rogerclient.timeout, int(self.roger_config.roger_timeout))

    def test_roger_get_state(self):
        (pargs, _) = self.roger_config.parser.parse_known_args()
        self.roger_config.read_config_and_override_with_pargs(pargs)
        rogerclient = RogerClient()
        state = rogerclient.get_state("teigitest01.cern.ch") # FIXME: test hosts in the config file
        self.assertTrue((isinstance(state, dict)))
        self.assertTrue(("hostname" in state))
        self.assertEqual(state["hostname"], "teigitest01.cern.ch")

    def test_roger_post_state(self):
        (pargs, _) = self.roger_config.parser.parse_known_args()
        self.roger_config.read_config_and_override_with_pargs(pargs)
        rogerclient = RogerClient()
        self.assertEqual(rogerclient.host, "teigitest.cern.ch")
        message = teststring_generator()
        state = rogerclient.put_state("teigitest01.cern.ch", nc_alarmed=False, message=message + " unittest entry")
        new_state = rogerclient.get_state("teigitest01.cern.ch")
        self.assertTrue((isinstance(new_state, dict)))
        self.assertTrue(("hostname" in new_state))
        self.assertEqual(new_state["hostname"], "teigitest01.cern.ch")
        self.assertFalse(new_state["nc_alarmed"])
        self.assertTrue((re.search("^%s" % message, new_state["message"])))

    def test_roger_delete_state(self):
        (pargs, _) = self.roger_config.parser.parse_known_args()
        self.roger_config.read_config_and_override_with_pargs(pargs)
        rogerclient = RogerClient()
        self.assertEqual(rogerclient.host, "teigitest.cern.ch")
        # need to add the damn thing first
        newstate = rogerclient.update_or_create_state("aiadm049.cern.ch")
        confirm_newstate = rogerclient.get_state("aiadm049.cern.ch")
        self.assertTrue(("hostname" in confirm_newstate))
        delstate = rogerclient.delete_state("aiadm049.cern.ch")
        try:
            rogerclient.get_state("aiadm049.cern.ch")
        except Exception, e:
            self.assertTrue((isinstance(e, AiToolsRogerNotFoundError)))






