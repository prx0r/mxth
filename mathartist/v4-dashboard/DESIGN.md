# Human aesthetic process

## Main loop

Machine:
1. generate thousands blindly
2. reject only technical failures
3. compress to a morphology-diverse batch
4. show 12–24 candidates

Human:
1. scan rapidly
2. mark anything with POTENTIAL
3. choose mutation pressure
4. branch explicitly
5. repeat

The word POTENTIAL is deliberate. The user does not need to decide whether an image is already beautiful; they only need to notice whether a direction is worth exploring.

## Literature-derived interaction choices

Sakana/Picbreeder:
- grid of siblings
- selected parents retained unchanged
- one-step evolve action
- undo/reset/new-parent
- small-vs-large mutation pressure
- ancestry and branching
- occasional root/random injection
- preserve fortunate accidents

Interactive evolutionary computation:
- qualitative selection rather than assigning numeric fitness to every specimen
- multiple parent selection
- small visible population to reduce fatigue

Quality-diversity:
- machine handles the huge population
- human sees a diverse coverage subset
- morphology diversity and aesthetic taste remain separate

## Three archive channels

OPEN_BLIND:
machine-only exploration; no human signals.

HUMAN_OPEN_ENDED:
explicit POTENTIAL/BRANCH lineages.

FOR_YOU later:
may learn P(branch | morphology, source, lineage), but must always reserve diverse/OOD slots.

## Delayed measurement

Do not reveal QRI/rasa/structural predictions before selection.
Retrospective response may record valence, absorption, beauty/rasa labels later.
