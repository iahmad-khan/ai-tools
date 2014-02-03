from ConfigParser import ConfigParser

# Monostate pattern, Borg impl
from argparse import ArgumentError
from aitools.errors import AiToolsError
import sys

class AiConfig(object):

    __monostate = {}

    def __new__(cls, *a, **k):
        obj = super(AiConfig, cls).__new__(cls, *a, **k)
        obj.__dict__ = cls.__monostate
        return obj

    def read_config_and_override_with_pargs(self, pargs):
        self.parser = ConfigParser()
        config_file = pargs.config
        try:
            with open(config_file) as f:
                self.parser.readfp(f)
        except IOError:
            sys.stderr.write("Config file (%s) could not be opened\n" % config_file)
            sys.exit(1)
        self.pargs = vars(pargs)

    def __getattr__(self, key):
        try:
            val = self._get_from_cli(key)
            if not val:
                val = self._get_from_configfile(key)
            return val
        except:
            raise AttributeError("'%s' configuration object has no attribute '%s'" % (self.__class__.__name__, key))

    def _get_from_configfile(self, key):
        return self.parser.get("main", key)

    def _get_from_cli(self, key):
        return self.pargs.get(key, None)

    @staticmethod
    def add_configfile_args(parser):
        try:
            parser.add_argument('--config', help="Configuration file",
                                default="/etc/ai/ai.conf")
        except ArgumentError:
            pass

class ForemanConfig(AiConfig):

    def _get_from_configfile(self, key):
        return self.parser.get("foreman", key)

    @staticmethod
    def add_standard_args(parser):
        parser.add_argument('--foreman-timeout', type=int, help="Timeout for Foreman operations")
        parser.add_argument('--foreman-hostname', help="Foreman hostname")
        parser.add_argument('--foreman-port', type=int, help="Foreman port")
        AiConfig.add_configfile_args(parser)

class PdbConfig(AiConfig):

    def _get_from_configfile(self, key):
        return self.parser.get("pdb", key)

    @staticmethod
    def add_standard_args(parser):
        parser.add_argument('--pdb-timeout', type=int, help="Timeout for PuppetDB operations")
        parser.add_argument('--pdb-hostname', help="PuppetDB hostname")
        parser.add_argument('--pdb-port', type=int, help="PuppetDB port")
        AiConfig.add_configfile_args(parser)

class EncConfig(AiConfig):

    def _get_from_configfile(self, key):
        return self.parser.get("enc", key)

    @staticmethod
    def add_standard_args(parser):
        parser.add_argument('--enc-timeout', type=int, help="Timeout for ENC operations")
        parser.add_argument('--enc-hostname', help="ENC hostname")
        parser.add_argument('--enc-port', type=int, help="ENC port")
        AiConfig.add_configfile_args(parser)

class RogerConfig(AiConfig):

    def _get_from_configfile(self, key):
        return self.parser.get("roger", key)

    @staticmethod
    def add_standard_args(parser):
        parser.add_argument('--roger-timeout', type=int, help="Timeout for Roger operations")
        parser.add_argument('--roger-hostname', help="Roger hostname")
        parser.add_argument('--roger-port', type=int, help="Roger port")
        AiConfig.add_configfile_args(parser)

class CertmgrConfig(AiConfig):

    def _get_from_configfile(self, key):
        return self.parser.get("certmgr", key)

    @staticmethod
    def add_standard_args(parser):
        parser.add_argument('--certmgr-timeout', type=int, help="Timeout for Cert manager operations")
        parser.add_argument('--certmgr-hostname', help="Certmanager hostname")
        parser.add_argument('--certmgr-port', type=int, help="Certmanager port")
        AiConfig.add_configfile_args(parser)


class NovaConfig(AiConfig):

    def _get_from_configfile(self, key):
        return self.parser.get("nova", key)

    @staticmethod
    def add_standard_args(parser):
        parser.add_argument('--nova-timeout', type=int, help="Timeout for Nova operations")
        AiConfig.add_configfile_args(parser)