# Changelog

## [0.10.0] - 2022-01-19

### Breaking changes
- change `Probe#run_command_on_host` to include a process monitor in its return values [#571](https://github.com/golemfactory/goth/pull/571)

### Other changes
- improve error reporting [#570](https://github.com/golemfactory/goth/pull/570)

## [0.9.0] - 2021-11-17

### Breaking changes
- change default payment configuration to erc20 rinkeby [#567](https://github.com/golemfactory/goth/pull/567)

### Other changes
- add `yagna` hybrid net support [#560](https://github.com/golemfactory/goth/pull/560)
- allow specifying Docker Compose file in `goth-config.yml` [bb4c732](https://github.com/golemfactory/goth/commit/bb4c73287191efb38568b86f1c1db11fde33ae49)

## [0.8.0] - 2021-11-09

### Features
- enable per-node payment platform configuration in `goth-config.yml` [#556](https://github.com/golemfactory/goth/pull/556)
- expose payment config object in `Probe`s [#564](https://github.com/golemfactory/goth/pull/564)

### Other changes
- increase proposal collection timeout to 30s [#563](https://github.com/golemfactory/goth/pull/563)
- decrease yagna broadcast intervals [#558](https://github.com/golemfactory/goth/pull/558)

## [0.7.4] - 2021-10-13

### Other changes
- reduce timeout to 1 sec on polling API calls [#552](https://github.com/golemfactory/goth/pull/552)

## [0.7.3] - 2021-09-27

### Other changes
- allow calling `stop` on an already stopped Docker container [#550](https://github.com/golemfactory/goth/pull/550)

## [0.7.2] - 2021-09-27

### Bugfixes
- stop the underlying Docker container when calling Probe.stop [#549](https://github.com/golemfactory/goth/pull/549)

## [0.7.1] - 2021-09-23

### Features
- enable specifying whether GitHub pre-releases should be included when building a `yagna` Docker image [#548](https://github.com/golemfactory/goth/pull/548)

### Other changes
- update default `goth-config.yml` to not include a custom `yagna` branch for building images [#548](https://github.com/golemfactory/goth/pull/548)

## [0.7.0] - 2021-09-09

### Breaking changes
- make default presets.json compatible with `yagna` 0.8+ [080a95f](https://github.com/golemfactory/goth/commit/080a95fd8c5b41b69da216cfdee6f0ac4dbe3acc)
- update mock zkSync server version [#544](https://github.com/golemfactory/goth/pull/544)

### Features
- disconnect `yagna` containers before stopping Docker network [#540](https://github.com/golemfactory/goth/pull/540)
- enable creating detached API assertions [#538](https://github.com/golemfactory/goth/pull/538)
- enable MITM proxy for requestor probes [#535](https://github.com/golemfactory/goth/pull/535)

### Other changes
- update `typing_extensions` to 3.10.0+ [cc956e1](https://github.com/golemfactory/goth/commit/cc956e14447b5d6f382b7f668e385fcee9c209be)

## [0.6.3] - 2021-08-16

### Bugfixes
- expand path variable in `Probe.get_agent_env_vars` [#534](https://github.com/golemfactory/goth/pull/534)

## [0.6.2] - 2021-08-11

### Features
- output interactive mode env variables to a file [#520](https://github.com/golemfactory/goth/pull/520)

### Bugfixes
- fix fetching latest workflow run when downloading a GitHub artifact [#531](https://github.com/golemfactory/goth/pull/531)

### Other changes
- bump aiohttp from 3.7.3 to 3.7.4 [#527](https://github.com/golemfactory/goth/pull/527)

### Other changes
- improved error reporting on timeouts in log monitors [#524](https://github.com/golemfactory/goth/pull/524)
- updated probe startup logic to start all probes in parallel [#523](https://github.com/golemfactory/goth/pull/523)

## [0.6.1] - 2021-07-27

### Other changes
- improved error reporting on timeouts in log monitors [#524](https://github.com/golemfactory/goth/pull/524)
- updated probe startup logic to start all probes in parallel [#523](https://github.com/golemfactory/goth/pull/523)

## [0.6.0] - 2021-07-16

### Breaking changes
- dependency update: `goth` now uses `ya-aioclient` v0.6.x; projects that use `goth` v0.6.x and `ya-aioclient` need to update their version of `ya-aioclient` to v0.6.x [#515](https://github.com/golemfactory/goth/pull/515)

## [0.5.2] - 2021-07-07

### Bugfixes
- fixed `goth` interactive mode log assertion [d36a149](https://github.com/golemfactory/goth/commit/d36a14924ece26cc44a5f551ee840e1f0b426617)

## [0.5.1] - 2021-07-05

### Bugfixes
- updated default mount point for `yagna` provider image cache [c546dd2](https://github.com/golemfactory/goth/commit/c546dd2b8eafe4bd65e782f2d73e60d5b6136eec)

## [0.5.0] - 2021-06-29

### Breaking changes
- removed `ProviderLogMixin`, provider log assertions have been moved to `yagna` repo tests [#514](https://github.com/golemfactory/goth/pull/514)

## [0.4.0] - 2021-06-01

### Breaking changes
- changed regex used for waiting on `yagna` REST API to come online (compatible with `yagna` 0.7+) [#508](https://github.com/golemfactory/goth/pull/508)

## [0.3.2] - 2021-05-27

### Features
- pinned specific revision of `debian` Docker image to be used as base in default Dockerfiles [c31288e](https://github.com/golemfactory/goth/commit/c31288edbb3e45235877b0674d36104d8b4a2af3)

## [0.3.1] - 2021-05-25

### Features
- enabled setting environment variables through `goth-config.yml` [#505](https://github.com/golemfactory/goth/pull/505)
- added generic `wait_for_log` step to provider probe [#434](https://github.com/golemfactory/goth/pull/434)

## [0.3.0] - 2021-05-17

### Breaking changes
- removed `yagna` integration tests from the repo [#503](https://github.com/golemfactory/goth/pull/503)

### Features
- added `poe` job for running `goth` interactive mode [bde7d5f](https://github.com/golemfactory/goth/commit/bde7d5faca9570af3455bd56c738c385ecd760a0)

### Other changes
- updated `GETH_ADDR` env variable in `yagna` nodes started by `goth` [#504](https://github.com/golemfactory/goth/pull/504)

## [0.2.4] - 2021-04-27

### Features
- added optional `extra_monitors` parameter to `Runner#check_assertion_errors` [#495](https://github.com/golemfactory/goth/pull/495)
- added the `--unstable` option to release downloader script [#500](https://github.com/golemfactory/goth/pull/500)

### Bugfixes
- fixed reporting of assertion success and failure in `EventMonitor` [#495](https://github.com/golemfactory/goth/pull/495)

### Other changes
- changed the `yagna` Docker image builder to use stable releases by default [#500](https://github.com/golemfactory/goth/pull/500)

## [0.2.3] - 2021-04-19

### Other changes
- added CHANGELOG.md and CONTRIBUTING.md files [#487](https://github.com/golemfactory/goth/pull/487)
- updated default goth assets [#490](https://github.com/golemfactory/goth/pull/490)

## [0.2.2] - 2021-04-15

### Features
- enabled overriding values when parsing `goth-config.yml` file [#489](https://github.com/golemfactory/goth/pull/489)

## [0.2.1] - 2021-04-14

### Bugfixes
- resolved issues with running external commands as part of a `goth` test [#485](https://github.com/golemfactory/goth/pull/485)
- fixed receiving proposals from providers in `yagna 0.6.4-rc3` and up [#486](https://github.com/golemfactory/goth/pull/486)

### Other changes
- added `yagna` payment driver CLI integration test [#453](https://github.com/golemfactory/goth/pull/453), [#479](https://github.com/golemfactory/goth/pull/479)
- added Actions workflow step which makes sure Docker network gets cleaned up properly [#481](https://github.com/golemfactory/goth/pull/481)

## [0.2.0] - 2021-04-09

### Bugfixes
- fixed `mitmproxy` thread not being stopped properly [#476](https://github.com/golemfactory/goth/pull/476)

### Features
- added optional, explicit name field to `Assertion` [#469](https://github.com/golemfactory/goth/pull/469)
- updated GitHub assets downloaders to use [`ghapi`](https://ghapi.fast.ai/core.html) [#455](https://github.com/golemfactory/goth/pull/455)

### Other changes
- added colours to various log messages from `goth` [#478](https://github.com/golemfactory/goth/pull/478)
- added Docker cleanup step to GitHub Actions test workflow [#475](https://github.com/golemfactory/goth/pull/475)
- updated project dependencies [#472](https://github.com/golemfactory/goth/pull/472)

## [0.1.0] - 2021-04-02
