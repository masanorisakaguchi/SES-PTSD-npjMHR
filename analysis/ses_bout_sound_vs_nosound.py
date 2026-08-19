"""Did the SES night's N3 fragmentation happen DURING sound, or also OUTSIDE sound?

Design fact that makes this discriminating: sound could only start after 3 consecutive
SWS epochs (90 s of stable SWS), and the cumulative sound cap was 600 s per night. So most
of each night's N3 carried no sound, and every sound-bearing bout is >=90 s by construction.

Therefore:
  * If fragmentation were caused by the sound, sound-bearing bouts should be truncated
    relative to comparable (>=90 s) bouts without sound.
  * If fragmentation is environmental (first-night effect / hospitalisation / device),
    the NO-SOUND bouts on the clinic night should already look fragmented relative to
    the in-home nights -- i.e. the effect is present where no sound was ever delivered.

The >=90 s restriction removes the selection bias (sound-bearing bouts cannot be short).

Staging: AASM 30-s epochs (same as Figure 3). Sound: playback log, volume > 0.
"""
import csv, io, os, sys, glob
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.environ.get("SES_STAGE_ROOT", "./_private/stage_scoring")
CLN = os.environ.get("SES_LOG_ROOT", "./_private/playback_logs")
SCR = os.environ.get("SES_SCREENING_ROOT", "./_private/screening")
N3 = {"N3", "NonREM3"}
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


def read(path):
    raw = open(path, "rb").read()
    for e in ("utf-8-sig", "cp932", "utf-8"):
        try:
            return raw.decode(e)
        except Exception:
            continue
    return raw.decode("utf-8", "replace")


def epochs(path):
    """-> [(start_sec_of_day, stage)] for consecutive 30-s epochs"""
    out = []
    for r in csv.reader(io.StringIO(read(path))):
        if len(r) < 3:
            continue
        try:
            hh, mm, ss = [int(x) for x in r[1].strip().split(":")]
        except Exception:
            continue
        out.append((hh * 3600 + mm * 60 + ss, r[2].strip()))
    return out


def sound_secs(pid):
    s = set()
    for rel in SOUND[pid]:
        p = os.path.join(ROOT, rel)
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
                s.add(hh * 3600 + mm * 60 + ss)
    return s


def n3_bouts(eps):
    """-> [(n_epochs, set_of_seconds)]"""
    out, cur = [], []
    for st, stg in eps:
        if stg in N3:
            cur.append(st)
        elif cur:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return [(len(b), set(t for s in b for t in range(s, s + 30))) for b in out]


def stats(vals):
    if not vals:
        return "n=0"
    v = sorted(vals)
    return "n=%d  mean %6.1f s  median %5d s  max %5d s" % (
        len(v), sum(v) * 30.0 / len(v), v[len(v) // 2] * 30, max(v) * 30)


print("=" * 104)
print("SES夜の N3 bout: 音刺激を含む bout と 含まない bout の比較（AASM判定・30秒エポック）")
print("=" * 104)
for pid in ["H01", "H02", "H03", "H08", "H09", "H14"]:
    if pid == "H14":
        eps = []
        for seg in "①②③":
            p = os.path.join(CLN, "stagelist_H14%s.csv" % seg)
            if os.path.exists(p): eps += epochs(p)
    else:
        p = os.path.join(CLN, "stagelist_%s.csv" % pid)
        eps = epochs(p) if os.path.exists(p) else []
    if not eps:
        print("\n### %s  (staging なし)" % pid); continue
    snd = sound_secs(pid)
    bouts = n3_bouts(eps)
    withs = [n for n, secs in bouts if secs & snd]
    without = [n for n, secs in bouts if not (secs & snd)]
    w90 = [n for n in withs if n >= 3]
    n90 = [n for n in without if n >= 3]
    # in-home comparison, >=90 s bouts only
    home = []
    for f in sorted(glob.glob(os.path.join(SCR, "%s_stage_*.csv" % pid))):
        if pid == "H08" and "25540_89801" in f:
            continue        # pre-consent recording, excluded in the paper
        home += [n for n, _ in n3_bouts(epochs(f))]
    h90 = [n for n in home if n >= 3]
    print("\n### %s" % pid)
    print("   院内 音を含む bout      : %s" % stats(withs))
    print("   院内 音を含まない bout  : %s" % stats(without))
    print("   --- 90秒以上に限定（選択バイアス除去）---")
    print("   院内 音あり >=90s       : %s" % stats(w90))
    print("   院内 音なし >=90s       : %s" % stats(n90))
    print("   在宅     >=90s          : %s" % stats(h90))
