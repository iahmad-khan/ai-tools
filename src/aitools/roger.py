__author__ = 'mccance'

import re
import requests
try:
    import simplejson as json
except ImportError:
    import json

from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsRogerNotFoundError
from aitools.errors import AiToolsRogerError
from aitools.errors import AiToolsRogerNotAllowedError
from aitools.errors import AiToolsRogerInternalServerError
from aitools.errors import AiToolsRogerNotImplementedError
from aitools.httpclient import HTTPClient
from aitools.config import RogerConfig


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

    def get_state(self, hostname):
        """
        Returns the current Roger state for a host.

        :param hostname: the hostname to query
        :return: the parsed structure from the returned JSON
        :raise AiToolsPdbError: in case the hostname is not found
        """
        host_endpoint = "/roger/v1/state/%s/" % hostname
        (code, body) = self.__do_api_request("get", host_endpoint)
        if code == requests.codes.not_found:
            raise AiToolsRogerNotFoundError("Host %s not found in Roger" % hostname)
        return body

    def put_state(self, hostname, appstate=False, message=None, **kwargs):
        alarms = set(["nc_alarmed", "hw_alarmed", "os_alarmed", "app_alarmed"])
        truth = set(["1", "true"])
        untruth = set(["0", "false"])
        data = dict()
        data["hostname"] = hostname
        host_endpoint = "/roger/v1/state/%s/" % hostname
        if message:
            data["message"] = message
        for n, alarm in kwargs.items():
            if not n in alarms:
                continue
            if str(alarm).lower() in truth:
                data[n] = True
            elif str(alarm).lower() in untruth:
                data[n] = False
            else:
                raise ValueError("invalid value for '%s' ('%s')" % (n, alarm))
        if appstate:
            data["appstate"] = appstate
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
            body = response.text
            if re.match('application/json', response.headers['content-type']):
                body = response.json()
            return (code, body)
        except AiToolsHTTPClientError, error:
            raise AiToolsRogerError(error)



