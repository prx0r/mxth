# Sakana AI Picbreeder-VLM design bridge

Reference: https://pub.sakana.ai/picbreeder-vlm/

MathArtist reuses the **open-ended archive pattern**, not the CPPN genotype:
- a shared unbounded archive;
- explicit ancestry / branching;
- sampling from recent, random and highly branched stepping stones;
- stochastic root injection to escape local attractors;
- no single target image;
- optional agents may inspect and branch archive members.

Our scientific genotype is intentionally different: a source variant is frozen and only its typed
interpretation genome may mutate. `app/archive.py` implements the default browser/archive breeder.
For program-level mutation of interpretation code, use the ShinkaEvolve bridge in `../shinka/`.
