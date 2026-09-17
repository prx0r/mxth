# paper2artist

This is the V2 ingestion bridge. Paper2Agent does the hard work of turning a paper/repository into a reviewed, tested MCP/skill output; `paper2artist` fingerprints that output and registers exported numerical observables as immutable MathArtist sources.

## 1. Agentify upstream science with Paper2Agent

Use the upstream Paper2Agent skill exactly as documented. Keep its delivered output unchanged.

## 2. Inspect the delivered agent

```bash
python -m paper2artist.cli inspect /path/to/dist/project-agent --out inspection.json
```

This records a deterministic tree SHA-256 and discovers decorated MCP tool/resource/prompt functions.

## 3. Export scientific observables

Have the paper agent execute the validated workflow and save one or more `.npy`/`.npz` trajectories. Do not edit values for aesthetics.

## 4. Register

Create a manifest using `manifest.example.json`, then:

```bash
python -m paper2artist.cli register manifest.json
```

The original array and Paper2Agent inspection are copied into `source_artifacts/<ID>/`; the dashboard display copy is derived from those frozen bytes. The interpretation genome never mutates them.
