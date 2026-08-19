# -*- coding: utf-8 -*-
"""音提示中の各秒を「技師の AASM 判定」×「当方の進む窓の基準」で交差集計する。

PI 直命（2026-08-17 判断シート 17_2144 記入）:
  「otherがそんなに多かったら納得してくれないだろう。説明なしには。
    覚醒やREMではぜったいにない、のは勿論書かないとダメ。
    全部技師判定しているのだから、otherもちゃんと判定すれば良いのでは無いか。
    これは境界線をどう引くかの問題で、それをひけばotherもちゃんと判定が付くのでは無いのか？」

→ "Other" は当方の基準から漏れた残りに付けた名前であって、技師判定が無いわけではない。
   ここで技師判定そのものを取り直し、交差表として全部出す。

集計の定義（regen_fig6bc_20260817.py と同一の関数を輸入して使う）:
  tech  : 技師の固定30秒グリッド判定（stagelist_*.csv）。秒 -> Wake/N1/N2/N3/REM
  arous : 技師の覚醒タグ（区間）。窓 [t-29, t+1] に重なるか
  sws   : 進む窓（1秒ステップ・30秒窓）で delta タグの合計 >= 6.0 秒
"""
import csv
import io
import importlib.util
import os
import sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ANA = os.path.join(os.path.dirname(HERE), "_analysis_20260725")
UNIFY = os.path.join(ANA, "ses_table2_unify_20260815.py")

_spec = importlib.util.spec_from_file_location("unify", UNIFY)
_src = open(UNIFY, encoding="utf-8").read()
_body = _src.split('print("PID')[0].replace(
    'sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")', '')
_m = importlib.util.module_from_spec(_spec)
exec(compile(_body, "unify", "exec"), _m.__dict__)
load_tags, overlap, on_seconds = _m.load_tags, _m.overlap, _m.on_seconds
DRIVE = _m.DRIVE

PIDS = ["H01", "H02", "H03", "H08", "H09", "H14"]
NORM = {"WK": "Wake", "Wk": "Wake", "W": "Wake", "Wake": "Wake", "N1": "N1", "N2": "N2",
        "N3": "N3", "NonREM1": "N1", "NonREM2": "N2", "NonREM3": "N3", "REM": "REM", "NS": "NS"}


def stage_lut(pid):
    lut = {}
    files = ["stagelist_H14①.csv", "stagelist_H14②.csv", "stagelist_H14③.csv"] \
        if pid == "H14" else ["stagelist_%s.csv" % pid]
    for fn in files:
        p = os.path.join(DRIVE, fn)
        if not os.path.exists(p):
            continue
        raw = open(p, "rb").read()
        for enc in ("utf-8-sig", "cp932", "utf-8"):
            try:
                text = raw.decode(enc)
                break
            except Exception:
                text = raw.decode("utf-8", "replace")
        for r in csv.reader(io.StringIO(text)):
            if len(r) < 3:
                continue
            try:
                hh, mm, ss = [int(x) for x in r[1].strip().split(":")]
            except Exception:
                continue
            s0 = hh * 3600 + mm * 60 + ss
            stg = NORM.get(r[2].strip(), r[2].strip())
            for k in range(30):
                lut[(s0 + k) % 86400] = stg
    return lut


TECH = ["N3", "N2", "N1", "REM", "Wake"]


def main():
    per_pid = {}
    tot = Counter()
    tot_tech = Counter()
    tot_n = 0
    print("== 交差集計: 行=技師の固定グリッド判定 / 列=進む窓の基準 ==\n")
    for pid in PIDS:
        delta, arous = load_tags(pid)
        secs = on_seconds(pid)
        lut = stage_lut(pid)
        c = Counter()
        for t in secs:
            lo, hi = t - 29, t + 1
            s = 0.0
            for d in delta:
                if d[1] <= lo:
                    continue
                if d[0] >= hi:
                    break
                s += overlap(d, lo, hi)
            sws = s >= 6.0
            ar = any(overlap(a, lo, hi) > 0 for a in arous)
            st = lut.get(t, "unscored")
            c[(st, sws, ar)] += 1
        per_pid[pid] = (c, len(secs))
        tot.update(c)
        tot_n += len(secs)
        for k, v in c.items():
            tot_tech[k[0]] += v
        print("%s: sound-on %d s" % (pid, len(secs)))
        for st in TECH + ["unscored"]:
            n = sum(v for k, v in c.items() if k[0] == st)
            if n == 0:
                continue
            n_sws = sum(v for k, v in c.items() if k[0] == st and k[1])
            n_ar = sum(v for k, v in c.items() if k[0] == st and k[2])
            print("   %-8s %5d  (うち進む窓でSWS %5d / 覚醒タグ重なり %4d)" % (st, n, n_sws, n_ar))
    print("\n== 6名合計（sound-on %d 秒） ==" % tot_n)
    print("%-8s %7s %8s %8s %8s" % ("技師判定", "秒", "全体%", "うちSWS", "覚醒タグ"))
    for st in TECH + ["unscored"]:
        n = tot_tech.get(st, 0)
        if n == 0 and st != "unscored":
            print("%-8s %7d %7.1f%% %8d %8d" % (st, 0, 0.0, 0, 0))
            continue
        if n == 0:
            continue
        n_sws = sum(v for k, v in tot.items() if k[0] == st and k[1])
        n_ar = sum(v for k, v in tot.items() if k[0] == st and k[2])
        print("%-8s %7d %7.1f%% %8d %8d" % (st, n, 100.0 * n / tot_n, n_sws, n_ar))
    sws_all = sum(v for k, v in tot.items() if k[1])
    print("\n進む窓の基準を満たした秒（Table 2 の分子）: %d / %d = %.1f%%"
          % (sws_all, tot_n, 100.0 * sws_all / tot_n))
    print("技師 N3 の秒                              : %d / %d = %.1f%%"
          % (tot_tech["N3"], tot_n, 100.0 * tot_tech["N3"] / tot_n))
    print("両方を満たす秒                            : %d"
          % sum(v for k, v in tot.items() if k[0] == "N3" and k[1]))
    print("技師N3だが進む窓では非SWS                 : %d"
          % sum(v for k, v in tot.items() if k[0] == "N3" and not k[1]))
    print("進む窓ではSWSだが技師はN3でない           : %d"
          % sum(v for k, v in tot.items() if k[0] != "N3" and k[1]))
    for st in TECH:
        n = sum(v for k, v in tot.items() if k[0] == st and k[1])
        if n and st != "N3":
            print("    └ 技師 %s かつ進む窓でSWS: %d" % (st, n))

    # 参加者別の技師判定内訳（図に使う数値）
    print("\n== 図 6b 用（技師の AASM 判定・排他5区分・秒） ==")
    print("PID   sound-on " + "".join("%8s" % s for s in TECH) + "   行和")
    rows = []
    for pid in PIDS:
        c, n = per_pid[pid]
        vals = [sum(v for k, v in c.items() if k[0] == st) for st in TECH]
        assert sum(vals) == n, "%s: %d != %d" % (pid, sum(vals), n)
        print("%-5s %8d " % (pid, n) + "".join("%8d" % v for v in vals) + "   %5d OK" % sum(vals))
        rows.append([pid, n] + vals)
    tv = [tot_tech.get(st, 0) for st in TECH]
    print("%-5s %8d " % ("計", tot_n) + "".join("%8d" % v for v in tv) + "   %5d" % sum(tv))
    print("      %8s " % "" + "".join("%7.1f%%" % (100.0 * v / tot_n) for v in tv))

    out = os.path.join(HERE, "prism_csv", "Fig_R1b_technician_stage_composition.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["Participant", "Sound-on total (s)"] + ["%s (s)" % s for s in TECH])
        wr.writerows(rows)
    print("\n[written] prism_csv/Fig_R1b_technician_stage_composition.csv")


if __name__ == "__main__":
    main()
