#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import logging
import socket
import json
import requests

from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsCertmgrError
from aitools.httpclient import HTTPClient
from aitools.config import CertmgrConfig
from distutils.util import strtobool
from aitools.common import deref_url


class CertmgrClient(HTTPClient):

    def __init__(self, host=None, port=None, timeout=None, dryrun=False, deref_alias=False):
        """
        Basic client to communicate with the Certificate Manager service. Autoconfigures via the
        AiConfig class.

        :param host: override the auto-configured cert manager host
        :param port: override the auto-configured cert manager port
        :param timeout: override the auto-configured cert manager timeout
        :param dryrun: make a dummy client
        :param deref_alias: dereference load balanced aliases
        """
        certmgrconf = CertmgrConfig()
        self.host = host or certmgrconf.certmgr_hostname
        self.port = int(port or certmgrconf.certmgr_port)
        self.timeout = int(timeout or certmgrconf.certmgr_timeout)
        self.dryrun = dryrun
        self.deref_alias = deref_alias
        self.cache = {}

    def stage(self, fqdn):
        """
        Stage the specified host in the Certificate Manager service.

        :param fqdn: the host to stage
        :raise AiToolsCertmgrError: if the staging action cannot be accomplished
        """
        logging.info("Staging host '%s' on Certmgr..." % fqdn)
        payload = {'hostname': fqdn}
        logging.debug("With payload: %s" % payload)

        if not self.dryrun:
            (code, body) = self.__do_api_request("post", "krb/certmgr/staged/", \
                data=json.dumps(payload))
            if code == requests.codes.created:
                logging.info("Host '%s' staged" % fqdn)
            elif code == requests.codes.unauthorized or code == requests.codes.forbidden:
                logging.info("Not authorized to stage host '%s'" % fqdn)
        else:
            logging.info("Host '%s' not staged because dryrun is enabled" % fqdn)

    def __do_api_request(self, method, url, data=None):
        url="https://%s:%u/%s" % \
            (self.host, self.port, url)
        if self.deref_alias:
            url = deref_url(url)
        headers = {'User-Agent': 'ai-tools'}
        if method in ('post', 'put'):
            headers['Content-type'] = 'application/json'
        else:
            headers['Accept'] = 'application/json'

        try:
            code, response = super(CertmgrClient, self).do_request(method, url, headers, data)
            return (code, response.text)
        except AiToolsHTTPClientError, error:
            raise AiToolsCertmgrError(error)
