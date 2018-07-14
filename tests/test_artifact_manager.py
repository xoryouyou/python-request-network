import unittest

from request_network.artifact_manager import (
    ArtifactManager,
)
from request_network.exceptions import (
    ArtifactNotFound,
)
from request_network.services import (
    RequestERC20Service,
)

# Request token on private network
TEST_TOKEN_ADDRESS = '0x345ca3e014aaf5dca488057592ee47305d9b3e10'
TEST_CURRENCY_CONTRACT_ADDRESS = '0xf25186B5081Ff5cE73482AD761DB0eB0d25abfBF'


class ArtifactMangerTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.am = ArtifactManager()

    def test_get_erc20_req(self):
        artifact_name = 'last-requesterc20-{}'.format(TEST_TOKEN_ADDRESS)
        request_currency_contract = self.am.get_contract_data(artifact_name)
        self.assertEqual(
            TEST_CURRENCY_CONTRACT_ADDRESS,
            request_currency_contract['address']
        )

    def test_get_invalid_token(self):
        # artifact_name = 'last-requesterc20-{}'.format(TEST_TOKEN_ADDRESS)
        with self.assertRaises(ArtifactNotFound):
            self.am.get_contract_data('foo')

    def test_get_valid_token_from_invalid_network(self):
        am = ArtifactManager()
        am.ethereum_network = 'fake-network'
        artifact_name = 'last-requesterc20-{}'.format(TEST_TOKEN_ADDRESS)
        with self.assertRaises(ArtifactNotFound):
            am.get_contract_data(artifact_name)

    def test_get_service_by_address(self):
        service_class = self.am.get_service_class_by_address(TEST_CURRENCY_CONTRACT_ADDRESS)
        self.assertEqual(RequestERC20Service, service_class)

    def test_get_invalid_service_class(self):
        with self.assertRaises(ArtifactNotFound):
            self.am.get_service_class_by_address('foo')

    def test_get_service_class_from_invalid_network(self):
        am = ArtifactManager()
        am.ethereum_network = 'fake-network'
        # with self.assertRaises(ArtifactNotFound):
        with self.assertRaises(ArtifactNotFound):
            am.get_service_class_by_address('foo')
