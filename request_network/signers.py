import os

from web3.auto import (
    w3,
)


def private_key_environment_variable_signer(message_hash, address):
    """ Sign a message hash using a private key stored in an environment variable.
    """
    # TODO raise ImproperlyConfigured exception if key not set

    private_key = os.environ['REQUEST_NETWORK_PRIVATE_KEY_{}'.format(address)]
    return w3.eth.account.signHash(message_hash, private_key)
