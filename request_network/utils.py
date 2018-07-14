import json
import os

from eth_utils import (
    add_0x_prefix,
    remove_0x_prefix,
)
import ipfsapi
from web3 import Web3
from web3.auto import (
    w3,
)
from web3.utils.abi import (
    map_abi_data,
)
from web3.utils.encoding import (
    hex_encode_abi_type,
)
from web3.utils.normalizers import (
    abi_ens_resolver,
)

from request_network.constants import (
    EMPTY_BYTES_20,
)
from request_network.currencies import (
    ERC20Currency,
)
from request_network.exceptions import (
    IPFSConnectionFailed,
    UnsupportedCurrency,
)


def get_ipfs():
    ipfs_args = {
        'host': os.environ.get('IPFS_NODE_HOST', 'localhost'),
        'port': os.environ.get('IPFS_NODE_PORT', 5001)
    }
    try:
        ipfs = ipfsapi.connect(**ipfs_args)
    except ipfsapi.exceptions.ConnectionError:
        raise IPFSConnectionFailed(
            'Could not connect to IPFS node on {host}:{port}'.format(**ipfs_args)
        )
    return ipfs


def store_ipfs_data(data):
    """ Store the given data as a JSON file on IPFS. Returns the IPFS hash
    """
    ipfs = get_ipfs()
    return ipfs.add_json(data)


def retrieve_ipfs_data(ipfs_hash):
    """ Retrieves the data stored at the given hash.
    """
    ipfs = get_ipfs()
    return json.loads(ipfs.cat(ipfs_hash))


def get_request_bytes_representation(payee_id_addresses, amounts, payer, ipfs_hash=None):
    """ Return the bytes representation of the given Request data.

        The JS version uses lower-cased addresses but web3.py expects checksum
        addresses. To work around this the encoded result is converted to lowercase.

        address(creator)
        address(payer)
        uint8(number_of_payees)
        [
            address(main_payee_address)
            int256(main_payee_expected_amount)
            address(second_payee_address)
            int256(second_payee_expected_amount)
            ...
        ]
        uint8(data_string_size)
        size(data)

    :return:
    """
    ipfs_hash = ipfs_hash if ipfs_hash else ''
    payer = payer if payer else EMPTY_BYTES_20

    parts = [
        (payee_id_addresses[0], 'address'),
        (payer, 'address'),
        (len(payee_id_addresses), 'uint8')
    ]

    for i in range(0, len(payee_id_addresses)):
        parts.append((payee_id_addresses[i], 'address'))
        parts.append((amounts[i], 'int256'))

    parts.append((len(ipfs_hash), 'uint8'))
    parts.append((ipfs_hash, 'string'))

    values, abi_types = zip(*parts)

    # Taken from `Web3.soliditySha3`
    normalized_values = map_abi_data([abi_ens_resolver(w3)], abi_types, values)
    return add_0x_prefix(''.join(
        remove_0x_prefix(hex_encode_abi_type(abi_type, value))
        for abi_type, value
        in zip(abi_types, normalized_values)
    )).lower()


def hash_request(currency_contract_address, id_addresses, amounts, payer,
                 payment_addresses, expiration_date, ipfs_hash=None):
    """ Compute the hash of a Request.

        Build a list of (value, abi_type) tuples representing the components
        of the Request, encode them as ABI abi_types, and hash them with `soliditySHA3`.

    :return: Hexadecimal string representing the hash of the Request
    """
    # TODO lots of duplication with bytes_request - can we call that and hash the
    # output? only difference is hash includes currency contract - is that
    # correct?
    payer = payer if payer else EMPTY_BYTES_20
    ipfs_hash = ipfs_hash if ipfs_hash else ''

    #
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


def hash_request_object(request, expiration_date=None, ignore_payer=False):
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
        payer = request.payer if request.payer else None

    return hash_request(
        currency_contract_address=request.currency_contract_address,
        id_addresses=request.id_addresses,
        amounts=request.amounts,
        payer=payer,
        payment_addresses=request.payment_addresses,
        expiration_date=expiration_date if expiration_date else request.expiration_date,
        ipfs_hash=request.ipfs_hash
    )


def get_service_for_currency(currency):
    """ Return the Request service class to use for the given currency.

    :param currency:
    :return:
    """
    from request_network.services import RequestERC20Service, RequestEthereumService

    if isinstance(currency, ERC20Currency):
        return RequestERC20Service(token_address=currency.token_address)
    elif currency.symbol == 'ETH':
        return RequestEthereumService()
    elif currency.symbol == 'BTC':
        raise NotImplementedError()
    else:
        raise UnsupportedCurrency('{} is not a supported currency'.format(currency.name))
