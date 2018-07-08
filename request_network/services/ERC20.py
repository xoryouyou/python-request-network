from web3 import Web3

from request_network.exceptions import (
    InvalidRequestParameters,
)
from request_network.services.core import (
    RequestCoreService,
)


class RequestERC20Service(RequestCoreService):
    token_address = None

    def __init__(self, request_api, token_address):
        super().__init__(request_api)
        self.token_address = token_address

    def get_currency_contract_artifact_name(self):
        return 'last-requesterc20-{}'.format(self.token_address)

    def sign_request_as_payee(self, id_addresses, amounts,
                              payment_addresses, expiration_date, data=None):
        """ ERC20-specific validation for signing requests """

        if not Web3.isAddress(self.token_address):
            raise InvalidRequestParameters(
                '{} is not a valid Ethereum address'.format(self.token_address)
            )

        return super().sign_request_as_payee(
            id_addresses, amounts, payment_addresses, expiration_date, data)
