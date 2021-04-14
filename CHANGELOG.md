# Changelog

## [Unreleased]

### Breaking changes

### Bugfixes

### Features

### Other changes

## [0.2.1] - 2021-04-14

### Bugfixes
- resolved issues with running external commands as part of a `goth` test (#485)
- fixed receiving proposals from providers in `yagna 0.6.4-rc3` and up (#486)

### Other changes
- added `yagna` payment driver CLI integration test (#453, #479)
- added Actions workflow step which makes sure Docker network gets cleaned up properly (#481)

## [0.2.0] - 2021-04-09

### Bugfixes
- fixed `mitmproxy` thread not being stopped properly (https://github.com/golemfactory/goth/pull/476)

### Features
- added optional, explicit name field to `Assertion` (https://github.com/golemfactory/goth/pull/469)
- updated GitHub assets downloaders to use [`ghapi`](https://ghapi.fast.ai/core.html) (https://github.com/golemfactory/goth/pull/455), thanks @pradeepbbl!

### Other changes
- added colours to various log messages from `goth` (https://github.com/golemfactory/goth/pull/478)
- added Docker cleanup step to GitHub Actions test workflow (https://github.com/golemfactory/goth/pull/475)
- updated project dependencies (#472)

## [0.1.0] - 2021-04-02
