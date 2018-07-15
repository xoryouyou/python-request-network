Testing
=======

Basic test cases can be found in the :code-block:`tests` directory, separated into
 unit tests, RequestNetwork.js integration tests, and Rinkeby integration tests.

At present these are more like smoke tests, and will be replaced with a full test
suite which mirrors that of RequestNetwork.js.

Tests in :code-block:`integration` assume the Request Network smart contracts have
been deployed to the addresses described in :code-block:`artifacts.json`. If working
with a private Ethereum network this assumes the contracts have been deployed to a
freshly-started Ganache instance.

In addition tests in :code-block:`integration/request_network` assume the
RequestNetwork.js test suite has been successfully executed. This is because the
integration tests retrieve Requests/transactions that were created by running the
JavaScript library's tests. The goal is to ensure compatibility between library
versions.