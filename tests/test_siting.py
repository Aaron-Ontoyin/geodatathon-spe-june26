from __future__ import annotations

import numpy as np

from geothermal.resource.siting import candidate_lattice
from geothermal import config


def test_lattice_covers_box_at_pitch_and_includes_wells() -> None:
    center = (141171.0, 454890.0)
    pts = candidate_lattice(center=center, size_km=20.0, pitch_km=1.5)
    xs = pts[:, 0]; ys = pts[:, 1]
    assert xs.min() >= center[0] - 10000 - 1e-6 and xs.max() <= center[0] + 10000 + 1e-6
    blt = config.WELLS["BLT-01"]
    assert np.any((np.abs(xs - blt.x) < 1e-6) & (np.abs(ys - blt.y) < 1e-6))


def test_no_two_candidates_closer_than_pitch() -> None:
    pts = candidate_lattice(center=(141171.0, 454890.0), size_km=20.0, pitch_km=1.5)
    d = np.hypot(pts[:, None, 0] - pts[None, :, 0], pts[:, None, 1] - pts[None, :, 1])
    np.fill_diagonal(d, np.inf)
    assert d.min() >= 1500.0 - 1.0
