__author__ = 'mccance'

from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsEncError
from aitools.httpclient import HTTPClient
from aitools.config import EncConfig
import yaml

class EncClient(HTTPClient):

    def __init__(self, host=None, port=None, timeout=None, dryrun=False):
        encconf = EncConfig()
        self.host = host or encconf.enc_hostname
        self.port = int(port or encconf.enc_port)
        self.timeout = int(timeout or encconf.enc_timeout)
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
