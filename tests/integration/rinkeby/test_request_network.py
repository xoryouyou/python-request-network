import unittest

from web3.auto import (
    w3,
)
from web3.middleware import geth_poa_middleware

from request_network.api import (
    RequestNetwork,
)
from request_network.types import (
    Payee,
)

# Insert POA middleware
w3.middleware_stack.inject(geth_poa_middleware, layer=0)

# TODO find better place to store these
test_token_address = '0x345ca3e014aaf5dca488057592ee47305d9b3e10'
test_account = '0x627306090abab3a6e1400e9345bc60c78a8bef57'
test_amounts = [
    100000000,
    20000000,
    3000000
]

payees = [
    Payee(
        id_address="0x821aea9a577a9b44299b9c15c88cf3087f3b5544",
        payment_address="0x6330a553fc93768f612722bb8c2ec78ac90b3bbc",
        amount=test_amounts[0],
        payment_amount=test_amounts[0]
    ),
    Payee(
        id_address="0x0d1d4e623d10f9fba5db95830f7d3839406c6af2",
        payment_address=None,
        amount=test_amounts[1],
        payment_amount=test_amounts[1]
    ),
    Payee(
        id_address="0x2932b7a2355d6fecc4b5c0b6bd44cc31df247a2e",
        payment_address="0x5aeda56215b167893e80b4fe645ba6d5bab767de",
        amount=test_amounts[2],
        payment_amount=test_amounts[2]
    )
]

expiration_date = 7952342400000


class GetRequestTestCase(unittest.TestCase):
    """ Ensure we can retrieve existing Requests on Rinkeby
    """

    def setUp(self):
        super().setUp()
        self.request_api = RequestNetwork()

    def test_get_request_by_id(self):
        request = self.request_api.get_request_by_id(
            '0x8fc2e7f2498f1d06461ee2d547002611b801202b0000000000000000000003e4')
        self.assertEqual(
            '0x627306090abaB3A6e1400e9345bC60c78a8BEf57',
            request.payer
        )
        self.assertEqual(
            100000000000000,
            request.payments[0].delta_amount
        )

    def test_get_request_by_transaction_hash(self):
        request = self.request_api.get_request_by_transaction_hash(
            '0xf9d484e56c038055e78344c9fa082e4bae640c7fde5d5063e6c394be20ceebd0')
        self.assertEqual(
            '0x627306090abaB3A6e1400e9345bC60c78a8BEf57',
            request.payer
        )


if __name__ == '__main__':
    unittest.main()
