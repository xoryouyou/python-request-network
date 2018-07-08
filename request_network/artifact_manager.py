import json
import os

from web3 import Web3
from web3.auto import (
    w3,
)


class ArtifactManager(object):
    """ Helper class for retrieving information about smart contract artifacts.
    """
    artifacts = None
    artifact_directory = None
    ethereum_network = None

    # TODO convert artifacts into lazy property
    def __init__(self, ethereum_network=None, artifact_directory=None):
        """
        :param ethereum_network: Ethereum network
        :type ethereum_network: request_network.types.EthereumNetwork
        :param artifact_directory: Path to the directory containing smart contract
        artifacts. Defaults to the `artifacts` subdirectory of the package.
        """
        self.ethereum_network = ethereum_network

        if not artifact_directory:
            self.artifact_directory = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                'artifacts')
        else:
            self.artifact_directory = artifact_directory

        with open(os.path.join(self.artifact_directory, 'artifacts.json')) as f:
            self.artifacts = json.load(f)

    def get_service_class_by_address(self, address):
        """ Given the address of a currency contract, return the related service class.

        :param ethereum_network:
        :param address:
        :return: The service class to use for the given currency contract address.
        """
        # Local import to avoid circular import, as RequestCoreService imports this module
        from request_network.services import RequestERC20Service, RequestEthereumService

        address = address.lower()
        contract_artifact_path = self.artifacts[self.ethereum_network.name][address]

        if 'RequestERC20' in contract_artifact_path:
            return RequestERC20Service
        if 'RequestEthereum' in contract_artifact_path:
            return RequestEthereumService
        if 'RequestBitcoinNodesValidation' in contract_artifact_path:
            raise NotImplementedError()

    def get_contract_instance(self, name):
        """

        :param name:
        :return:
        :rtype: web3.eth.Contract
        """
        data = self.get_contract_data(name)
        return w3.eth.contract(abi=data['abi'], address=data['address'])

    def get_contract_data(self, name):
        """ Return a dict describing the contract related to artifact `name`.

        `name` might be an ERC20 token address, or something like `RequestEthereum`.

        :param name:
        :return:
        :rtype: dict
        """
        # Force name to lowercase in case it includes a checksummed address
        name = name.lower()
        try:
            network_artifacts = self.artifacts[self.ethereum_network.name]
        except KeyError:
            raise Exception(
                'Could not find artifacts for {} network'.format(self.ethereum_network.name))
        try:
            contract_artifact_path = network_artifacts[name]
        except KeyError:
            raise Exception(
                'Could not find artifact for "{}" on {} network'.format(
                    name, self.ethereum_network.name))

        with open(os.path.join(self.artifact_directory, contract_artifact_path)) as f:
            contract_artifact = json.load(f)

        try:
            network_data = contract_artifact['networks'][self.ethereum_network.name]
        except KeyError:
            raise Exception(
                'Could not find artifact for "{}" on {} network'.format(
                    name, self.ethereum_network.name))

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
