#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import logging
import socket
import json
import requests
import urllib
from requests_kerberos import HTTPKerberosAuth

from aitools.errors import AiToolsCertmgrError
from aitools.common import CERN_CA_BUNDLE, HTTPClient

class CertmgrClient(HTTPClient):
    def stage(self, fqdn):
        logging.info("Staging host '%s' on certmgr (%s)" % 
            (fqdn, self.host))
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
        logging.debug("Issuing %s on %s" % (method, url))
        headers = {'Content-type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'ai-tools'}
        logging.debug("With headers: %s" % headers)

        try:
            caller = getattr(requests, method)
            response = caller(url, timeout=self.timeout,
                headers=headers, auth=HTTPKerberosAuth(),
                verify=CERN_CA_BUNDLE, allow_redirects=True,
                data=data)
            logging.debug("Returned %s", response.status_code)
            body = response.text
            if response.status_code == requests.codes.ok:
                try:
                    body = response.json()
                except:
                    pass #FIMXE
                logging.debug("Done")
            elif response.status_code == requests.codes.forbidden or \
                response.status_code == requests.codes.unauthorized:
                    raise AiToolsCertmgrError("Authentication failed (expired or non-existent TGT?)")
            elif response.status_code == requests.codes.internal_server_error:
                raise AiToolsCertmgrError("Certmgr's ISE. Open a bug against Certmgr")
        except requests.exceptions.ConnectionError, error:
            raise AiToolsCertmgrError("Connection error (%s)" % error)
        except requests.exceptions.Timeout, error:
            raise AiToolsCertmgrError("Connection timeout")

        return (response.status_code, body)
