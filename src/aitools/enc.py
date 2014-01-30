__author__ = 'mccance'

DEFAULT_ENC_TIMEOUT = 15
DEFAULT_ENC_HOSTNAME = "judy.cern.ch"
DEFAULT_ENC_PORT = 8443

from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsEncError
from aitools.httpclient import HTTPClient
import re
import yaml

class EncClient(HTTPClient):

    def __init__(self, host, port, timeout, dryrun=False):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.dryrun = dryrun
        self.cache = {}

    def get_node_enc(self, hostname):
        return self.__do_api_request("get", "node/%s?format=yml" % (hostname,))

    def __do_api_request(self, method, url, data=None):
        url="https://%s:%u/%s" % \
            (self.host, self.port, url)
        headers = {'Accept': 'application/yaml'}

        try:
            code, response = super(EncClient, self).do_request(method, url, headers, data)
            body = response.text
            yam = yaml.load(body)
            return (code, yam)
        except AiToolsHTTPClientError, error:
            raise AiToolsEncError(error)


def add_common_enc_args(parser):
    parser.add_argument('--enc-timeout', type=int,
        help="Timeout for ENC operations (default: %s seconds)" % \
        DEFAULT_ENC_TIMEOUT,
        default = DEFAULT_ENC_TIMEOUT)
    parser.add_argument('--enc-hostname',
        help="ENC hostname (default: %s)" % DEFAULT_ENC_HOSTNAME,
        default=DEFAULT_ENC_HOSTNAME)
    parser.add_argument('--enc-port', type=int,
        help="ENC  port (default: %s)" % DEFAULT_ENC_PORT,
        default=DEFAULT_ENC_PORT)