from goth.runner.container import DockerContainerConfig

COMPOSE_TOPOLOGY = [
    DockerContainerConfig(name="ethereum"),
    DockerContainerConfig(name="mock-api"),
    DockerContainerConfig(name="proxy"),
    DockerContainerConfig(name="router"),
]
