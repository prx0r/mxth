# Integration with current mxth

The current V3.3 dashboard is technically rich but exposes too many analytical objectives during the creative act.

## Top-level creative tabs

Keep:
OPEN / POTENTIAL / LINEAGE / SAVED / STUDY

Move:
5s / 10s / 20s / replay / YouTube / analytics
into Study/Analysis surfaces.

## Required API behavior

GET `/api/population?...mode=open-blind&count=24`

POST `/api/branch`
```json
{
  "parent_ids": ["specimen-id"],
  "sigma": 0.35,
  "count": 24,
  "lineage_channel": "HUMAN_OPEN_ENDED",
  "preserve_parents": true
}
```

POST `/api/root` for fresh blind roots.

## Event semantics

Strong creative signal ordering:
branch > potential > save > fullscreen/replay > dwell

Never feed these into OPEN_BLIND.

## UI rules

- current generation visible
- immediate parent available
- full lineage hidden until requested
- no sliders by default
- controls surface hidden by default
- generation step should feel instantaneous
- branch pressure is the main creative control
- native renderer should be used in ART mode; minimal observer remains available in SCIENCE mode
