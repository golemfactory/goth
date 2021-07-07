# Changelog

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
- changed regex used for waiting on yagna REST API to come online (compatible with `yagna` 0.7+) [#508](https://github.com/golemfactory/goth/pull/508)

## [0.3.2] - 2021-05-27

### Features
- pinned specific revision of `debian` Docker image to be used as base in default Dockerfiles [c31288e](https://github.com/golemfactory/goth/commit/c31288edbb3e45235877b0674d36104d8b4a2af3)

## [0.3.1] - 2021-05-25

### Features
- enabled setting environment variables through `goth-config.yml` [#505](https://github.com/golemfactory/goth/pull/505)
- added generic `wait_for_log` step to provider probe [#434](https://github.com/golemfactory/goth/pull/434)

### Other changes

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
