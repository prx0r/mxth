# Architecture

```
scientific source / paper
        |
        +-- Paper2Agent / author code / simulator
        v
IMMUTABLE SOURCE ADAPTER  --hash/tests--> provenance level
        |
        v
source state(t) ------------------------------+
                                               |
INTERPRETATION GENOME                         |
(view / sample / projection / time / exposure)|
        |                                      |
        +--------------> renderer <------------+
                           |
                           v
                       phenotype
                     /     |      \
             open archive human   attention experiment
                |          |          |
           Sakana/Shinka   |      5/10/20/replay
                \          |          /
                 +------ SQLite -----+
                          |
                    pyribs QD sweeps
```

Hard invariant: evolutionary operators cannot edit the source equations, source variant, seed/data,
scientific parameters or author implementation. A lineage may be born from a different valid source
variant, but descendants freeze that variant.
