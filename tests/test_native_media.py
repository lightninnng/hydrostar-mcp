"""Phase validation must reject a closed field with missing motion quadrature."""

import pytest

from scripts.check_native_media import validate_complex_radiation
from scripts.encode_native_media import viewport_pixel_hashes, require_field_variation


def test_closed_components_with_missing_motion_phase_are_rejected():
    incident = 1 + 0j
    diffraction = 0.2 - 0.1j
    motion = 0.3 + 0.4j
    unit_velocity_radiation = 0.5 + 0.2j
    correct = 1j * 0.8 * motion * unit_velocity_radiation
    incomplete = 1j * 0.8 * motion.real * unit_velocity_radiation
    # Adding incomplete components gives a perfectly closed but incorrect field.
    closed_total = incident + diffraction + incomplete
    with pytest.raises(ValueError, match="Full-complex radiation"):
        validate_complex_radiation(closed_total, incident, diffraction, correct, 1e-8)
    assert (
        validate_complex_radiation(
            incident + diffraction + correct, incident, diffraction, correct, 1e-8
        )
        < 1e-12
    )


def test_changing_png_metadata_does_not_count_as_dynamic_field_pixels(tmp_path):
    from PIL import Image, PngImagePlugin
    import hashlib

    paths = []
    for i in range(2):
        path = tmp_path / f"frame{i}.png"
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("time", str(i))
        Image.new("RGB", (3600, 680), "white").save(path, pnginfo=metadata)
        paths.append(path)
    assert (
        hashlib.sha256(paths[0].read_bytes()).digest()
        != hashlib.sha256(paths[1].read_bytes()).digest()
    )
    with pytest.raises(ValueError, match="did not refresh"):
        require_field_variation(viewport_pixel_hashes(paths), minimum_unique=2)
