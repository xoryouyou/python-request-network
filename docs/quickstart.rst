Quickstart
==========

.. contents:: :local:

Installation
------------

.. code-block:: shell

    $ pip install request-network

.. _configuration:

Configuration
-------------

Web3
~~~~

Web3py is configured using
`automatic provider detection <http://web3py.readthedocs.io/en/stable/providers.html#automatic-provider-detection>`_.


For example, to use an Infura node connected to the Rinkeby test net:

.. code-block:: bash

    export WEB3_PROVIDER_URI=https://rinkeby.infura.io/your-api-key

IPFS
~~~~

The IPFS RPC node's hostname and port are stored in the :code:`IPFS_NODE_HOST` and :code:`IPFS_NODE_PORT` environment variables.

.. code-block:: bash

    export IPFS_NODE_HOST="https://ipfs.infura.io"

The IPFS node is only used when storing or retrieving a Request's optional JSON data.

Request Network
~~~~~~~~~~~~~~~

The :code:`REQUEST_NETWORK_ETHEREUM_NETWORK_NAME` variable specifies the friendly name of the Ethereum network
to use, e.g. "main", "rinkeby", or "private". This is used when looking up Request Network
artifacts (i.e. deployed smart contracts).

:code:`REQUEST_NETWORK_ARTIFACT_DIRECTORY` specifies the directory from which smart contract artifacts
are loaded. Most users will not need to change this - the default is to load the artifacts which are
distributed with this library.

Signing Messages with Local Private Keys
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Private keys are stored in environment variables, where the address is part of the environment variable name.

For example the private key for address :code:`0x123` would be stored in the
:code:`REQUEST_NETWORK_PRIVATE_KEY_0x123` environment variable.

Note that the address used in the environment variable must be checksummed (i.e. not all in lower-case).
:code:`Web3.toChecksumAddress()` can be used to correctly format an address.

In future the signing mechanism will be extended to make it configurable, providing support for
use cases such as signing messages with a separate signing microservice.

Creating a Signed Request
-------------------------

The Request online payments app
provides a gateway for displaying the parameters of a signed Request and allowing it to be paid
(`example <https://app.request.network/#/pay-with-request/eyJzaWduZWRSZXF1ZXN0IjogeyJjdXJyZW5jeUNvbnRyYWN0IjogIjB4ZDg4YWI5YjE2OTEzNDBFMDRhNUJCZjc4NTI5YzExZDU5MmQzNWY1NyIsICJkYXRhIjogIiIsICJleHBlY3RlZEFtb3VudHMiOiBbIjEwMDAwMDAwMDAwMDAwMDAwMDAiXSwgImV4cGlyYXRpb25EYXRlIjogMTUzMDc5MDMzNiwgImhhc2giOiAiMHhlYTdiNTY1NmQ5YjQyN2U5NmY3NmE0MTQ4ZTU3ZjRhZmVlN2JjMjc4ZDU2MTkwODU3YWI4OTg2ZjgyZDU1N2JhIiwgInBheWVlc0lkQWRkcmVzcyI6IFsiMHg4MjFhRWE5YTU3N2E5YjQ0Mjk5QjljMTVjODhjZjMwODdGM2I1NTQ0Il0sICJwYXllZXNQYXltZW50QWRkcmVzcyI6IFtudWxsXSwgInNpZ25hdHVyZSI6ICIweGY0MDI1MzNkYTZjMWU4YjZhMGI4YmE1NjU5YjE3MzIyODQ3NDk4N2E0NjA4NDlmMmZjNzRjNzE5ZTQyNmUxNmQ2NjM0NWM3MjI3MTAwYmY5YzQ3NzQ0N2Q3ZDUwYjJiOGMyNjJiMDQ0MGNhZTBlZmE1YmU2Mjk5ZWNjMzI2ZTkzMWIifSwgImNhbGxiYWNrVXJsIjogImh0dHBzOi8vZXhhbXBsZS5jb20vcmVxdWVzdC1jYWxsYmFjay8iLCAibmV0d29ya0lkIjogNH0>`_).
The `documentation <https://docs.request.network/development/guides/online-payments>`_ describes
the payment flow in more detail.

The gateway expects to receive the signed Request as base64-encoded JSON.

Once the Request has been accepted and paid, or if the user decides to cancel the Request, they
will be returned to the :code:`callback_url`.

If the Request was accepted and paid the URL will be suffixed with the transaction hash. If the
Request was cancelled the suffix will be the JSON-encoded Request data.

A full example of creating a signed Request and verifying that it has been paid is shown below.

First set the environment variables required to sign and validate the Request. Because the request
does not contain any extra data we do not need to configure IPFS.

.. code-block:: bash

    export REQUEST_NETWORK_ETHEREUM_NETWORK_NAME=rinkeby
    export WEB3_PROVIDER_URI=https://rinkeby.infura.io/your-api-key
    # This key is already publicly exposed in various documentation online.
    export REQUEST_NETWORK_PRIVATE_KEY_0x821aEa9a577a9b44299B9c15c88cf3087F3b5544=c88b703fb08cbea894b6aeff5a544fb92e78a18e19814cd85da83b71f772aa6c


.. code-block:: python

    from time import time
    from web3.auto import w3
    from web3.middleware import geth_poa_middleware

    from request_network.api import RequestNetwork
    from request_network import types
    from request_network.currencies import currencies_by_symbol

    # Inject the POA middleware so we can work with Rinkeby
    from request_network.utils import hash_request_object

    w3.middleware_stack.inject(geth_poa_middleware, layer=0)

    request_api = RequestNetwork()

    # Generate a Request which will send 0.0001 ETH to the recipient
    payee = types.Payee(
        id_address='0x821aea9a577a9b44299b9c15c88cf3087f3b5544',
        payment_address=None,
        amount=int(0.0001 * 10 ** 18)  # 0.0001 ETH in Wei
    )

    # Generate the signed Request data
    signed_request = request_api.create_signed_request(
        role=types.Roles.PAYEE,
        currency=currencies_by_symbol['ETH'],
        payees=[payee],
        expiration_date=int(time()) + 3600  # Expire one hour in the future
    )

    # Redirect the user to the following URL -
    payment_url = 'https://app.request.network/#/pay-with-request/' + signed_request.as_base64(
        callback_url='https://example.com/request-callback/',
        ethereum_network_id=4  # Rinkeby
    )

    # Later, after the user has paid the Request
    transaction_hash = '0xf9d484e56c038055e78344c9fa082e4bae640c7fde5d5063e6c394be20ceebd0'
    request = request_api.get_request_by_transaction_hash(transaction_hash)

    # Make sure the Request we retrieved from the blockchain matches the one we created earlier
    retrieved_hash = hash_request_object(
        request,
        ignore_payer=True,
        expiration_date=signed_request.expiration_date)
    stored_hash = hash_request_object(signed_request)
    assert retrieved_hash == stored_hash

    # Check if the Request has been fully paid. This is a naive implementation - see code for details
    if request.is_paid:
        print('The Request has been paid')


Note that calling :code:`RequestNetwork.create_signed_request()` with a :code:`data` parameter will write
the data to IPFS.

For web developers: this also means that calling the function is too slow to do within the
request/response cycle, so it should be done in an asynchronous task.

Depending on the use case it might be feasible to pre-generate signed Requests. For example if each
order consists of a single product and users can be identified by their Ethereum addresses,
a signed Request can be generated for each product in advance, as the same data can be used for
multiple Requests.

If the Request needs to contain order-specific information (such as a unique
order or product identifier) the data will vary between Requests. In this case a new Request must
be generated and signed for each order.

Payment Gateway Integration
---------------------------

The Request object provides some convenience methods for simplifying integration with the
payment gateway.

Once a Request has been signed the URL for paying it can be retrieved with:

.. code-block:: python

    payment_url = request.get_payment_gateway_url(
        callback_url='https://example.com/request-callback/',
        ethereum_network_id=4
    )

It is also possible to retrieve a QR code containing a link to the payment gateway.

.. figure:: data:text/png;base64,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
    :align: center

    Example QR code representing a Request to pay three payees on the Rinkeby test net.

The QR code can be written to a file-like object:

.. code-block:: python

    with open('qr_code.png', 'wb') as f:
        signed_request.write_qr_code(
            f,
            callback_url='https://example.com/request-callback/',
            ethereum_network_id=4
        )

... or retrieved as data URI image, ready for use in an HTML `<img>` tag as shown above:

.. code-block:: python

    data_uri = signed_request.get_qr_code_data_uri(
        callback_url='https://example.com/request-callback/',
        ethereum_network_id=4
    )
    print('<img src="{}">'.format(data_uri))


The last two functions both accept an optional :code:`pyqrcode_kwargs` dict which is passed through to
`pyqrcode <https://github.com/mnooner256/pyqrcode>`_'s :code:`png()` function to control how the PNG is generated.