import os
import time

from eth_account.messages import (
    defunct_hash_message,
)
import ipfsapi
from web3 import Web3

from request_network.artifact_manager import (
    ArtifactManager,
)
from request_network.constants import (
    EMPTY_BYTES_20,
)
from request_network.exceptions import (
    InvalidRequestParameters,
)
from request_network.signers import (
    private_key_environment_variable_signer,
)
from request_network.types import (
    Request,
)


class RequestCoreService(object):
    request_api = None

    """ Class for Request Core """
    def __init__(self, request_api):
        """
        :param request_api: Instance of RequestNetwork
        :type request_api: request_network.RequestNetwork
        """
        # self.ethereum_network = ethereum_network
        self.request_api = request_api

    def get_currency_contract_address(self):
        """ Return the currency contract for the given currency. `artifact_name` could
            be `last-RequestEthereum`, or `last-requesterc20-{token_address}`.
        """
        artifact_name = self.get_currency_contract_artifact_name()
        artifact_manager = ArtifactManager(ethereum_network=self.request_api.ethereum_network)
        contract_data = artifact_manager.get_contract_data(artifact_name)
        return contract_data['address']

    def get_currency_contract_artifact_name(self):
        """ Return the artifact name used when looking up the currency contract.
        """
        raise NotImplementedError()

    def create_signed_request(self, currency_contract_address, id_addresses, amounts,
                              payment_addresses, expiration_date,
                              data=None):
        """ Return the signed request object.

        TODO this only supports creating the Request as the payee.

        :param currency_contract_address:
        :param id_addresses:
        :param amounts:
        :param expiration_date:
        :param payment_addresses:
        :param data: Additional data to store with the Request
        :return:
        """
        # If we have data, store it on IPFS
        if data:
            # TODO error handling, move to separate function to make it configurable
            ipfs_node_host = os.environ.get('IPFS_NODE_HOST')
            ipfs_node_port = os.environ.get('IPFS_NODE_PORT', 5001)
            ipfs = ipfsapi.connect(ipfs_node_host, ipfs_node_port)
            ipfs_hash = ipfs.add_json(data)
        else:
            ipfs_hash = ''

        request_hash = self.request_api.hash_request(
            currency_contract_address=currency_contract_address,
            id_addresses=id_addresses,
            amounts=amounts,
            payer=None,
            expiration_date=expiration_date,
            payment_addresses=payment_addresses,
            ipfs_hash=ipfs_hash)

        # `defunct_hash_message` is used to maintain compatibility with `web3Single.sign()`
        message_hash = defunct_hash_message(hexstr=request_hash)
        # TODO make signing strategy configurable
        signer_function = private_key_environment_variable_signer
        signed_message = signer_function(
            message_hash=message_hash,
            address=id_addresses[0]
        )

        sub_payees = []
        # Iterate through id_addresses, skipping the first which is the main payee
        for i, payee in enumerate(payment_addresses[1:]):
            sub_payees.append({
                'id_address': id_addresses[i + 1],
                'payment_address': payment_addresses[i + 1],
                'amount': str(amounts[i + 1])
            })

        request = Request(
            _id=None,
            creator=None,
            _hash=request_hash,
            currency_contract_address=currency_contract_address,
            ipfs_hash=ipfs_hash,
            data=data,
            payer=None,
            payee={
                'id_address': id_addresses[0],
                'payment_address': payment_addresses[0],
                'amount': amounts[0]
            },
            state=None,
            sub_payees=sub_payees,
            expiration_date=expiration_date,
            signature=Web3.toHex(signed_message.signature)
        )
        return request

    def sign_request_as_payee(self, id_addresses, amounts,
                              payment_addresses, expiration_date,
                              data=None):
        """ Sign a Request as the payee.

        :param id_addresses:
        :param amounts:
        :param expiration_date:
        :param payment_addresses:
        :param data:
        :return:
        """
        currency_contract_address = self.get_currency_contract_address()

        # Iterate through payee addresses - if a None value is given for any address,
        # replace it with the 0x0 address (padded to 20 bytes).
        parsed_payee_payment_addresses = [
            Web3.toChecksumAddress(a) if a else EMPTY_BYTES_20 for a in payment_addresses
        ]
        id_addresses = [
            Web3.toChecksumAddress(a) for a in id_addresses
        ]

        # Validate Request parameters
        if len(id_addresses) != len(amounts):
            raise InvalidRequestParameters(
                'payees and amounts must be the same size'
            )

        if payment_addresses and len(id_addresses) < len(payment_addresses):
            raise InvalidRequestParameters(
                'payees can not be larger than payee_payment_addresses'
            )

        if int(expiration_date) <= int(time.time()):
            raise InvalidRequestParameters(
                'expiration_date must be in the future'
            )

        for amount in amounts:
            if int(amount) < 0:
                raise InvalidRequestParameters(
                    'amounts must be positive integers'
                )

        for address in id_addresses:
            if not Web3.isAddress(address):
                raise InvalidRequestParameters(
                    '{} is not a valid Ethereum address'.format(address)
                )

        return self.create_signed_request(
            currency_contract_address=currency_contract_address,
            id_addresses=id_addresses,
            amounts=amounts,
            payment_addresses=parsed_payee_payment_addresses,
            expiration_date=expiration_date,
            data=data
        )
