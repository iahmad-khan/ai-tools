import unittest
import sys
import os
sys.path.append("../../sys/")
from aitools.config import RogerConfig, AiConfig
from ConfigParser import ConfigParser


class TestRogerGetState(unittest.TestCase):

    def setUp(self):
        self.roger_config = RogerConfig(configfile=os.path.abspath("../ai.conf"))

    def test_config_obj(self):
        self.assertTrue(isinstance(self.roger_config.parser, ConfigParser))


