#!/usr/bin/env python3
"""Effective jelly-roll properties of the LG M50 from the PyBaMM "ORegan2022" parameter set (D3).

One electrode pair per unit area: half the copper foil, negative electrode, separator, positive electrode,
half the aluminium foil. Density and specific heat are mass-weighted; through-layer conductivity is the series
(harmonic) mean and in-plane conductivity the parallel (arithmetic) mean, both thickness-weighted.
Usage: python3 oregan2022_properties.py > oregan2022_properties.txt
"""
import pybamm

p = pybamm.ParameterValues("ORegan2022")


def ev(name, T):
    v = p[name]
    if callable(v):
        return float(p.process_symbol(v(pybamm.Scalar(T))).evaluate())
    return float(v)


names = {"cn": "Negative current collector", "n": "Negative electrode", "s": "Separator",
         "p": "Positive electrode", "cp": "Positive current collector"}
L = {"cn": p["Negative current collector thickness [m]"] / 2, "n": p["Negative electrode thickness [m]"],
     "s": p["Separator thickness [m]"], "p": p["Positive electrode thickness [m]"],
     "cp": p["Positive current collector thickness [m]"] / 2}
Ltot = sum(L.values())
area = p["Electrode height [m]"] * p["Electrode width [m]"]
print(f"PyBaMM {pybamm.__version__}, parameter set ORegan2022")
print(f"pair thickness {Ltot*1e6:.1f} um, electrode area {area:.4f} m2, roll volume {area*Ltot:.4e} m3")
print(f"cell volume {p['Cell volume [m3]']:.3e} m3, cooling area {p['Cell cooling surface area [m2]']:.5f} m2")
print("T_C   rho_eff  cp_eff  k_radial  k_inplane  roll_mass_g")
for TC in (0, 25, 40, 60, 80, 100, 150, 200):
    T = TC + 273.15
    rho = {k: ev(names[k] + " density [kg.m-3]", T) for k in L}
    cp = {k: ev(names[k] + " specific heat capacity [J.kg-1.K-1]", T) for k in L}
    kk = {k: ev(names[k] + " thermal conductivity [W.m-1.K-1]", T) for k in L}
    m = sum(rho[k] * L[k] for k in L)
    print(f"{TC:4d} {m/Ltot:8.1f} {sum(rho[k]*cp[k]*L[k] for k in L)/m:7.1f} "
          f"{Ltot/sum(L[k]/kk[k] for k in L):8.3f} {sum(kk[k]*L[k] for k in L)/Ltot:9.2f} {m/Ltot*area*Ltot*1e3:10.1f}")
print("Note: the component specific-heat fits are polynomials; above about 150 C they are non-physical "
      "(positive electrode cp at 200 C:", round(ev("Positive electrode specific heat capacity [J.kg-1.K-1]", 473.15)), "J/kgK).")
