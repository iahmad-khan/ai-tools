__author__ = 'mccance'

DEFAULT_PUPPETDB_TIMEOUT = 15
DEFAULT_PUPPETDB_HOSTNAME = "judy.cern.ch"
DEFAULT_PUPPETDB_PORT = 9081

from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsPdbError
from aitools.httpclient import HTTPClient
import re

class PdbClient(HTTPClient):

    def __init__(self, host, port, timeout, dryrun=False):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.dryrun = dryrun
        self.cache = {}

    def get_host(self, hostname):
        host_endpoint = "v3/nodes/%s" % hostname
        (code, body) = self.__do_api_request("get", host_endpoint)
        #todo: handle errors
        return body

    def get_facts(self, hostname):
        host_endpoint = "v3/nodes/%s/facts" % hostname
        (code, body) = self.__do_api_request("get", host_endpoint)
        #todo: handle errors
        return body

    def get_landb(self, hostname):
        host_endpoint = "v3/nodes/%s/resources/Cernfw::Landbset" % hostname
        (code, body) = self.__do_api_request("get", host_endpoint)
        #todo: handle errors
        return body

    def __do_api_request(self, method, url, data=None):
        url="https://%s:%u/%s" % \
            (self.host, self.port, url)
        headers = {'Accept': 'application/json',
                   'Accept-Encoding': 'deflate'}

        try:
            code, response = super(PdbClient, self).do_request(method, url, headers, data)
            body = response.text
            if re.match('application/json', response.headers['content-type']):
                body = response.json()
            return (code, body)
        except AiToolsHTTPClientError, error:
            raise AiToolsPdbError(error)