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

class AiToolsCertmgrError(AiToolsHTTPClientError):
    pass

class AiToolsNovaError(AiToolsError):
    pass

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

class AiToolsEncError(AiToolsHTTPClientError):
    pass
