# tests/test_refs_integration.py
import importlib.util
from pathlib import Path

def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parent.parent / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

refs = _load("refs")
ra = _load("read_anchors")

# (ref string, expected first (slug, anchor)) — sampled from book verse_refs.
SAMPLES = [
    ("Q 2:25", ("quran", "s2v25")),
    ("Q 27:15–44", ("quran", "s27v15")),
    ("Bukhari 224", ("bukhari", "h224")),
    ("Bukhari 3185", ("bukhari", "h3185")),
    ("Nasa'i 5397", ("nasai", "h5397")),
]


def test_sampled_refs_resolve_to_existing_anchors():
    for ref, expected in SAMPLES:
        slug, anchor = refs.primary_anchor(ref)
        assert (slug, anchor) == expected, f"{ref} -> {(slug, anchor)}"
        assert anchor in ra.read_anchor_set(slug), \
            f"{ref}: anchor {slug}#{anchor} missing from read page"
