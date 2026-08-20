# -*- coding: utf-8 -*-
"""補足図 S7 — 版で分けない n=6 の解析（PI 指示 2026-08-20）。

査読者1の条件 "abandon any comparison between versions" に対する実体。
版を層に使わず、6名を1つの散布図に置き、夜の SUDS 変化（%）と
追跡時の PCL-5 侵入症状の変化の関係を Pearson r（有意性の言明なし）で示す。
版は点の色にだけ使う（解析には使わない）。

数値の出どころ: Source_Data_1_REV2.xlsx の Fig4_SUDS_PrePost / Fig5_PCL5_Change。
出力: _rev2_20260814/Figure_S7_Pooled_SUDS_vs_Intrusion.(png|pdf)
"""
import io, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "_rev2_20260814")

DATA = [("H01","A",  16.67,  3), ("H02","A",  14.29,  1),
        ("H03","B", -50.00, -4), ("H08","B", -50.00, -7),
        ("H09","B", -80.00, -7), ("H14","B", -20.00, -2)]
BLACK, RED = "#1a1a1a", "#c0392b"
plt.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Arial","DejaVu Sans"],
                     "font.size":9,"axes.linewidth":0.8,"figure.facecolor":"white",
                     "axes.facecolor":"white"})
x = np.array([d[2] for d in DATA]); y = np.array([d[3] for d in DATA], float)
r = float(np.corrcoef(x, y)[0,1])

fig, ax = plt.subplots(figsize=(3.4, 3.0))
xs = np.linspace(x.min()-6, x.max()+6, 50)
m, b = np.polyfit(x, y, 1)
ax.plot(xs, m*xs+b, color="#8a8a8a", linewidth=0.9, zorder=2)
for pid, ver, xv, yv in DATA:
    ax.scatter([xv], [yv], s=30, facecolors="none",
               edgecolors=BLACK if ver == "A" else RED, linewidths=1.2, zorder=3)
    ax.annotate(pid, (xv, yv), textcoords="offset points", xytext=(4, 4),
                fontsize=6.5, color="#444444")
ax.axhline(0, color="#cccccc", linewidth=0.6, zorder=1)
ax.axvline(0, color="#cccccc", linewidth=0.6, zorder=1)
ax.set_xlabel("SUDS change (post \u2212 pre) / pre (%)", fontsize=8)
ax.set_ylabel("PCL-5 intrusion change (points)", fontsize=8)
ax.set_xlim(-92, 30); ax.set_ylim(-9, 5)
ax.text(0.04, 0.94, "r = %+.2f  (n = 6)" % r, transform=ax.transAxes, fontsize=8, va="top")
ax.tick_params(labelsize=7.5)
for s in ("top","right"): ax.spines[s].set_visible(False)
fig.tight_layout()
for ext in ("png","pdf"):
    p = os.path.join(OUT, "Figure_S7_Pooled_SUDS_vs_Intrusion." + ext)
    fig.savefig(p, dpi=600 if ext=="png" else None)
    print("[written] %s  %s バイト" % (os.path.basename(p), format(os.path.getsize(p), ",")))
print("検算: Pearson r = %+.4f  点 %d 個（版A 2・版B 4）／回帰線1本・p 値の表示なし" % (r, len(DATA)))
