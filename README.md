# Yagna Integration

![codestyle](https://github.com/golemfactory/yagna-integration/workflows/codestyle/badge.svg?event=push)
![test](https://github.com/golemfactory/yagna-integration/workflows/test/badge.svg?event=push)

The Yagna Integration project, intending to build the Integration Harness around LWG software implementation.

## Running the tests locally

### Python setup

#### Python 3.8
The test runner requires Python 3.8+ to be installed on the system. You can check your currently installed Python version by running:
```
python3 --version
```

If you don't have Python installed, download the appropriate package and follow instructions from the [releases page](https://www.python.org/downloads/).

For the sake of compatibility with other projects and/or your local Python 3 installation you can install [`pyenv`](https://github.com/pyenv/pyenv) to manage and switch between multiple Python versions. The `pyenv` installer can be found [here](https://github.com/pyenv/pyenv-installer).

#### Project installation
To install the `yagna-integration` package in development mode with all dependencies, run the below command from the project's root directory:
```
python3 setup.py develop
```

### Docker setup

#### Docker Engine
The tests are performed on live Yagna nodes running in an isolated network. Currently, this setup is achieved by running a number of Docker containers locally using Docker Compose.

To run the test containers you will need to have both Docker and Docker Compose installed on your system. To install the Docker engine on your system follow these [instructions](https://docs.docker.com/engine/install/). To verify your installation you can run the `hello-world` Docker image:
```
docker run hello-world
```

#### Docker Compose
Docker Compose is a separate binary which needs to be available on your system in order to run Yagna integration tests. `goth` requires `docker-compose` **version 1.27** or higher. There are two ways you can install it:
1. Download the appropriate executable from the [releases page](https://github.com/docker/compose/releases) and make sure its present on your system's `PATH`.
2. Use the `docker-compose` installed to your `goth` Python environment (you will need to activate the environment in the shell from which you run your tests).

### Running the test network

#### Getting a GitHub API token
When first starting the test network, `goth` uses the GitHub API to fetch metadata and download artifacts and images. Although all of these assets are public, using the GitHub API still requires basic authentication. Therefore, you need to provide `goth` with a personal access token.

To generate a new token, go to your account's [developer settings](https://github.com/settings/tokens).
You will need to grant your new token the `public_repo` scope, as well as the `read:packages` scope. The packages scope is required in order to pull Docker images from GitHub.

Once your token is generated you need to do two things:
1. Log in to GitHub's Docker registry by calling: `docker login docker.pkg.github.com -u {username}`, replacing `{username}` with your GitHub username and pasting in your access token as the password. You only need to do this once on your development machine.
2. Export an environment variable named `GITHUB_API_TOKEN` and use the access token as its value. This environment variable will need to be available in the shell from which you run `goth`.

### Running the integration tests
With project dependencies installed and environment set up you are now ready to launch integration tests.

All tests related to `yagna` can be found under `test/yagna` with end-to-end tests located in `test/yagna/e2e`. To run them, issue the below command from the project's root directory:
```
python -m pytest test/yagna/e2e -svx
```
The test runner of choice here is `pytest`, therefore each test is defined as a separate Python function in a given `.py` file.

Every test run consists of the following steps:
1. `docker-compose` is used to start the so-called "static" containers (e.g. local blockchain, HTTP proxy) and create a common Docker network for all containers participating in the test.
2. The test runner creates a number of Yagna containers (as defined in the test's topology) which are connected to the `docker-compose` network.
3. For each Yagna container started a so-called "probe" object is created and made available inside the test via the `Runner` object.
4. The integration test scenario is executed as defined in the function called by `pytest`.
5. Once the test is finished, all previously started Docker containers (both "static" and "dynamic") are removed.

### Custom test options

#### Assets path
It's possible to provide a custom assets directory which will be mounted in all Yagna containers used for the test. The assets include files such as the exe script definition (`exe-script.json`) or payment configuration (`accounts.json`).

To override the default path, use the `--assets-path` parameter, passing in the custom path:
```
python -m pytest test/yagna/e2e -svx --assets-path test/custom_assets/some_directory
```

#### Log level
By default, the test runner will use `INFO` log level. To override it and enable more verbose logging, use the `--log-cli-level` parameter in the `pytest` invocation:
```
python -m pytest test/yagna/e2e -svx --log-cli-level DEBUG
```

#### Logs path
The destination path for all test logs can be overridden using the option `--logs-path`:
```
python -m pytest test/yagna/e2e -svx --logs-path your/custom/path
```

#### Yagna binary path
By default, a set of yagna binaries is downloaded from GitHub to be used for a given test session. The option `--yagna-binary-path` allows you to use binaries from the local file system instead. Its value must be a path to either a directory tree containing yagna binaries (e.g. `target` directory from a local `cargo` build) or a `.zip` archive file (e.g. downloaded manually from GitHub Actions):
```
python -m pytest test/yagna/e2e -svx --yagna-binary-path /path/to/binaries
```

#### Yagna commit hash
By default, `goth` uses a `yagna` binary from the latest GitHub Actions successful build on `master` branch. This option can be used to override that behaviour. The value here needs to be a git commit hash being the head for one of the build workflow runs:
```
python -m pytest test/yagna/e2e -svx --yagna-commit-hash b0ac62f
```

#### Yagna .deb path
Path to a local .deb file or a directory containing a number of such archives. All of these .deb files will be installed in the Docker image used for Yagna nodes in the tests. To specify the path, use the option `--yagna-deb-path`:
```
python -m pytest test/yagna/e2e -svx --yagna-deb-path path/to/yagna.deb
```

### Troubleshooting integration test runs
All components launched during the integration test run record their logs in a pre-determined location. By default, this location is: `$TEMP_DIR/yagna-tests`, where `$TEMP_DIR` is the path of the directory used for temporary files. This path will depend either on the shell environment or the operating system on which the tests are being run (see [`tempfile.gettempdir`](https://docs.python.org/3/library/tempfile.html) for more details). This default location can be overridden using the option `--logs-path` when running `pytest`.

The logs from a test run are recorded in the following directory structure:
- `runner.log` - logs recorded by the integration test runner engine.
- `proxy.log` - logs recorded by the HTTP 'sniffer' proxy, which monitors network traffic going into the yagna daemons launched for the test.
-  `test_*` - directory with logs generated by nodes running as part of a single test (as defined in the test's topology). This directory is named after the name of the test scenario itself.
 The logs follow a straightforward naming convention, with daemons and their clients logging into dedicated files, eg.:
   - `provider.log` - console output from `provider` yagna daemon.
   - `provider_agent.log` - console output of the provider agent, running alongside `provider` daemon.
