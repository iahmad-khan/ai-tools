__author__ = 'mccance'

import re
import requests
try:
    import simplejson as json
except ImportError:
    import json
import logging
from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsTrustedBagNotFoundError
from aitools.errors import AiToolsTrustedBagError
from aitools.errors import AiToolsTrustedBagNotAllowedError
from aitools.errors import AiToolsTrustedBagInternalServerError
from aitools.errors import AiToolsTrustedBagNotImplementedError
from aitools.httpclient import HTTPClient
from aitools.config import TrustedBagConfig
import base64
from distutils.util import strtobool
from urllib import quote_plus
from aitools.common import deref_url

logger = logging.getLogger(__name__)


class TrustedBagClient(HTTPClient):

    def __init__(self, host=None, port=None, timeout=None, show_url=False, dryrun=False, deref_alias=False):
        """
        Tbag client for interacting with the Tbag service. Autoconfigures via the AiConfig
        object.

        :param host: override the auto-configured Rogert host
        :param port: override the auto-configured Roger port
        :param timeout: override the auto-configured Roger timeout
        :param show_url: print the URLs used to sys.stdout
        :param dryrun: create a dummy client
        :param deref_alias: dereference dns load balanced aliases
        """
        tbag = TrustedBagConfig()
        self.host = host or tbag.tbag_hostname
        self.port = int(port or tbag.tbag_port)
        self.timeout = int(timeout or tbag.tbag_timeout)
        self.dryrun = dryrun
        self.show_url = show_url
        self.deref_alias = strtobool(deref_alias)

    def get_keys(self, entity, scope):
        tbag_endpoint = self.fetch_keys_endpoint(entity, scope)
        (code, body) = self.__do_api_request("get", tbag_endpoint)
        if code == requests.codes.not_found:
            raise AiToolsTrustedBagNotFoundError("%s '%s' not found in tbag" % (scope.capitalize(), entity))
        return body

    def get_key(self, entity, scope, key):
        tbag_endpoint = self.fetch_secret_endpoint(entity, key, scope)
        (code, body) = self.__do_api_request("get", tbag_endpoint)
        if code == requests.codes.not_found:
            raise AiToolsTrustedBagNotFoundError("Key '%s' not found for %s '%s' in tbag" % (key, scope, entity))
        if body.has_key("encoding") and body["encoding"] == 'b64':
            body["secret"] = base64.b64decode(body["secret"])
        return body

    def get_from_tree(self, hostname, key):
        tbag_endpoint = self.fetch_secret_tree_endpoint(hostname, key)
        (code, body) = self.__do_api_request("get", tbag_endpoint)
        if code == requests.codes.not_found:
            raise AiToolsTrustedBagNotFoundError("Key '%s' not found for '%s' in tbag tree" % (key, hostname))
        return body

    def fetch_secret_tree_endpoint(self, hostname, key):
        tbag_endpoint = "tbag/v1/hosttree/%s/secret/%s/" % (hostname, key)
        return tbag_endpoint

    def fetch_keys_endpoint(self, entity, scope):
        if scope == 'host':
            tbag_endpoint = "tbag/v1/host/%s/" % (entity,)
        elif scope == 'hostgroup':
            tbag_endpoint = "tbag/v1/hostgroup/%s/" % entity.replace("/", "-")
        else:
            raise AttributeError("scope must be either 'host' or 'hostgroup'")
        return tbag_endpoint

    def fetch_secret_endpoint(self, entity, key, scope):
        if scope == 'host':
            tbag_endpoint = "tbag/v1/host/%s/secret/%s/" % (entity, key)
        elif scope == 'hostgroup':
            tbag_endpoint = "tbag/v1/hostgroup/%s/secret/%s/" % (entity.replace("/", "-"), key)
        else:
            raise AttributeError("scope must be either 'host' or 'hostgroup'")
        return tbag_endpoint

    def add_key(self, entity, scope, key, secret, b64_value=False):
        if self.dryrun:
            logger.info("Not creating key '%s' on '%s' in tbag as dryrun enabled" % (key, entity))
            return True
        logger.info("Adding key '%s' to tbag for %s '%s'" % (key, scope, entity))
        data = dict()
        data["secret"] = secret
        if b64_value:
            data["encoding"] = "b64"
        tbag_endpoint = self.fetch_secret_endpoint(entity, key, scope)

        d = json.dumps(data)
        (code, body) = self.__do_api_request("post", tbag_endpoint, data=d)
        if code == requests.codes.not_found:
            raise AiToolsTrustedBagNotFoundError("%s '%s' not found in tbag" % (scope.capitalize(), entity))
        elif code == requests.codes.not_allowed:
            raise AiToolsTrustedBagNotAllowedError("Not allowed to post key '%s' to '%s'" % (key, tbag_endpoint))
        elif code == requests.codes.not_implemented:
            raise AiToolsTrustedBagNotImplementedError("Not implemented trying to post to '%s'" % tbag_endpoint)
        elif code == requests.codes.internal_server_error:
            raise AiToolsTrustedBagInternalServerError("Received 500 trying to post to '%s'" % tbag_endpoint)
        return body

    def delete_key(self, entity, scope, key):
        if self.dryrun:
            logger.info("Not deleting key '%s' from '%s' in tbag as dryrun selected" % (key, entity))
            return True
        tbag_endpoint = self.fetch_secret_endpoint(entity, key, scope)

        (code, body) = self.__do_api_request("delete", tbag_endpoint)
        if code == requests.codes.not_found:
            raise AiToolsTrustedBagNotFoundError("Key '%s' not found on %s '%s', can't delete" % (key, scope, entity))
        elif code == requests.codes.not_allowed:
            raise AiToolsTrustedBagNotAllowedError("Not allowed to delete key '%s' on %s '%s'" % (key, scope, entity))
        elif code == requests.codes.not_implemented:
            raise AiToolsTrustedBagNotImplementedError("Not implemented trying to delete from '%s'" % tbag_endpoint)
        elif code == requests.codes.internal_server_error:
            raise AiToolsTrustedBagInternalServerError("Received a 500 trying to delete from '%s'" % tbag_endpoint)
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
            code, response = super(TrustedBagClient, self).do_request(method, url, headers, data)
            body = response.text
            if code == requests.codes.unauthorized or code == requests.codes.forbidden:
                raise AiToolsTrustedBagNotAllowedError("Unauthorized trying '%s' at '%s'" % (method, url))
            if code == requests.codes.ok:
                if re.match('application/json', response.headers['content-type']):
                    body = response.json()
            return (code, body)
        except AiToolsHTTPClientError, error:
            raise AiToolsTrustedBagError(error)



