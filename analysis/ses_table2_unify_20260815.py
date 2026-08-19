"""Table 2（3,610秒）と回答書・追加図（3,604秒）の秒数を一次データから一本化する。
PI 判断3 = A（2026-08-15）: 提出前に一次データから両方を計算し直して一本化する。

規約は川上千夏さんの正本スライドとハンさんのメール（25_1058 §8.5.1）に逐語で書かれている:
  1. 音ON/OFF: V4音出しログの音量。0→OFF / >0→ON。
     ★「1秒刻みでない箇所は重複削除＋前行複製で補充」＝ run 内の1秒の抜けは埋める。
        （これまでの実装は重複を削らず・抜けも埋めていなかった＝3,604秒の出所）
  2. 秒 t のステージ: 直前30秒窓 [t-29, t+1)。
  3. arousalタグが窓に重なれば Wake。無く かつ Σoverlap(deltaタグ,窓) >= 6.0秒 なら N3。
  4. 分子 = ON秒のうち N3。分母 = ON秒数。

出力: 参加者別の分母・N3・Wake・割合と、6名の合計。
"""
import csv, io, os, sys, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.environ.get("SES_STAGE_ROOT", "./_private/stage_scoring")
DRIVE = os.environ.get("SES_LOG_ROOT", "./_private/playback_logs")
INBOX = os.environ.get("SES_INBOX_ROOT", "./_private")
Z = zipfile.ZipFile(os.path.join(
    ROOT, r"Manuscript\data\EEGdata\タグ付け済み-20250622T062816Z-1-001.zip"))
ARCH = {
    "H01": ("タグ付け済み/H01_東大/delta_H01-20241026.csv", "タグ付け済み/H01_東大/arousal_H01-20241026.csv"),
    "H02": ("タグ付け済み/H02_東大/delta_H02-20241221.csv", "タグ付け済み/H02_東大/arousal_H02-20241221.csv"),
    "H03": ("タグ付け済み/H03_東大/delta_H03.csv", "タグ付け済み/H03_東大/arousal_H03.csv"),
    "H09": ("タグ付け済み/H09_東大/delta_H09.csv", "タグ付け済み/H09_東大/arousal_H09.csv"),
}
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
PUB_N3 = {"H01": 504, "H02": 309, "H03": 503, "H08": 424, "H09": 533, "H14": 189}
PUB_DEN = {"H01": 600, "H02": 601, "H03": 601, "H08": 601, "H09": 602, "H14": 605}
GAP_FILL = 2   # run 内の抜け（<= GAP_FILL 秒）を埋める。それ以上離れていれば別 run。


def dec(b):
    for e in ("cp932", "utf-8-sig", "utf-8"):
        try:
            return b.decode(e)
        except Exception:
            pass
    return b.decode("utf-8", "replace")


def intervals(text):
    out = []
    rd = csv.reader(io.StringIO(text))
    next(rd, None)
    for r in rd:
        if len(r) < 5:
            continue
        try:
            hh, mm, ss = [int(x) for x in r[2].strip().split(":")]
            d = float(r[4])
        except Exception:
            continue
        s = hh * 3600 + mm * 60 + ss
        out.append((s, s + d))
    return sorted(out)


def load_tags(pid):
    if pid == "H08":
        return (intervals(dec(open(os.path.join(INBOX, "20251104_chinatsu23k_delta_H08_#237_removed.csv"), "rb").read())),
                intervals(dec(open(os.path.join(INBOX, "20251104_chinatsu23k_arousal_H08_#237_add.csv"), "rb").read())))
    if pid == "H14":
        d, a = [], []
        for seg in "①②③":
            d += intervals(dec(open(os.path.join(DRIVE, f"H14tag_H14{seg}_delta.csv"), "rb").read()))
            a += intervals(dec(open(os.path.join(DRIVE, f"H14tag_H14{seg}_arousal.csv"), "rb").read()))
        return sorted(d), sorted(a)
    return intervals(dec(Z.read(ARCH[pid][0]))), intervals(dec(Z.read(ARCH[pid][1])))


def raw_on(path):
    """音量>0 の秒（重複を含む生の行）"""
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        rd = csv.reader(fh)
        next(rd, None)
        cols = next(rd, None)
        n = len(cols) if cols else 0
        for r in rd:
            if n == 7 and len(r) >= 7:
                ts, vol = r[0], r[6]
            elif len(r) >= 8:
                ts, vol = r[0], r[7]
            else:
                continue
            try:
                v = float(vol)
            except Exception:
                continue
            if v <= 0:
                continue
            try:
                hh, mm, ss = [int(x) for x in ts.strip().split(" ", 1)[1].split(":")]
            except Exception:
                continue
            out.append(hh * 3600 + mm * 60 + ss)
    return out


def on_seconds(pid):
    """規約1を実装: 重複削除 → run 内の抜けを前行複製で補充"""
    secs = []
    for rel in SOUND[pid]:
        uniq = sorted(set(raw_on(os.path.join(ROOT, rel))))
        if not uniq:
            continue
        filled = [uniq[0]]
        for s in uniq[1:]:
            if 1 < s - filled[-1] <= GAP_FILL + 1:
                filled += list(range(filled[-1] + 1, s))
            filled.append(s)
        secs += filled
    return secs


def overlap(iv, lo, hi):
    return max(0.0, min(iv[1], hi) - max(iv[0], lo))


print("PID   分母(再計算) 公表分母  差 |  N3(再計算) 公表N3  差 | Wake |  %(再計算)  %(公表)")
tot = dict(den=0, n3=0, wake=0, pden=0, pn3=0)
rowsout = []
for pid in ["H01", "H02", "H03", "H08", "H09", "H14"]:
    delta, arous = load_tags(pid)
    on = on_seconds(pid)
    n3 = wake = 0
    for t in on:
        lo, hi = t - 29, t + 1
        if any(overlap(a, lo, hi) > 0 for a in arous):
            wake += 1
            continue
        s = 0.0
        for d in delta:
            if d[1] <= lo:
                continue
            if d[0] >= hi:
                break
            s += overlap(d, lo, hi)
        if s >= 6.0:
            n3 += 1
    den = len(on)
    pct, ppct = 100.0 * n3 / den, 100.0 * PUB_N3[pid] / PUB_DEN[pid]
    print(f"{pid}  {den:>10} {PUB_DEN[pid]:>8} {den-PUB_DEN[pid]:>+4} | "
          f"{n3:>10} {PUB_N3[pid]:>6} {n3-PUB_N3[pid]:>+4} | {wake:>4} | "
          f"{pct:>9.1f} {ppct:>8.1f}")
    rowsout.append((pid, den, n3, wake, pct))
    tot["den"] += den; tot["n3"] += n3; tot["wake"] += wake
    tot["pden"] += PUB_DEN[pid]; tot["pn3"] += PUB_N3[pid]
print(f"計   {tot['den']:>10} {tot['pden']:>8} {tot['den']-tot['pden']:>+4} | "
      f"{tot['n3']:>10} {tot['pn3']:>6} {tot['n3']-tot['pn3']:>+4} | {tot['wake']:>4} | "
      f"{100.0*tot['n3']/tot['den']:>9.1f} {100.0*tot['pn3']/tot['pden']:>8.1f}")
print(f"\n参加者平均の割合: 再計算 {sum(r[4] for r in rowsout)/6:.1f}%  "
      f"公表 {sum(100.0*PUB_N3[p]/PUB_DEN[p] for p in PUB_N3)/6:.1f}%")
