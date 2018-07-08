import unittest

from request_network.artifact_manager import (
    ArtifactManager,
)
from request_network.services import (
    RequestERC20Service,
)
from request_network.types import (
    EthereumNetworks,
)

# Request token on private network
TEST_TOKEN_ADDRESS = '0x345ca3e014aaf5dca488057592ee47305d9b3e10'
TEST_CURRENCY_CONTRACT_ADDRESS = '0xf25186B5081Ff5cE73482AD761DB0eB0d25abfBF'


class ArtifactMangerTestCase(unittest.TestCase):
    def test_get_erc20_req(self):
        am = ArtifactManager(ethereum_network=EthereumNetworks.private)
        artifact_name = 'last-requesterc20-{}'.format(TEST_TOKEN_ADDRESS)
        request_currency_contract = am.get_contract_data(artifact_name)
        self.assertEqual(
            TEST_CURRENCY_CONTRACT_ADDRESS,
            request_currency_contract['address']
        )

    def test_get_service_by_address(self):
        am = ArtifactManager(ethereum_network=EthereumNetworks.private)
        service_class = am.get_service_class_by_address(TEST_CURRENCY_CONTRACT_ADDRESS)
        self.assertEqual(RequestERC20Service, service_class)
