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
python setup.py develop
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
In the current setup, the Yagna Docker image is built locally when the test network is first started. To install the Yagna binary in the Docker image, a .deb package is downloaded from GitHub Actions. Since access to this package is currently restricted, before building the Docker image we need to obtain a GitHub API token with appropriate rights.

To generate a new token, go to your account's [developer settings](https://github.com/settings/tokens) and generate a new token (giving it the `repo` OAuth scope is enough).

Once your token is generated, create an environment variable named `GITHUB_API_TOKEN` and store the token as its value. This environment variable will need to be available in the terminal from which you run `docker-compose`.

#### Starting the Docker Compose network
Having the GitHub API token available in your environment, navigate to this project's root directory and run the following command:
```
docker-compose -f docker/docker-compose.yml up -d
```

This command starts the network defined by the `.yml` file in detached mode (running in the background). If everything is correctly configured you should see log output about building the Yagna Docker image. Once the network is up, you can verify it by checking the currently active docker containers:
```
docker ps
```

Assuming you have no other Docker containers currently running, the output of this command should look similar to this:
```
CONTAINER ID        IMAGE                                  COMMAND                  CREATED             STATUS              PORTS                    NAMES
1735fd81d742        golemfactory/golem-client-mock:0.1.2   "dotnet GolemClientM…"   5 seconds ago       Up 2 seconds        0.0.0.0:5001->5001/tcp   docker_mock-api_1
9127e534e86b        yagna                                  "/usr/bin/ya_sb_rout…"   5 seconds ago       Up 3 seconds                                 docker_router_1
```

#### Running the integration tests
With the Yagna test network running locally we can now launch the integration tests. To do so, navigate to the project's root directory and run:
```
python -m pytest test/level1 -svx --assets-path test/level0/asset
```

The path passed in `--assets-path` is used to define assets to be mounted in Yagna Docker containers for the tests. These files include e.g. the provider presets or the exe script definition to be used.
You should be able to see the tests' progress being reported in the command's output.
