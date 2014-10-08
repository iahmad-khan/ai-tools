__author__ = 'mccance'

import re
import requests
import urllib

from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsPdbNotFoundError
from aitools.errors import AiToolsPdbError
from aitools.errors import AiToolsPdbNotAllowedError
from aitools.httpclient import HTTPClient
from aitools.config import PdbConfig
from distutils.util import strtobool
from aitools.common import deref_url


class PdbClient(HTTPClient):

    def __init__(self, host=None, port=None, timeout=None, show_url=False, dryrun=False, deref_alias=False):
        """
        PuppetDB client for interacting with the PuppetDB service. Autoconfigures via the AiConfig
        object.

        :param host: override the auto-configured PuppetDB host
        :param port: override the auto-configured PuppetDB port
        :param timeout: override the auto-configured PuppetDB timeout
        :param show_url: print the URLs used to sys.stdout
        :param dryrun: create a dummy client
        :param deref_alias: resolve dns load balanced aliases
        """
        pdbcondfig = PdbConfig()
        self.host = host or pdbcondfig.pdb_hostname
        self.port = int(port or pdbcondfig.pdb_port)
        self.timeout = int(timeout or pdbcondfig.pdb_timeout)
        self.dryrun = dryrun
        self.show_url = show_url
        self.deref_alias = strtobool(deref_alias)
        self.cache = {}

    def get_host(self, hostname):
        """
        Returns the basic host info record for a host from the /v3/nodes/[hostname] URL.

        :param hostname: the hostname to query
        :return: the parsed structure from the returned JSON
        :raise AiToolsPdbError: in case the hostname is not found
        """
        host_endpoint = "v3/nodes/%s" % hostname
        (code, body) = self.__do_api_request("get", host_endpoint)
        if code == requests.codes.not_found:
            raise AiToolsPdbNotFoundError("Host %s not found in PuppetDB" % hostname)
        return body

    def get_facts(self, hostname):
        """
        Return all current facts for the specified host, from the /v3/nodes/[hostname]/facts URL.

        :param hostname: the hostname to query
        :return: dict of facts
        :raise AiToolsPdbError: in case the hostname is not found
        """
        host_endpoint = "v3/nodes/%s/facts" % hostname
        (code, body) = self.__do_api_request("get", host_endpoint)
        if code == requests.codes.not_found:
            raise AiToolsPdbNotFoundError("Host %s not found in PuppetDB" % hostname)
        return dict([ (f['name'], f['value']) for f in body ])

    def get_resources(self, hostname, resource):
        """
        Return the specificed resource record for the specified host, from the
        /v3/nodes/[hostname]/resources/[resource] URL

        :param hostname: the hostname to query
        :param resource: the resource to query
        :return: the parsed structure from the returned JSON
        :raise AiToolsPdbError: in case the hostname,resource combination is not found
        """
        host_endpoint = "v3/nodes/%s/resources/%s" % (hostname, resource)
        (code, body) = self.__do_api_request("get", host_endpoint)
        if code == requests.codes.not_found:
            raise AiToolsPdbNotFoundError("Resource %s for host %s not found in PuppetDB" % (resource, hostname))
        return body

    def get_landbsets(self, hostname):
        """
        Return the list of LANDB sets for the specified hostname

        :param hostname: the hostname to query
        :return: a (possibly empty) list of LANDB set strings
        :raise AiToolsPdbError: in case the hostname does not exist
        """
        json_landbsets = self.get_resources(hostname, "Cernfw::Landbset")
        return [ j['title'] for j in json_landbsets ]

    def get_lbaliases(self, hostname):
        """
        Return the list of DNS load-balanced aliases for the specified hostname

        :param hostname: the hostname to query
        :return: a (possibly empty) list of DNS aliases
        :raise AiToolsPdbError: in case the hostname does not exist
        """
        json_lb = self.get_resources(hostname, "Lbd::Client")
        return [ l['parameters']['lbalias'] for l in json_lb ]

    def raw_request(self, url, query=None):
        if query:
            url = "%s?%s" % (url, urllib.urlencode({'query': query}))
        return self.__do_api_request("get", url)

    def __do_api_request(self, method, url, data=None):
        url="https://%s:%u/%s" % \
            (self.host, self.port, url)
        if self.deref_alias:
            url = deref_url(url)
        headers = {'Accept': 'application/json',
                   'Accept-Encoding': 'deflate'}

        if self.show_url:
            print url
        try:
            code, response = super(PdbClient, self).do_request(method, url, headers, data)
            body = response.text
            if code == requests.codes.forbidden or code == requests.codes.unauthorized:
                raise AiToolsPdbNotAllowedError("Unauthorized trying '%s' at '%s'" % (method, url))
            if re.match('application/json', response.headers['content-type']):
                body = response.json()
            return (code, body)
        except AiToolsHTTPClientError, error:
            raise AiToolsPdbError(error)


