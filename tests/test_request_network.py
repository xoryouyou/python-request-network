import unittest

from eth_abi.decoding import (
    StringDecoder,
    decode_uint_256,
)
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
from request_network.exceptions import (
    RequestNotFound,
    TransactionNotFound,
)
from request_network.types import (
    Payee,
    Payer,
    Roles,
)
from request_network.utils import (
    get_request_bytes_representation,
    hash_request_object,
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


payees_for_broadcast = [
    Payee(
        id_address="0x821aea9a577a9b44299b9c15c88cf3087f3b5544",
        payment_address="0x6330a553fc93768f612722bb8c2ec78ac90b3bbc",
        amount=1000,
        # payment_amount=1000
    ),
    Payee(
        id_address="0x0d1d4e623d10f9fba5db95830f7d3839406c6af2",
        payment_address=None,
        amount=200,
        # payment_amount=test_amounts[1]
    ),
    Payee(
        id_address="0x2932b7a2355d6fecc4b5c0b6bd44cc31df247a2e",
        payment_address="0x5aeda56215b167893e80b4fe645ba6d5bab767de",
        amount=300,
        # payment_amount=test_amounts[2]
    )
]



class TestSignedRequests(unittest.TestCase):
    def setUp(self):
        super().setUp()
        # TODO remove
        # private_key_env_var = 'REQUEST_NETWORK_PRIVATE_KEY_0x821aEa9a577a9b44299B9c15c88cf3087F3b5544'
        # os.environ[private_key_env_var] = 'c88b703fb08cbea894b6aeff5a544fb92e78a18e19814cd85da83b71f772aa6c'
        self.request_api = RequestNetwork()


    def test_create_ethereum_signed_request_as_payee(self):
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
            payment_amounts=[payee.amount for payee in payees_for_broadcast]
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
            '0x954fcc32f2fa56beff4933d11fdda7c5f5f94fa708eef8af803e2d196e6d24a75cca40c1bceeef2c3786157bb0fc76ca0b6b00c957e5a1dde5247e59b0750c761c',
            signed_request.signature)

        data = get_request_bytes_representation(
            payee_id_addresses=[payee.id_address for payee in payees],
            amounts=test_amounts,
            payer=payees[0].id_address,
            ipfs_hash=None
        )


class GetRequestTestCase(unittest.TestCase):
    """ These tests are using transactions created by running the RequestNetwork.js
        test suite.
    """

    def setUp(self):
        super().setUp()
        self.request_api = RequestNetwork()

    def test_hash_request_object(self):
        # TODO integration test, relies on request network js tests
        request = self.request_api.get_request_by_transaction_hash(
            '0x1f97459c45402fcb6562410cf4b4253a9d5d9528f247a892f9bddeefdd878b2d')
        # Manually add the expiration date as it is not stored on the contract
        request.expiration_date = expiration_date
        hash_request_object(request)

    def test_get_request_by_id(self):
        # TODO integration test, relies on request network js tests
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

    def test_get_nonexistent_request_by_id(self):
        with self.assertRaises(RequestNotFound):
            self.request_api.get_request_by_id(
                '0x8cdaf0cd259887258bc13a92c0a6da92698644c0000000000000000000000000')

    def test_get_request_by_transaction_hash(self):
        # TODO integration test, relies on request network js tests
        request = self.request_api.get_request_by_transaction_hash(
            '0x8d3ec9ef287f09577707bd8ffe7f053394d4cb5355f62495886dbd4a5589971b')
        self.assertEqual(
            '0x0F4F2Ac550A1b4e2280d04c21cEa7EBD822934b5',
            request.payer
        )
        self.assertEqual(
            {'reason': 'weed purchased'},
            request.data
        )

    def test_get_nonexistent_request_by_transaction_hash(self):
        with self.assertRaises(TransactionNotFound):
            self.request_api.get_request_by_transaction_hash(
                '0x8d3ec9ef287f09577707bd8ffe7f053394d4cb5355f62495886dbd4a55800000')


if __name__ == '__main__':
    unittest.main()
