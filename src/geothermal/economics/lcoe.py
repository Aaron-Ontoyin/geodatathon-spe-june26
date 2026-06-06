"""Levelized cost of energy — the core annuity formulation.

Ports the provided TNO/ECN ``LCOE.xlsx`` model to the standard levelized form
``LCoE = (CRF·CAPEX + annual OPEX) / annual energy``. The provider's spreadsheet
uses a detailed debt/equity/tax cash flow (80/20 split, 6% debt, 15% equity, 25%
tax, 15-year life, straight-line depreciation), discounting levered after-tax
cash flows at the equity return; we capture that with a single **effective
discount rate of 9.3%**, chosen so this form reproduces the spreadsheet's
base-case direct-heat result (5.77 €/GJ for 2 wells, 290,449 GJ/yr, 8.79 M€).

This single rate is not merely a base-case fit: with the financial structure
fixed (as it is across our designs) and flat annual profiles (inflation = 0),
the spreadsheet's LCoE is *linear* in CAPEX, OPEX and energy, and the OPEX and
energy terms carry the same discount factor, which cancels in the ratio. So the
spreadsheet LCoE reduces to ``(α·CAPEX + OPEX) / energy`` for a structural
constant ``α``; calibrating CRF to ``α`` makes this form reproduce the
spreadsheet for *every* design, not just the base case. We verified this
empirically: a faithful re-implementation of the levered DCF tracks this form
by a constant ratio across capex/opex/energy-varied designs. The only place the
two part company is when ``discount_rate`` or ``economic_lifetime_years`` are
themselves swept as levers, where this rate is a simplification of the full
WACC/tax structure rather than a re-derivation of it.
"""

from __future__ import annotations

DISCOUNT_RATE = 0.093  # effective; reproduces LCOE.xlsx base-case heat LCoE
ECONOMIC_LIFETIME_YEARS = 15
GJ_PER_MWH = 3.6


def capital_recovery_factor(discount_rate: float, lifetime_years: int) -> float:
    """Annuity factor converting an up-front cost into an equal yearly charge."""
    if discount_rate == 0.0:
        return 1.0 / lifetime_years
    growth = (1.0 + discount_rate) ** lifetime_years
    return discount_rate * growth / (growth - 1.0)


def levelized_cost_eur_per_mwh(
    *,
    capex_eur: float,
    annual_opex_eur: float,
    annual_energy_mwh: float,
    discount_rate: float = DISCOUNT_RATE,
    lifetime_years: int = ECONOMIC_LIFETIME_YEARS,
) -> float:
    """Levelized cost (€/MWh) of delivered energy."""
    if annual_energy_mwh <= 0.0:
        return float("inf")
    crf = capital_recovery_factor(discount_rate, lifetime_years)
    return (crf * capex_eur + annual_opex_eur) / annual_energy_mwh


def levelized_cost_eur_per_gj(
    *,
    capex_eur: float,
    annual_opex_eur: float,
    annual_energy_gj: float,
    discount_rate: float = DISCOUNT_RATE,
    lifetime_years: int = ECONOMIC_LIFETIME_YEARS,
) -> float:
    """Levelized cost (€/GJ) of delivered energy."""
    return (
        levelized_cost_eur_per_mwh(
            capex_eur=capex_eur,
            annual_opex_eur=annual_opex_eur,
            annual_energy_mwh=annual_energy_gj / GJ_PER_MWH,
            discount_rate=discount_rate,
            lifetime_years=lifetime_years,
        )
        / GJ_PER_MWH
    )
