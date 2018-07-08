class Currency(object):
    name = None
    symbol = None
    decimals = None
    request_service_class = None

    def __init__(self, name, symbol, decimals, request_service_class):
        self.name = name
        self.symbol = symbol
        self.decimals = decimals
        self.request_service_class = request_service_class

    def get_service_class(self, ethereum_network):
        """ :returns An instance of the service for this currency
            :rtype request_network.services.RequestCoreService
        """
        # TODO do not commit, hacky testing
        from request_network import RequestNetwork

        # https://stackoverflow.com/a/547867/394423
        components = 'request_network.services'.split('.')
        mod = __import__(components[0])
        for comp in components[1:]:
            mod = getattr(mod, comp)
        service_class = getattr(mod, self.request_service_class)
        return service_class(
            request_api=RequestNetwork(ethereum_network=ethereum_network),
            **self.get_service_instance_kwargs())

    def get_service_instance_kwargs(self):
        return {}


class ERC20Currency(Currency):
    token_address = None

    def __init__(self, name, symbol, decimals, request_service_class, token_address):
        super().__init__(name, symbol, decimals, request_service_class)
        self.token_address = token_address

    def get_service_instance_kwargs(self):
        data = super(ERC20Currency, self).get_service_instance_kwargs()
        data['token_address'] = self.token_address
        return data


# TODO refactor as Enum loaded from JSON file?
# TODO how to best manage live and test currency sets? Can we load them from the artifact manager?
currencies_by_symbol = {
    'ETH': Currency('Ethereum', 'ETH', 18, 'RequestEthereumService'),
    'DAI': ERC20Currency(
        'Dai',
        'DAI',
        18,
        'RequestERC20Service',
        '0x345ca3e014aaf5dca488057592ee47305d9b3e10'
    )
}

currencies_by_name = {c.name: c for c in currencies_by_symbol.values()}
