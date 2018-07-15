import unittest

from request_network.api import (
    RequestNetwork,
)
from request_network.exceptions import (
    RequestNotFound,
    TransactionNotFound,
)
from request_network.utils import (
    hash_request_object,
)


class GetRequestTestCase(unittest.TestCase):
    """ Retrieve Requests that were created by running the RequestNetwork.js
        test suite.

        This test case assumes it is running against a private Ethereum network
        on which the Request Network smart contracts have been deployed and tested.
    """

    def setUp(self):
        super().setUp()
        self.request_api = RequestNetwork()

    def test_hash_request_object(self):
        request = self.request_api.get_request_by_transaction_hash(
            '0x1f97459c45402fcb6562410cf4b4253a9d5d9528f247a892f9bddeefdd878b2d')
        # Manually add the expiration date as it is not stored on the contract
        request.expiration_date = 7952342400000
        hash_request_object(request)

    def test_get_request_by_id(self):
        request = self.request_api.get_request_by_id(
            '0x8cdaf0cd259887258bc13a92c0a6da92698644c0000000000000000000000050')
        self.assertEqual(
            '0xC5fdf4076b8F3A5357c5E395ab970B5B54098Fef',
            request.payer
        )
        self.assertEqual(
            100000000,
            request.payments[0].delta_amount
        )

    def test_get_request_by_transaction_hash(self):
        request = self.request_api.get_request_by_transaction_hash(
            '0x8d3ec9ef287f09577707bd8ffe7f053394d4cb5355f62495886dbd4a5589971b')
        self.assertEqual(
            '0x0F4F2Ac550A1b4e2280d04c21cEa7EBD822934b5',
            request.payer
        )
        self.assertIn('reason', request.data)

    def test_get_nonexistent_request_by_id(self):
        with self.assertRaises(RequestNotFound):
            self.request_api.get_request_by_id(
                '0x8cdaf0cd259887258bc13a92c0a6da92698644c0000000000000000000000000')

    def test_get_nonexistent_request_by_transaction_hash(self):
        with self.assertRaises(TransactionNotFound):
            self.request_api.get_request_by_transaction_hash(
                '0x8d3ec9ef287f09577707bd8ffe7f053394d4cb5355f62495886dbd4a55800000')


if __name__ == '__main__':
    unittest.main()
