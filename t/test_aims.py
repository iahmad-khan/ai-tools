import unittest
from aitools.aims import AimsClient
from aitools.errors import AiToolsAimsError

class TestAimsClient(unittest.TestCase):

    def setUp(self):
        self.aims = AimsClient()

    def test_foreman_os_translation(self):
        os = {}
        os['name'] = "SLC"
        os['major'] = "6"
        os['minor'] = "5"
        arch = {}
        arch['name'] = "x86_64"
        self.assertEquals("SLC65_X86_64",
            self.aims._translate_foreman_os_to_target(os, arch))

        os['major'] = "5"
        os['minor'] = "7"
        arch['name'] = "i386"
        self.assertEquals("SLC57_I386",
            self.aims._translate_foreman_os_to_target(os, arch))

        os['name'] = "RedHat"
        os['major'] = "6"
        os['minor'] = "5"
        arch['name'] = "x86_64"
        self.assertEquals("RHEL6_U5_X86_64",
            self.aims._translate_foreman_os_to_target(os, arch))

        os['name'] = "CentOS"
        os['major'] = "7"
        os['minor'] = "0"
        arch['name'] = "x86_64"
        self.assertEquals("CC7_X86_64",
            self.aims._translate_foreman_os_to_target(os, arch))

        os['name'] = "CentOS"
        os['major'] = "7"
        os['minor'] = "1"
        arch['name'] = "i386"
        self.assertEquals("CC7_I386",
            self.aims._translate_foreman_os_to_target(os, arch))

        #self.assertRaises(AiToolsAimsError,
        #    self.aims._translate_foreman_os_to_target, os, arch)
