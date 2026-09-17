# pyribs integration
Use pyribs for offline quality-diversity sweeps over the same numeric interpretation genomes used by
the browser. The dashboard's SQLite archive is the interoperability layer: export genomes + measured
features, run pyribs, then insert selected elites back through the API/importer.

Upstream: https://github.com/icaros-usc/pyribs
The core app intentionally does not reimplement CMA-ME / CMA-MAE.
