Scripts
==========

Utility scripts to work with Request Network from the command line.

See the :ref:`Configuration <configuration>` section for required environment variables.

.. contents:: :local:

request-network-qr-code
-----------------------

Generate a Request and save the QR code to a file.

.. code-block:: bash

    $ request-network-qr-code --payee 0x821aea9a577a9b44299b9c15c88cf3087f3b5544 \
        --amount 0.01  \
        --output-file test.png \
        --callback-url http://example.com \
        --network main

    Generating signed Request and QR code
    Payee: 0x821aEa9a577a9b44299B9c15c88cf3087F3b5544
    Amount:  0.01 ETH (10000000000000000 Wei)
    Expiration: 2018-07-06 19:38:01
    Ethereum network name: main (ID: 1)
    Callback URL: http://example.com
    QR code written to test.png
