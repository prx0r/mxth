.PHONY: run test regenerate preview bundles package clean-runtime
run:
	./run.sh

test:
	python3 scripts/verify_suite.py

regenerate:
	python3 tools/generate_trajectories.py

preview:
	python3 tools/render_preview.py

bundles:
	PYTHONPATH=app python3 -c "from archive import load_specs; from source_bundles import write_manifests; write_manifests(load_specs())"

video:
	@echo "Usage: python tools/render_video.py PHENOTYPE_ID --out organism.mp4"

clean-runtime:
	rm -f data/mathartist.sqlite3 data/mathartist.sqlite3-wal data/mathartist.sqlite3-shm data/selfcheck.sqlite3*
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +

package: test preview bundles clean-runtime
	python3 tools/package.py
