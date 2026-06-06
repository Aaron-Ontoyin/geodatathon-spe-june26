from __future__ import annotations

import numpy as np

from geothermal import config
from geothermal.resource import siting
from geothermal.resource.properties import SiteProperties
from geothermal.resource.siting import candidate_lattice


def test_lattice_covers_box_at_pitch_and_includes_wells() -> None:
    center = (141171.0, 454890.0)
    pts = candidate_lattice(center=center, size_km=20.0, pitch_km=1.5)
    xs = pts[:, 0]
    ys = pts[:, 1]
    assert xs.min() >= center[0] - 10000 - 1e-6 and xs.max() <= center[0] + 10000 + 1e-6
    blt = config.WELLS["BLT-01"]
    assert np.any((np.abs(xs - blt.x) < 1e-6) & (np.abs(ys - blt.y) < 1e-6))


def test_no_two_candidates_closer_than_pitch() -> None:
    pts = candidate_lattice(center=(141171.0, 454890.0), size_km=20.0, pitch_km=1.5)
    d = np.hypot(pts[:, None, 0] - pts[None, :, 0], pts[:, None, 1] - pts[None, :, 1])
    np.fill_diagonal(d, np.inf)
    assert d.min() >= 1500.0 - 1.0


def _fake_site(x: float, y: float) -> SiteProperties:
    power = (x - 131000.0) / 2000.0
    return SiteProperties(
        x=x,
        y=y,
        transmissivity_dm=power,
        temperature_c=77.0,
        power_mw_p50=power,
        depth_m=2200.0,
        sigma_log_trans=0.9,
        source="thermogis_grid",
    )


def test_candidates_filtered_and_shortlisted() -> None:
    pts = siting.candidate_lattice(center=(141171.0, 454890.0), size_km=20.0, pitch_km=1.5)
    sites = siting.build_candidates(pts, provider=_fake_site, viability_floor_mw=2.0)
    assert all(s.power_mw_p50 >= 2.0 for s in sites)
    short = siting.shortlist(sites, size=10)
    assert len(short) == 10
    assert short[0].power_mw_p50 >= short[-1].power_mw_p50
