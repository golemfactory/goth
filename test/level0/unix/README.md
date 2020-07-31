# Unix scripts for Integration Scenario "0"

See the [toplevel README.md](../README.md) for the description of the test scenario and artifacts.

The convention is that scripts with the executable bit set should be run directly, and those without should be run using the `with_env.sh` wrapper (see examples below).

*Note: I'm not sure which of the steps below belong to the **Setup** stage and which ones to the proper **Run** stage. Some adjustments may be required.*


## Setup

Follow these steps to setup the test environment:

1. Install `yagna` deb package (**TODO**: reference).

1b. Build `yagna` binaries and add them to your path:
```
export YAGNA_GIT_DIR=/path/to/yagna/repo/

cd ${YAGNA_GIT_DIR}

cargo build --release -p yagna -p ya-provider -p ya-requestor -p ya-exe-unit
cargo build --release -p ya-sb-router --example ya_sb_router

EXPORT PATH=${YAGNA_GIT_DIR}/target/release
EXPORT PATH=${YAGNA_GIT_DIR}/target/release/examples
```
Setup exe-unit:
- Build `ya-runtime-wasi` in `--release` mode
- Create `local-exeunit-descriptor.json`
```
[
    {
        "name": "wasmtime",
        "version": "0.1.0",
        "supervisor-path": "/path/to/yagna.git/target/release/exe-unit",
        "runtime-path": "/path/to/ya-runtime-wasi.git/target/release/ya-runtime-wasi"
    }
]
```
- Update `supervisor-path` and `runtime-path` locations and version in the json
- edit `start_provider.sh` to use `local-exeunit-descriptor.json`

2. Build and start Market API Mock TestBed using the standard port `5001` (https://github.com/stranger80/golem-client-mock).

3. Start the network hub:
   ```
   $ ./start_net_mk1_hub.sh &
   ```

4. Setup the provider node:
   ```
   $ ./with_env.sh provider.env setup_node.sh
   ```
   This will create the data directory `provider_data` and create an
   app key for the provider.

5. Perform the same setup for the requestor node:
   ```
   $ ./with_env.sh requestor.env setup_node.sh
   ```

6. Stop the network hub:
   ```
   $ ./stop_net_mk1_hub.sh
   ```

7. Log in to github package registry in your local docker
   ```
   $ cat ~/TOKEN.txt | docker login docker.pkg.github.com -u USERNAME --password-stdin
   ```
   `TOKEN.txt` contains a [github api token](https://github.com/golemfactory/yagna-integration#getting-a-github-api-token)
   `USERNAME` should be replaced by your github user name

## Run

1. Start the network hub (as in **Setup**)

2. Start the `gnt2-docker-yagna` image
   ```
   $ docker run -d --rm -ti -p 8545:8545 --name docker_ethereum docker.pkg.github.com/golemfactory/gnt2/gnt2-docker-yagna:latest
   ```


3. Start the provider and the requestor daemons:
   ```
   $ ./with_env.sh provider.env start_daemon.sh &
   $ ./with_env.sh requestor.env start_daemon.sh &
   ```

4. Start the provider and the requestor agents:
   ```
   $ ./start_provider.sh &
   $ ./start_requestor.sh
   ```

5. Wait for the activity to complete and stop the agents:
   __TODO__

6. Stop the daemons:
   ```
   $ ./with_env.sh provider.env stop_daemon.sh
   $ ./with_env.sh requestor.env stop_daemon.sh
   ```

7. Stop the network hub (as in **Setup**)
