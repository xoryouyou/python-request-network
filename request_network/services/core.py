import time

from eth_account.messages import (
    defunct_hash_message,
)
from web3 import Web3

from request_network.artifact_manager import (
    ArtifactManager,
)
from request_network.constants import (
    EMPTY_BYTES_20,
)
from request_network.exceptions import (
    InvalidRequestParameters,
)
from request_network.signers import (
    private_key_environment_variable_signer,
)
from request_network.types import (
    Payee,
    Request,
)
from request_network.utils import (
    hash_request,
    store_ipfs_data,
)


class RequestCoreService(object):
    """ Class for Request Core """

    def get_currency_contract_data(self):
        """ Return the currency contract for the given currency. `artifact_name` could
            be `last-RequestEthereum`, or `last-requesterc20-{token_address}`.
        """
        artifact_name = self.get_currency_contract_artifact_name()
        artifact_manager = ArtifactManager()
        contract_data = artifact_manager.get_contract_data(artifact_name)
        return contract_data

    def get_currency_contract_artifact_name(self):
        """ Return the artifact name used when looking up the currency contract.
        """
        raise NotImplementedError()

    def create_request_as_payee(self, id_addresses, amounts,
                                payment_addresses, payer_refund_address, payer_id_address,
                                data, options):
        # validate request args

        # call collectEstimation on the currency contract

        ipfs_hash = store_ipfs_data(data) if data else ''

        # TODO better validation, more DRY
        # Validate Request parameters
        if len(id_addresses) != len(amounts):
            raise InvalidRequestParameters(
                'payees and amounts must be the same size'
            )

        if payment_addresses and len(id_addresses) < len(payment_addresses):
            raise InvalidRequestParameters(
                'payees can not be larger than payee_payment_addresses'
            )

        for amount in amounts:
            if int(amount) < 0:
                raise InvalidRequestParameters(
                    'amounts must be positive integers'
                )

        for address in id_addresses + payment_addresses:
            if not Web3.isAddress(address):
                raise InvalidRequestParameters(
                    '{} is not a valid Ethereum address'.format(address)
                )

        # call fee estimator, set as value for tx
        currency_contract_data = self.get_currency_contract_data()
        currency_contract = currency_contract_data['instance']
        estimated_value = currency_contract.functions.collectEstimation(
            _expectedAmount=sum(a for a in amounts)
        ).call()

        transaction_options = {
            # TODO allow configuration of from address
            'from': id_addresses[0],
            'value': estimated_value
        }

        tx_hash = currency_contract.functions.createRequestAsPayee(
            _payeesIdAddress=id_addresses,
            _payeesPaymentAddress=payment_addresses,
            _expectedAmounts=amounts,
            _payer=payer_id_address,
            _payerRefundAddress=payer_refund_address,
            _data=ipfs_hash
        ).transact(transaction_options)
        return Web3.toHex(tx_hash)

    def create_request_as_payer(self, id_addresses, amounts,
                                payment_addresses, payer_refund_address, payer_id_address,
                                data=None,
                                creation_payments=None, additional_payments=None, options=None):
        """
        :param id_addresses:
        :param amounts:
        :param payment_addresses:
        :param payer_refund_address:
        :param payer_id_address:
        :param data:
        :param creation_payments: Amount to pay when Requst is created
        :param additional_payments: Additional amount to pay each payee, on top of expected amount
        :param options:
        :return:
        """
        # validate request
        # get collection/value estimation
        # store file in ipfs
        # call contract
        creation_payments = creation_payments if creation_payments else []
        additional_payments = additional_payments if additional_payments else []

        ipfs_hash = store_ipfs_data(data) if data else ''

        # TODO better validation, more DRY
        # Validate Request parameters
        if len(id_addresses) != len(amounts):
            raise InvalidRequestParameters(
                'payees and amounts must be the same size'
            )

        if payment_addresses and len(id_addresses) < len(payment_addresses):
            raise InvalidRequestParameters(
                'payees can not be larger than payee_payment_addresses'
            )

        if creation_payments and len(id_addresses) < len(creation_payments):
            raise InvalidRequestParameters(
                'payees can not be larger than creation_payments'
            )

        if additional_payments and len(id_addresses) < len(additional_payments):
            raise InvalidRequestParameters(
                'payees can not be larger than additional_payments'
            )

        for amount in amounts:
            if int(amount) < 0:
                raise InvalidRequestParameters(
                    'amounts must be positive integers'
                )

        for amount in creation_payments:
            if int(amount) < 0:
                raise InvalidRequestParameters(
                    'amounts must be positive integers'
                )

        for address in id_addresses + payment_addresses:
            if not Web3.isAddress(address):
                raise InvalidRequestParameters(
                    '{} is not a valid Ethereum address'.format(address)
                )

        # call fee estimator, set as value for tx
        currency_contract_data = self.get_currency_contract_data()
        currency_contract = currency_contract_data['instance']
        estimated_value = currency_contract.functions.collectEstimation(
            _expectedAmount=sum(a for a in creation_payments)
        ).call()

        transaction_options = {
            'from': payer_id_address,
            'value': estimated_value
        }

        tx_hash = currency_contract.functions.createRequestAsPayer(
            _payeesIdAddress=id_addresses,
            _expectedAmounts=amounts,
            _payerRefundAddress=payer_refund_address,
            _payeeAmounts=creation_payments,
            _additionals=additional_payments,
            _data=ipfs_hash
        ).transact(transaction_options)
        return Web3.toHex(tx_hash)

    def create_signed_request(self, currency_contract_address, id_addresses, amounts,
                              payment_addresses, expiration_date,
                              data=None):
        """ Return the signed request object.

        TODO this only supports creating the Request as the payee.

        :param currency_contract_address:
        :param id_addresses:
        :param amounts:
        :param expiration_date:
        :param payment_addresses:
        :param data: Additional data to store with the Request
        :return:
        """
        # If we have data, store it on IPFS
        ipfs_hash = store_ipfs_data(data) if data else ''

        request_hash = hash_request(
            currency_contract_address=currency_contract_address,
            id_addresses=id_addresses,
            amounts=amounts,
            payer=None,
            expiration_date=expiration_date,
            payment_addresses=payment_addresses,
            ipfs_hash=ipfs_hash)

        # `defunct_hash_message` is used to maintain compatibility with `web3Single.sign()`
        message_hash = defunct_hash_message(hexstr=request_hash)
        # TODO make signing strategy configurable
        # TODO signer should accept an optional dict describing the Request attributes so
        # it can perform enforce controls (rate-limiting, max Request amount, etc.)
        signer_function = private_key_environment_variable_signer
        signed_message = signer_function(
            message_hash=message_hash,
            address=id_addresses[0]
        )

        # Combine id_addresses/payment_addresses/amounts into a list of Payees
        payees = []
        for id_address, payment_address, amount in zip(id_addresses, payment_addresses, amounts):
            payees.append(Payee(
                id_address=id_address,
                payment_address=payment_address,
                amount=amount))

        request = Request(
            payees=payees,
            _hash=request_hash,
            currency_contract_address=currency_contract_address,
            ipfs_hash=ipfs_hash,
            data=data,
            payer=None,
            expiration_date=expiration_date,
            signature=Web3.toHex(signed_message.signature)
        )

        return request

    def sign_request_as_payee(self, id_addresses, amounts,
                              payment_addresses, expiration_date,
                              data=None):
        """ Sign a Request as the payee.

        :param id_addresses:
        :param amounts:
        :param expiration_date:
        :param payment_addresses:
        :param data:
        :return:
        """
        # Iterate through payee addresses - if a None value is given for any address,
        # replace it with the 0x0 address (padded to 20 bytes).
        parsed_payee_payment_addresses = [
            Web3.toChecksumAddress(a) if a else EMPTY_BYTES_20 for a in payment_addresses
        ]
        id_addresses = [
            Web3.toChecksumAddress(a) for a in id_addresses
        ]

        # Validate Request parameters
        if len(id_addresses) != len(amounts):
            raise InvalidRequestParameters(
                'payees and amounts must be the same size'
            )

        if payment_addresses and len(id_addresses) < len(payment_addresses):
            raise InvalidRequestParameters(
                'payees can not be larger than payee_payment_addresses'
            )

        if int(expiration_date) <= int(time.time()):
            raise InvalidRequestParameters(
                'expiration_date must be in the future'
            )

        for amount in amounts:
            if int(amount) < 0:
                raise InvalidRequestParameters(
                    'amounts must be positive integers'
                )

        for address in id_addresses:
            if not Web3.isAddress(address):
                raise InvalidRequestParameters(
                    '{} is not a valid Ethereum address'.format(address)
                )

        currency_contract_data = self.get_currency_contract_data()
        return self.create_signed_request(
            currency_contract_address=currency_contract_data['address'],
            id_addresses=id_addresses,
            amounts=amounts,
            payment_addresses=parsed_payee_payment_addresses,
            expiration_date=expiration_date,
            data=data
        )
