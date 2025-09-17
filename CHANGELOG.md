# CHANGELOG

## [release-cognit-4.0]

- Release M33.

### Additions, changes and fixes

- Latency mechanisms to select the faster Edge Cluster Frontend if MAX_LATENCY parameter is provided in requirements
- Requirement parameter GEOLOCATION is now mandatory and made up of a latitud and longitude value.
- Fix: CallQueue and SyncResultQueue are no longer Singletons
- Examples: MinIO service usage within a offloaded function
- Improved documentation

## [release-cognit-3.0]

- Release M27.

### Added

- State machine runs on an independent thread.
- Independent thread that sends latency metrics to the `EdgeClusterFrontend`: `LatencyCalculator`
- `StateMachineHandler` manages the state machine transitions.
- Queues for message exchange between threads: `CallQueue` and `SyncResultQueue`.
- DeviceRuntime `call_async` and `stop` functions.
- DeviceRuntime data models.

### Changed

- DeviceRuntime `init`, `call` and `update_requirements` functions.
- `CognitFrontendClient` and `EdgeClusterFrontendClient`.
- Data Models for `CognitFrontendClient` and `EdgeClusterFrontendClient`.
- Unit tests for each of the components.
- Integration tests.
- `minimal_offload_sync.py` example file.

## [release-cognit-2.0]

- Release M21.

## [release-cognit-1.0]

- Release M15.

## [1.0.0]

- Initial release (M9)
