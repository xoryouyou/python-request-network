import json
import os

from web3 import Web3
from web3.auto import (
    w3,
)

from request_network.constants import (
    ARTIFACT_DIRECTORY_ENVIRONMENT_VARIABLE,
    NETWORK_NAME_ENVIRONMENT_VARIABLE,
)
from request_network.exceptions import (
    ArtifactNotFound,
)


class ArtifactManager(object):
    """ Provides access to smart contract artifacts.
    """
    artifacts = None
    artifact_directory = None
    ethereum_network = None

    # TODO convert artifacts into lazy property
    def __init__(self):
        """
        """
        try:
            self.ethereum_network = os.environ[NETWORK_NAME_ENVIRONMENT_VARIABLE]
        except KeyError:
            self.ethereum_network = 'private'

        try:
            self.artifact_directory = os.environ[ARTIFACT_DIRECTORY_ENVIRONMENT_VARIABLE]
        except KeyError:
            # Environment variable not set, using default
            self.artifact_directory = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                'artifacts')

        with open(os.path.join(self.artifact_directory, 'artifacts.json')) as f:
            self.artifacts = json.load(f)

    def get_service_class_by_address(self, address):
        """ Given the address of a currency contract, return the related service class.

        :param address:
        :return: The service class to use for the given currency contract address.
        """
        # Local import to avoid circular import, as RequestCoreService imports this module
        from request_network.services import RequestERC20Service, RequestEthereumService

        address = address.lower()
        try:
            contract_artifact_path = self.artifacts[self.ethereum_network][address]
        except KeyError:
            raise ArtifactNotFound(
                'Could not find artifact for "{}" on {} network'.format(
                    address, self.ethereum_network))

        if 'RequestERC20' in contract_artifact_path:
            return RequestERC20Service
        if 'RequestEthereum' in contract_artifact_path:
            return RequestEthereumService
        if 'RequestBitcoinNodesValidation' in contract_artifact_path:
            raise NotImplementedError()

    def get_contract_instance(self, name):
        """ Helper function to return a `web3.eth.Contract` instance of the specified contract.

        :param name:
        :return:
        :rtype: web3.eth.Contract
        """
        return self.get_contract_data(name)['instance']

    def get_contract_data(self, name):
        """ Return a dict describing the contract related to artifact `name`.

        `name` might be an ERC20 token address, or an identifier such as `RequestEthereum`.

        :param name:
        :return:
        :rtype: dict
        """
        # Force name to lowercase in case it includes a checksummed address
        name = name.lower()
        try:
            network_artifacts = self.artifacts[self.ethereum_network]
        except KeyError:
            raise ArtifactNotFound(
                'Could not find artifacts for {} network'.format(self.ethereum_network))
        try:
            contract_artifact_path = network_artifacts[name]
        except KeyError:
            raise ArtifactNotFound(
                'Could not find artifact for "{}" on {} network'.format(
                    name, self.ethereum_network))

        with open(os.path.join(self.artifact_directory, contract_artifact_path)) as f:
            contract_artifact = json.load(f)

        try:
            network_data = contract_artifact['networks'][self.ethereum_network]
        except KeyError:
            raise ArtifactNotFound(
                'Could not find artifact for "{}" on {} network'.format(
                    name, self.ethereum_network))

        return {
            'abi': contract_artifact['abi'],
            'version': contract_artifact['version'],
            'address': Web3.toChecksumAddress(network_data['address']),
            'block_number': network_data['blockNumber'],
            'instance': w3.eth.contract(
                abi=contract_artifact['abi'],
                address=Web3.toChecksumAddress(network_data['address'])
            )
        }
