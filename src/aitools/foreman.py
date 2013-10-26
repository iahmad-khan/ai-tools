#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import logging
import socket
import json
import requests
import urllib
from requests_kerberos import HTTPKerberosAuth

from aitools.errors import AiToolsForemanError
from aitools.common import CERN_CA_BUNDLE, HTTPClient

DEFAULT_FOREMAN_TIMEOUT = 15
DEFAULT_FOREMAN_HOSTNAME = "judy.cern.ch"
DEFAULT_FOREMAN_PORT = 8443

class ForemanClient(HTTPClient):
    def addhost(self, fqdn, environment, hostgroup):
        logging.info("Adding host '%s' to Foreman" % fqdn)
        payload = {'managed': False, 'name': fqdn}
        payload['environment_id'] = self.__resolve_environment_id(environment)
        payload['hostgroup_id'] = self.__resolve_hostgroup_id(hostgroup)
        logging.debug("With payload: %s" % payload)

        if not self.dryrun:
            (code, body) = self.__do_api_request("post", "hosts", data=json.dumps(payload))
            if code == requests.codes.ok:
                logging.info("Host '%s' created in Foreman" % fqdn)
            elif code == requests.codes.unprocessable_entity:
                raise AiToolsForemanError("Host '%s' not created (already in Foreman)" % fqdn)
        else:
            logging.info("Host '%s' not added because dryrun is enabled" % fqdn)

    def delhost(self, fqdn):
        logging.info("Deleting host '%s' from Foreman" % fqdn)

        if not self.dryrun:
            (code, body) = self.__do_api_request("delete", "hosts/%s" % fqdn)
            if code == requests.codes.ok:
                logging.info("Host '%s' deleted from Foreman" % fqdn)
            elif code == requests.codes.not_found:
                raise AiToolsForemanError("Host '%s' not found in Foreman" % fqdn)
        else:
            logging.info("Host '%s' not deleted because dryrun is enabled" % fqdn)

    def addhostparameter(self, fqdn, name, value):
        logging.info("Adding parameter '%s' to host '%s' with value '%s'"
                        % (name, fqdn, value))
        payload = {'parameter': {'name' : name, 'value': value}}
        logging.debug("With payload: %s" % payload)

        if not self.dryrun:
            (code, body) = self.__do_api_request("post", "hosts/%s/parameters" % fqdn,
                                data=json.dumps(payload))
            if code == requests.codes.ok:
                logging.info("Parameter '%s' created in Foreman" % name)
            elif code == requests.codes.not_found:
                raise AiToolsForemanError("Host '%s' not found in Foreman" % fqdn)
        else:
            logging.info("Parameter '%s' not added because dryrun is enabled" % name)

    def power_operation(self, fqdn, operation):
        logging.info("Executing '%s' on host '%s'" % (operation, fqdn))
        payload = {'power_action': operation}
        logging.debug("With payload: %s" % payload)

        if not self.dryrun:
            return self.__do_api_request("put", "hosts/%s/power" % fqdn,
                                data=json.dumps(payload))
        else:
            logging.info("Power operation on '%s' cancelled because dryrun is enabled" % fqdn)
            return (requests.codes.ok, {'power': 'dryrun'})

    def __resolve_environment_id(self, name):
        return self.__resolve_model_id('environment', name)

    def __resolve_hostgroup_id(self, name):
        return self.__resolve_model_id('hostgroup', name, search_key='label')

    def __resolve_model_id(self, modelname, value, results_filter=None,
                            search_key="name",
                            value_filter=None):
        cache_key = '%s_%s_id' % (modelname, value)
        if cache_key in self.cache:
            logging.debug("'%s' found in cache" % cache_key)
            return self.cache[cache_key]
        else:
            logging.debug("Asking Foreman for %s '%s'" %
                (modelname, value))
            search_string_value = value
            if value_filter is not None:
                search_string_value = value_filter(value)
            search_string = "%s=\"%s\"" % (search_key, search_string_value)
            results = self.__search_query("%ss" % modelname, search_string)
            if results_filter:
                results = results_filter(results)
            if not results:
                raise AiToolsForemanError("%s '%s' not found" %
                    (modelname, value))
            if len(results) > 1:
                raise AiToolsForemanError("Multiple choices for %s lookup" % modelname)
            self.cache[cache_key] = results[0][modelname]['id']
            return results[0][modelname]['id']

    def __search_query(self, model, search_string):
        query_string = urllib.urlencode({'search': search_string})
        url = "%s/?%s" % (model, query_string)
        (code, body) = self.__do_api_request("get", url)
        if code == requests.codes.ok:
            return body
        else:
            msg = "Foreman didn't return a controlled status code when looking up %s" \
                % model
            raise AiToolsForemanError(msg)

    def __do_api_request(self, method, url, data=None):
        url="https://%s:%u/api/%s" % \
            (self.host, self.port, url)
        logging.debug("Issuing %s on %s" % (method, url))
        headers = {'Content-type': 'application/json',
            'Accept': 'application/json, version=2',
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
                    raise AiToolsForemanError("Authentication failed (expired or non-existent TGT?)")
            elif response.status_code == requests.codes.internal_server_error:
                raise AiToolsForemanError("Foreman's ISE. Open a bug against Foreman")
        except requests.exceptions.ConnectionError, error:
            raise AiToolsForemanError("Connection error (%s)" % error)
        except requests.exceptions.Timeout, error:
            raise AiToolsForemanError("Connection timeout")

        return (response.status_code, body)
