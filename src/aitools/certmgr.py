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

class CertmgrClient(HTTPClient):

    def __init__(self, host=None, port=None, timeout=None, dryrun=False):
        certmgrconf = CertmgrConfig()
        self.host = host or certmgrconf.certmgr_hostname
        self.port = int(port or certmgrconf.certmgr_port)
        self.timeout = int(timeout or certmgrconf.certmgr_timeout)
        self.dryrun = dryrun
        self.cache = {}

    def stage(self, fqdn):
        logging.info("Staging host '%s' on Certmgr..." % fqdn)
        payload = {'hostname': fqdn}
        logging.debug("With payload: %s" % payload)

        if not self.dryrun:
            (code, body) = self.__do_api_request("post", "krb/certmgr/staged/", \
                data=json.dumps(payload))
            if code == requests.codes.created:
                logging.info("Host '%s' staged" % fqdn)
        else:
            logging.info("Host '%s' not staged because dryrun is enabled" % fqdn)

    def __do_api_request(self, method, url, data=None):
        url="https://%s:%u/%s" % \
            (self.host, self.port, url)
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
