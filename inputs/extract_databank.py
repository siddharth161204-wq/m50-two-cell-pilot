#!/usr/bin/env python3
"""Cell-body energies of the LG 21700-M50 at 100 % SOC from the Battery Failure Databank (D18, D19).

Usage:
  python3 extract_databank.py --xlsx battery-failure-databank-revision2-feb24.xlsx   (regenerates databank/databank_m50_rows.csv)
  python3 extract_databank.py                                                         (uses databank/databank_m50_rows.csv)
Writes databank/databank_m50_used.csv (the tests the energies rest on) and prints min, median, max.
"""
import argparse, csv, hashlib, io, os, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = os.path.join(HERE, "databank", "databank_m50_rows.csv")
XLSX_SHA256 = "18a6b0ed0bbc881295ef9c832e4dd1937b653702ec6481834e3c6ee50c86a7c4"
ROWS_SHA256 = "b5a8792d390acd7031c555ac3230a3206405309c4a663887ffc9b9b17e57c000"
OCV_FULL = 4.1     # V: tests at or above this open-circuit voltage are the 100 % SOC tests (D18)


def from_xlsx(path):
    import openpyxl
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print("workbook SHA-256", h, "(matches)" if h == XLSX_SHA256 else "(DIFFERENT from the recorded revision)")
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)["Battery Failure Databank"]
    rows = [[("" if v is None else v) for v in r] for r in ws.iter_rows(values_only=True)]
    return rows[0], [r for r in rows[1:] if "M50" in str(r[0])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", default=None)
    args = ap.parse_args()
    if args.xlsx:
        header, rows = from_xlsx(args.xlsx)
        print(f"{len(rows)} M50 rows in the workbook")
    else:
        raw = open(ROWS, "rb").read()
        h = hashlib.sha256(raw).hexdigest()
        print("rows file SHA-256", h, "(matches)" if h == ROWS_SHA256 else "(DIFFERENT)")
        rd = list(csv.reader(io.StringIO(raw.decode("utf-8"))))
        header, rows = rd[0], rd[1:]
    col = {name: i for i, name in enumerate(header)}

    def num(r, name):
        try:
            return float(r[col[name]])
        except (TypeError, ValueError):
            return None

    used, excluded = [], []
    for r in rows:
        ocv = num(r, "Pre-Test-Cell-Open-Circuit-Voltage-V")
        rec = {"Test-ID": r[col["Test-ID"]], "Trigger-Mechanism": r[col["Trigger-Mechanism"]], "OCV_V": ocv,
               "Corrected-Total-Energy-Yield-kJ": num(r, "Corrected-Total-Energy-Yield-kJ"),
               "Energy-Fraction-Cell-Body-kJ": num(r, "Energy-Fraction-Cell-Body-kJ"),
               "Energy-Fraction-Positive-Ejecta-kJ": num(r, "Energy-Fraction-Positive-Ejecta-kJ"),
               "Energy-Fraction-Negative-Ejecta-kJ": num(r, "Energy-Fraction-Negative-Ejecta-kJ"),
               "Energy-Percent-Cell-Body-%": num(r, "Energy-Percent-Cell-Body-%"),
               "Pre-Test-Cell-Mass-g": num(r, "Pre-Test-Cell-Mass-g"),
               "Post-Test-Mass-Cell-Body-g": num(r, "Post-Test-Mass-Cell-Body-g"),
               "Mass-Ejected-g": None, "Cell-Failure-Mechanism": r[col["Cell-Failure-Mechanism"]]}
        if rec["Pre-Test-Cell-Mass-g"] is not None and rec["Post-Test-Mass-Cell-Body-g"] is not None:
            rec["Mass-Ejected-g"] = round(rec["Pre-Test-Cell-Mass-g"] - rec["Post-Test-Mass-Cell-Body-g"], 4)
        (used if (ocv is not None and ocv >= OCV_FULL) else excluded).append(rec)
    with open(os.path.join(HERE, "databank", "databank_m50_used.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(used[0].keys()))
        w.writeheader(); w.writerows(used)
    e = sorted(x["Energy-Fraction-Cell-Body-kJ"] for x in used)
    by = {}
    for x in used:
        by.setdefault(x["Trigger-Mechanism"], []).append(x["Energy-Fraction-Cell-Body-kJ"])
    print(f"100 % SOC tests (OCV >= {OCV_FULL} V): {len(used)}; by trigger:", {k: len(v) for k, v in by.items()})
    print("excluded:", [(x["Test-ID"], x["OCV_V"]) for x in excluded])
    print(f"cell-body energy kJ: min {e[0]:.4f}  median {statistics.median(e):.4f}  max {e[-1]:.4f}")
    for k, v in by.items():
        print(f"  {k}: n={len(v)} min {min(v):.3f} median {statistics.median(v):.3f} max {max(v):.3f}")
    tot = [x["Corrected-Total-Energy-Yield-kJ"] for x in used]
    pct = [x["Energy-Percent-Cell-Body-%"] for x in used]
    print(f"corrected total kJ: {min(tot):.1f} to {max(tot):.1f} (median {statistics.median(tot):.1f}); "
          f"cell-body share {min(pct):.1f} to {max(pct):.1f} % (median {statistics.median(pct):.1f} %)")
    me = [x["Mass-Ejected-g"] for x in used]
    print(f"mass ejected g: {min(me):.1f} to {max(me):.1f} (median {statistics.median(me):.1f})")
    alt = sorted(e + [x["Energy-Fraction-Cell-Body-kJ"] for x in excluded if x["OCV_V"] is None])
    print(f"if tests without a recorded OCV were included: n={len(alt)}, median {statistics.median(alt):.4f} kJ")
    print("E_BODY_LIST =", [round(e[0] * 1e3, 1), round(statistics.median(e) * 1e3, 1), round(e[-1] * 1e3, 1)])


if __name__ == "__main__":
    main()
