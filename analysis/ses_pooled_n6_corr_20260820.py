# -*- coding: utf-8 -*-
"""n=6 全員をまとめた解析（版で分けない）。
   PI 指示 2026-08-20（判断シート 19_2301 §5 記入欄）:
   「abandon any comparison between versions をするために、実際に n=6 全員をまとめて
     分析したらどうか。PCL-5 intrusion (pre vs fu), SUDS (pre vs post) の変化について、
     それぞれの個人の最初の音に対する SUDS との相関をとってみたらどうか。
     相関分析では統計的有意差はないのか？」
   出典: Source_Data_1_REV2.xlsx の Fig4_SUDS_PrePost / Fig5_PCL5_Change / FigS4_PDS5_Change
"""
import sys, io, json
import numpy as np
from scipy import stats
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

P   = ["H01","H02","H03","H08","H09","H14"]
VER = ["A","A","B","B","B","B"]
pre_suds  = np.array([30,35,60,20,50,50], float)   # 最初の音に対する SUDS（覚醒時・夜の初回提示）
post_suds = np.array([35,40,30,10,10,40], float)
d_suds    = post_suds - pre_suds
d_suds_pc = d_suds/pre_suds*100.0
intr_pre  = np.array([12,15, 8, 9,14, 4], float)
intr_fu   = np.array([15,16, 4, 2, 7, 2], float)
d_intr    = intr_fu - intr_pre
d_sum     = np.array([0,1,-4,-26,-18,-6], float)   # PCL-5 total change
d_pds     = np.array([-1,1,3,-18,-12,-7], float)   # PDS-5 total change

def ci_r(r, n):
    if abs(r) >= 1: return (r, r)
    z = np.arctanh(r); se = 1/np.sqrt(n-3)
    return tuple(np.tanh([z-1.96*se, z+1.96*se]))

def corr(x, y, xl, yl, out):
    n = len(x)
    r, pr = stats.pearsonr(x, y)
    rho, ps = stats.spearmanr(x, y)
    lo, hi = ci_r(r, n)
    print(f"{xl}  vs  {yl}")
    print(f"   Pearson  r = {r:+.3f}  [95% CI {lo:+.3f} to {hi:+.3f}]   p = {pr:.4f}   r2 = {r*r:.3f}")
    print(f"   Spearman rho = {rho:+.3f}   p = {ps:.4f}")
    print(f"   {'有意 (p<0.05)' if pr<0.05 else '有意差なし (p>=0.05)'}  / Spearman: {'有意' if ps<0.05 else '有意差なし'}")
    print()
    out[f"{xl} vs {yl}"] = dict(n=n, pearson_r=round(float(r),4), pearson_p=round(float(pr),4),
                                ci95=[round(float(lo),4), round(float(hi),4)],
                                spearman_rho=round(float(rho),4), spearman_p=round(float(ps),4))

def paired(a, b, lab, out):
    d = b - a; n = len(d)
    m = d.mean(); sd = d.std(ddof=1); se = sd/np.sqrt(n)
    t, p = stats.ttest_rel(b, a)
    tcrit = stats.t.ppf(0.975, n-1)
    w, pw = stats.wilcoxon(b, a)
    dz = m/sd
    print(f"{lab}  (n=6 pooled, paired)")
    print(f"   mean change = {m:+.2f}  SD {sd:.2f}   95% CI [{m-tcrit*se:+.2f}, {m+tcrit*se:+.2f}]")
    print(f"   Cohen's dz = {dz:+.3f}    paired t = {t:+.3f}, p = {p:.4f}    Wilcoxon p = {pw:.4f}")
    print(f"   個票: {[f'{v:+.0f}' for v in d]}")
    print(f"   減少した人 {int((d<0).sum())}/6 ・ 増加 {int((d>0).sum())}/6 ・ 不変 {int((d==0).sum())}/6")
    print()
    out[lab] = dict(n=n, mean=round(float(m),3), sd=round(float(sd),3),
                    ci95=[round(float(m-tcrit*se),3), round(float(m+tcrit*se),3)],
                    dz=round(float(dz),3), t=round(float(t),3), p_t=round(float(p),4),
                    p_wilcoxon=round(float(pw),4))

out = {}
print("="*78)
print("【1】n=6 全員をまとめた前後比較（版で分けない）")
print("="*78)
paired(pre_suds, post_suds, "SUDS pre→post (points)", out)
paired(intr_pre, intr_fu,  "PCL-5 intrusion pre→FU (points)", out)

print("="*78)
print("【2】最初の音に対する SUDS（Pre-SES SUDS）との相関  n=6")
print("="*78)
corr(pre_suds, d_suds,    "Pre-SES SUDS", "SUDS change (post-pre, points)", out)
corr(pre_suds, d_suds_pc, "Pre-SES SUDS", "SUDS change (%)", out)
corr(pre_suds, d_intr,    "Pre-SES SUDS", "PCL-5 intrusion change", out)
corr(pre_suds, d_sum,     "Pre-SES SUDS", "PCL-5 total change", out)
corr(pre_suds, d_pds,     "Pre-SES SUDS", "PDS-5 total change", out)

print("="*78)
print("【3】2つの変化どうしの相関（SUDS の動きと PCL-5 侵入症状の動き）")
print("="*78)
corr(d_suds, d_intr, "SUDS change (points)", "PCL-5 intrusion change", out)
corr(d_suds_pc, d_intr, "SUDS change (%)", "PCL-5 intrusion change", out)

print("="*78)
print("【4】個票（版は色分けにのみ使う・解析では分けない）")
print("="*78)
print(f"{'ID':4} {'ver':3} {'preSUDS':>8} {'postSUDS':>9} {'dSUDS':>6} {'dSUDS%':>7} {'intrPre':>8} {'intrFU':>7} {'dIntr':>6}")
for i,p in enumerate(P):
    print(f"{p:4} {VER[i]:3} {pre_suds[i]:8.0f} {post_suds[i]:9.0f} {d_suds[i]:+6.0f} {d_suds_pc[i]:+7.1f} {intr_pre[i]:8.0f} {intr_fu[i]:7.0f} {d_intr[i]:+6.0f}")
print()
json.dump(out, open("_scripts/_out/pooled_n6_corr_20260820.json","w",encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("JSON -> _scripts/_out/pooled_n6_corr_20260820.json")
