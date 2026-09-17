#!/usr/bin/env bash
set -euo pipefail
mkdir -p external
clone(){ [ -d "external/$2/.git" ] || git clone --depth 1 "$1" "external/$2"; }
clone https://github.com/Chakazul/Lenia.git lenia
clone https://github.com/evoluteur/cymatics.git cymatics
clone https://github.com/icaros-usc/pyribs.git pyribs
clone https://github.com/SakanaAI/ShinkaEvolve.git shinka-evolve
clone https://github.com/jmiao24/Paper2Agent.git paper2agent
clone https://github.com/betsee/betse.git betse
clone https://github.com/santamanicka/ElectricMorphogenesis.git electric-morphogenesis
printf 'Upstreams cloned under external/ (gitignored).\n'
