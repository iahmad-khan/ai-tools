__author__ = 'ahencz'

try:
    import simplejson as json
except ImportError:
    import json
import requests
import logging
import re
from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsAuthzNotFoundError
from aitools.errors import AiToolsAuthzError
from aitools.errors import AiToolsAuthzNotAllowedError
from aitools.errors import AiToolsAuthzInternalServerError
from aitools.errors import AiToolsAuthzNotImplementedError
from aitools.httpclient import HTTPClient
from aitools.config import AuthzConfig
from aitools.common import deref_url

logger = logging.getLogger(__name__)

class AuthzClient(HTTPClient):

    def __init__(self, host=None, port=None, timeout=None, show_url=False, dryrun=False, deref_alias=False):
        """
        Authz client for interacting with the Authz service. Autoconfigures via the AiConfig
        object.

        :param host: override the auto-configured Authz host
        :param port: override the auto-configured Authz port
        :param timeout: override the auto-configured Authz timeout
        :param show_url: print the URLs used to sys.stdout
        :param dryrun: create a dummy client
        :param deref_alias: dereference dns load balanced aliases
        """
        authz = AuthzConfig()
        self.host = host or authz.authz_hostname
        self.port = int(port or authz.authz_port)
        self.timeout = int(timeout or authz.authz_timeout)
        self.dryrun = dryrun
        self.show_url = show_url
        self.deref_alias = deref_alias

    def fetch_authz_endpoint(self, entity=None, scope=None, requestor=None):
        # if scope and entity and not requestor:
        #     if scope == 'hostname':
        #         authz_endpoint = "authz/v1/hostname/%s/"%entity
        #     elif scope == 'hostgroup':
        #         authz_endpoint = "authz/v1/hostgroup/%s/"%entity.replace('/','-')
        #     else:
        #         raise AttributeError("scope must be either 'hostname' or 'hostgroup'")
        if scope and entity and requestor:
            if scope == 'hostname':
                authz_endpoint = "authz/v1/hostname/%s/username/%s/" % (entity, requestor)
            elif scope == 'hostgroup':
                authz_endpoint = "authz/v1/hostgroup/%s/username/%s/" % (entity.replace('/','-'), requestor)
            else:
                raise AttributeError("scope must be either 'hostname' or 'hostgroup'")
        else:
            raise AttributeError("At least scope and entity must be provided")
        return authz_endpoint

    def get_authz(self, entity, scope, requestor):
        authz_endpoint = self.fetch_authz_endpoint(entity, scope, requestor)
        (code, body) = self.__do_api_request("get", authz_endpoint)
        if code == requests.codes.not_found:
            raise AiToolsAuthzNotFoundError("%s %s not found in Authz" % (scope.title(), entity))
        return body

    def __do_api_request(self, method, url, data=None):
        url="https://%s:%u/%s" % \
            (self.host, self.port, url)
        if self.deref_alias:
            url = deref_url(url)
        headers = {'Accept': 'application/json',
                   'Accept-Encoding': 'deflate'}
        if data:
            headers["Content-Type"] = "application/json"

        if self.show_url:
            print url
        try:
            code, response = super(AuthzClient, self).do_request(method, url, headers, data)
            body = response.text
            if code == requests.codes.unauthorized or code == requests.codes.forbidden:
                raise AiToolsAuthzNotAllowedError("Unauthorized trying '%s' at '%s'" % (method, url))
            if code == requests.codes.ok:
                if re.match('application/json', response.headers['content-type']):
                    body = response.json()
            return (code, body)
        except AiToolsHTTPClientError, error:
            raise AiToolsAuthzError(error)
