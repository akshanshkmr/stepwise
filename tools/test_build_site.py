"""The deployed site must not contain a single reference solution.

GitHub Pages serves whatever it is handed, so this is the check standing
between the build and publishing every answer the app exists to withhold.
"""
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    subprocess.run([sys.executable, "tools/build_site.py"], cwd=ROOT, check=True,
                   capture_output=True)
    out = ROOT / "_site"
    assert out.is_dir(), "build_site.py produced no _site/"
    return out


def test_the_app_is_actually_there(site):
    for required in ["index.html", "app.js", "style.css", "tracer.py",
                     "problems/index.json", "views/manifest.json"]:
        assert (site / required).exists(), f"missing {required}"


def test_solution_holding_directories_are_absent(site):
    for forbidden in ["tools", "dev", "docs", ".github"]:
        assert not (site / forbidden).exists(), f"{forbidden}/ reached the site"


def test_no_reference_solution_body_is_present(site):
    """Signatures are shown to the learner on purpose; bodies never are."""
    bodies = [
        "l, r = 0, len(",
        "while l < r:",
        "numbers[l] + numbers[r]",
        "stack.pop()",
        "nums[slot], nums[scan] = ",
        "height[l] >= left_max",
    ]
    for path in site.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(errors="ignore")
        for body in bodies:
            assert body not in text, f"{path.relative_to(site)} contains {body!r}"


def test_record_py_is_not_reachable(site):
    assert not (site / "tools" / "record.py").exists()
    assert not list(site.rglob("record.py"))
    assert not list(site.rglob("test-runner.html"))
