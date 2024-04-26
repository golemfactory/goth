# Golem Test Harness

![codestyle](https://github.com/golemfactory/goth/workflows/codestyle/badge.svg?event=push)
![test](https://github.com/golemfactory/goth/workflows/test/badge.svg?event=push)
[![PyPI version](https://badge.fury.io/py/goth.svg)](https://badge.fury.io/py/goth)
[![GitHub license](https://img.shields.io/github/license/golemfactory/goth)](https://github.com/golemfactory/goth/blob/master/LICENSE)

`goth` is an integration testing framework intended to aid the development process of [`yagna`](https://github.com/golemfactory/yagna) itself, as well as apps built on top of it.


## Dependencies on other Golem projects

- [golemfactory/gnt2](https://github.com/golemfactory/gnt2) - Dockerized environment with Ganache and contracts
- [golemfactory/pylproxy](https://github.com/golemfactory/pylproxy) - [![PyPI version](https://badge.fury.io/py/pylproxy.svg)](https://badge.fury.io/py/pylproxy) Python proxy for catching http calls between actors (replacement for mitmproxy used previously)

## How it works

Key features:
- creates a fully local, isolated network of Golem nodes including an Ethereum blockchain (through [`ganache`](https://www.trufflesuite.com/ganache))
- provides an interface for controlling the local Golem nodes using either `yagna`'s REST API or CLI
- includes tools for defining complex integration testing scenarios, e.g. HTTP traffic and log assertions
- configurable through a YAML file as well as using a number of CLI parameters

Within a single `goth` invocation (i.e. test session) the framework executes all tests which are defined in its given directory tree.

Internally, `goth` uses `pytest`, therefore each integration test is defined as a function with the `test_` prefix in its name.

Every test run consists of the following steps:
1. `docker-compose` is used to start the so-called "static" containers (e.g. local blockchain, HTTP proxy) and create a common Docker network for all containers participating in the given test.
2. The test runner creates a number of Yagna containers (as defined in `goth-config.yml`) which are then connected to the `docker-compose` network.
3. For each Yagna container started an interface object called a `Probe` is created and made available inside the test via the `Runner` object.
4. The integration test scenario is executed as defined in the test function itself.
5. Once the test is finished, all previously started Docker containers (both "static" and "dynamic") are removed and other cleanup is performed before repeating these steps for the next test.

## Requirements
- Linux (tested on Ubuntu 18.04 and 20.04)
- Python 3.8+
- Docker

#### Python 3.8+
You can check your currently installed Python version by running:
```
python3 --version
```

If you don't have Python installed, download the appropriate package and follow instructions from the [releases page](https://www.python.org/downloads/).
#### Docker
To run `goth` you will need to have Docker installed. To install the Docker engine on your system follow these [instructions](https://docs.docker.com/engine/install/).

To verify your installation you can run the `hello-world` Docker image:
```
docker run hello-world
```

## Installation
`goth` is available as a PyPI package:
```
pip install goth
```

It is encouraged to use a Python virtual environment.

## Usage

### Getting a GitHub API token
When starting the local Golem network, `goth` uses the GitHub API to fetch metadata and download artifacts and images. Though all of these assets are public, using this API still requires basic authentication. Therefore, you need to provide `goth` with a personal access token.

To generate a new token, go to your account's [developer settings](https://github.com/settings/tokens).

You will need to grant your new token the `public_repo` scope, as well as the `read:packages` scope. The packages scope is required in order to pull Docker images from GitHub.

Once your token is generated you need to do two things:
1. Log in to GitHub's Docker registry by calling: `docker login ghcr.io -u {username}`, replacing `{username}` with your GitHub username and pasting in your access token as the password. You only need to do this once on your machine.
2. Export an environment variable named `GITHUB_TOKEN` and use the access token as its value. This environment variable will need to be available in the shell from which you run `goth`.

### Starting a local network

First, create a copy of the default assets:
```
python -m goth create-assets your/output/dir
```

Where `your/output/dir` is the path to a directory under which the default assets should be created. The path can be relative and it cannot be pointing to an existing directory.
These assets do not need to be re-created between test runs.

With the default assets created you can run the local test network like so:

```
python -m goth start your/output/dir/goth-config.yml
```

If everything went well you should see the following output:
```
Local goth network ready!

You can now load the requestor configuration variables to your shell:

source /tmp/goth_interactive.env

And then run your requestor agent from that same shell.

Press Ctrl+C at any moment to stop the local network.
```

This is a special case of `goth`'s usage. Running this command does not execute a test, but rather sets up a local Golem network which can be used for debugging purposes. The parameters required to connect to the requestor `yagna` node running in this network are output to the file `/tmp/goth_interactive.env` and can be `source`d from your shell.

### Creating and running test cases
Take a look at the `yagna` integration tests [`README`](https://github.com/golemfactory/yagna/blob/master/goth_tests/README.md) to learn more about writing and launching your own test cases.

### Logs from `goth` tests
All containers launched during an integration test record their logs in a pre-determined location. By default, this location is: `$TEMP_DIR/goth-tests`, where `$TEMP_DIR` is the path of the directory used for temporary files.

This path will depend either on the shell environment or the operating system on which the tests are being run (see [`tempfile.gettempdir`](https://docs.python.org/3/library/tempfile.html) for more details).

#### Log directory structure
```
.
└── goth_20210420_093848+0000
    ├── runner.log                      # debug console logs from the entire test session
    ├── test_e2e_vm                     # directory with logs from a single test
    │   ├── ethereum-mainnet.log
    │   ├── ethereum-holesky.log
    │   ├── ethereum-polygon.log
    │   ├── provider_1.log              # debug logs from a single yagna node
    │   ├── provider_1_ya-provider.log  # debug logs from an agent running in a yagna node
    │   ├── provider_2.log
    │   ├── provider_2_ya-provider.log
    │   ├── proxy-nginx.log
    │   ├── proxy.log                   # HTTP traffic going into the yagna daemons recorded by a "sniffer" proxy
    │   ├── requestor.log
    │   ├── router.log
    │   ├── test.log                    # debug console logs from this test case only, duplicated in `runner.log`
    └── test_e2e_wasi
        └── ...
```

### Test configuration

#### `goth-config.yml`
`goth` can be configured using a YAML file. The default `goth-config.yml` is located in `goth/default-assets/goth-config.yml` and looks something like this:
```
docker-compose:

  docker-dir: "docker"                          # Where to look for docker-compose.yml and Dockerfiles

  build-environment:                            # Fields related to building the yagna Docker image
    # binary-path: ...
    # deb-path: ...
    # branch: ...
    # commit-hash: ...
    # release-tag: ...
    # use-prerelease: ...

  compose-log-patterns:                         # Log message patterns used for container ready checks
    ethereum-mainnet: ".*Wallets supplied."
    ethereum-holesky: ".*Wallets supplied."
    ethereum-polygon: ".*Wallets supplied."
    ...

key-dir: "keys"                                 # Where to look for pre-funded Ethereum keys

node-types:                                     # User-defined node types to be used in `nodes`
  - name: "Requestor"
    class: "goth.runner.probe.RequestorProbe"

  - name: "Provider"
    class: "goth.runner.probe.ProviderProbe"
    mount: ...

nodes:                                          # List of yagna nodes to be run in the test
  - name: "requestor"
    type: "Requestor"

  - name: "provider-1"
    type: "Provider"
    use-proxy: True
```

When you generate test assets using the command `python -m goth create-assets your/output/dir`, this default config file will be present in the output location of your choice. You can make changes to that generated file and always fall back to the default one by re-generating the assets.

## Local development setup

### Poetry
`goth` uses [`poetry`](https://python-poetry.org/) to manage its dependencies and provide a runner for common tasks.

If you don't have `poetry` available on your system then follow its [installation instructions](https://python-poetry.org/docs/#installation) before proceeding.
Verify your installation by running:
```
poetry --version
```

### Project dependencies
To install the project's dependencies run:
```
poetry install
```
By default, `poetry` looks for the required Python version on your `PATH` and creates a virtual environment for the project if there's none active (or already configured by Poetry).

All of the project's dependencies will be installed to that virtual environment.
