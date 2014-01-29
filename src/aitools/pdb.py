__author__ = 'mccance'

DEFAULT_PUPPETDB_TIMEOUT = 15
DEFAULT_PUPPETDB_HOSTNAME = "judy.cern.ch"
DEFAULT_PUPPETDB_PORT = 9081

from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsPdbError
from aitools.httpclient import HTTPClient
import re

class PdbClient(HTTPClient):

    def __init__(self, host, port, timeout, show_url=False, dryrun=False):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.dryrun = dryrun
        self.show_url = show_url
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
        return dict([ (f['name'], f['value']) for f in body ])

    def get_landbsets(self, hostname):
        json_landbsets = self.get_resources(hostname, "Cernfw::Landbset")
        return [ j['title'] for j in json_landbsets ]

    def get_lbaliases(self, hostname):
        json_lb = self.get_resources(hostname, "Lbd::Client")
        return [ l['parameters']['lbalias'] for l in json_lb ]

    def get_resources(self, hostname, resource):
        host_endpoint = "v3/nodes/%s/resources/%s" % (hostname, resource)
        (code, body) = self.__do_api_request("get", host_endpoint)
        #todo: handle errors
        return body

    def raw_request(self, url):
        return self.__do_api_request("get", url)

    def __do_api_request(self, method, url, data=None):
        url="https://%s:%u/%s" % \
            (self.host, self.port, url)
        headers = {'Accept': 'application/json',
                   'Accept-Encoding': 'deflate'}

        if self.show_url:
            print url
        try:
            code, response = super(PdbClient, self).do_request(method, url, headers, data)
            body = response.text
            if re.match('application/json', response.headers['content-type']):
                body = response.json()
            return (code, body)
        except AiToolsHTTPClientError, error:
            raise AiToolsPdbError(error)