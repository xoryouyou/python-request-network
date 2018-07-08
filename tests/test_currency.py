import unittest

from request_network.currencies import (
    currencies_by_name,
    currencies_by_symbol,
)
from request_network.services.ERC20 import (
    RequestERC20Service,
)
from request_network.types import (
    EthereumNetworks,
)


class CurrencyTestCase(unittest.TestCase):
    def test_name_lookup(self):
        ethereum = currencies_by_name['Ethereum']
        self.assertEqual('ETH', ethereum.symbol)

    def test_symbol_lookup(self):
        ethereum = currencies_by_symbol['ETH']
        self.assertEqual('Ethereum', ethereum.name)

    def test_get_service_class(self):
        dai = currencies_by_symbol['DAI']
        service = dai.get_service_class(ethereum_network=EthereumNetworks.rinkeby)
        self.assertTrue(isinstance(service, RequestERC20Service))
