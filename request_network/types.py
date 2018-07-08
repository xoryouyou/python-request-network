from base64 import (
    b64encode,
)
from enum import (
    Enum,
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


class EthereumNetworks(Enum):
    main = (1, )
    rinkeby = (4, )
    private = (99, )

    def __init__(self, network_id):
        self.network_id = network_id

    def __repr__(self):
        return self.name


class Payment(object):
    payee_index = None
    delta_amount = None

    def __init__(self, payee_index, delta_amount):
        self.payee_index = payee_index
        self.delta_amount = delta_amount


class Payee(object):
    id_address = None
    payment_address = None
    amount = None

    def __init__(self, id_address, payment_address, amount):
        if payment_address:
            payment_address = Web3.toChecksumAddress(payment_address)
        else:
            # TODO should be using None here?
            payment_address = EMPTY_BYTES_20
        self.id_address = Web3.toChecksumAddress(id_address)
        self.payment_address = payment_address
        self.amount = amount


# TODO need to rethink this class. What is the best canonical representation?
class Request(object):
    id = None
    creator = None
    currency_contract_address = None
    ipfs_hash = None
    data = None
    payer = None
    payee = None
    state = None
    sub_payees = None

    id_addresses = None
    payment_address = None
    amounts = None
    expiration_date = None
    signature = None
    hash = None
    payments = None

    def __init__(self, currency_contract_address, ipfs_hash, data, payer,
                 payee, sub_payees,
                 _id=None, creator=None, state=None,
                 expiration_date=None, signature=None, _hash=None,
                 payments=None):
        """ This object stores the Request in the format described in request.js, which
            closely mirrors the data format of the smart contract.

            In many cases we want a slightly different object, where instead of having e.g.
            separate payee and sub_payee fields, we have a combined list of id_addresses.

            As a convenience those fields are derived from the given values and stored
            on the object, although that makes the interface slightly different to the
            JS version.

            :type payments: [request_network.types.Payment]
        """
        self.id = _id,
        self.creator = creator
        self.currency_contract_address = currency_contract_address
        self.ipfs_hash = ipfs_hash
        self.data = data
        self.payer = payer
        self.payee = payee
        self.state = state
        self.sub_payees = sub_payees
        self.expiration_date = expiration_date
        self.signature = signature
        self.hash = _hash
        self.payments = payments if payments else []

        sub_payee_amounts = [str(s['amount']) for s in sub_payees]
        sub_payee_id_addresses = [s['id_address'] for s in sub_payees]
        sub_payee_payment_addresses = [s['payment_address']
                                       if s['payment_address'] else EMPTY_BYTES_20
                                       for s in sub_payees]
        self.id_addresses = [self.payee['id_address'], *sub_payee_id_addresses]
        self.payment_addresses = [self.payee['payment_address'], *sub_payee_payment_addresses]
        self.amounts = [str(self.payee['amount']), *sub_payee_amounts]

    def as_base64(self, callback_url, ethereum_network):
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
            'networkId': ethereum_network.network_id
        }).encode('utf-8')).decode()

    def write_qr_code(self, f, callback_url, ethereum_network, pyqrcode_kwargs=None):
        """ Generate a QR code containing a URL to pay this Request via the payment gateway, and
            write it to file-like object `f`.
        """
        url = '{}{}'.format(
            PAYMENT_GATEWAY_BASE_URL,
            self.as_base64(callback_url, ethereum_network)
        )
        kwargs = pyqrcode_kwargs if pyqrcode_kwargs else {}
        # Use 2 as the default scale. Request's URLs are quite long so they result in
        # pixel-dense QR codes.
        kwargs['scale'] = 2 if 'scale' not in kwargs else kwargs['scale']

        qr_code = pyqrcode.create(url)
        qr_code.png(f, **kwargs)
        f.seek(0)

    def get_qr_code_data_uri(self, callback_url, ethereum_network, pyqrcode_kwargs=None):
        """ Return a link to the payment gateway as a data URI, suitable for inclusion in an
            <img> tag.

        """
        with TemporaryFile() as f:
            self.write_qr_code(f, callback_url, ethereum_network, pyqrcode_kwargs)
            encoded_uri = b64encode(f.read())

        mime = "text/png;"
        return "data:%sbase64,%s" % (mime, encoded_uri.decode())

    def is_paid(self):
        """ Naive implementation to see if a Request has been paid. Does not take into account
            modifications (subtractions/additions). Assumes entire amount was paid at once.

        :return: True if the Request has been fully paid.
        """
        paid_amounts = [p.delta_amount for p in self.payments]
        if self.amounts == paid_amounts:
            return True
        else:
            return False
