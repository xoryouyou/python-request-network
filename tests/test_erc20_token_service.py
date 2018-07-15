from datetime import (
    datetime,
)
import time
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
from request_network.exceptions import (
    InvalidRequestParameters,
)
from request_network.services.ERC20 import (
    RequestERC20Service,
)

test_token_address = '0x345ca3e014aaf5dca488057592ee47305d9b3e10'
test_account = '0x1b77F92aaEEE6249358907E1D33ae52F424D6292'
test_amounts = [
    100000000,
    20000000,
    3000000
]


class TestSignRequestAsPayee(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.request_api = RequestNetwork()
        self.service = RequestERC20Service(
            token_address=test_token_address
        )

    def test_sign_request_as_payee(self):
        # https://github.com/RequestNetwork/requestNetwork/blob/master/packages/requestNetwork.js/test/unit/erc20Services/signRequestAsPayee.ts
        payees = [
            Web3.toChecksumAddress("0x821aea9a577a9b44299b9c15c88cf3087f3b5544"),
            Web3.toChecksumAddress("0x0d1d4e623d10f9fba5db95830f7d3839406c6af2"),
            Web3.toChecksumAddress("0x2932b7a2355d6fecc4b5c0b6bd44cc31df247a2e")
        ]
        payee_payment_addresses = [
            Web3.toChecksumAddress("0x6330a553fc93768f612722bb8c2ec78ac90b3bbc"),
            None,
            Web3.toChecksumAddress("0x5aeda56215b167893e80b4fe645ba6d5bab767de")
        ]
        expiration_date = 7952342400000

        signed_request = self.service.sign_request_as_payee(
            id_addresses=payees,
            amounts=test_amounts,
            payment_addresses=payee_payment_addresses,
            expiration_date=expiration_date
        )
        self.assertEqual(
            '0x0b19a8ca1fcf735bffaacc7a9e4e2b86f9a9e98e382fff27edbf721bf70d351d',
            signed_request.hash
        )

        # make sure returned address is signer's address
        recovered_address = w3.eth.account.recoverHash(
            message_hash=defunct_hash_message(hexstr=signed_request.hash),
            signature=signed_request.signature)
        self.assertEqual(
            Web3.toChecksumAddress('0x821aea9a577a9b44299b9c15c88cf3087f3b5544'),
            recovered_address
        )

        self.assertEqual(
            # Signature taken from requestnetwork.js tests for signing request
            '0x954fcc32f2fa56beff4933d11fdda7c5f5f94fa708eef8af803e2d196e6d'
            '24a75cca40c1bceeef2c3786157bb0fc76ca0b6b00c957e5a1dde5247e59b0750c761c',
            signed_request.signature)

    def test_sign_request_invalid_expiration(self):
        with self.assertRaises(InvalidRequestParameters):
            self.service.sign_request_as_payee(
                id_addresses=[test_account],
                amounts=[test_amounts[0]],
                payment_addresses=[test_account],
                expiration_date=time.mktime(datetime.strptime('2000-01-01', '%Y-%m-%d').timetuple())
            )


if __name__ == '__main__':
    unittest.main()
