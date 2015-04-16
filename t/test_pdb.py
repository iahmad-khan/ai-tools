import unittest
from mock import Mock, patch
from aitools.pdb import PdbClient
from aitools.errors import AiToolsPdbError, AiToolsPdbNotFoundError


class TestPdbClient(unittest.TestCase):

    def setUp(self):
        self.pdb = PdbClient(host='fakepdb', port=1, timeout=100)
        self.hostname = 'fakehostname1'
        self.fact = 'fakefact1'

    # PdbClient.get_facts
    @patch.object(PdbClient, '_PdbClient__do_api_request', side_effect=AiToolsPdbError)
    def test_get_facts_do_api_request_error(self, mock_pdb_request):
        self.assertRaises(AiToolsPdbError, self.pdb.get_facts, self.hostname)
        mock_pdb_request.assert_called_once()

    @patch.object(PdbClient, '_PdbClient__do_api_request', return_value=(200, []))
    def test_get_facts_machine_not_in_pdb(self, mock_pdb_request):
        self.assertRaises(AiToolsPdbNotFoundError, self.pdb.get_facts, self.hostname)
        mock_pdb_request.assert_called_once()

    @patch.object(PdbClient, '_PdbClient__do_api_request', return_value=(200, []))
    def test_get_facts_machine_doesnt_have_fact(self, mock_pdb_request):
        self.assertRaises(AiToolsPdbNotFoundError, self.pdb.get_facts, self.hostname, self.fact)
        mock_pdb_request.assert_called_once()

    @patch.object(PdbClient, '_PdbClient__do_api_request')
    def test_get_facts_happy_path(self, mock_pdb_request):
        returned_body = [{
                          u'certname': self.hostname,
                          u'name': u'fact1',
                          u'value': u'value1'
                         },
                         {
                          u'certname': self.hostname,
                          u'name': u'fact2',
                          u'value': u'value2'
                         },
                         {
                          u'certname': self.hostname,
                          u'name': u'fact3',
                          u'value': u'value3'
                          }]
        mock_pdb_request.return_value = (200, returned_body)
        assert self.pdb.get_facts(self.hostname) == {'fact1':'value1',
                                                     'fact2':'value2',
                                                     'fact3':'value3'}
        mock_pdb_request.assert_called_once()

    @patch.object(PdbClient, '_PdbClient__do_api_request')
    def test_get_facts_single_fact_happy_path(self, mock_pdb_request):
        returned_body = [{
                          u'certname': self.hostname,
                          u'name': u'fact1',
                          u'value': u'value1'
                         }]
        mock_pdb_request.return_value = (200, returned_body)
        assert self.pdb.get_facts(self.hostname, self.fact) == {'fact1':'value1'}
        mock_pdb_request.assert_called_once()
