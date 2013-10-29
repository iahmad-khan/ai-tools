class AiToolsError(Exception):
    pass

class AiToolsInitError(AiToolsError):
    pass

class AiToolsHTTPClientError(AiToolsError):
    pass

class AiToolsForemanError(AiToolsHTTPClientError):
    pass

class AiToolsCertmgrError(AiToolsHTTPClientError):
    pass

class AiToolsNovaError(AiToolsError):
    pass

class AiToolsRogerError(AiToolsHTTPClientError):
    pass
