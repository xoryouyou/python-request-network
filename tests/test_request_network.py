from unittest import mock

import os
import unittest

from eth_abi.decoding import StringDecoder, decode_uint_256
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


class TestCreateRequestAsPayee(unittest.TestCase):
    def setUp(self):
        super().setUp()
        # TODO remove
        private_key_env_var = 'REQUEST_NETWORK_PRIVATE_KEY_0x821aEa9a577a9b44299B9c15c88cf3087F3b5544'
        os.environ[private_key_env_var] = 'c88b703fb08cbea894b6aeff5a544fb92e78a18e19814cd85da83b71f772aa6c'
        self.request_api = RequestNetwork(ethereum_network=EthereumNetworks.private)

    def test_create_request_as_payee(self):
        request = self.request_api.create_request_as_payee(
            'token address if erc20',
            'payees',
            'payer',
            'payer refund address',
            'data',
            'options'
        )

        self.assertIsNotNone(request.transaction_hash)
        self.assertIsNotNone(request.id)




class TestSignRequestAsPayee(unittest.TestCase):
    def setUp(self):
        super().setUp()
        # TODO remove
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
    """ These tests are using transactions created by running the RequestNetwork.js
        test suite.
    """

    def setUp(self):
        super().setUp()
        self.request_api = RequestNetwork(ethereum_network=EthereumNetworks.private)

    def test_hash_request_object(self):
        request = self.request_api.get_request_by_transaction_hash(
            '0x2c98588e792da8dec816e625cb7a6d014ad0e510684d4fff5166715ea61efa09')
        # monkey patch expiration, because I don't think it is stored after request is signed/broadcast
        # Manually add the expiration date as it is not stored on the contract
        request.expiration_date = expiration_date
        self.request_api.hash_request_object(request)

    def test_get_request_by_id(self):
        request = self.request_api.get_request_by_id(
            '0x8cdaf0cd259887258bc13a92c0a6da92698644c000000000000000000000026b')
        self.assertEqual(
            '0xC5fdf4076b8F3A5357c5E395ab970B5B54098Fef',
            request.payer['address']
        )
        self.assertEqual(
            100000000,
            request.payments[0].delta_amount
        )

    def test_get_request_by_transaction_hash(self):
        with mock.patch.object(
                StringDecoder,
                'read_data_from_stream',
                new=read_padded_data_from_stream):
            request = self.request_api.get_request_by_transaction_hash(
                # 'simple' request
                # '0x1f97459c45402fcb6562410cf4b4253a9d5d9528f247a892f9bddeefdd878b2d')
                # 'complex' request, with data
                '0x809bab406bf6251e49cb04c2e3e99d52dacec3b1b6ec89557ca1c4d0b71d3fec')
            self.assertEqual(
                '0x0F4F2Ac550A1b4e2280d04c21cEa7EBD822934b5',
                request.payer['address']
            )
            self.assertEqual(
                {'reason': 'weed purchased'},
                request.data
            )


if __name__ == '__main__':
    unittest.main()


def read_padded_data_from_stream(self, stream):
    """
        For some reason the IPFS hash is not encoded correctly when we retrieve
        it from the core_contract's events. This worked previously when testing
        against a signed request. Appears to be this bug:

        https://github.com/ethereum/web3.py/issues/602
        https://github.com/ethereum/solidity/issues/3493

        Carver reported a bug in solidity - data from logs differs if the event
        is emitted during an external or internal solidity function call.

        `broadcastSignedRequestAsPayerAction` calls `createAcceptAndPayFromBytes`,
        which is internal, and calls `requestCore.createRequestFromBytes`.

        But then `createRequestAsPayeeAction` calls `createCoreRequestInternal`
        on the currency contract, which is also internal and then calls
        `requestCore.createRequest`.

        The event/tx contains 'QmbFpULNpMJEj9LfvhH4hSTfTse5YrS2JvhbHW6bDCNpwS',
        but it seems that it should contain the padded value
        'QmbFpULNpMJEj9LfvhH4hSTfTse5YrS2JvhbHW6bDCNpwS\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

        Is it possible that this happens because of slightly different code paths
        between broadcastSignedRequestAsPayee and createAcceptRequest?

        The former extracts the data string (IPFS hash) from the bytes-encoded
        Request. The latter uses a string passed by the library.
        slightly different code paths - first one pulls data from requestbytes
        second one uses data as a string throughout

    :param self:
    :param stream:
    :return:
    """
    from eth_abi.utils.numeric import ceil32
    data_length = decode_uint_256(stream)
    padded_length = ceil32(data_length)

    data = stream.read(padded_length)
    # Start hack
    # Manually pad data to force it to desired length
    if len(data) < padded_length:
        data += b'\x00' * (padded_length - data_length)
    # Example:
    # if data == b'QmbFpULNpMJEj9LfvhH4hSTfTse5YrS2JvhbHW6bDCNpwS':
    #     data = b'QmbFpULNpMJEj9LfvhH4hSTfTse5YrS2JvhbHW6bDCNpwS\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    # End hack

    if len(data) < padded_length:
        from eth_abi.exceptions import InsufficientDataBytes
        raise InsufficientDataBytes(
            "Tried to read {0} bytes.  Only got {1} bytes".format(
                padded_length,
                len(data),
            )
        )

    padding_bytes = data[data_length:]

    if padding_bytes != b'\x00' * (padded_length - data_length):
        from eth_abi.exceptions import NonEmptyPaddingBytes
        raise NonEmptyPaddingBytes(
            "Padding bytes were not empty: {0}".format(repr(padding_bytes))
        )

    return data[:data_length]
