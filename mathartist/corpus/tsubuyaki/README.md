# #つぶやきProcessing corpus adapter

V3.3 treats the public #つぶやきProcessing ecosystem as a *seed mine*, not a training set and not an aesthetic objective.

Canonical discovery sources:
- https://tsubuyaki.art/ (attribution-forward runnable archive; use its latest JSON/feed where available)
- https://tweetprocessing.projectroom.jp/ (Hau_kun portal)
- https://haukun.projectroom.jp/ (roundups / historical source)
- https://github.com/pianocurve/skepara (numeric-constant extraction precedent)
- https://medium.com/neort/pchj03-challenge-picks-526dccf4c19a (curated challenge examples)

Rules:
1. Never strip artist, original URL, archive URL, code hash, or license/status metadata.
2. Unknown redistribution license => store metadata + source URL + hash; fetch runnable code locally, do not republish it in release archives.
3. Exact source program is frozen. Search mutates only an extracted candidate control surface.
4. Numeric literals are *candidates*, not automatically legitimate parameters. Classify literal role before sweeping.
5. OPEN never receives favorite/beauty/rasa/valence labels.
6. Human POTENTIAL may spawn a branch but may not become OPEN's objective.
