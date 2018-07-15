import unittest

from request_network.api import (
    RequestNetwork,
)
from request_network.currencies import (
    currencies_by_symbol,
)
from request_network.types import (
    Payee,
    Payer,
    Roles,
)

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


payees_for_broadcast = [
    Payee(
        id_address="0x821aea9a577a9b44299b9c15c88cf3087f3b5544",
        payment_address="0x6330a553fc93768f612722bb8c2ec78ac90b3bbc",
        amount=1000,
    ),
    Payee(
        id_address="0x0d1d4e623d10f9fba5db95830f7d3839406c6af2",
        payment_address=None,
        amount=200,
    ),
    Payee(
        id_address="0x2932b7a2355d6fecc4b5c0b6bd44cc31df247a2e",
        payment_address="0x5aeda56215b167893e80b4fe645ba6d5bab767de",
        amount=300,
    )
]


class TestCreateRequestAsPayee(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.request_api = RequestNetwork()

    def test_create_request_as_payee(self):
        tx_hash = self.request_api.create_request(
            role=Roles.PAYEE,
            currency=currencies_by_symbol['ETH'],
            payees=payees,
            payer=Payer(id_address=test_account, refund_address=None),
            data={
                'reason': 'selling cool stuff'
            }
        )
        self.assertIsNotNone(tx_hash)
        # Retrieve the request and validate it
        request = self.request_api.get_request_by_transaction_hash(tx_hash)

        self.assertEqual(
            test_amounts,
            [payee.amount for payee in request.payees]
        )
        self.assertEqual(
            'selling cool stuff',
            request.data['reason']
        )

    def test_create_request_as_payer(self):
        tx_hash = self.request_api.create_request(
            role=Roles.PAYER,
            currency=currencies_by_symbol['ETH'],
            payees=payees,
            payer=Payer(id_address=test_account, refund_address=None),
            data={
                'reason': 'buying cool stuff'
            }
        )
        self.assertIsNotNone(tx_hash)
        # Retrieve the request and validate it
        request = self.request_api.get_request_by_transaction_hash(tx_hash)

        self.assertEqual(
            test_amounts,
            [payee.amount for payee in request.payees]
        )
        self.assertEqual(
            'buying cool stuff',
            request.data['reason']
        )
