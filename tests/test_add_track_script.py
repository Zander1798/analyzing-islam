import subprocess, sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

def test_track_injected_after_auth_ui_everywhere():
    subprocess.run([sys.executable, str(ROOT / "add-track-script.py")], cwd=ROOT, check=True)
    pages = [p for p in SITE.rglob("*.html") if "auth-ui.js" in p.read_text(encoding="utf-8")]
    assert pages, "no auth-ui pages found"
    missing = [str(p) for p in pages if "assets/js/track.js" not in p.read_text(encoding="utf-8")]
    assert not missing, f"track.js missing on {len(missing)} pages, e.g. {missing[:3]}"

def test_idempotent_no_duplicate_track_tags():
    subprocess.run([sys.executable, str(ROOT / "add-track-script.py")], cwd=ROOT, check=True)
    sample = SITE / "index.html"
    assert sample.read_text(encoding="utf-8").count('assets/js/track.js"') == 1
