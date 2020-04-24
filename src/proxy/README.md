_This is just a stub of a proper README_

# Running API Calls Tracer

In the current directory start `nginx` and `mitmproxy` with:
```
$ ./start_proxy.sh
```

Meanwhile, in another terminal run the test script (e.g. (../../test/level0/unix/run-test.sh)) with `USE_PROXY` environment variable set:
```
$ USE_PROXY=1 ./run-test.sh
```

