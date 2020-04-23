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

#### Installing dependencies
To install dependencies, run the below command from the project's root directory:
```
pip install -r requirements.txt
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
In the current setup, the Yagna Docker image is built locally when the test network is first started. Since Yagna is not (yet) publicly available, cloning its repository from GitHub requires having appropriate access rights. Therefore, before running the network we need to first obtain a GitHub API token with rights to clone the Yagna repository.

To generate a new token, go to your account's [developer settings](https://github.com/settings/tokens) and generate a new token (giving it the `repo` OAuth scope is enough). Once your token is generated, create an environment variable named `GITHUB_API_TOKEN` and store the token as its value. This environment variable will need to be available in the terminal from which you start the `docker-compose` network.

#### Starting a Docker Compose network
Having the GitHub API token available in your environment, navigate to this project's `src/docker` directory and run the below command:
```
docker-compose up
```

If everything is correctly configured you should see Docker pulling and building images, followed by logs from the containers in the network.

#### Running the integration tests
With the Yagna test network running locally we can now launch the integration tests. To do so, navigate to the project's root directory and run:
```
python -m pytest test/level0 -svx --log-cli-level=INFO
```

You should be able to see the tests' progress being reported in the command's output.
