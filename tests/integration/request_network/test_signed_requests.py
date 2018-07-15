import unittest

from eth_account.messages import (
    defunct_hash_message,
)
from web3 import Web3
from web3.auto import (
    w3,
)

from request_network.api import (
    RequestNetwork,
)
from request_network.currencies import (
    currencies_by_symbol,
)
from request_network.types import (
    Payee,
    Roles,
)
from request_network.utils import (
    get_request_bytes_representation,
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


class TestSignedRequests(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.request_api = RequestNetwork()

    def test_create_and_broadcast_ethereum_signed_request_as_payee(self):
        signed_request = self.request_api.create_signed_request(
            role=Roles.PAYEE,
            currency=currencies_by_symbol['ETH'],
            payees=payees_for_broadcast,
            expiration_date=expiration_date,
            data={'reason': 'pay in advance'}
        )

        # Sanity check - can we recover the signers address by re-hashing the request?
        recovered_address = w3.eth.account.recoverHash(
            message_hash=defunct_hash_message(hexstr=signed_request.hash),
            signature=signed_request.signature)
        self.assertEqual(
            Web3.toChecksumAddress('0x821aea9a577a9b44299b9c15c88cf3087f3b5544'),
            recovered_address
        )

        # Broadcast the Request, retrieve it from the blockchain, and validate payment status
        tx_hash = self.request_api.broadcast_signed_request(
            signed_request=signed_request,
            payment_amounts=[payee.amount for payee in payees_for_broadcast],
            payer_address=Web3.toChecksumAddress('0x627306090abab3a6e1400e9345bc60c78a8bef57')
        )

        request = self.request_api.get_request_by_transaction_hash(tx_hash)
        self.assertEqual(
            request.payees[0].id_address,
            payees[0].id_address
        )
        self.assertTrue(request.is_paid)

    def test_create_erc20_signed_request_as_payee(self):
        # https://github.com/RequestNetwork/requestNetwork/blob/master/packages/requestNetwork.js/test/unit/erc20Services/signRequestAsPayee.ts
        request_api = RequestNetwork()

        signed_request = request_api.create_signed_request(
            role=Roles.PAYEE,
            currency=currencies_by_symbol['DAI'],
            payees=payees,
            expiration_date=expiration_date
        )
        self.assertEqual(
            '0x0b19a8ca1fcf735bffaacc7a9e4e2b86f9a9e98e382fff27edbf721bf70d351d',
            signed_request.hash
        )
        recovered_address = w3.eth.account.recoverHash(
            message_hash=defunct_hash_message(hexstr=signed_request.hash),
            signature=signed_request.signature)
        self.assertEqual(
            Web3.toChecksumAddress('0x821aea9a577a9b44299b9c15c88cf3087f3b5544'),
            recovered_address
        )

        self.assertEqual(
            '0x954fcc32f2fa56beff4933d11fdda7c5f5f94fa708eef8af803e2d19'
            '6e6d24a75cca40c1bceeef2c3786157bb0fc76ca0b6b00c957e5a1dde5247e59b0750c761c',
            signed_request.signature)

        # TODO get_request_bytes_representation should have its own unit tests
        get_request_bytes_representation(
            payee_id_addresses=[payee.id_address for payee in payees],
            amounts=test_amounts,
            payer=payees[0].id_address,
            ipfs_hash=None
        )
