"""Reviewer 1: report HRV / SCL over the FULL 600-s sound-delivery window, not 3x200-s windows.

Reviewer's words: "My recommendation would be to simply report the Pearson R correlation value
over the full 600s window and refrain from discussing significance statements."

Built-in validation: the published FigS1 note says H03 was a "single continuous 600s segment -
same HRV value across all epochs". So my full-600s value for H03 must match the published
43.82 (SDNN) / 52.35 (RMSSD). If it does, the pipeline matches theirs.

HRV from Empatica PPI (peak-to-peak intervals, ms):
  SDNN  = SD of the intervals inside the window
  RMSSD = sqrt(mean of squared successive differences)
SCL from Empatica EDA, standardised within participant against a 90-s pre-onset baseline
(as stated in the Figure S2 legend), then averaged over the window.
"""
import csv, io, os, sys, math, statistics as st
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SES = os.environ.get("SES_STAGE_ROOT", "./_private/stage_scoring")

PIDS = ["H01", "H02", "H03", "H08", "H09", "H14"]
SUDS = {"H01": 0.1667, "H02": 0.1429, "H03": -0.5, "H08": -0.5, "H09": -0.8, "H14": -0.2}
PUB_SDNN = {"H01": (19.27, 17.54, 18.22), "H02": (78.99, 26.35, 25.33), "H03": (43.82, 43.82, 43.82),
            "H08": (22.80, 26.89, 28.57), "H09": (21.02, 20.41, 18.12), "H14": (51.61, 46.45, 46.45)}
PUB_RMSSD = {"H01": (20.99, 20.73, 21.47), "H02": (83.81, 19.35, 19.83), "H03": (52.35, 52.35, 52.35),
             "H08": (12.37, 14.47, 14.35), "H09": (17.66, 17.35, 16.19), "H14": (28.68, 25.09, 25.09)}
SOUND = {
    "H01": [r"Participants\H01\20241026SES-A1\sound_log\records_2024-10-26-21-46.csv"],
    "H02": [r"Participants\未整理データ\UnidentifiedSoundLogs\records_2024-12-21-22-09.csv"],
    "H03": [r"Participants\H03\Visit-4\Soundlog\records_2025-04-19-22-06.csv"],
    "H08": [r"Participants\H08\Visit-4\Soundlog\records_2025-05-23-22-00.csv"],
    "H09": [r"Participants\H09\Visit-4\Soundlog\records_2025-05-23-21-27.csv"],
    "H14": [r"Participants\H14\Visit-4\SoundPlayerLogforSleep\records_2025-08-17-21-35.csv",
            r"Participants\H14\Visit-4\SoundPlayerLogforSleep\records_2025-08-17-23-03.csv",
            r"Participants\H14\Visit-4\SoundPlayerLogforSleep\records_2025-08-18-01-53.csv"],
}
PPI = {
    "H01": r"Participants\H01\Visit-4 20241026\EmpaticaData\PPI_H01_Visit4.csv",
    "H02": r"Participants\H02\Visit-4\EmpaticaData\PPI_H02_Visit4.csv",
    "H03": r"Participants\H03\Visit-4\EmpaticaData\PPI_H03_Visit4.csv",
    "H08": r"Participants\H08\Visit-4\EmpaticaData\PPI_H08_Visit4.csv",
    "H09": r"Participants\H09\Visit-4\EmpaticaData\PPI_H09_Visit4.csv",
    "H14": r"Participants\H14\Visit-4\EmpaticaData\PPI_H14_Visit-4.csv",
}


def sound_on_secs(pid):
    """seconds-of-day where volume > 0, in order of occurrence"""
    out = []
    for rel in SOUND[pid]:
        p = os.path.join(SES, rel)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8", errors="replace", newline="") as fh:
            rd = csv.reader(fh); next(rd, None); cols = next(rd, None); n = len(cols)
            for r in rd:
                if n == 7 and len(r) >= 7: ts, vol = r[0], r[6]
                elif len(r) >= 8: ts, vol = r[0], r[7]
                else: continue
                try: v = int(float(vol))
                except Exception: continue
                if v <= 0: continue
                try: hh, mm, ss = [int(x) for x in ts.strip().split(" ", 1)[1].split(":")]
                except Exception: continue
                out.append(hh*3600+mm*60+ss)
    return out


def load_ppi(pid):
    """-> [(sec_of_day, interval_ms)]"""
    p = os.path.join(SES, PPI[pid])
    out = []
    with open(p, encoding="utf-8", errors="replace", newline="") as fh:
        rd = csv.reader(fh); next(rd, None)
        for r in rd:
            if len(r) < 2: continue
            try:
                t = r[0].strip()
                hhmmss = t.split(" ")[1].split("+")[0].split(".")[0]
                hh, mm, ss = [int(x) for x in hhmmss.split(":")]
                v = float(r[1])
            except Exception:
                continue
            out.append((hh*3600+mm*60+ss, v))
    return out


def hrv(vals):
    if len(vals) < 3:
        return None, None
    sdnn = st.pstdev(vals) if len(vals) > 1 else 0.0
    sdnn = st.stdev(vals)
    d = [vals[i+1]-vals[i] for i in range(len(vals)-1)]
    rmssd = math.sqrt(sum(x*x for x in d)/len(d)) if d else None
    return round(sdnn, 2), round(rmssd, 2)


def pearson(x, y):
    n = len(x)
    mx, my = sum(x)/n, sum(y)/n
    sx = math.sqrt(sum((a-mx)**2 for a in x)); sy = math.sqrt(sum((b-my)**2 for b in y))
    if sx == 0 or sy == 0: return None
    return sum((a-mx)*(b-my) for a, b in zip(x, y))/(sx*sy)


print("=" * 92)
print("HRV over the FULL 600-s sound-delivery window (Empatica PPI)")
print("=" * 92)
print(f"{'PID':<5} {'n intervals':>11} {'SDNN full':>10} {'RMSSD full':>11}   {'published 3 windows (SDNN)':<30}")
res = {}
for pid in PIDS:
    on = set(sound_on_secs(pid))
    ppi = load_ppi(pid)
    inwin = [v for t, v in ppi if t in on]
    sd, rm = hrv(inwin)
    res[pid] = (sd, rm, len(inwin))
    print(f"{pid:<5} {len(inwin):>11} {str(sd):>10} {str(rm):>11}   {PUB_SDNN[pid]}")

print("\n--- 検算: H03 は単一600秒区間なので公表値と一致するはず ---")
sd, rm, n = res["H03"]
print(f"   H03 SDNN  computed {sd}  vs published 43.82   diff {None if sd is None else round(sd-43.82,2)}")
print(f"   H03 RMSSD computed {rm}  vs published 52.35   diff {None if rm is None else round(rm-52.35,2)}")

ok = [p for p in PIDS if res[p][0] is not None]
if len(ok) >= 3:
    x = [SUDS[p] for p in ok]
    print("\n--- Pearson r vs SUDS change, full 600 s (n=%d) ---" % len(ok))
    for lab, idx in (("SDNN", 0), ("RMSSD", 1)):
        y = [res[p][idx] for p in ok]
        r = pearson(x, y)
        print(f"   {lab:<6} r = {r:+.3f}" if r is not None else f"   {lab}: undefined")
