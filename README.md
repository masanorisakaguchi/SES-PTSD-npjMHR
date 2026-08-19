# SES-PTSD-npjMHR

Analysis code for:

> Ino K, Zempo K, Hori A, Maruyama T, Tominaga M, Sugaya Y, Oba M, Yamauchi Y, Sato L,
> Sekiba H, Kawakami C, Bachman G, Waki I, Kitagawa H, Yanagisawa M, Kim Y, Sakaguchi M.
> **Sound Exposure During Sleep in individuals with PTSD: An Open-Label Feasibility Study.**
> Trial registration: jRCT1030230706. Preprint: https://doi.org/10.64898/2026.05.02.26352243

Corresponding author: Masanori Sakaguchi (masakagu@med.kobe-u.ac.jp),
Department of Neurophysiology, Kobe University Graduate School of Medicine.

---

## What is here

`analysis/` contains the custom code written for this study. Everything else in the
paper (group means, confidence intervals, effect sizes, correlation coefficients) was
computed with standard scientific-computing library calls using default parameters, as
described in Methods §Statistical analysis, and needs no code of its own.

| File | What it does | Where it appears in the paper |
|---|---|---|
| `ses_table2_unify_20260815.py` | Reconstructs sound delivery from the per-second playback log (duplicate entries removed, single-second dropouts filled from the preceding entry) and applies the advancing 30-s window in 1-s steps that operationalizes the AASM N3 criterion. | Table 2; Results §SWS Stage Targeting |
| `crosstab_stage_20260817.py` | Cross-classifies every delivered second by the registered sleep technologist's clock-aligned 30-s scoring and by the advancing-window criterion. | Figure 6b; Source Data `Fig6b_CrossClassification` |
| `ses_stage_breakdown.py` | Stage composition of the delivered sound on the technologist's grid. | Figure 6b; Source Data `Fig6b_StageComposition` |
| `ses_bouts_v3.py` | Extracts N3 bouts and derives mean bout duration, bout count and fragmentation index (bouts per hour of N3), handling recordings that cross midnight. | Figure 6a; Supplementary Table S4(a) |
| `ses_bout_sound_vs_nosound.py` | Splits bouts of ≥90 s by whether the bout carried sound delivery. | Figure 6d; Supplementary Table S4(b) |
| `ses_hrv_scl_600s.py` | SDNN and RMSSD over the full 600-s exposure window and their relation to SUDS change. | Supplementary Figure S1 |
| `ses_scl_600s.py` | Standardized skin conductance level over the full 600-s exposure window. | Supplementary Figure S2 |

`data/Source_Data_1.xlsx` is the de-identified numerical Source Data released with the
Article. Every value plotted in the main and supplementary figures is in it.

## What is **not** here

Individual participant clinical data, per-participant trauma-content audio descriptions,
the raw EEG recordings, and the raw playback logs are **controlled-access**: they carry a
re-identification and re-traumatization risk in a cohort of six people with PTSD. They are
available to qualified researchers on request to the corresponding author and the NCNP
Ethics Committee under a Data Use Agreement (see the Data Availability statement of the
Article). The structured physician multi-criteria sound-determination instrument is held
under sponsor confidentiality pending a patent application (Japanese domestic filing
JP-2026-027927, filed 24 February 2026) and is not part of this repository.

The scripts therefore do not run end-to-end from a clean checkout. They are published so
that the operative definitions — how a delivered second is counted, what counts as
slow-wave sleep under each of the two definitions, how a bout is delimited — can be read
and checked line by line, which is the part a reader cannot reconstruct from the Methods
alone.

## Running them against the controlled-access inputs

Set the input roots as environment variables and run any script directly:

```bash
export SES_STAGE_ROOT=/path/to/technologist_scoring
export SES_LOG_ROOT=/path/to/playback_logs
export SES_SCREENING_ROOT=/path/to/home_screening
python3 analysis/ses_table2_unify_20260815.py
```

Python 3.10 or later. Dependencies are in `requirements.txt`.

## Licence

MIT (see `LICENSE`). The Source Data file is released under the terms of the Article.

## Citing

Please cite the Article. If you need to cite the code specifically, cite this repository
together with the commit hash you used.
