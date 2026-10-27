import pytest

from scripts.mesh_study import compare_rao
from scripts.frequency_study import sampled, peak


def sample(amp=1.0, phase=0.0, unit="m/m"):
    return dict(
        omega=[0.1], headings=[0], amplitude=[[amp]], phase=[[phase]], unit=unit
    )


def test_phase_wrap_is_continuous():
    result = compare_rao(sample(phase=360), sample())
    assert result["complex_relative_pct"] < 1e-10


def test_complex_change_includes_phase_and_amplitude():
    assert compare_rao(sample(amp=1.1), sample())[
        "complex_relative_pct"
    ] == pytest.approx(10)
    assert compare_rao(sample(phase=180), sample())[
        "complex_relative_pct"
    ] == pytest.approx(200)


def test_comparison_requires_consistent_units():
    with pytest.raises(ValueError):
        compare_rao(sample(unit="deg/m"), sample())


def test_zero_reference_uses_absolute_difference():
    result = compare_rao(sample(amp=0), sample(amp=0))
    assert result["complex_relative_pct"] is None
    assert result["complex_max_difference"] == 0


def test_complete_phase_matrix_is_required():
    value = sample()
    value["phase"] = [[]]
    with pytest.raises(ValueError):
        compare_rao(value, sample())


def test_nonfinite_response_is_rejected():
    with pytest.raises(ValueError):
        compare_rao(sample(amp=float("nan")), sample())


def test_peak_check_covers_interleaved_sampling_phases():
    values = dict(
        omega=[0.08, 0.081, 0.082, 0.083, 0.084],
        headings=[90],
        unit="m/m",
        amplitude=[[1], [9], [2], [3], [1]],
    )
    assert peak(sampled(values, 0.002))["amplitude"] == 2
    assert peak(sampled(values, 0.002, 0.001))["amplitude"] == 9
    assert peak(values)["omega"] == 0.081
