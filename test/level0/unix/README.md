# Unix scripts for Integration Scenario "0"

See the [toplevel README.md](../README.md) for the description of the test scenario and artifacts.


*Note: I'm not sure which of the steps below belong to the **Setup** stage and which ones to the proper **Run** stage. Some adjustments may be required.*


## Setup

Follow these steps to setup the test environment:

1. Install `yagna` deb package (**TODO**: reference).

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


## Run

1. Start the network hub (as in **Setup**)

2. Start the provider and the requestor daemons:
   ```
   $ ./with_env.sh provider.env start_daemon.sh &
   $ ./with_env.sh requestor.env start_daemon.sh &
   ```

3. Start the provider and the requestor agents:
   ```
   $ ./start_provider.sh &
   $ ./start_requestor.sh
   ```

4. Wait for the activity to complete and stop the agents:
   __TODO__

5. Stop the daemons:
   ```
   $ ./with_env.sh provider.env stop_daemon.sh
   $ ./with_env.sh requestor.env stop_daemon.sh
   ```

6. Stop the network hub (as in **Setup**)





