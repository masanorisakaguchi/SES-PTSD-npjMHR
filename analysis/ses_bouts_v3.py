"""R1 requirement (1), corrected for midnight wraparound.

Bug in v1: tag clock times wrap at 00:00, so min/max over seconds-of-day produced a
nonsense span for recordings that cross midnight (H01 in-clinic came out 3.4 min, H14 0).
Fix: unwrap within each tag file (rows are chronological -- add 86400 whenever time
decreases), and treat each tag file as its own recording segment.

SWS second = no arousal tag overlapping [t-29, t+1) AND sum of delta overlap >= 6.0 s
bout       = maximal run of consecutive SWS seconds
frag       = bouts per hour of SWS
"""
import csv, io, os, sys, zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.environ.get("SES_STAGE_ROOT", "./_private/stage_scoring")
DRIVE = os.environ.get("SES_LOG_ROOT", "./_private/playback_logs")
INBOX = os.environ.get("SES_INBOX_ROOT", "./_private")
Z = zipfile.ZipFile(os.path.join(ROOT, r"宿泊SES臨床研究\Manuscript\data\EEGdata\タグ付け済み-20250622T062816Z-1-001.zip"))
SU = os.path.join(ROOT, r"S'UIMIN\20250319 6nights data for RangeAI")


def dec(b):
    for e in ("cp932", "utf-8-sig", "utf-8"):
        try: return b.decode(e)
        except Exception: pass
    return b.decode("utf-8", "replace")


def intervals(text):
    """chronological rows -> unwrapped (start, end) seconds on a monotonic timeline"""
    out, prev, off = [], None, 0
    rd = csv.reader(io.StringIO(text)); next(rd, None)
    for r in rd:
        if len(r) < 5: continue
        try:
            hh, mm, ss = [int(x) for x in r[2].strip().split(":")]
            d = float(r[4])
        except Exception:
            continue
        s = hh*3600 + mm*60 + ss
        if prev is not None and s + off < prev - 3600:   # wrapped past midnight
            off += 86400
        prev = s + off
        out.append((s + off, s + off + d))
    return out


def zf(n):  return intervals(dec(Z.read(n)))
def ff(p):  return intervals(dec(open(p, "rb").read())) if os.path.exists(p) else []
def n2(rec): return (ff(os.path.join(DRIVE, "new202512_delta_%s.csv" % rec)),
                     ff(os.path.join(DRIVE, "new202512_arousal_%s.csv" % rec)))


def sws(delta, arous):
    if not delta: return []
    lo = int(min(d[0] for d in delta)) - 60
    hi = int(max(d[1] for d in delta)) + 60
    out = []
    for t in range(lo, hi):
        a, b = t - 29, t + 1
        if any(x[1] > a and x[0] < b for x in arous):
            continue
        s = 0.0
        for x in delta:
            if x[1] <= a: continue
            if x[0] >= b: break
            s += min(x[1], b) - max(x[0], a)
        if s >= 6.0:
            out.append(t)
    return out


def bouts(secs):
    if not secs: return []
    runs, cur = [], 1
    for i in range(1, len(secs)):
        if secs[i] == secs[i-1] + 1: cur += 1
        else: runs.append(cur); cur = 1
    runs.append(cur)
    return runs


def show(tag, runs_list):
    runs = [r for rs in runs_list for r in rs]
    if not runs:
        print("   %-24s (SWS 0)" % tag); return
    tot = sum(runs); s = sorted(runs)
    print("   %-24s SWS %6.1f min | bouts %4d | mean %6.1f s | median %5d s | max %5d s | frag %5.1f /h"
          % (tag, tot/60, len(runs), tot/len(runs), s[len(s)//2], max(runs), len(runs)/(tot/3600.0)))


CLINIC = {
    "H01": [zf("タグ付け済み/H01_東大/delta_H01-20241026.csv"), zf("タグ付け済み/H01_東大/arousal_H01-20241026.csv")],
    "H02": [zf("タグ付け済み/H02_東大/delta_H02-20241221.csv"), zf("タグ付け済み/H02_東大/arousal_H02-20241221.csv")],
    "H03": [zf("タグ付け済み/H03_東大/delta_H03.csv"), zf("タグ付け済み/H03_東大/arousal_H03.csv")],
    "H08": [ff(os.path.join(INBOX, "20251104_chinatsu23k_delta_H08_#237_removed.csv")),
            ff(os.path.join(INBOX, "20251104_chinatsu23k_arousal_H08_#237_add.csv"))],
    "H09": [zf("タグ付け済み/H09_東大/delta_H09.csv"), zf("タグ付け済み/H09_東大/arousal_H09.csv")],
}
SCREEN = {
    "H01": [("n1 71950", n2("18955_71950")), ("n2 72113", n2("18955_72113")),
            ("n3 72025", (ff(os.path.join(SU, "H01_スクリーニング (ID18955 ir72025)", "delta_H01スクリーニング(ID18955 ir72025).csv")),
                          ff(os.path.join(SU, "H01_スクリーニング (ID18955 ir72025)", "arousal_H01スクリーニング(ID18955 ir72025).csv"))))],
    "H02": [("n1 75789", n2("18954_75789")),
            ("n2 75978", (ff(os.path.join(SU, "H02_スクリーニング (ID18954 ir75978)", "delta_H02スクリーニング(ID18954 ir75978).csv")),
                          ff(os.path.join(SU, "H02_スクリーニング (ID18954 ir75978)", "arousal_H02スクリーニング(ID18954 ir75978).csv"))))],
    "H03": [("n1 88500", n2("25542_88500")), ("n2 88652", n2("25542_88652")), ("n3 88753", n2("25542_88753"))],
    "H08": [("初回 89801", n2("25540_89801")),
            ("再n1 91242", n2("26278_91242")), ("再n2 91279", n2("26278_91279")), ("再n3 91373", n2("26278_91373"))],
    "H09": [("n1 95182", n2("26626_95182")), ("n2 95387", n2("26626_95387")),
            ("n3 96390", n2("26626_96390")), ("n4 96393", n2("26626_96393"))],
}

print("=" * 116)
print("R1 requirement (1) -- N3 bouts, in-home screening vs in-clinic SES night")
print("SWS = Table 2 delta-tag rule, applied identically to both conditions")
print("=" * 116)
for pid in ["H01", "H02", "H03", "H08", "H09", "H14"]:
    print("\n### %s" % pid)
    if pid == "H14":
        rs = []
        for seg in "①②③":
            d = ff(os.path.join(DRIVE, "H14tag_H14%s_delta.csv" % seg))
            a = ff(os.path.join(DRIVE, "H14tag_H14%s_arousal.csv" % seg))
            rs.append(bouts(sws(d, a)))
        show("in-clinic (3 segments)", rs)
    else:
        d, a = CLINIC[pid]
        show("in-clinic SES night", [bouts(sws(d, a))])
    for name, (sd, sa) in SCREEN.get(pid, []):
        show("in-home " + name, [bouts(sws(sd, sa))])
    if pid not in SCREEN:
        print("   %-24s (screening tags not mapped to this participant)" % "in-home")
