__author__ = 'bejones'

import re
import requests
try:
    import simplejson as json
except ImportError:
    import json
import logging
from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsRogerNotFoundError
from aitools.errors import AiToolsRogerError
from aitools.errors import AiToolsRogerNotAllowedError
from aitools.errors import AiToolsRogerInternalServerError
from aitools.errors import AiToolsRogerNotImplementedError
from aitools.httpclient import HTTPClient
from aitools.config import RogerConfig

logger = logging.getLogger(__name__)


class RogerClient(HTTPClient):

    def __init__(self, host=None, port=None, timeout=None, show_url=False, dryrun=False):
        """
        Roger client for interacting with the Roger service. Autoconfigures via the AiConfig
        object.

        :param host: override the auto-configured Rogert host
        :param port: override the auto-configured Roger port
        :param timeout: override the auto-configured Roger timeout
        :param show_url: print the URLs used to sys.stdout
        :param dryrun: create a dummy client
        """
        rogerconfig = RogerConfig()
        self.host = host or rogerconfig.roger_hostname
        self.port = int(port or rogerconfig.roger_port)
        self.timeout = int(timeout or rogerconfig.roger_timeout)
        self.dryrun = dryrun
        self.show_url = show_url
        self.cache = {}
        self.alarm_fields = set(["nc_alarmed", "hw_alarmed", "os_alarmed", "app_alarmed"])
        self.truth = set(["1", "true"])
        self.untruth = set(["0", "false"])

    def get_state(self, hostname):
        """
        Returns the current Roger state for a host.

        :param hostname: the hostname to query
        :return: the parsed structure from the returned JSON
        :raise AiToolsPdbError: in case the hostname is not found
        """
        host_endpoint = "roger/v1/state/%s/" % hostname
        (code, body) = self.__do_api_request("get", host_endpoint)
        if code == requests.codes.not_found:
            raise AiToolsRogerNotFoundError("Host %s not found in Roger" % hostname)
        return body

    def update_or_create_state(self, hostname, appstate=False, message=None, **kwargs):
        try:
            self.get_state(hostname)
        except AiToolsRogerNotFoundError:
            return self.create_state(hostname, appstate=appstate, message=message, **kwargs)
        else:
            return self.put_state(hostname, appstate=appstate, message=message, **kwargs)

    def _construct_alarm_data(self, data, **kwargs):
        if not isinstance(data, dict):
            raise ValueError("supplied data argument should be a dict")
        for k, v in kwargs.items():
            if not k in self.alarm_fields:
                continue
            if str(v).lower() in self.truth:
                data[k] = True
            elif str(v).lower() in self.untruth:
                data[k] = False
            else:
                raise ValueError("invalid value for '%s' ('%s'" % (k, v))
        return data

    def create_state(self, hostname, appstate=False, message=None, **kwargs):
        if self.dryrun:
            logger.info("Not creating '%s' in roger as dryrun enabled" % hostname)
            return True
        logger.info("Adding '%s' to Roger" % hostname)
        data = dict()
        data["hostname"] = hostname
        state_endpoint = "roger/v1/state/"
        if message:
            data["message"] = message
        if appstate:
            data["appstate"] = appstate
        data = self._construct_alarm_data(data, **kwargs)
        d = json.dumps(data)
        (code, body) = self.__do_api_request("post", state_endpoint, data=d)
        if code == requests.codes.not_found:
            raise AiToolsRogerNotFoundError("State endpoint '%s' not found in Roger" % state_endpoint)
        elif code == requests.codes.not_allowed:
            raise AiToolsRogerNotAllowedError("Not allowed to post '%s' to '%s'" % (hostname, state_endpoint))
        elif code == requests.codes.not_implemented:
            raise AiToolsRogerNotImplementedError("Not implemented trying to post to '%s'" % state_endpoint)
        elif code == requests.codes.internal_server_error:
            raise AiToolsRogerInternalServerError("Received 500 trying to post to '%s'" % state_endpoint)
        return body

    def delete_state(self, hostname):
        if self.dryrun:
            logger.info("Not deleting '%s' from roger as dryrun selected" % hostname)
            return True
        host_endpoint = "roger/v1/state/%s/" % hostname
        (code, body) = self.__do_api_request("delete", host_endpoint)
        if code == requests.codes.not_found:
            raise AiToolsRogerNotFoundError("Host %s not found, can't delete" % hostname)
        elif code == requests.codes.not_allowed:
            raise AiToolsRogerNotAllowedError("Not allowed to delete host '%s'" % hostname)
        elif code == requests.codes.not_implemented:
            raise AiToolsRogerNotImplementedError("Not implemented trying to delete at '%s'" % host_endpoint)
        elif code == requests.codes.internal_server_error:
            raise AiToolsRogerInternalServerError("Received a 500 trying to delete at '%s'" % host_endpoint)
        return body

    def put_state(self, hostname, appstate=False, message=None, **kwargs):
        if self.dryrun:
            logger.info("Not adding '%s' to roger as dryrun selected" % hostname)
            return True
        data = dict()
        data["hostname"] = hostname
        host_endpoint = "roger/v1/state/%s/" % hostname
        if message:
            data["message"] = message
        if appstate:
            data["appstate"] = appstate
        data = self._construct_alarm_data(data, **kwargs)
        d = json.dumps(data)
        (code, body) = self.__do_api_request("put", host_endpoint, data=d)
        if code == requests.codes.not_found:
            raise AiToolsRogerNotFoundError("Host %s not found in Roger" % hostname)
        elif code == requests.codes.not_allowed:
            raise AiToolsRogerNotAllowedError("Not allowed to put details for %s in Roger" % hostname)
        elif code == requests.codes.not_implemented:
            raise AiToolsRogerNotImplementedError("Not implemented when trying to put to %s" % host_endpoint)
        elif code == requests.codes.internal_server_error:
            raise AiToolsRogerInternalServerError("Received 500 when trying to put to %s" % host_endpoint)
        return body

    def __do_api_request(self, method, url, data=None):
        url="https://%s:%u/%s" % \
            (self.host, self.port, url)
        headers = {'Accept': 'application/json',
                   'Accept-Encoding': 'deflate'}
        if data:
            headers["Content-Type"] = "application/json"

        if self.show_url:
            print url
        try:
            code, response = super(RogerClient, self).do_request(method, url, headers, data)
            if code == requests.codes.unauthorized or code == requests.codes.forbidden:
                raise AiToolsRogerNotAllowedError("Forbidden trying '%s' at '%s'" % (method, url))
            body = response.text
            if re.match('application/json', response.headers['content-type']):
                body = response.json()
            return (code, body)
        except AiToolsHTTPClientError, error:
            raise AiToolsRogerError(error)



