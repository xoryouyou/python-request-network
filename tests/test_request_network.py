import os
import unittest

from eth_account.messages import (
    defunct_hash_message,
)
from web3 import Web3
from web3.auto import (
    w3,
)
from web3.middleware import (
    geth_poa_middleware,
)

from request_network import (
    RequestNetwork,
)
from request_network.currencies import (
    currencies_by_symbol,
)
from request_network.services.core import (
    RequestCoreService,
)
from request_network.types import (
    EthereumNetworks,
    Payee,
    Roles,
)

test_token_address = '0x345ca3e014aaf5dca488057592ee47305d9b3e10'
test_account = '0x1b77F92aaEEE6249358907E1D33ae52F424D6292'
test_amounts = [
    100000000,
    20000000,
    3000000
]

payees = [
    Payee(
        id_address="0x821aea9a577a9b44299b9c15c88cf3087f3b5544",
        payment_address="0x6330a553fc93768f612722bb8c2ec78ac90b3bbc",
        amount=test_amounts[0]
    ),
    Payee(
        id_address="0x0d1d4e623d10f9fba5db95830f7d3839406c6af2",
        payment_address=None,
        amount=test_amounts[1]
    ),
    Payee(
        id_address="0x2932b7a2355d6fecc4b5c0b6bd44cc31df247a2e",
        payment_address="0x5aeda56215b167893e80b4fe645ba6d5bab767de",
        amount=test_amounts[2]
    )
]

expiration_date = 7952342400000


class TestSignRequestAsPayee(unittest.TestCase):
    def setUp(self):
        super().setUp()
        private_key_env_var = 'REQUEST_NETWORK_PRIVATE_KEY_0x821aEa9a577a9b44299B9c15c88cf3087F3b5544'
        os.environ[private_key_env_var] = 'c88b703fb08cbea894b6aeff5a544fb92e78a18e19814cd85da83b71f772aa6c'
        self.request_api = RequestNetwork(ethereum_network=EthereumNetworks.private)

    def test_create_ethereum_signed_request_as_payee(self):
        request_api = RequestNetwork(
            ethereum_network=EthereumNetworks.private
        )

        signed_request = request_api.create_signed_request(
            role=Roles.PAYEE,
            currency=currencies_by_symbol['ETH'],
            payees=payees,
            expiration_date=expiration_date
        )
        self.assertEqual(
            '0xadd6e7024686c4223ca55d4b33c08668adecbcb7a89ea941e31ed629e8c3b76e',
            signed_request.hash
        )

        # Sanity check - can we recover the signers address by re-hashing the request?
        recovered_address = w3.eth.account.recoverHash(
            message_hash=defunct_hash_message(hexstr=signed_request.hash),
            signature=signed_request.signature)
        self.assertEqual(
            Web3.toChecksumAddress('0x821aea9a577a9b44299b9c15c88cf3087f3b5544'),
            recovered_address
        )

        self.assertEqual(
            '0x9e1c91c2d9070602fbe56aa1ac6590a03c472e4dceb77bb9c4acba9f69cb14497aace6ad62a3fbcf0d3b4f9cbf1f9ead603529ac33e946e9668538455bb4fff91b',
            signed_request.signature)

        self.request_api.get_request_bytes_representation(
            payees=[payee.id_address for payee in payees],
            amounts=test_amounts,
            payer=payees[0].id_address,
            data=None
        )

    def test_create_erc20_signed_request_as_payee(self):
        # https://github.com/RequestNetwork/requestNetwork/blob/master/packages/requestNetwork.js/test/unit/erc20Services/signRequestAsPayee.ts
        request_api = RequestNetwork(ethereum_network=EthereumNetworks.private)

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

        data = self.request_api.get_request_bytes_representation(
            payees=[payee.id_address for payee in payees],
            amounts=test_amounts,
            payer=payees[0].id_address,
            data=None
        )


class GetRequestTestCase(unittest.TestCase):
    # TODO test with ganache instead of infura - the get_request_by_* tests are using
    # a known transaction on Rinkeby, but they should be using a tx from request.js' test suite
    def setUp(self):
        super().setUp()
        os.environ['WEB3_PROVIDER_URI'] = 'https://rinkeby.infura.io/{}'.format(os.environ['INFURA_API_KEY'])
        # Insert POA middleware so we can work with Rinkeby
        w3.middleware_stack.inject(geth_poa_middleware, layer=0)
        self.request_api = RequestNetwork(ethereum_network=EthereumNetworks.rinkeby)

    def tearDown(self):
        super().tearDown()
        w3.middleware_stack.remove(geth_poa_middleware)

    def test_hash_request_object(self):
        request = self.request_api.get_request_by_transaction_hash(
            '0xbb0a82e551c590013ce8eb53be06936c694dd28749cd679092b76dc7388cb9ed')
        # monkey patch expiration, because I don't think it is stored after request is signed/broadcast
        request.expiration_date = expiration_date

        self.request_api.hash_request_object(request)

    def test_get_request_by_id(self):
        request = self.request_api.get_request_by_id(
            '0x8fc2e7f2498f1d06461ee2d547002611b801202b0000000000000000000003e4')
        self.assertEqual(
            '0x627306090abaB3A6e1400e9345bC60c78a8BEf57',
            request.payer['address']
        )
        self.assertEqual(
            '100000000000000',
            request.payments[0].delta_amount
        )
        self.assertEqual(
            True,
            request.is_paid()
        )

    def test_get_request_by_transaction_hash(self):
        request = self.request_api.get_request_by_transaction_hash('0xbb0a82e551c590013ce8eb53be06936c694dd28749cd679092b76dc7388cb9ed')
        self.assertEqual(
            '0x627306090abaB3A6e1400e9345bC60c78a8BEf57',
            request.payer['address']
        )


if __name__ == '__main__':
    unittest.main()
