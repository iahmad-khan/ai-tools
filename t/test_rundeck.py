__author__ = "ahencz"

import os
import sys
sys.path.insert(0, os.path.abspath("../src"))
import unittest
from mock import Mock, patch
import requests
import json
from aitools.httpclient import HTTPClient
from argparse import ArgumentParser
from aitools.config import RundeckConfig
from aitools.rundeck import RundeckClient
from aitools.errors import AiToolsHTTPClientError
from aitools.errors import AiToolsRundeckError
from aitools.errors import AiToolsRundeckNotAllowedError
from aitools.errors import AiToolsRundeckNotFoundError
from aitools.errors import AiToolsRundeckInternalServerError
from aitools.errors import AiToolsRundeckNotImplementedError

# Test cases were based on Tbag tests

class TestRundeck(unittest.TestCase):

    # ugly global variable to be used by the decorators
    test_job_hash = "e4778de3-eed2-479c-ba5e-cc8d198e62db"
    test_job_execution = "34587"

    my_test_json_response = '{"valid": "json"}'

    already_running_xml = """<result error='true' apiversion='13'>
          <error code='api.error.execution.conflict'>
            <message>Execution had a conflict: Job "API test" [e4778de3-eed2-479c-ba5e-cc8d198e62db] is currently being executed (execution [[34570]])</message>
          </error>
        </result>"""

    job_spec_xml = """<joblist>
          <job>
            <id>e4778de3-eed2-479c-ba5e-cc8d198e62db</id>
            <loglevel>INFO</loglevel>
            <sequence keepgoing='false' strategy='node-first'>
              <command>
                <exec>echo Hello World with $RD_OPTION_MYARG! - says $RD_JOB_USERNAME</exec>
                <description>Test</description>
              </command>
              <command>
                <exec>echo Step 2 part 1 &amp;&amp; sleep 15 &amp;&amp; echo Step 2 part 2</exec>
                <description>Long step 1</description>
              </command>
              <command>
                <exec>echo Step 3 part 1 &amp;&amp; sleep 15 &amp;&amp; echo Step 3 part 2</exec>
                <description>Long step 2</description>
              </command>
            </sequence>
            <description>Dummy job to test the API   </description>
            <name>API test</name>
            <context>
              <project>DEV-AI-automation</project>
              <options>
                <option name='myArg' value='DefaultValue' required='true'>
                  <description>To test option pasing via the API</description>
                </option>
              </options>
            </context>
            <uuid>e4778de3-eed2-479c-ba5e-cc8d198e62db</uuid>
          </job>
        </joblist>"""

    successful_execution_xml = """<executions count='1'>
          <execution id='34576' href='https://rosita.cern.ch:4443/execution/follow/34576' status='running' project='DEV-AI-automation'>
            <user>ahencz</user>
            <date-started unixtime='1433168747914'>2015-06-01T14:25:47Z</date-started>
            <job id='e4778de3-eed2-479c-ba5e-cc8d198e62db' averageDuration='29698'>
              <name>API test</name>
              <group></group>
              <project>DEV-AI-automation</project>
              <description>Dummy job to test the API   </description>
              <options>
                <option name='myArg' value='myValue' />
              </options>
            </job>
            <description>echo Hello World with $RD_OPTION_MYARG! - says $RD_JOB_USERNAME ('Test') [... 3 steps]</description>
            <argstring>-myArg myValue</argstring>
            <serverUUID>58384454-544e-0025-901a-0025901ad644</serverUUID>
          </execution>
        </executions>"""

    execution_output_json = [
        '{"id":"34878","offset":"749","completed":false,"execCompleted":false,"hasFailedNodes":false,"execState":"running","lastModified":"1433254176000","execDuration":10959,"percentLoaded":100.0,"totalSize":749,"entries":[{"time":"16:09:36","absolute_time":"2015-06-02T14:09:36Z","log":"Hello World with myvalue! - says ahencz","level":"NORMAL","user":"rundeck","command":null,"stepctx":"1","node":"rosita.cern.ch"},{"time":"16:09:36","absolute_time":"2015-06-02T14:09:36Z","log":"Step 2 part 1","level":"NORMAL","user":"rundeck","command":null,"stepctx":"2@rosita/1","node":"rosita.cern.ch"}]}',
        '{"id":"34878","offset":"1273","completed":false,"execCompleted":false,"hasFailedNodes":false,"execState":"running","lastModified":"1433254192000","execDuration":26157,"percentLoaded":100.0,"totalSize":1273,"entries":[{"time":"16:09:51","absolute_time":"2015-06-02T14:09:51Z","log":"Step 2 part 2","level":"NORMAL","user":"rundeck","command":null,"stepctx":"2@rosita/1","node":"rosita.cern.ch"},{"time":"16:09:52","absolute_time":"2015-06-02T14:09:52Z","log":"Step 3 part 1","level":"NORMAL","user":"rundeck","command":null,"stepctx":"3@rosita/1","node":"rosita.cern.ch"}]}',
        '{"id":"34878","offset":"1533","completed":true,"execCompleted":true,"hasFailedNodes":false,"execState":"succeeded","lastModified":"1433254207000","execDuration":32000,"percentLoaded":99.61013645224172,"totalSize":1539,"entries":[{"time":"16:10:07","absolute_time":"2015-06-02T14:10:07Z","log":"Step 3 part 2","level":"NORMAL","user":"rundeck","command":null,"stepctx":"3","node":"rosita.cern.ch"}]}'
    ]

    def setUp(self):
        self.rundeck_config = RundeckConfig(configfile=os.path.abspath("ai.conf"))
        parser = ArgumentParser()
        self.rundeck_config.add_standard_args(parser)
        (pargs, _) = self.rundeck_config.parser.parse_known_args()
        self.rundeck_config.read_config_and_override_with_pargs(pargs)

        # self.test_entities = { "hostgroup": "punch/puppetdb", "hostname": "ahencz-dev" }
        # self.test_user = 'ahencz'
        self.rundeck_config.read_config_and_override_with_pargs(pargs)
        self.client = RundeckClient()

# Regular unit tests for the one single function the lib
#
    # __do_api_request

    @patch.object(HTTPClient, 'do_request', return_value=(requests.codes.OK, Mock(text=my_test_json_response,
        headers={'content-type':'application-json'},
        json=Mock(return_value=json.loads(my_test_json_response)))))
    def test_api_request_OK(self, mock_response):
        result = self.client._RundeckClient__do_api_request('get','someurl', 'xml')
        self.assertTrue(isinstance(result,tuple))
        self.assertEqual(200, result[0])
        # from nose.tools import set_trace; set_trace()config
        HTTPClient.do_request.assert_called_once_with('get',
            "https://%s:%s/someurl"%(self.rundeck_config.rundeck_hostname, self.rundeck_config.rundeck_port),
            {'Accept': "application/xml"}, None)
        self.assertEqual(mock_response()[1].text, result[1])

    @patch.object(HTTPClient, 'do_request', return_value=(requests.codes.forbidden, Mock(text=my_test_json_response,
        headers={'content-type':'application-json'},
        json=Mock(return_value=json.loads(my_test_json_response)))))
    def test_api_request_forbidden(self, mock_response):
        self.assertRaises(AiToolsRundeckNotAllowedError, self.client._RundeckClient__do_api_request, 'get', 'someurl')

    @patch.object(HTTPClient, 'do_request', return_value=(requests.codes.unauthorized, Mock(text=my_test_json_response,
        headers={'content-type':'application-json'},
        json=Mock(return_value=json.loads(my_test_json_response)))))
    def test_api_request_unauthorized(self, mock_response):
        self.assertRaises(AiToolsRundeckNotAllowedError, self.client._RundeckClient__do_api_request, 'get', 'someurl')

    @patch.object(HTTPClient, 'do_request', side_effect=AiToolsHTTPClientError)
    def test_api_request_clienterror(self, mock_response):
        self.assertRaises(AiToolsRundeckError, self.client._RundeckClient__do_api_request, 'get', 'someurl')

    @patch.object(HTTPClient, 'do_request', return_value=(requests.codes.not_implemented, Mock(text=my_test_json_response,
        headers={'content-type':'application-json'},
        json=Mock(return_value=json.loads(my_test_json_response)))))
    def test_api_request_notimplemented(self, mock_response):
        self.assertRaises(AiToolsRundeckNotImplementedError, self.client._RundeckClient__do_api_request, 'get', 'someurl')

    @patch.object(HTTPClient, 'do_request', return_value=(requests.codes.internal_server_error, Mock(text=my_test_json_response,
        headers={'content-type':'application-json'},
        json=Mock(return_value=json.loads(my_test_json_response)))))
    def test_api_request_itnernalserverrror(self, mock_response):
        self.assertRaises(AiToolsRundeckInternalServerError, self.client._RundeckClient__do_api_request, 'get', 'someurl')

    # run_job
    @patch.object(RundeckClient, '_RundeckClient__do_api_request', return_value=(requests.codes.OK, successful_execution_xml))
    def test_run_job_ok(self, mock_response):
        response = self.client.run_job(somearg="someval")
        # it makes a call using POST, accepting XML, and using the data
        RundeckClient._RundeckClient__do_api_request.assert_called_once_with('post',
            RundeckClient.EXECUTIONS_ENDPOINT%self.test_job_hash,
            accept='xml', data={'argString':'-somearg someval'})

        # and it parses the respone xml into a json
        self.assertEqual(response,
            {"status": "running",
            "project": "DEV-AI-automation",
            "href": "https://rosita.cern.ch:4443/execution/follow/34576",
            "id": "34576",
            "jobid": self.test_job_hash})

    @patch.object(RundeckClient, '_RundeckClient__do_api_request', return_value=(requests.codes.conflict, already_running_xml))
    def test_run_job_already_running_conflict(self, mock_response):
        self.assertRaises(AiToolsRundeckError, self.client.run_job, somearg="someval")

    @patch.object(RundeckClient, '_RundeckClient__do_api_request', return_value=(requests.codes.not_found, ""))
    def test_run_job_job_not_found(self, mock_response):
        self.assertRaises(AiToolsRundeckNotFoundError, self.client.run_job, somearg="someval")

    # show_execution

    # helper function to mock muliple subsequent API calls
    def show_execution_sideeffect(*args, **kwargs):
        # from nose.tools import set_trace; set_trace()
        if args[0]=='get':
            # we are querying for job details
            return (requests.codes.OK, TestRundeck.job_spec_xml)
        # otherwise we poll for the job output
        return  (requests.codes.OK, json.loads(TestRundeck.execution_output_json.pop(0)))

    def show_execution_sideeffect_job_not_found(*args, **kwargs):
        if args[0]=='get':
            # we are querying for job details
            return (requests.codes.not_found, TestRundeck.job_spec_xml)
        # otherwise we poll for the job output
        return  (requests.codes.OK, "")

    def show_execution_sideeffect_execution_not_found(*args, **kwargs):
        if args[0]=='get':
            # we are querying for job details
            return (requests.codes.OK, TestRundeck.job_spec_xml)
        # otherwise we poll for the job output
        return  (requests.codes.not_found, "")

    @patch.object(RundeckClient, '_RundeckClient__do_api_request', side_effect=show_execution_sideeffect)
    def test_show_execution_ok(self, mock_response):
        response = self.client.show_execution(self.test_job_execution, self.test_job_hash)
        # it makes 4 API calls (with the provided data)
        self.assertEqual(RundeckClient._RundeckClient__do_api_request.call_count, 4)
        expected_calls = [ (('get', 'job/e4778de3-eed2-479c-ba5e-cc8d198e62db'), {'accept': 'xml'}),
            (('post', '/output/34587'), {'data': {'lastmod': 0, 'offset': 0}}),
            (('post', '/output/34587'), {'data': {'lastmod': u'1433254176000', 'offset': u'749'}}),
            (('post', '/output/34587'), {'data': {'lastmod': u'1433254192000', 'offset': u'1273'}}) ]
        self.assertEqual(RundeckClient._RundeckClient__do_api_request.call_args_list, expected_calls)

    @patch.object(RundeckClient, '_RundeckClient__do_api_request', side_effect=show_execution_sideeffect_job_not_found)
    def test_show_execution_job_not_found(self, mock_response):
        self.assertRaises(AiToolsRundeckNotFoundError, self.client.show_execution, self.test_job_execution, self.test_job_hash)

    @patch.object(RundeckClient, '_RundeckClient__do_api_request', side_effect=show_execution_sideeffect_execution_not_found)
    def test_show_execution_execution_not_found(self, mock_response):
        self.assertRaises(AiToolsRundeckNotFoundError, self.client.show_execution, self.test_job_execution, self.test_job_hash)
