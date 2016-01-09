import unittest
from unittest.mock import patch, Mock
from asynctest import CoroutineMock
from PyQt5.QtCore import QLocale
from sakia.core.registry.identities import IdentitiesRegistry
from sakia.core import Account
from sakia.tests import QuamashTest
from sakia.tests.mocks.bma import nice_blockchain
from ucoinpy.api import bma

class TestAccount(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))
        self.identities_registry = IdentitiesRegistry()

    def tearDown(self):
        self.tearDownQuamash()

    def test_load_save_account(self):
        account = Account("test_salt", "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                          "test_uid", [], [], [], self.identities_registry)
        json_data = account.jsonify()
        account_from_json = Account.load(json_data, self.identities_registry)

        self.assertEqual(account.name, account_from_json.name)
        self.assertEqual(account.pubkey, account_from_json.pubkey)
        self.assertEqual(len(account.communities), len(account_from_json.communities))
        self.assertEqual(len(account.wallets), len(account.wallets))

    @patch('sakia.core.Application')
    @patch('sakia.core.Community')
    @patch('sakia.core.net.api.bma.access.BmaAccess')
    def test_check_register_success(self, app, community, bma_access):
        account = Account("test_salt", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                          "john", [], [], [], self.identities_registry)

        def mock_simple_request(request, req_args, get_args={}):
            if request is bma.wot.Lookup:
                if req_args['search'] == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ":
                    return nice_blockchain.bma_lookup_john
                elif req_args['search'] == "john":
                    return nice_blockchain.bma_lookup_john
            elif request is bma.wot.CertifiersOf:
                if req_args['search'] == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ":
                    return nice_blockchain.bma_certifiers_of_john
                elif req_args['search'] == "john":
                    return nice_blockchain.bma_certifiers_of_john
        community.bma_access = bma_access
        bma_access.simple_request = CoroutineMock(side_effect=mock_simple_request)

        async def exec_test():
            result = await account.check_registered(community)
            self.assertEqual(result, (True, "john",
                                      "john"))

        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Application')
    @patch('sakia.core.Community')
    @patch('sakia.core.net.api.bma.access.BmaAccess')
    def test_check_register_pubkey_failure(self, app, community, bma_access):
        account = Account("test_salt", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                          "john", [], [], [], self.identities_registry)

        def mock_simple_request(request, req_args, get_args={}):
            if request is bma.wot.Lookup:
                if req_args['search'] == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ":
                    raise ValueError('404 not found')
                elif req_args['search'] == "john":
                    result = nice_blockchain.bma_lookup_john
                    result['pubkey'] = "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
                    return result
            elif request is bma.wot.CertifiersOf:
                if req_args['search'] == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ":
                    raise ValueError('404 not found')
                elif req_args['search'] == "john":
                    result = nice_blockchain.bma_certifiers_of_john
                    result['pubkey'] = "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"
                    return result
        community.bma_access = bma_access
        bma_access.simple_request = CoroutineMock(side_effect=mock_simple_request)

        async def exec_test():
            result = await account.check_registered(community)
            self.assertEqual(result, (False, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                      "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn"))

        self.lp.run_until_complete(exec_test())

    @patch('sakia.core.Application')
    @patch('sakia.core.Community')
    @patch('sakia.core.net.api.bma.access.BmaAccess')
    def test_check_register_uid_failure(self, app, community, bma_access):
        account = Account("test_salt", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                          "john", [], [], [], self.identities_registry)

        def mock_simple_request(request, req_args, get_args={}):
            if request is bma.wot.Lookup:
                if req_args['search'] == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ":
                    result = nice_blockchain.bma_lookup_john
                    result['uid'] = "imnotjohn"
                    return result
                elif req_args['search'] == "john":
                    raise ValueError('404 not found')
            elif request is bma.wot.CertifiersOf:
                if req_args['search'] == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ":
                    result = nice_blockchain.bma_certifiers_of_john
                    result['uid'] = "imnotjohn"
                    return result
                elif req_args['search'] == "john":
                    raise ValueError('404 not found')
        community.bma_access = bma_access
        bma_access.simple_request = CoroutineMock(side_effect=mock_simple_request)

        async def exec_test():
            result = await account.check_registered(community)
            self.assertEqual(result, (False, "john",
                                      "imnotjohn"))

        self.lp.run_until_complete(exec_test())