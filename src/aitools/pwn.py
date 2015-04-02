__author__ = 'ahencz'

try:
    import simplejson as json
except ImportError:
    import json
import requests
import logging
import re
from collections import OrderedDict
from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsPwnNotFoundError
from aitools.errors import AiToolsPwnError
from aitools.errors import AiToolsPwnNotAllowedError
from aitools.errors import AiToolsPwnInternalServerError
from aitools.errors import AiToolsPwnNotImplementedError
from aitools.httpclient import HTTPClient
from aitools.config import PwnConfig
from aitools.common import deref_url


logger = logging.getLogger(__name__)

class PwnClient(HTTPClient):

    def __init__(self, host=None, port=None, timeout=None, show_url=False, dryrun=False, deref_alias=False):
        """
        Pwn client for interacting with the Pwn service. Autoconfigures via the AiConfig
        object.

        :param host: override the auto-configured Pwn host
        :param port: override the auto-configured Pwn port
        :param timeout: override the auto-configured Pwn timeout
        :param show_url: print the URLs used to sys.stdout
        :param dryrun: create a dummy client
        :param deref_alias: dereference dns load balanced aliases
        """
        pwn = PwnConfig()
        self.host = host or pwn.pwn_hostname
        self.port = int(port or pwn.pwn_port)
        self.timeout = int(timeout or pwn.pwn_timeout)
        self.dryrun = dryrun
        self.show_url = show_url
        self.deref_alias = deref_alias

    def fetch_pwn_endpoint(self, entity=None, scope=None):
        if scope and not entity:
            if scope == 'module':
                pwn_endpoint = "pwn/v1/module/"
            elif scope == 'hostgroup':
                pwn_endpoint = "pwn/v1/hostgroup/"
            else:
                raise AttributeError("scope must be either 'module' or 'hostgroup'")
        elif scope and entity:
            if scope == 'module':
                pwn_endpoint = "pwn/v1/module/%s/" % entity
            elif scope == 'hostgroup':
                pwn_endpoint = "pwn/v1/hostgroup/%s/" % entity.replace("/", "-")
            else:
                raise AttributeError("scope must be either 'module' or 'hostgroup'")
        else:
            raise AttributeError("scope must be provided")
        return pwn_endpoint

    def clean_owners(self, owners):
        """
        Make the owners into a list (if it was a single string)
        Strip @cern.ch from the owners list
        """
        if isinstance(owners, str):
            mylist = [ owners ]
        elif isinstance(owners, list):
            mylist = owners
        else:
            raise AttributeError("owners must be either a string or a list of strings")
        return map( lambda owner: owner.lower().strip().replace('@cern.ch',''), mylist )

    def get_ownership(self, entity, scope):
        pwn_endpoint = self.fetch_pwn_endpoint(entity, scope)
        (code, body) = self.__do_api_request("get", pwn_endpoint)
        if code == requests.codes.not_found:
            raise AiToolsPwnNotFoundError("%s %s not found in Pwn" % (scope.title(), entity))
        return body

    def update_or_create_ownership(self, entity, scope, owners, options=None, **kwargs):
        try:
            self.get_ownership(entity, scope)
        except AiToolsPwnNotFoundError:
            return self.create_ownership(entity, scope, owners, options=options, **kwargs)
        else:
            return self.put_ownership(entity, scope, owners, options=options, **kwargs)

    def add_owners(self, entity, scope, owners, options=None, **kwargs):
        try:
            result = self.get_ownership(entity, scope)
        except AiToolsPwnNotFoundError:
            return self.create_ownership(entity, scope, owners, options=options, **kwargs)
        existing_owners = result['owners']
        new_owners = list(OrderedDict.fromkeys(existing_owners+self.clean_owners(owners)))
        return self.put_ownership(entity, scope, new_owners, options=options, **kwargs)

    def remove_owners(self, entity, scope, owners, options=None, **kwargs):
        try:
            result = self.get_ownership(entity, scope)
        except AiToolsPwnNotFoundError:
            return self.create_ownership(entity, scope, owners, options=options, **kwargs)
        existing_owners = result['owners']
        new_owners = [owner for owner in existing_owners if owner not in self.clean_owners(owners)]
        return self.put_ownership(entity, scope, new_owners, options=options, **kwargs)

    def create_ownership(self, entity, scope, owners, options=None, **kwargs):
        if self.dryrun:
            logger.info("Not adding '%s' to Pwn as dryrun enabled" % entity)
            return True
        logger.info("Adding ownership of '%s' to Pwn" % entity)
        pwn_endpoint = self.fetch_pwn_endpoint(scope=scope)
        data = dict()
        data[scope] = entity.replace("/", "-")
        data["owners"] = self.clean_owners(owners)
        if options:
            data["options"] = options
        d = json.dumps(data)
        (code, body) = self.__do_api_request("post", pwn_endpoint, data=d)
        if code == requests.codes.not_found:
            raise AiToolsPwnNotFoundError("Ownership endpoint '%s' not found in Pwn" % pwn_endpoint)
        elif code == requests.codes.not_allowed:
            raise AiToolsPwnNotAllowedError("Not allowed to post '%s' to '%s'" % (entity, pwn_endpoint))
        elif code == requests.codes.not_implemented:
            raise AiToolsPwnNotImplementedError("Not implemented trying to post to '%s'" % pwn_endpoint)
        elif code == requests.codes.internal_server_error:
            raise AiToolsPwnInternalServerError("Received 500 trying to post to '%s'" % pwn_endpoint)
        return body

    def put_ownership(self, entity, scope, owners, options=None, **kwargs):
        if self.dryrun:
            logger.info("Not adding '%s' to Pwn as dryrun enabled" % entity)
            return True
        pwn_endpoint = self.fetch_pwn_endpoint(entity, scope)
        data = dict()
        data[scope] = entity.replace("/", "-")
        data["owners"] = self.clean_owners(owners)
        if options:
            data["options"] = options
        d = json.dumps(data)
        (code, body) = self.__do_api_request("put", pwn_endpoint, data=d)
        if code == requests.codes.not_found:
            raise AiToolsPwnNotFoundError("%s %s not found in Pwn" % (scope.title(), entity))
        elif code == requests.codes.not_allowed:
            raise AiToolsPwnNotAllowedError("Not allowed to put details for %s in Pwn" % entity)
        elif code == requests.codes.not_implemented:
            raise AiToolsPwnNotImplementedError("Not implemented when trying to put to %s" % pwn_endpoint)
        elif code == requests.codes.internal_server_error:
            raise AiToolsPwnInternalServerError("Received 500 when trying to put to %s" % pwn_endpoint)
        return body

    def delete_ownership(self, entity, scope):
        if self.dryrun:
            logger.info("Not deleting '%s' from Pwn as dryrun selected" % entity)
            return True
        pwn_endpoint = self.fetch_pwn_endpoint(entity, scope)
        (code, body) = self.__do_api_request("delete", pwn_endpoint)
        if code == requests.codes.not_found:
            raise AiToolsPwnNotFoundError("%s %s not found, can't delete" % (scope.title(), entity))
        elif code == requests.codes.not_allowed:
            raise AiToolsPwnNotAllowedError("Not allowed to delete %s '%s'" % (scope.title(), entity))
        elif code == requests.codes.not_implemented:
            raise AiToolsPwnNotImplementedError("Not implemented trying to delete at '%s'" % pwn_endpoint)
        elif code == requests.codes.internal_server_error:
            raise AiToolsPwnInternalServerError("Received a 500 trying to delete at '%s'" % pwn_endpoint)
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
            code, response = super(PwnClient, self).do_request(method, url, headers, data)
            body = response.text
            if code == requests.codes.unauthorized or code == requests.codes.forbidden:
                raise AiToolsPwnNotAllowedError("Unauthorized trying '%s' at '%s'" % (method, url))
            if code == requests.codes.ok:
                if re.match('application/json', response.headers['content-type']):
                    body = response.json()
            return (code, body)
        except AiToolsHTTPClientError, error:
            raise AiToolsPwnError(error)
