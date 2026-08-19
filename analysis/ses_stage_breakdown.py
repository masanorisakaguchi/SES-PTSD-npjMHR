"""R1 requirement (2): in which sleep stages did the sound actually occur?

Joins the 1 Hz Audioplay sound-on timeline to the post-hoc expert hypnogram
(30-s epochs, clock time) and reports the stage composition of sound-on seconds.

Built-in validation: the resulting N3 share must reproduce the published Table 2
(H01 84.0%, H02 51.4%, H03 83.7%, H08 70.5%, H09 88.5%, H14 31.2%). If it does,
the two clocks are aligned; if not, alignment (or the epoch convention) is wrong
and the number must NOT be reported.

Read-only.
"""
import csv, io, os, sys, datetime
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.environ.get("SES_STAGE_ROOT", "./_private/stage_scoring")
HYP = os.path.join(ROOT, r"Manuscript\data\20250722 SleepAnalysisData\P1 Unit recording")

SOUND = {
    "H01": [r"Participants\H01\20241026SES-A1\sound_log\records_2024-10-26-21-46.csv"],
    "H02": [r"Participants\未整理データ\UnidentifiedSoundLogs\records_2024-12-21-22-09.csv"],
    "H03": [r"Participants\H03\Visit-4\Soundlog\records_2025-04-19-22-06.csv"],
    "H08": [r"Participants\H08\Visit-4\Soundlog\records_2025-05-23-22-00.csv"],
    "H09": [r"Participants\H09\Visit-4\Soundlog\records_2025-05-23-21-27.csv"],
}
PUBLISHED = {"H01": 84.0, "H02": 51.4, "H03": 83.7, "H08": 70.5, "H09": 88.5}


def load_hypno(pid):
    """-> list of (start_seconds_of_day, stage) for consecutive 30-s epochs"""
    p = os.path.join(HYP, pid + ".csv")
    if not os.path.exists(p):
        return None
    out = []
    with open(p, encoding="utf-8-sig", errors="replace", newline="") as fh:
        rd = csv.reader(fh)
        next(rd, None)
        for r in rd:
            if len(r) < 3:
                continue
            t = r[1].strip()
            st = r[2].strip()
            try:
                hh, mm, ss = [int(x) for x in t.split(":")]
            except Exception:
                continue
            out.append((hh * 3600 + mm * 60 + ss, st))
    return out


def load_sound_on(pid):
    """-> list of seconds-of-day where volume > 0"""
    secs = []
    for rel in SOUND[pid]:
        p = os.path.join(ROOT, rel)
        with open(p, encoding="utf-8", errors="replace", newline="") as fh:
            rd = csv.reader(fh)
            next(rd, None)
            cols = next(rd, None)
            n = len(cols)
            for r in rd:
                if n == 7 and len(r) >= 7:
                    ts, vol = r[0], r[6]
                elif len(r) >= 8:
                    ts, vol = r[0], r[7]
                else:
                    continue
                try:
                    v = int(float(vol))
                except Exception:
                    continue
                if v <= 0:
                    continue
                # timestamp format "DD HH:MM:SS"
                try:
                    clock = ts.strip().split(" ", 1)[1]
                    hh, mm, ss = [int(x) for x in clock.split(":")]
                except Exception:
                    continue
                secs.append(hh * 3600 + mm * 60 + ss)
    return secs


NORM = {"N3": "N3", "NonREM3": "N3", "N2": "N2", "NonREM2": "N2",
        "N1": "N1", "NonREM1": "N1", "REM": "REM", "R": "REM",
        "WK": "Wake", "W": "Wake", "Wake": "Wake", "NS": "NotScored"}

print("=" * 76)
print("R1 req(2): stage composition of sound-on seconds")
print("=" * 76)

for pid in ["H01", "H02", "H03", "H08", "H09"]:
    hyp = load_hypno(pid)
    if hyp is None:
        print(f"\n{pid}: hypnogram MISSING")
        continue
    on = load_sound_on(pid)
    # epoch lookup: hypnogram epochs are consecutive 30 s from the listed start time
    # build a dict second-of-day -> stage
    lut = {}
    for start, st in hyp:
        for k in range(30):
            lut[(start + k) % 86400] = st
    comp = Counter()
    for s in on:
        comp[NORM.get(lut.get(s, "?"), lut.get(s, "?") or "?")] += 1
    tot = sum(comp.values())
    n3 = comp.get("N3", 0)
    pub = PUBLISHED[pid]
    got = 100.0 * n3 / tot if tot else 0.0
    ok = "MATCH" if abs(got - pub) <= 1.5 else "*** MISMATCH ***"
    print(f"\n----- {pid} -----  sound-on {len(on)} s, matched to hypnogram {tot} s")
    print(f"   published Table 2 N3 = {pub}%   computed N3 = {got:.1f}%   -> {ok}")
    for k in ["N3", "N2", "N1", "REM", "Wake", "NotScored", "?"]:
        if comp.get(k):
            print(f"      {k:<10} {comp[k]:5d} s  ({100.0*comp[k]/tot:5.1f}%)")

print("\n" + "=" * 76)
print("H14: no in-clinic hypnogram available -> cannot be computed (see strategy doc §4.2)")
