# Sakana AI ShinkaEvolve integration

Install `shinka-evolve`, then point a Shinka task at an **interpretation module only**. The source
adapter and its immutable core stay outside the evolved program directory. The evaluator must hash
that source core before/after each candidate and reject a candidate if the hash changes.

Why: ShinkaEvolve already provides populations, archives, islands, LLM mutation operators, parallel
evaluation and a WebUI. We should not rebuild those. We use it only when we want program-level
search over observation code; normal continuous interpretation search is cheaper through pyribs.

Upstream: https://github.com/SakanaAI/ShinkaEvolve (Apache-2.0)

A task skeleton is in this directory. `evaluate.py` demonstrates the contract and emits a numeric
score from an externally supplied experiment metric while enforcing an immutable-core SHA-256.
