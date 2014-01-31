#!/usr/bin/env python
#  Nacho Barrientos <nacho.barrientos@cern.ch>

import logging
import json
import urllib

import re

import requests

from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsForemanError
from aitools.httpclient import HTTPClient
from aitools.config import ForemanConfig

class ForemanClient(HTTPClient):

    def __init__(self, host=None, port=None, timeout=None, dryrun=False):
        fmconfig = ForemanConfig()
        self.host = host or fmconfig.foreman_hostname
        self.port = int(port or fmconfig.foreman_port)
        self.timeout = int(timeout or fmconfig.foreman_timeout)
        self.dryrun = dryrun
        self.cache = {}

    def addhost(self, fqdn, environment, hostgroup, owner):
        logging.info("Adding host '%s' to Foreman..." % fqdn)
        payload = {'managed': False, 'name': fqdn}
        payload['environment_id'] = self.__resolve_environment_id(environment)
        payload['hostgroup_id'] = self.__resolve_hostgroup_id(hostgroup)
        payload['owner_type'] = "User"
        payload['owner_id'] = self.__resolve_user_id(owner)
        logging.debug("With payload: %s" % payload)

        if not self.dryrun:
            (code, body) = self.__do_api_request("post", "hosts", data=json.dumps(payload))
            if code == requests.codes.ok:
                logging.info("Host '%s' created in Foreman" % fqdn)
            elif code == requests.codes.unprocessable_entity:
                error = ','.join(body['host']['full_messages'])
                raise AiToolsForemanError("addhost call failed (%s)" % error)
        else:
            logging.info("Host '%s' not added because dryrun is enabled" % fqdn)

    def gethost(self, fqdn):
        logging.info("Getting host '%s' from Foreman..." % fqdn)

        (code, body) = self.__do_api_request("get", "hosts/%s" % fqdn)
        if code == requests.codes.ok:
            body['host']['hostgroup'] = self.__resolve_model('hostgroup',
                body['host']['hostgroup_id'])
            return body
        elif code == requests.codes.not_found:
            raise AiToolsForemanError("Host '%s' not found in Foreman" % fqdn)
        elif code == requests.codes.unprocessable_entity:
            error = ','.join(body['host']['full_messages'])
            raise AiToolsForemanError("gethost call failed (%s)" % error)

    def getfacts(self, fqdn):
        logging.info("Getting facts for host '%s' from Foreman..." % fqdn)

        (code, body) = self.__do_api_request("get", "hosts/%s/facts/?per_page=500" % fqdn)
        if code == requests.codes.ok:
            return body
        elif code == requests.codes.not_found:
            raise AiToolsForemanError("Host '%s' (or facts) not found in Foreman" % fqdn)
        elif code == requests.codes.unprocessable_entity:
            error = ','.join(body[fqdn]['full_messages'])
            raise AiToolsForemanError("getfacts call failed (%s)" % error)

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
        logging.info("Adding parameter '%s' to host '%s' with value '%s'..."
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

    def get_environment_by_name(self, name):
        return self.__get_model_by_name('environment', name)

    def __get_model_by_name(self, model, name):
        logging.debug("Requesting %s '%s' from Foreman" % (model, name))

        (code, body) = self.__do_api_request("get", "%ss/%s" % (model, name))
        if code == requests.codes.ok:
            logging.debug("Found: %s" % body)
            return body[model]
        elif code == requests.codes.not_found:
            raise AiToolsForemanError("%s '%s' not found in Foreman" % \
                    (model, name))

    def __resolve_environment_id(self, name):
        return self.__resolve_model_id('environment', name)

    def __resolve_hostgroup_id(self, name):
        return self.__resolve_model_id('hostgroup', name, search_key='label')

    def __resolve_user_id(self, name):
        return self.__resolve_model_id('user', name, search_key='login')

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
            results = self.search_query("%ss" % modelname, search_string)
            if results_filter:
                results = results_filter(results)
            if not results:
                raise AiToolsForemanError("%s '%s' not found" %
                    (modelname, value))
            if len(results) > 1:
                raise AiToolsForemanError("Multiple choices for %s lookup" % modelname)
            self.cache[cache_key] = results[0][modelname]['id']
            return results[0][modelname]['id']

    def __resolve_model(self, modelname, id):
        cache_key = '%s_%s' % (modelname, id)
        if cache_key in self.cache:
            logging.debug("'%s' found in cache" % cache_key)
            return self.cache[cache_key]
        else:
            logging.debug("Asking Foreman for %s with id '%s'" %
                (modelname, id))
            (code, body) = self.__do_api_request("get", "%ss/%s" % (modelname, id))
            if code == requests.codes.ok:
                self.cache[cache_key] = body
                return body
            elif code == requests.codes.not_found:
                raise AiToolsForemanError("Model not found in Foreman)" % modelname)
            elif code == requests.codes.unprocessable_entity:
                error = ','.join(body['host']['full_messages'])
                raise AiToolsForemanError("__resolve_model_name call failed (%s)" % error)

    def search_query(self, model, search_string):
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
        # Yes, Foreman is stupid
        headers = {'User-Agent': 'ai-tools',
            'Content-type': 'application/json',
            'Accept': 'application/json, version=2'}

        try:
            code, response = super(ForemanClient, self).do_request(method, url, headers, data)
            body = response.text
            if re.match('application/json', response.headers['content-type']):
                body = response.json()
            return (code, body)
        except AiToolsHTTPClientError, error:
            raise AiToolsForemanError(error)


