# evmos-node-verify

## Requirements
python3.8 or later

## How to run

```shell
python3 verify-evmos.py <rest-url> <tendermint-rpc-url> <json-rpc-url> --network mainnet/testnet
```

## Usage:
```
usage: Lava Evmos providers node verification [-h] [--network NETWORK] rest tendermintrpc ethjsonrpc

positional arguments:
rest               evmos node rest endpoint
tendermintrpc      evmos node tendermint-rpc endpoint
ethjsonrpc         evmos node json-rpc endpoint

options:
-h, --help         show this help message and exit
--network NETWORK  mainnet or testnet, default mainnet
```
