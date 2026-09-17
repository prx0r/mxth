# Paper2Agent bridge
Upstream: https://github.com/jmiao24/Paper2Agent (MIT)

The bridge is intentionally an adapter, not a fork. Paper2Agent is responsible for turning a paper,
supplements and its codebase into executable tools. MathArtist then performs a second compilation:

`paper agent -> observable manifest -> immutable source adapter -> interpretation genome`

The required output is `observable-manifest.json`: source files/SHAs, executable entry points,
parameters that are scientifically fixed, valid observables, and tests. Only after the manifest passes
its tests should a source be admitted as EXACT / INVARIANT. Otherwise mark it DERIVED.
