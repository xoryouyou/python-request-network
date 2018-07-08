from request_network.services.core import (
    RequestCoreService,
)


class RequestEthereumService(RequestCoreService):

    def get_currency_contract_artifact_name(self):
        return 'last-RequestEthereum'
