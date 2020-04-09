# Wrapper scripts and low-level scripts

Wrapper scripts can be used for conveniently setting up and running the test
scenario on a single machine. Wrapper scripts are:
```
setup_nodes.sh
start_daemons.sh
start_apps.sh
```

Wrapper scripts call lower-level scripts that can be used in a more flexible
setup, for example to run the provider and the requestor daemons and agents
on separate machines, or in separate docker containers.



# Running the test scenario using wrapper scripts


## Setup

Run the `setup_nodes.sh` to create data directories for the
provider and requestor daemons and to generate the node identities:
```
$ ./setup_nodes.sh
```

## Starting daemons

Start the provider and requestor daemons:
```
$ ./start_daemons.sh
```

## Running the agents

Start the provider and requestor agents:
```
$ ./start_apps.sh
```



# Using the low-level scripts 


## Setting up the provider node

1. Make sure the network hub is running. If not, start it with
```
$ ./start_net_mk1_hub.sh
```

2. Run `setup_node.sh` to create the data directory and generate node ID
for the provider node:
```
$ ./setup_node.sh ./provider.env
```

3. Start the yagna daemon:
```
$ ./start_damon.sh ./provider.env
```

4. Create an app key for the provider agent:
```
$ ./create_key.sh provider.env
```

5, Run the provider app:
```
$ ./start_provider.sh provider.env
```

