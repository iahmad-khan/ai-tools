from ConfigParser import ConfigParser, NoOptionError

# Monostate pattern, Borg impl
from argparse import ArgumentError
import sys


class AiConfig(object):
    """
    Borg class holding the contents of the AI config dile, munged with eponymous CLI options.
    The CLI options, if specified, override the config file. Being a monostate, all instances of the class
    (including subclasses) share the configuration data. The AiConfig class refernces the "main" section,
    the subclasses represent their own section (e.g. ForemanConfig answers for the [foreman] section of the config
    file).

    Use as::

       parser = argparse.ArgumentParser()

       ForemanConfig.add_standard_args(parser)  # adds standard Foreman CLI options, as needed
       PdbConfig.add_standard_args(parser)      # adds standard Foreman PDB options, as needed

       parser.parse_args()                      # the standard --conf option is added automatically

       config = AiConfig()
       config.read_config_and_override_with_pargs(pargs)

       print config.config        # location of the c onfig file
       f = ForemanConfig()
       p = PdbConfig()

       # Access the config values directly as attributes
       print f.foreman_hostname
       print p.pdb_timeout

    """
    __monostate = {}

    def __init__(self, configfile=None):
        self.__dict__ = self.__monostate
        self.configfile = "/etc/ai/ai.conf"
        if configfile:
            self.configfile = configfile
        self.bool_globals = set(['dereference_alias'])

    def read_config_and_override_with_pargs(self, pargs):
        """
        Read the config file and override with the supplied pargs.
        The config file is found using the "--conf" option of the argparser.

        :param pargs: the parser arguments of argparser.
        """
        self.parser = ConfigParser()
        config_file = pargs.config
        try:
            with open(config_file) as f:
                self.parser.readfp(f)
        except IOError:
            sys.stderr.write("Config file (%s) could not be opened\n" % config_file)
            sys.exit(10)
        self.pargs = vars(pargs)

    def __getattr__(self, key):
        try:
            val = self._get_from_cli(key)
            if not val:
                val = self._get_from_configfile(key)
            return val
        except:
            raise AttributeError("'%s' configuration object has no attribute '%s'" % (self.__class__.__name__, key))

    def _get_from_configfile(self, key, section="DEFAULT"):
        if key in self.bool_globals:
            return self.parser.getboolean(section, key)
        else:
            return self.parser.get(section, key)

    def _get_from_cli(self, key):
        return self.pargs.get(key, None)

    def add_global_args(self, parser):
        try:
            parser.add_argument('--config', help="Configuration file",
                                default=self.configfile)
        except ArgumentError:
            pass
        try:
            parser.add_argument('--dereference_alias', help="dereference any lb aliases",
                                default="false")
        except ArgumentError:
            pass

        self.parser = parser


class ForemanConfig(AiConfig):

    def _get_from_configfile(self, key, section="foreman"):
        return super(ForemanConfig, self)._get_from_configfile(key, section=section)

    def add_standard_args(self, parser):
        parser.add_argument('--foreman-timeout', type=int, help="Timeout for Foreman operations")
        parser.add_argument('--foreman-hostname', help="Foreman hostname")
        parser.add_argument('--foreman-port', type=int, help="Foreman port")
        self.add_global_args(parser)


class PdbConfig(AiConfig):

    def _get_from_configfile(self, key, section="pdb"):
        return super(PdbConfig, self)._get_from_configfile(key, section=section)

    def add_standard_args(self, parser):
        parser.add_argument('--pdb-timeout', type=int, help="Timeout for PuppetDB operations")
        parser.add_argument('--pdb-hostname', help="PuppetDB hostname")
        parser.add_argument('--pdb-port', type=int, help="PuppetDB port")
        self.add_global_args(parser)


class EncConfig(AiConfig):

    def _get_from_configfile(self, key, section="enc"):
        return super(EncConfig, self)._get_from_configfile(key, section=section)

    def add_standard_args(self, parser):
        parser.add_argument('--enc-timeout', type=int, help="Timeout for ENC operations")
        parser.add_argument('--enc-hostname', help="ENC hostname")
        parser.add_argument('--enc-port', type=int, help="ENC port")
        self.add_global_args(parser)


class RogerConfig(AiConfig):

    def _get_from_configfile(self, key, section="roger"):
        return super(RogerConfig, self)._get_from_configfile(key, section=section)

    def add_standard_args(self, parser):
        parser.add_argument('--roger-timeout', type=int, help="Timeout for Roger operations")
        parser.add_argument('--roger-hostname', help="Roger hostname")
        parser.add_argument('--roger-port', type=int, help="Roger port")
        self.add_global_args(parser)


class CertmgrConfig(AiConfig):

    def _get_from_configfile(self, key, section="certmgr"):
        return super(CertmgrConfig, self)._get_from_configfile(key, section=section)

    def add_standard_args(self, parser):
        parser.add_argument('--certmgr-timeout', type=int, help="Timeout for Cert manager operations")
        parser.add_argument('--certmgr-hostname', help="Certmanager hostname")
        parser.add_argument('--certmgr-port', type=int, help="Certmanager port")
        self.add_global_args(parser)


class NovaConfig(AiConfig):

    def _get_from_configfile(self, key, section="nova"):
        return super(NovaConfig, self)._get_from_configfile(key, section=section)

    def add_standard_args(self, parser):
        parser.add_argument('--nova-timeout', type=int, help="Timeout for Nova operations")
        self.add_global_args(parser)


class TrustedBagConfig(AiConfig):

    def _get_from_configfile(self, key, section="tbag"):
        return super(TrustedBagConfig, self)._get_from_configfile(key, section=section)

    def add_standard_args(self, parser):
        parser.add_argument('--tbag-timeout', type=int, help="Timeout for trusted bag operations")
        parser.add_argument('--tbag-hostname', help="Trusted bag hostname")
        parser.add_argument('--tbag-port', type=int, help="Trusted bag port")
        self.add_global_args(parser)

class PwnConfig(AiConfig):

    def _get_from_configfile(self, key, section="pwn"):
        return super(PwnConfig, self)._get_from_configfile(key, section=section)

    def add_standard_args(self, parser):
        parser.add_argument('--pwn-timeout', type=int, help="Timeout for pwn operations")
        parser.add_argument('--pwn-hostname', help="Pwn hostname")
        parser.add_argument('--pwn-port', type=int, help="Pwn port")
        self.add_global_args(parser)

class AuthzConfig(AiConfig):

    def _get_from_configfile(self, key, section="authz"):
        return super(AuthzConfig, self)._get_from_configfile(key, section=section)

    def add_standard_args(self, parser):
        parser.add_argument('--authz-timeout', type=int, help="Timeout for authz operations")
        parser.add_argument('--authz-hostname', help="Authz hostname")
        parser.add_argument('--authz-port', type=int, help="Authz port")
        self.add_global_args(parser)

class LandbConfig(AiConfig):

    def _get_from_configfile(self, key, section="landb"):
        return super(LandbConfig, self)._get_from_configfile(key, section=section)

    def add_standard_args(self, parser):
        parser.add_argument('--landb-hostname', help="Landb hostname")
        parser.add_argument('--landb-port', type=int, help="Landb port")
        self.add_global_args(parser)

class AiDisownHostConfig(AiConfig):

    def _get_from_configfile(self, key, section="aidisownhost"):
        return super(AiDisownHostConfig, self)._get_from_configfile(key, section=section)

    def add_standard_args(self, parser):
        parser.add_argument('-o', '--owner', type=str,
            help="LANDB responsible after disowning (default: see /etc/ai/)")
        parser.add_argument('-g', '--hostgroup', type=str,
            help="Target hostgroup after disowning (default: see /etc/ai/)")
        self.add_global_args(parser)
