__author__ = 'ahencz'

import requests
import logging
import re
import time
import sys
from xml.etree import ElementTree
from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsRundeckNotFoundError
from aitools.errors import AiToolsRundeckError
from aitools.errors import AiToolsRundeckNotAllowedError
from aitools.errors import AiToolsRundeckInternalServerError
from aitools.errors import AiToolsRundeckNotImplementedError
from aitools.httpclient import HTTPClient
from aitools.config import RundeckConfig
from aitools.common import deref_url

logger = logging.getLogger(__name__)



class RundeckClient(HTTPClient):

    JOB_ENDPOINT = "job/%s"
    EXECUTIONS_ENDPOINT = "job/%s/executions"
    OUTPUT_ENDPOINT = "/output/%s"

    def __init__(self, host=None, port=None, timeout=None, show_url=False, dryrun=False, deref_alias=False):
        """
        Rundeck client for interacting with the Rundeck API. Autoconfigures via the AiConfig
        object.

        :param host: override the auto-configured Authz host
        :param port: override the auto-configured Authz port
        :param timeout: override the auto-configured Authz timeout
        :param show_url: print the URLs used to sys.stdout
        :param dryrun: create a dummy client
        :param deref_alias: dereference dns load balanced aliases
        """
        rundeck = RundeckConfig()
        self.host = host or rundeck.rundeck_hostname
        self.port = int(port or rundeck.rundeck_port)
        self.timeout = int(timeout or rundeck.rundeck_timeout)
        self.dryrun = dryrun
        self.show_url = show_url
        self.deref_alias = deref_alias
        self.job_hashes = {}
        jobs = [ option for option in rundeck.parser.options('rundeck')\
            if re.match('rundeck.*job', option)]
        for job in jobs:
            self.job_hashes[job] = getattr(rundeck,job)



    def show_execution(self, execid, jobid, output=sys.stdout):
        execution_completed = False
        #first get step descriptions... a bit stupid
        (code, body) = self.__do_api_request("get",
            self.JOB_ENDPOINT % str(jobid), accept='xml')
        if code == requests.codes.not_found:
            raise AiToolsRundeckNotFoundError("Job '%s' is not found in Rundeck"%jobid)
        steps = [i.text for i in
            ElementTree.fromstring(body)[0].find('sequence').getiterator('description')]
        output_entries = []
        offset = 0
        lastmod = 0
        while not execution_completed:
            (code, body) = self.__do_api_request("post",
                self.OUTPUT_ENDPOINT % str(execid), data={'offset':offset, 'lastmod':lastmod})
            if code == requests.codes.not_found:
                raise AiToolsRundeckNotFoundError("Execution '%s' is not found in Rundeck"%str(execid))
            execution_completed = body['completed']
            offset = body['offset']
            lastmod = body.get('lastModified',0)
            output_entries = body['entries']
            for entry in output_entries:
                if entry['stepctx']:
                    output.write("%s: %s\n" % (steps[int(entry['stepctx'].split('/')[0].split('@')[0])-1], entry['log']))
                else:
                    output.write("%s\n" % entry['log'])
            output.flush()
            time.sleep(2)
        output.write('Execution finished. You can also review the output on the link given above.\n')
        output.flush()


    def run_job(self, job='test', **kwargs):
        data = None
        if kwargs:
            data = { 'argString' : ' '.join(["-%s %s"%item for item in
                kwargs.items()]) }
        (code, body) = self.__do_api_request("post",
            self.EXECUTIONS_ENDPOINT % self.job_hashes["rundeck_%s_job"%job], accept='xml', data=data )
        if code == requests.codes.not_found:
            raise AiToolsRundeckNotFoundError("The job is not found in Rundeck")
        respxml = ElementTree.fromstring(body)
        if respxml[0].tag == 'error':
            raise AiToolsRundeckError(respxml[0][0].text)
        results = respxml.find('execution').attrib
        results["jobid"] = self.job_hashes["rundeck_%s_job"%job]
        # The API on this endpoint can only return XML
        # We need to JSONify it. The returned JSON looks like:
        # '{"status": "running", "project": "DEV-AI-automation", "href": "https://rosita.cern.ch:4443/execution/follow/33864", "id": "33864", "jobid": "somehash"}'
        return results


    def __do_api_request(self, method, url, accept='json', data=None):
        url = "https://%s:%u/%s" % \
            (self.host, self.port, url)
        if self.deref_alias:
            url = deref_url(url)
        headers = {'Accept': "application/%s"%accept}

        if self.show_url:
            print url
        try:
            code, response = super(RundeckClient, self).do_request(method, url, headers, data)
            body = response.text
            if code == requests.codes.unauthorized or code == requests.codes.forbidden:
                raise AiToolsRundeckNotAllowedError("Unauthorized trying '%s' at '%s'" % (method, url))
            if code == requests.codes.not_implemented:
                raise AiToolsRundeckNotImplementedError("Server response 501 - Not Implemented")
            if code == requests.codes.internal_server_error:
                raise AiToolsRundeckInternalServerError("Server response 500 - Internal server error")
            if code == requests.codes.ok:
                if re.match('application/json', response.headers['content-type']):
                    body = response.json()
            return (code, body)
        except AiToolsHTTPClientError, error:
            raise AiToolsRundeckError(error)
