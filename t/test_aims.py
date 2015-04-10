import unittest
from aitools.aims import AimsClient
from aitools.errors import AiToolsAimsError

class TestAimsClient(unittest.TestCase):

    def setUp(self):
        self.aims = AimsClient()
        self.arch_64 = {'name': 'x86_64'}
        self.arch_32 = {'name': 'i386'}

    def generate_os(self, name, major, minor):
        os = {}
        os['name'] = name
        os['major'] = major
        os['minor'] = minor
        return os

    def test_foreman_os_translation_slc(self):
        self.assertEquals("SLC65_X86_64",
            self.aims._translate_foreman_os_to_target(
                self.generate_os("SLC", 6, 5), self.arch_64))

        self.assertEquals("SLC510_I386",
            self.aims._translate_foreman_os_to_target(
                self.generate_os("SLC", 5, 10), self.arch_32))

    def test_foreman_is_translation_rh(self):
        self.assertEquals("RHEL_7_1_X86_64",
            self.aims._translate_foreman_os_to_target(
                self.generate_os("RedHat", 7, 1), self.arch_64))

        self.assertEquals("RHEL_6_5_X86_64",
            self.aims._translate_foreman_os_to_target(
                self.generate_os("RedHat", 6, 5), self.arch_64))

        self.assertEquals("RHEL_5_10_I386",
            self.aims._translate_foreman_os_to_target(
                self.generate_os("RedHat", 5, 10), self.arch_32))

    def test_foreman_is_translation_centos(self):
        self.assertEquals("CC71_X86_64",
            self.aims._translate_foreman_os_to_target(
                self.generate_os("CentOS", 7, 1), self.arch_64))

        self.assertEquals("CC70_X86_64",
            self.aims._translate_foreman_os_to_target(
                self.generate_os("CentOS", 7, 0), self.arch_64))

    def test_foreman_is_translation_notfound(self):
        self.assertRaises(AiToolsAimsError,
            self.aims._translate_foreman_os_to_target,
            self.generate_os("FooOS", 4, 1), self.arch_64)
