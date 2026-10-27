"""Publication integrity uses actual recorded native data, without executing a solver."""

from scripts.check_release import check_results
from hydrostar_mcp.visualization import plot_rao
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent


def test_public_native_results_match_raw_files_and_gallery():
    result = check_results()
    assert result["native_cases"] == 3
    assert result["response_values"] == 77844


def test_scientific_plot_exports_raster_and_vector(tmp_path):
    responses = json.loads(
        (ROOT / "examples/results/semisub_oc4_style/motions.json").read_text(
            encoding="utf-8"
        )
    )
    target = plot_rao(responses, tmp_path / "response.png")
    assert target.stat().st_size > 1000
    assert target.with_suffix(".pdf").read_bytes().startswith(b"%PDF")
