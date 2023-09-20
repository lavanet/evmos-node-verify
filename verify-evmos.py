import argparse
from urllib.request import urlopen, Request
import json

PRUNING = 50000

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"}

POST_HEADERS = {
    'Content-Type': 'application/json'
}
POST_HEADERS.update(HEADERS)

MAINNET = {
    'chain-id': "evmos_9001-2",
    'tx-indexing': 'on',
    "eth": {
        'chain-id': '0x2329',
        'net-version': '9001',
    }
}

TESTNET = {
    'chain-id': "evmos_9000-4",
    'tx-indexing': 'on',
    "eth": {
        'chain-id': '0x2328',
        'net-version': '9000',
    }
}


def test_rest_earliest_block(base_url, test_values):
    rest_url = f'{base_url}/cosmos/base/tendermint/v1beta1/blocks/latest'
    httprequest = Request(rest_url, headers=HEADERS)
    with urlopen(httprequest) as response:
        if response.status != 200:
            print('ERROR: Pruning verification: failed getting latest block from rest api')
            return
        info = response.read().decode()
        latest_block = json.loads(info)

    height = int(latest_block['block']['header']['height'])
    earliest = height-PRUNING
    rest_url = f'{base_url}/cosmos/base/tendermint/v1beta1/blocks/{earliest}'
    httprequest = Request(rest_url, headers=HEADERS)
    with urlopen(httprequest) as response:
        if response.status != 200:
            print('ERROR: Pruning verification: failed getting earliest block from rest api')
            return
        result = response.read().decode()
        result = json.loads(result)
        if ('block' not in result
                or 'header' not in result['block']
                or 'height' not in result['block']['header']
                or int(result['block']['header']['height']) != earliest):
            print(f"ERROR: Pruning verification failed: expected to have default pruning of 100 blocks")
            return
    print("PASSED Pruning verification")


def test_rest_general_info(base_url, test_values):
    rest_url = f"{base_url}/cosmos/base/tendermint/v1beta1/node_info"
    httprequest = Request(rest_url, headers=HEADERS)
    with urlopen(httprequest) as response:
        if response.status != 200:
            print('ERROR: failed getting node_info from rest api')
            return
        info = response.read().decode()
        info = json.loads(info)
        if info['default_node_info']['network'] != test_values['chain-id']:
            print(f"ERROR: Chain ID verification failed: expected: {test_values['chain-id'].lower()}, got: {info['default_node_info']['network'].lower()}")
        else:
            print("PASSED Chain ID verification")
        if info["default_node_info"]['other']['tx_index'].lower() != test_values['tx-indexing'].lower():
            print(f"ERROR: TX indexing verification failed: expected: {test_values['tx-indexing']}, got: {info['default_node_info']['other']['tx_index']}")
        else:
            print("PASSED TX indexing verification")


def test_tendermint_rpc_info(base_url, test_values):
    url = f"{base_url}/status"
    httprequest = Request(url, headers=HEADERS)
    with urlopen(httprequest) as response:
        if response.status != 200:
            print('ERROR: failed getting node_info from rest api')
            return
        status = response.read().decode()
        status = json.loads(status)['result']
        node_info = status['node_info']

        if node_info['network'] != test_values['chain-id']:
            print(f"ERROR: Chain ID verification failed: expected: {test_values['chain-id'].lower()}, got: {status['node_info']['network'].lower()}")
        else:
            print("PASSED Chain ID verification")
        if node_info['other']['tx_index'].lower() != test_values['tx-indexing'].lower():
            print(f"ERROR: TX indexing verification failed: expected: {test_values['tx-indexing']}, got: {status['node_info']['other']['tx_index']}")
        else:
            print("PASSED TX indexing verification")

        earliest = int(status['sync_info']['earliest_block_height'])
        latest = int(status['sync_info']['latest_block_height'])
        if status['sync_info']['catching_up']:
            print("ERROR: Your node is still catching up")
            return

        if latest - earliest >= PRUNING:
            print("PASSED Pruning verification")
        else:
            print(f"ERROR: Pruning verification failed: expected to have default pruning of 100 blocks, got: {latest-earliest}, latest {latest}, earliest {earliest}")


def test_eth_chain_id(base_url, test_values):
    url = f"{base_url}"
    httprequest = Request(url,
                          json.dumps({"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1}).encode('utf-8'),
                          headers=POST_HEADERS,
                          method='POST')
    with urlopen(httprequest) as response:
        if response.status != 200:
            print('ERROR: failed getting node_info from rest api')
            return
        result = response.read().decode()
        result = json.loads(result)['result']

        if result == test_values['eth']['chain-id']:
            print("PASSED chain-id verification")
        else:
            print(f"ERROR: chain-id verification failed: got {result} expected {test_values['eth']['chain-id']}")


def test_eth_pruning(base_url, test_values):
    url = f"{base_url}"
    httprequest = Request(url,
                          json.dumps({"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}).encode('utf-8'),
                          headers=POST_HEADERS,
                          method='POST')

    with urlopen(httprequest) as response:
        if response.status != 200:
            print('ERROR: failed getting node_info from rest api')
            return
        result = response.read().decode()
        latest_block = json.loads(result)['result']
        latest_block = int(latest_block, 16)
    httprequest = Request(url,
                          json.dumps({"jsonrpc": "2.0", "method": "eth_getBlockByNumber",
                                      "params": [hex(latest_block - PRUNING), False], "id": 1}).encode('utf-8'),
                          headers=POST_HEADERS,
                          method='POST')

    with urlopen(httprequest) as response:
        if response.status != 200:
            print('ERROR: failed getting node_info from rest api')
            return
        result = response.read().decode()
        earliest = json.loads(result)['result']
        if 'number' in earliest:
            print('PASSED Pruning verification')
        else:
            print(f'Failed Pruning verification, could not fetch block height {latest_block-PRUNING}')


def test_eth_net_api_set(base_url, test_values):
    url = f"{base_url}"
    httprequest = Request(url,
                          json.dumps({"jsonrpc": "2.0", "method": "net_version", "params": [], "id": 1}).encode('utf-8'),
                          headers=POST_HEADERS,
                          method='POST')
    with urlopen(httprequest) as response:
        if response.status != 200:
            print('ERROR: failed getting node_info from rest api')
            return
        result = response.read().decode()
        result = json.loads(result)['result']

        if result == test_values['eth']['net-version']:
            print("PASSED net apis are enabled")
        else:
            print(f"ERROR: net api verification failed: api should be enabled")


def test_web3_api_set(base_url, test_values):
    url = f"{base_url}"
    httprequest = Request(url,
                          json.dumps({"jsonrpc": "2.0", "method": "web3_clientVersion", "params": [], "id": 1}).encode('utf-8'),
                          headers=POST_HEADERS,
                          method='POST')
    try:
        with urlopen(httprequest) as response:
            result = response.read().decode()
            if 'result' in json.loads(result):
                print("PASSED web3 api set verification")
            else:
                print('ERROR: failed getting web3_clientVersion from eth json-rpc api')
    except:
        print('ERROR: failed getting web3_clientVersion from eth json-rpc api')
        return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('rest', help="evmos node rest endpoint")
    parser.add_argument('tendermintrpc', help="evmos node tendermint-rpc endpoint")
    parser.add_argument('ethjsonrpc', help="evmos node json-rpc endpoint")
    parser.add_argument('--network', help="mainnet or testnet, default mainnet", default='mainnet')

    args = parser.parse_args()

    test_values = MAINNET if args.network == 'mainnet' else TESTNET
    print("Testing REST endpoint:")
    test_rest_general_info(args.rest, test_values)
    test_rest_earliest_block(args.rest, test_values)
    print("*" * 20)
    print("\nTesting Tendermint-RPC endpoint:")
    test_tendermint_rpc_info(args.tendermintrpc, test_values)
    print("*" * 20)
    print("\nTesting EVM JSON-RPC endpoint:")
    test_eth_chain_id(args.ethjsonrpc, test_values)
    test_eth_pruning(args.ethjsonrpc, test_values)
    test_eth_net_api_set(args.ethjsonrpc, test_values)
    test_web3_api_set(args.ethjsonrpc, test_values)


if "__main__" == __name__:
    main()
