import unittest

# TODO fix test data, this uses data from other tests
from request_network.api import (
    RequestNetwork,
)
from request_network.currencies import (
    currencies_by_symbol,
)
from request_network.types import (
    Payee,
    Roles,
)


class Base64EncodingTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.request_api = RequestNetwork()

    def test_get_qr_code(self):
        """ Generate the base64 and QR code data URI for a Signed Request, and validate the first
            32 characters of each.
        """
        signed_request = self.request_api.create_signed_request(
            role=Roles.PAYEE,
            currency=currencies_by_symbol['ETH'],
            payees=[Payee(
                id_address='0x821aea9a577a9b44299b9c15c88cf3087f3b5544',
                amount=int(0.1 * 10 ** 18)
            )],
            expiration_date=7952342400000,
            data={'reason': 'pay in advance'}
        )

        params = dict(callback_url='https://example.com', ethereum_network_id=4)
        self.assertEqual(
            'eyJzaWduZWRSZXF1ZXN0IjogeyJjdXJy',
            signed_request.as_base64(**params)[:32]
        )
        self.assertEqual(
            'data:text/png;base64,iVBORw0KGgo',
            signed_request.get_qr_code_data_uri(**params)[:32]
        )
