__author__ = 'mccance'

import yaml
import requests
import logging

from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsEncError
from aitools.httpclient import HTTPClient
from aitools.config import EncConfig

class EncClient(HTTPClient):

    def __init__(self, host=None, port=None, timeout=None, dryrun=False):
        """
        ENC client for interacting with the ENC service. Autoconfigures via the AiConfig
        object.

        :param host: override the auto-configured ENC host
        :param port: override the auto-configured ENC port
        :param timeout: override the auto-configured ENC timeout
        :param dryrun: create a dummy client
        """
        encconf = EncConfig()
        self.host = host or encconf.enc_hostname
        self.port = int(port or encconf.enc_port)
        self.timeout = int(timeout or encconf.enc_timeout)
        self.dryrun = dryrun
        self.cache = {}

    def get_node_enc(self, hostname):
        """
        Return the specified node's ENC data.

        :param hostname: the node to query
        :return: the parsed YAML of the node's ENC
        """
        logging.info("Getting host '%s' from the ENC..." % hostname)
        return self.__do_api_request("get", "node/%s?format=yml" % (hostname,))

    def __do_api_request(self, method, url, data=None):
        url="https://%s:%u/%s" % \
            (self.host, self.port, url)
        headers = {'Accept': 'application/yaml'}

        try:
            code, response = super(EncClient, self).do_request(method, url, headers, data)
            if code == requests.codes.not_found:
                raise AiToolsEncError("Could not find node in ENC")
            elif code == requests.codes.unauthorized or code == requests.codes.forbidden:
                raise AiToolsEncError("Unauthorized when contacting ENC")
            body = response.text
            yam = yaml.load(body)
            return (code, yam)
        except AiToolsHTTPClientError, error:
            raise AiToolsEncError(error)
