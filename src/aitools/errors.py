class AiToolsError(Exception):
    pass

class AiToolsInitError(AiToolsError):
    pass

class AiToolsHTTPClientError(AiToolsError):
    pass

class AiToolsForemanError(AiToolsHTTPClientError):
    pass

class AiToolsForemanNotFoundError(AiToolsForemanError):
    pass

class AiToolsForemanNotAllowedError(AiToolsForemanError):
    pass

class AiToolsPdbError(AiToolsHTTPClientError):
    pass

class AiToolsPdbNotFoundError(AiToolsPdbError):
    pass

class AiToolsPdbNotAllowedError(AiToolsPdbError):
    pass

class AiToolsCertmgrError(AiToolsHTTPClientError):
    pass

class AiToolsNovaError(AiToolsError):
    pass

class AiToolsCinderError(AiToolsError):
    pass

class AiToolsOpenstackAuthError(AiToolsError):
    pass

class AiToolsOpenstackAuthBadEnvError(AiToolsOpenstackAuthError):
    def __str__(self):
        return """
Unable to chat to Openstack. This is normally because you have sourced a
Password-based Openstack RC file which is no longer compatible with ai-tools.
The fastest way to get a working environment back is to get a new shell by, for
instance, logging out and back in again.

Please bear in mind that it is no longer necessary to source a different OpenRC
file to switch between Openstack projects (ai-rc should be used instead)."""

class AiToolsRogerError(AiToolsHTTPClientError):
    pass

class AiToolsRogerNotFoundError(AiToolsRogerError):
    pass

class AiToolsRogerNotAllowedError(AiToolsRogerError):
    pass

class AiToolsRogerNotImplementedError(AiToolsRogerError):
    pass

class AiToolsRogerInternalServerError(AiToolsRogerError):
    pass

class AiToolsHieraError(AiToolsHTTPClientError):
    pass

class AiToolsHieraKeyNotFoundError(AiToolsHieraError):
    def __str__(self):
        return \
"""Key not found:
  Either the key is not defined in the hostgroup-level hierarchy for the given
  node or it is defined at module-level and you're not passing any via -m. If for
  instance you're looking up a Lemon metric you definetely want to pass -m lemon
  --hash. Use --trace to know what files this tool is looking into."""

class AiToolsEncError(AiToolsHTTPClientError):
    pass

class AiToolsGitError(AiToolsError):
    pass

class AiToolsAimsError(AiToolsError):
    pass

class AiToolsTrustedBagError(AiToolsHTTPClientError):
    pass

class AiToolsTrustedBagNotFoundError(AiToolsTrustedBagError):
    pass

class AiToolsTrustedBagNotAllowedError(AiToolsTrustedBagError):
    pass

class AiToolsTrustedBagNotImplementedError(AiToolsTrustedBagError):
    pass

class AiToolsTrustedBagInternalServerError(AiToolsTrustedBagError):
    pass

class AiToolsAiForemanError(AiToolsError):
    pass

class AiToolsPwnError(AiToolsError):
    pass

class AiToolsPwnNotFoundError(AiToolsPwnError):
    pass

class AiToolsPwnNotAllowedError(AiToolsPwnError):
    pass

class AiToolsPwnNotImplementedError(AiToolsPwnError):
    pass

class AiToolsPwnInternalServerError(AiToolsPwnError):
    pass

class AiToolsAuthzError(AiToolsError):
    pass

class AiToolsAuthzNotFoundError(AiToolsAuthzError):
    pass

class AiToolsAuthzNotAllowedError(AiToolsAuthzError):
    pass

class AiToolsAuthzNotImplementedError(AiToolsAuthzError):
    pass

class AiToolsAuthzInternalServerError(AiToolsAuthzError):
    pass

class AiToolsLandbError(AiToolsError):
    pass

class AiToolsLandbInitError(AiToolsLandbError):
    pass
