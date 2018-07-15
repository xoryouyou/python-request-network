import unittest

# TODO fix test data, this uses data from other tests
from request_network.api import (
    RequestNetwork,
)
from request_network.currencies import (
    currencies_by_symbol,
)
from request_network.types import (
    Roles,
)
from tests.test_request_network import (
    expiration_date,
    payees_for_broadcast,
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
            payees=payees_for_broadcast,
            expiration_date=expiration_date,
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
