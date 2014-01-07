import logging
import requests
from requests_kerberos import HTTPKerberosAuth

from aitools.params import CERN_CA_BUNDLE
from aitools.errors import AiToolsHTTPClientError

class HTTPClient(object):
    def __init__(self, host, port, timeout, dryrun=False):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.dryrun = dryrun
        self.cache = {}

    def do_request(self, method, url, headers, data=None):
        logging.debug("Issuing %s on %s" % (method, url))
        logging.debug("With headers: %s" % headers)

        try:
            caller = getattr(requests, method)
            response = caller(url, timeout=self.timeout,
                headers=headers, auth=HTTPKerberosAuth(),
                verify=CERN_CA_BUNDLE, allow_redirects=True,
                data=data)
            logging.debug("Returned (%s) %s",
                            response.status_code, response.text)
            if response.status_code == requests.codes.forbidden or \
                response.status_code == requests.codes.unauthorized:
                    raise AiToolsHTTPClientError("Authentication failed (expired or non-existent TGT?)")
            elif response.status_code == requests.codes.internal_server_error:
                raise AiToolsHTTPClientError("Internal Server Error")
        except requests.exceptions.ConnectionError, error:
            raise AiToolsHTTPClientError("Connection error (%s)" % error)
        except requests.exceptions.Timeout, error:
            raise AiToolsHTTPClientError("Connection timeout")

        return (response.status_code, response)
