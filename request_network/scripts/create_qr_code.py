import argparse
import datetime
import os
import time

from web3 import Web3

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


def main():
    parser = argparse.ArgumentParser(
        description='Create a signed Request and save it as a QR code in a PNG image.')
    parser.add_argument('--payee', type=str, required=True,
                        help='Ethereum address which will receive the payment')
    parser.add_argument('--amount', type=float, required=True,
                        help='The payment amount in ETH')
    parser.add_argument('--output-file', type=str, required=True,
                        help='Output filename')
    parser.add_argument('--callback-url', type=str, required=True,
                        help='Callback URL')
    parser.add_argument('--network-id', type=str, required=True,
                        help='Ethereum network ID, e.g. 1 for "main" or 4 for "rinkeby"')
    parser.add_argument('--expiration', type=int,
                        default=3600,
                        help='The number of seconds after which this Request expires')

    args = parser.parse_args()
    if os.path.exists(args.output_file):
        raise Exception('{} already exists'.format(args.output_file))
    expiration_timestamp = int(time.time()) + (args.expiration if args.expiration else 3600)

    # Use format to get a string instead of a number in scientific notation
    amount_in_wei = format(args.amount * (10 ** 18), '.0f')
    payee = Payee(
        id_address=Web3.toChecksumAddress(args.payee),
        amount=amount_in_wei,
        payment_address=None
    )

    print('Generating signed Request and QR code')
    print('Payee: {}'.format(payee.id_address))
    print('Amount:  {} ETH ({} Wei)'.format(args.amount, amount_in_wei))
    print('Expiration: {}'.format(
        datetime.datetime.fromtimestamp(expiration_timestamp).strftime('%Y-%m-%d %H:%M:%S')))
    print('Ethereum network name: ID: {}'.format(args.network_id))
    print('Callback URL: {}'.format(args.callback_url))

    request_api = RequestNetwork()
    signed_request = request_api.create_signed_request(
        role=Roles.PAYEE,
        currency=currencies_by_symbol['ETH'],
        payees=[payee],
        expiration_date=expiration_timestamp
    )

    with open(args.output_file, 'wb') as f:
        signed_request.write_qr_code(
            f, callback_url=args.callback_url, ethereum_network_id=args.network_id)
    print('QR code written to {}'.format(args.output_file))


if __name__ == '__main__':
    main()
