from base64 import (
    b64encode,
)
from enum import (
    IntEnum,
)
import json
from tempfile import (
    TemporaryFile,
)

import pyqrcode as pyqrcode
from web3 import Web3

from request_network.constants import (
    EMPTY_BYTES_20,
    PAYMENT_GATEWAY_BASE_URL,
)


class Roles(IntEnum):
    PAYER = 0
    PAYEE = 1


class States(IntEnum):
    PENDING = 0  # Request might not have been broadcast, or has been broadcast but not confirmed
    CREATED = 1
    ACCEPTED = 2
    CANCELED = 3


class Payment(object):
    payee_index = None
    delta_amount = None

    def __init__(self, payee_index, delta_amount):
        self.payee_index = payee_index
        self.delta_amount = delta_amount

    def __repr__(self):
        return "{}:{}".format(self.payee_index, self.delta_amount)


class Payee(object):
    def __init__(self, id_address, amount, payment_address=None,
                 additional_amount=None, payment_amount=None, balance=None,
                 paid_amount=None):
        """

        :param id_address:
        :param payment_address:
        :param amount: Expected amount to be paid for this Request
        :param additional_amount: Extra amount, on top of expected amount
        :param payment_amount: Amount to pay at creation when Request is created by payer
        :param paid_amount: Track how much has been paid to this payee
        """

        if payment_address:
            payment_address = Web3.toChecksumAddress(payment_address)
        else:
            payment_address = None
        self.id_address = Web3.toChecksumAddress(id_address)
        self.payment_address = payment_address
        self.amount = amount
        # TODO these are only set when using create_request_as_payer. Better place for them?
        self.additional_amount = additional_amount if additional_amount else 0
        self.payment_amount = payment_amount if payment_amount else 0
        # TODO when is balance used?
        self.balance = balance if balance else 0
        self.paid_amount = paid_amount if paid_amount else 0

    @property
    def is_paid(self):
        """ Return True if the payee has received payments with a total greater than
            or equal to the expected amount. The paid amount can be greater than the
            expected amount if the payer supplied additional payments.
        """
        # TODO rather naive, needs to be tested with additionals/subtractions
        return self.paid_amount >= self.amount


class Payer(object):
    """ Represents a Payer. BitcoinRefundAddresses not yet supported.

        If `refund_address` is not given `id_address` is used as the refund address.
    """
    def __init__(self, id_address, refund_address=None):
        self.id_address = Web3.toChecksumAddress(id_address)
        self.refund_address = Web3.toChecksumAddress(refund_address) \
            if refund_address else self.id_address


class Request(object):
    def __init__(self, currency_contract_address, payees, ipfs_hash, id=None, data=None,
                 payer=None, state=None, payments=None, creator=None,
                 expiration_date=None, signature=None, _hash=None,
                 transaction_hash=None):
        """ Represents a Request which may be in one of multiple states:

            - a Request that was retrieved from the blockchain
            - a Signed Request that has been generated locally but does not exist on-chain
        """
        self.id = id
        self.currency_contract_address = currency_contract_address
        self.payer = payer
        self.payees = payees
        self.ipfs_hash = ipfs_hash
        self.data = data if data else {}
        self.state = state
        self.expiration_date = expiration_date
        self.signature = signature
        self.hash = _hash
        self.payments = payments if payments else []
        self.creator = creator
        self.transaction_hash = transaction_hash

    @property
    def amounts(self):
        return [p.amount for p in self.payees]

    @property
    def payment_addresses(self):
        return [p.payment_address for p in self.payees]

    @property
    def id_addresses(self):
        return [p.id_address for p in self.payees]

    @property
    def is_paid(self):
        """ Returns True if all payees have received their expected amounts.
        """
        return all([p.is_paid for p in self.payees])

    def as_base64(self, callback_url, ethereum_network_id):
        """ Return the base64-encoded JSON string required by the payment gateway.

        :param callback_url:
        :type ethereum_network: request_network.types.EthereumNetwork
        :return:
        """
        if not self.hash:
            raise Exception('Can not base64 encode a Request with no hash')
        if not self.signature:
            raise Exception('Can not base64 encode a Request with no signature')
        return b64encode(json.dumps({
            'signedRequest': {
                'currencyContract': self.currency_contract_address,
                # Although the parameter is called data, it is expecting the ipfs_hash.
                'data': self.ipfs_hash,
                'expectedAmounts': [a for a in self.amounts],
                'expirationDate': self.expiration_date,
                'hash': self.hash,
                'payeesIdAddress': self.id_addresses,
                'payeesPaymentAddress': [
                    None if a == EMPTY_BYTES_20 else a for a in self.payment_addresses],
                'signature': self.signature
            },
            'callbackUrl': callback_url,
            'networkId': ethereum_network_id
        }).encode('utf-8')).decode()

    def get_payment_gateway_url(self, callback_url, ethereum_network_id):
        return '{}{}'.format(
            PAYMENT_GATEWAY_BASE_URL,
            self.as_base64(callback_url, ethereum_network_id)
        )

    def write_qr_code(self, f, callback_url, ethereum_network_id, pyqrcode_kwargs=None):
        """ Generate a QR code containing a URL to pay this Request via the payment gateway, and
            write it to file-like object `f`.
        """
        url = self.get_payment_gateway_url(
            callback_url=callback_url,
            ethereum_network_id=ethereum_network_id)
        kwargs = pyqrcode_kwargs if pyqrcode_kwargs else {}
        # Use 2 as the default scale. Request's URLs are quite long so they result in
        # pixel-dense QR codes.
        kwargs['scale'] = 2 if 'scale' not in kwargs else kwargs['scale']

        qr_code = pyqrcode.create(url)
        qr_code.png(f, **kwargs)
        f.seek(0)

    def get_qr_code_data_uri(self, callback_url, ethereum_network_id, pyqrcode_kwargs=None):
        """ Return a link to the payment gateway as a data URI, suitable for inclusion in an
            <img> tag.

        """
        # TODO remove this and other QR code function, give example in docs.
        # no point including png/pyqrcode for a function that is only a few lines
        with TemporaryFile() as f:
            self.write_qr_code(f, callback_url, ethereum_network_id, pyqrcode_kwargs)
            encoded_uri = b64encode(f.read())

        mime = "text/png;"
        return "data:%sbase64,%s" % (mime, encoded_uri.decode())
