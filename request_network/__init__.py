from eth_abi import decode_abi
from eth_utils import add_0x_prefix, remove_0x_prefix, event_abi_to_log_topic
from web3 import Web3
from web3.auto import w3
from web3.utils.abi import map_abi_data
from web3.utils.contracts import find_matching_event_abi
from web3.utils.encoding import hex_encode_abi_type
from web3.utils.normalizers import abi_ens_resolver

from request_network.artifact_manager import ArtifactManager
from request_network.constants import EMPTY_BYTES_20
from request_network.currencies import ERC20Currency
from request_network.exceptions import UnsupportedCurrency, RequestNotFound, TransactionNotFound
from request_network.services import RequestERC20Service, RequestEthereumService
from request_network.types import Roles, Payment, Request


class RequestNetwork(object):
    """ The main interaction point with the Request Network API.
    """
    ethereum_network = None

    def __init__(self, ethereum_network=None):
        """
        :param ethereum_network: The Ethereum network to interact with
        :type ethereum_network: request_network.types.EthereumNetwork
        """
        self.ethereum_network = ethereum_network

    def create_signed_request(self, role, currency, payees,
                              expiration_date, data=None, request_options=None):
        """ Create a signed Request instance

        :param role: Role of the signer - payer or payee (currently only payee is supported)
        :type role: types.Roles.PAYEE
        :param currency: The currency in which payment will be made
        :type currency: currency.Currency
        :param payees: Array of Payee objects
        :type payees: [types.Payee]
        :param expiration_date: Unix timestamp after which Request can no longer be broadcast
        :param request_options: Dictionary of options (not supported)
        :return: A Request instance
        :rtype: request_network.types.Request
        """
        # TODO should this function accept a Request object? Means we can do all of the validation
        # the object.

        if role != Roles.PAYEE:
            raise NotImplementedError('Signing Requests as the payer is not yet supported')

        if request_options:
            # TODO implement request options
            raise NotImplementedError()

        service_args = {
            'id_addresses': [payee.id_address for payee in payees],
            'payment_addresses': [payee.payment_address for payee in payees],
            'amounts': [payee.amount for payee in payees],
            'expiration_date': expiration_date,
            'data': data
        }
        if isinstance(currency, ERC20Currency):
            service = RequestERC20Service(request_api=self, token_address=currency.token_address)
        elif currency.symbol == 'ETH':
            service = RequestEthereumService(request_api=self)
        elif currency.symbol == 'BTC':
            raise NotImplementedError()
        else:
            raise UnsupportedCurrency('{} is not a supported currency'.format(currency.name))

        return service.sign_request_as_payee(**service_args)

    def hash_request(self, currency_contract_address, id_addresses, amounts, payer,
                     payment_addresses, expiration_date, ipfs_hash=None):
        """ Compute the hash of a Request.

            Build a list of (value, abi_type) tuples representing the components
            of the Request, encode them as ABI abi_types, and hash them with `soliditySHA3`.

        :return: Hexadecimal string representing the hash of the Request
        """
        if not payer:
            payer = EMPTY_BYTES_20
        if not ipfs_hash:
            ipfs_hash = ''

        parts = [
            (currency_contract_address, 'address'),
            (id_addresses[0], 'address'),
            (payer, 'address'),
            (len(id_addresses), 'uint8')
        ]

        for i in range(len(id_addresses)):
            parts.append((id_addresses[i], 'address'))
            parts.append((int(amounts[i]), 'int256'))

        parts.append((len(ipfs_hash), 'uint8'))
        parts.append((ipfs_hash, 'string'))

        parts.append((payment_addresses, 'address[]'))
        parts.append((int(expiration_date), 'uint256'))

        values, abi_types = zip(*parts)
        return Web3.toHex(Web3.soliditySha3(abi_types, values))

    def hash_request_object(self, request, expiration_date=None, ignore_payer=False):
        """ Compute the hash of a Request object.

            One use of this function is to compare a Request that was generated and signed to
            one that was retrieved from the blockchain with `get_request_by_id()`.

            The generated Request will have an `expiration_date` but no `payer`.
            A retrieved Request will have a `payer` but no `expiration_date`.

            This results in different hashes for Requests that actually match. To work around
            this the `payer` field can be ignored and an `expiration_date` explicitly added
            before the object is hashed.

        :type request: request_network.types.Request
        :return: Hexadecimal string representing the hash of the Request
        """
        if ignore_payer:
            payer = None
        else:
            payer = request.payer['address'] if request.payer else None

        return self.hash_request(
            currency_contract_address=request.currency_contract_address,
            id_addresses=request.id_addresses,
            amounts=request.amounts,
            payer=payer,
            payment_addresses=request.payment_addresses,
            expiration_date=expiration_date if expiration_date else request.expiration_date,
            ipfs_hash=request.ipfs_hash
        )

    def get_request_bytes_representation(self, payees, amounts, payer, data):
        """ Return the bytes representation of the given Request data.

        :return:
        """
        if not data:
            data = ''

        parts = [
            (payees[0], 'address'),
            (payer, 'address'),
            (len(payees), 'uint8')
        ]

        for i in range(0, len(payees)):
            parts.append((payees[i], 'address'))
            parts.append((amounts[i], 'int256'))

        parts.append((len(data), 'uint8'))
        parts.append((data, 'string'))

        values, abi_types = zip(*parts)

        # Taken from `Web3.soliditySha3`
        normalized_values = map_abi_data([abi_ens_resolver(w3)], abi_types, values)
        return add_0x_prefix(''.join(
            remove_0x_prefix(hex_encode_abi_type(abi_type, value))
            for abi_type, value
            in zip(abi_types, normalized_values)
        ))

    def get_request_by_id(self, request_id, block_number=None):
        """ Get a Request from its request_id.

        :param request_id: 32 byte hex string
        :param block_number: If provided, only search for Created events from this block onwards.
        :return: A Request instance
        :rtype: request_network.types.Request
        """
        core_contract_address = Web3.toChecksumAddress(request_id[:42])
        am = ArtifactManager(ethereum_network=self.ethereum_network)
        core_contract_data = am.get_contract_data(core_contract_address)

        core_contract = w3.eth.contract(
            address=core_contract_address,
            abi=core_contract_data['abi'])

        result = core_contract.functions.getRequest(request_id).call()
        request_data = {
            '_id': request_id,
            'payer': {
                'address': result[0]
            },
            'currency_contract_address': result[1],
            'state': result[2],
            'payee': {
                'id_address': result[3],
                'amount': result[4],
                'balance': result[5]
            },
            'payments': []
        }
        # TODO request.js uses 'creator' here, but RequestCore:getRequest does not return creator
        # Should it be payer?
        if request_data['payer'] == EMPTY_BYTES_20:
            raise RequestNotFound('Request ID {} not found on core contract {}'.format(
                request_id,
                core_contract_address
            ))

        # The smart contract stores payment addresses separately to the Request's data, so
        # we need to look those up separately.
        service_contract = am.get_contract_instance(request_data['currency_contract_address'])
        request_data['payee']['payment_address'] = \
            service_contract.functions.payeesPaymentAddress(request_id, 0).call()

        # Get sub-payees
        sub_payees_count = core_contract.functions.getSubPayeesCount(request_id).call()
        request_data['sub_payees'] = []
        for i in range(sub_payees_count):
            data = core_contract.functions.subPayees(request_id, i).call()
            request_data['sub_payees'].append({
                'id_address': data['addr'],
                'payment_address': service_contract.call().payeesPaymentAddress(request_id, i + 1),
                'balance': data['balance'],
                'amount': data['amount'],

            })

        # Get the ABI of the Created event so we can calculate the log topic
        created_logs = self.get_logs_for_request(
            request_id=request_id,
            event_name='Created',
            start_block_number=block_number if block_number else core_contract_data['block_number'],
            core_contract=core_contract)

        if len(created_logs) == 0:
            raise Exception('Could not get Created event for Request {}'.format(request_id))
        if len(created_logs) > 1:
            raise Exception('Multiple logs returned for Request {}'.format(request_id))

        tx_receipt = w3.eth.getTransactionReceipt(Web3.toHex(created_logs[0]['transactionHash']))
        rich_logs = core_contract.events.Created().processReceipt(tx_receipt)
        created_log_args = rich_logs[0]['args']
        request_data['creator'] = created_log_args['creator']
        # See if we have an IPFS hash, and get the file if so
        if created_log_args['data'] != '':
            request_data['ipfs_hash'] = created_log_args['data']
            # TODO retrieve data from IPFS
        else:
            request_data['ipfs_hash'] = None
            request_data['data'] = {}

        # Iterate through UpdateBalance events to build a list of payments made for this request
        update_balance_logs = self.get_logs_for_request(
            request_id=request_id,
            event_name='UpdateBalance',
            start_block_number=block_number if block_number else core_contract_data['block_number'],
            core_contract=core_contract)

        for log in update_balance_logs:
            tx_receipt = w3.eth.getTransactionReceipt(Web3.toHex(log['transactionHash']))
            rich_logs = core_contract.events.UpdateBalance().processReceipt(tx_receipt)
            request_data['payments'].append(Payment(
                payee_index=rich_logs[0]['args']['payeeIndex'],
                delta_amount=str(rich_logs[0]['args']['deltaAmount']))
            )

        if request_data['ipfs_hash']:
            # TODO get data from IPFS
            request_data['data'] = {'foo': 'bar'}

        return Request(**request_data)

    def get_logs_for_request(self, request_id, event_name, core_contract,
                             start_block_number, end_block_number=None):
        event = find_matching_event_abi(abi=core_contract.abi, event_name=event_name)
        # Get the Created event which was emitted when this Request was created - we do not
        # use 'latest' because it requires creating a new filter, which is not supported on Infura.
        logs = w3.eth.getLogs({
            'fromBlock': start_block_number,
            'toBlock': end_block_number if end_block_number else w3.eth.blockNumber,
            'address': [core_contract.address],
            'topics': [
                Web3.toHex(event_abi_to_log_topic(event)),
                request_id
            ]
        })

        return logs

    def get_request_by_transaction_hash(self, transaction_hash):
        """ Get a Request from an Ethereum transaction hash.

        :param transaction_hash:
        :return: A Request instance
        :rtype: request_network.types.Request
        """
        tx_data = w3.eth.getTransaction(transaction_hash)
        if not tx_data:
            raise TransactionNotFound(transaction_hash)

        am = ArtifactManager(ethereum_network=self.ethereum_network)
        currency_contract_address = tx_data['to']
        currency_contract_data = am.get_contract_data(currency_contract_address)

        currency_contract = w3.eth.contract(abi=currency_contract_data['abi'])

        # Look up the function by its signature so we can use its ABI
        function_signature = tx_data['input']
        func = currency_contract.get_function_by_selector(function_signature[:10])
        input_types = [i['type'] for i in func.abi['inputs']]
        input_names = [i['name'] for i in func.abi['inputs']]
        input_values = decode_abi(input_types, Web3.toBytes(hexstr=tx_data['input'][10:]))
        inputs = dict(zip(input_names, input_values))

        # some above code might be better in RequestNetwork object? maybe this whole function?

        # If this is a 'simple' Request we can take the ID from the transaction input.
        if '_requestId' in inputs:
            return self.get_request_by_id(inputs['_requestId'])

        # For more complex Requests (e.g. those created by broadcasting a signed Request)
        # we need to find the 'Created' event log that was emitted and take the ID from there.
        tx_receipt = w3.eth.getTransactionReceipt(transaction_hash)
        if not tx_receipt:
            raise Exception('TODO could not get tx receipt')

        # TODO safe to assume that this will always be the first log?
        core_contract_data = am.get_contract_data(tx_receipt['logs'][0]['address'])
        # Get an instance of the core contract and use it to decode the events in the tx_receipt
        core_contract = w3.eth.contract(abi=core_contract_data['abi'])
        # rich_logs contain the full decoded data emitted with the event
        rich_logs = core_contract.events.Created().processReceipt(tx_receipt)
        # The first log item contains the requestId
        # TODO confirm we can rely on this being in the first log
        event_data = rich_logs[0].args

        return self.get_request_by_id(
            Web3.toHex(event_data.requestId),
            block_number=tx_data['blockNumber'])
