# Yagna Integration

![codestyle](https://github.com/golemfactory/yagna-integration/workflows/codestyle/badge.svg?event=push)
![test](https://github.com/golemfactory/yagna-integration/workflows/test/badge.svg?event=push)

The Yagna Integration project, intending to build the Integration Harness around LWG software implementation.

## Running the tests locally

### Python setup

#### Python 3.7
The test runner requires Python 3.7+ to be installed on the system. You can check your currently installed Python version by running:
```
python3 --version
```

If you don't have Python installed, download the appropriate package and follow instructions from the [releases page](https://www.python.org/downloads/).

For the sake of compatibility with other projects and/or your local Python 3 installation you can install [`pyenv`](https://github.com/pyenv/pyenv) to manage and switch between multiple Python versions. The `pyenv` installer can be found [here](https://github.com/pyenv/pyenv-installer).

#### Installing the `yagna-integration` package
To install the `yagna-integration` package in the development mode, with all dependencies, run the below command from the project's root directory:
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
Docker Compose is a separate binary which needs to be available on your system in order to run Yagna integration tests. To install it, download the appropriate executable from its [releases page](https://github.com/docker/compose/releases) and make sure its present on your system's `PATH`.

### Running the test network

#### Getting a GitHub API token
In the current setup, the Yagna Docker image is built locally when the test network is first started. To install the Yagna binary a .deb package is downloaded from GitHub. Downloading artifacts requires authentication, therefore we need to use a GitHub API personal token with appropriate permissions.

To generate a new token, go to your account's [developer settings](https://github.com/settings/tokens).
You will need to grant your new token the full `repo` scope, as well as the `read:packages` scope. The packages scope is required in order to pull a Docker image from the [gnt2 repo](https://github.com/golemfactory/gnt2), which is currently private.

Once your token is generated you need to do two things:
1. Log in to GitHub's Docker registry by calling: `docker login docker.pkg.github.com -u {username}`, replacing `{username}` with your GitHub username and pasting in your access token as the password. You only need to do this once on your development machine.
2. Create an environment variable named `GITHUB_API_TOKEN` and store the access token as its value. This environment variable will need to be available in the terminal from which you run `docker-compose`.

#### Starting the Docker Compose network
Having the GitHub API token available in your environment, navigate to this project's root directory and run the following command:
```
docker-compose -f docker/docker-compose.yml up -d --build
```

This command starts the network defined by the `.yml` file in detached mode (running in the background). The flag `--build` forces a re-build of all images used in the network. If everything is correctly configured you should see log output about building the Yagna Docker image. Once the network is up, you can verify it by checking the currently active docker containers:
```
docker ps
```

Assuming you have no other Docker containers currently running, the output of this command should look similar to this:
```
CONTAINER ID        IMAGE                                  COMMAND                  CREATED             STATUS              PORTS                    NAMES
62b7b648fee0        yagna-goth:latest                      "/usr/bin/ya_sb_rout…"   6 seconds ago       Up 3 seconds                                 docker_router_1
ac8abb60e2a9        golemfactory/golem-client-mock:0.1.2   "dotnet GolemClientM…"   6 seconds ago       Up 5 seconds        0.0.0.0:5001->5001/tcp   docker_mock-api_1
3ca69f966418        proxy                                  "/docker-entrypoint.…"   6 seconds ago       Up 4 seconds        80/tcp                   docker_proxy_1
```

#### Using a specific yagna build
Running the `docker-compose` network includes a step which builds the `yagna-goth` image. By default, this image is created using the latest `.deb` package from the yagna repo [GitHub Actions build workflow](https://github.com/golemfactory/yagna/actions?query=workflow%3A%22Build+.deb%22).

In some cases we may want to use a specific build of Yagna rather than the latest one. To achieve this, it's possible to use a git commit hash being the head for one of the build workflow runs. The commit hash needs to be available under the variable `YAGNA_COMMIT_HASH` in the environment of the shell from which we run `docker-compose`:
```
YAGNA_COMMIT_HASH=b0ac62f docker-compose -f docker/docker-compose.yml up -d --build
```

The flag `--build` is passed to `docker-compose` here to force rebuilding the required images (including `yagna-goth`).


#### Running the integration tests
With the Yagna test network running locally we can now launch the integration tests. The repo currently includes two versions of the same test scenario (level0 and level1).

The level0 test scenario is considered deprecated and may be removed in the future. It's maintained to enable testing the `ya-requestor` binary, which acts as a requestor agent, performing a set of fixed commands on its requestor node.

In level1, the test author has full control over their requestor nodes, since all commands are issued from the `goth` test scenario, without the need for an external binary.

To run the level1 test scenario, navigate to the project's root directory and run:
```
python -m pytest test/level1 -svx
```

If you'd like to run level0 instead, simply replace `test/level1` with `test/level0` in the above command.

##### Setting the log level
By default, the test runner will use `INFO` log level. To override it and enable more verbose logging, use the `--log-cli-level` parameter in the `pytest` invocation:
```
python -m pytest test/level1 -svx --log-cli-level DEBUG
```

##### Overriding default assets
It's possible to provide a custom assets directory which will be mounted in all Yagna containers used for the test. The assets include files such as the exe script definition to be used by the node.

To override the default path, use the `--assets-path` parameter, passing in the custom path:
```
python -m pytest test/level1 -svx --assets-path test/custom_assets/some_directory
```

#### Troubleshooting integration test runs
All components launches during the integration test run record their logs in configured logs path. The default value of this path is:
```
$TEMP_DIR/yagna-tests
```

Where `$TEMP_DIR` is the path of the directory used for temporary files. This path will depend either on the shell environment or the operating system on which the tests are being run (see [`tempfile.gettempdir`](https://docs.python.org/3/library/tempfile.html) for more details).

The logs from a test run are recorded in the following directory structure:
- `runner.log` - logs recorded by the integration test runner engine.
- `proxy.log` - logs recorded by the HTTP 'sniffer' proxy, which monitors network traffic going into the yagna daemons launched for the test.
-  `test_*` - directory with logs generated by nodes running as part of a single test (as defined in the test's topology). This directory is named after the name of the test scenario itself.
 The logs follow a straightforward naming convention, with daemons and their clients logging into dedicated files, eg.:
   - `provider.log` - console output from `provider` yagna daemon.
   - `provider_agent.log` - console output of the provider agent, running alongside `provider` daemon.
