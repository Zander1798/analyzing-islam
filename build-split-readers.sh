#!/usr/bin/env bash
set -euo pipefail
# Run AFTER build-quran-reader.py / build-hadith-readers.py and the post-build
# decorators have produced the monolithic read/*.html files.
python split_readers.py --all
echo "Split readers regenerated. Sub-pages, shells, indexes, manifests updated."
