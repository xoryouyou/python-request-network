from web3 import Web3

from request_network.services.core import (
    RequestCoreService,
)
from request_network.utils import (
    get_request_bytes_representation,
)


class RequestEthereumService(RequestCoreService):

    def get_currency_contract_artifact_name(self):
        return 'last-RequestEthereum'

    def broadcast_signed_request_as_payer(self, signed_request, creation_payments=None,
                                          additional_payments=None, options=None):
        """

        :param signed_request:
        :type signed_request: request_network.types.Request
        :param creation_payments:
        :param additional_payments:
        :param options:
        :return:
        """
        # TODO validate request signature, other params

        # In case we do not have creation_payments/additional_payments, generate a list
        # of 0s of the same size as payees
        empty_payments = [0] * len(signed_request.payees)
        creation_payments = creation_payments if creation_payments else empty_payments
        additional_payments = additional_payments if additional_payments else empty_payments

        currency_contract_data = self.get_currency_contract_data()
        currency_contract = currency_contract_data['instance']
        estimated_value = currency_contract.functions.collectEstimation(
            _expectedAmount=sum(a for a in signed_request.amounts)
        ).call()

        transaction_options = {
            'from': Web3.toChecksumAddress('0x627306090abab3a6e1400e9345bc60c78a8bef57'),
            # TODO should the value also include additionals?
            'value': estimated_value + sum(creation_payments),
            # 'gas': 90000000
        }
        request_bytes = get_request_bytes_representation(
            payee_id_addresses=signed_request.id_addresses,
            amounts=signed_request.amounts,
            payer=None,
            ipfs_hash=signed_request.ipfs_hash
        )

        # TODO almost working, up to here... tx is failing with revert, not yet sure why.
        tx_hash = currency_contract.functions.broadcastSignedRequestAsPayer(
            _requestData=Web3.toBytes(hexstr=request_bytes),
            _payeesPaymentAddress=signed_request.payment_addresses,
            _payeeAmounts=creation_payments,
            _additionals=additional_payments,
            _expirationDate=signed_request.expiration_date,
            _signature=Web3.toBytes(hexstr=signed_request.signature)
        ).transact(transaction_options)

        return Web3.toHex(tx_hash)
