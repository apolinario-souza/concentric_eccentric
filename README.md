# Data and analysis code: load and contraction type in a fast elbow flexion timing task


Raw data and analysis code for the article [title, journal, DOI].

Participants (n = 45) performed fast elbow flexion movements on a Scott (preacher) bench,
in concentric (`con`) and eccentric (`exc`) actions, with three loads (planned at 37, 65 and
89% of the maximum load; actual mean 33, 68 and 91%, see `participants.csv`). The movement had
a 60° amplitude [TODO: confirm amplitude] and a target movement time of 250 ms.

## Equipment

The data were collected with the elbow goniometer, Arduino code and LabVIEW program available at
https://github.com/apolinario-souza/variability-con-exc.

## Contents

| Path | Content |
|---|---|
| `dados/` | Raw data: one folder per participant (`suj1` ... `suj46`) |
| `participants.csv` | Anonymized participant characteristics and loads |
| `medidas_brutas.py` | Computes the measures of every trial from the raw traces → `dados_5pct.xlsx` |
| `analise_cargas.py` | Repeated-measures ANOVAs and post hoc tests → `resultados_cargas.xlsx` |
| `graficos_cargas.py` | Figures of the results → `graficos/*.png` |
| `serie_temporal.py` | Mean velocity and displacement time series → `graficos/serie_temporal.png` |
| `dados_5pct.xlsx` | Output of `medidas_brutas.py` (trial-level and participant-level measures) |
| `resultados_cargas.xlsx` | Output of `analise_cargas.py` (statistical results) |
| `graficos/` | Figures of the article |

Identifiers in the code and spreadsheets are in Portuguese (see the glossary at the end).

## Raw data (`dados/sujX/`)

There is no participant 32 (participants are numbered 1 to 46; participant 32 has no data).

### File names

`<condition>.txt` is the summary of a block (one line per trial) and
`<condition>_tentativa_N.xls` is the trace of trial N of that block.

| Condition | Description |
|---|---|
| `37con`, `65con`, `89con`, `37exc`, `65exc`, `89exc` | Experimental conditions (load label + action); these are the data analysed in the article |
| `famcon`, `famexc` | Familiarization [TODO: describe] |
| `testcon1`, `testcon2`, ..., `testexc1`, ... | Maximum load tests [TODO: describe the procedure] |
| `retcon`, `retexc` | [TODO: describe] |

The load labels (37, 65, 89) are the planned percentages of the maximum load. Because free
weights were used in 1 kg increments, the actual percentage differs between participants
(`participants.csv`).

### Trace files (`*_tentativa_N.xls`)

Despite the extension, these are tab-separated text files, without header, with comma as the
decimal separator (Brazilian locale). Each row is one frame; each frame is 5 ms (200 Hz). The
imperative stimulus occurs at frame 800 (4000 ms) and the trace ends ~1500 ms after it.

| Column | Content |
|---|---|
| 1 | Frame number |
| 2 | Position (raw potentiometer units) |
| 3 | Velocity (raw units) |
| 4 | Elbow angle (°) |
| 5 | Angular velocity (°/s) |


### Summary files (`<condition>.txt`)

Generated online by the LabVIEW program: tab-separated, no header, comma as decimal separator,
one line per trial. Columns: reaction time (ms), movement time (ms), absolute error (°),
constant error (°), peak velocity (°/s). the analysis recomputes everything
from the traces at **5%** (see below). `dados_5pct.xlsx`, sheet `conferencia`, shows the
agreement between the two.

Known gaps (files never recorded or lost): traces without summary in suj3 and suj27 (`famcon`),
suj7 (`testexc4`, `testexc5`), suj12 (`65con`) and suj21 (`testcon4`); summaries without traces
in suj45 (`famcon`), suj37 (`testexc2`), suj38 (`famexc`, `retexc`), suj42 (`testexc3`) and
suj43 (`testcon2`). Only suj12 `65con` belongs to the experimental conditions; its traces are
complete.

## Participants (`participants.csv`)

One row per participant (`participant` = folder name in `dados/`; `has_data` = FALSE for
participant 32). Columns: age (years), sex, body mass (kg), height (cm), upper limb length,
olecranon–wrist and acromion–olecranon lengths, relaxed and flexed arm circumference (cm);
maximum load in each action (`max_con_kg`, `max_exc_kg`) and the actual percentage of the
maximum used in each condition (`pct_<load label>_<action>`). The load in kg of a condition is
maximum × percentage / 100.

## Measures (`medidas_brutas.py`)

For each trial: peak velocity (PV) is the maximum velocity after frame 700; movement onset and
end are the points where velocity crosses 5% of PV before and after the peak (linear
interpolation between frames).

- **RT**: onset − stimulus (ms). **MT**: end − onset (ms). **Amplitude**: |angle at end − angle
  at onset| (°).
- **Target position**: estimated from the summary files (constant error + final position at 20%),
  same for all participants: 78.3° (con) and 137.1° (exc).
- **Signed spatial error**: final position − target, positive = beyond the target in both
  actions. **Absolute error (EA)**: its absolute value.
- **Signed temporal error**: MT − 250 ms. **Absolute timing error (ETA)**: its absolute value.
- **Relative time to peak velocity (TRPV)**: 100 × (peak − onset) / MT (% of MT).

Per participant and condition: means of EA, ETA, amplitude, RT, MT, PV and TRPV; spatial and
temporal variable error (SD of the signed errors, `EC_sd`, `ETC_sd`); coefficient of variation
of PV (`PV_cv`).

Exclusions (25 of 3242 trials, 0.8%): MT at 20% < 150 ms (21; anticipations), trace ending
before velocity fell to 5% of PV (2), amplitude < 30° (2; the detected peak was not the
movement).

## Statistical analysis (`analise_cargas.py`)

3 (load) × 2 (action) repeated-measures ANOVA with Greenhouse–Geisser correction, partial η²;
post hoc paired t tests with Holm correction. `EC_sd`, `ETC_sd`, `PV_cv` and `TR_mean` are
tested after natural log transformation (skewed residuals); `dados_5pct.xlsx` (sheet `medidas`)
has these variables already transformed (`ln*` columns), for use in other software (e.g. JASP).

## How to reproduce

Python 3.13 with the packages in `requirements.txt`:

```
pip install -r requirements.txt
python medidas_brutas.py     # ~10 s
python analise_cargas.py
python graficos_cargas.py
python serie_temporal.py     # ~15 s
```

## Glossary

| Code | Meaning |
|---|---|
| `sujeito` | participant |
| `carga` | load (37, 65, 89 = planned % of maximum) |
| `acao` | action (`con` concentric, `exc` eccentric) |
| `tentativa` | trial |
| `TR` | reaction time (ms) |
| `TM` | movement time (ms) |
| `PV` | peak velocity (°/s) |
| `TPV` / `TRPV` | time to peak velocity (ms) / relative time to peak velocity (% of MT) |
| `AMP` | movement amplitude (°) |
| `EA` / `EC` | absolute / signed (constant) spatial error (°) |
| `ETA` / `ETC` | absolute / signed (constant) timing error (ms) |
| `EC_sd` / `ETC_sd` | spatial / temporal variable error |
| `_mean`, `_sd`, `_cv` | mean, standard deviation, coefficient of variation (%) |
| `_20` | computed with onset/end at 20% of PV (online criterion) |
| `_resumo` | value from the LabVIEW summary file |
| `valida` | trial kept in the analysis |
| `alvo` | target position (°) |
| `pos_ini` / `pos_fim` | angle at movement onset / end (°) |
| `na_borda` | trace ended before velocity fell below the threshold |
| `dimensao` | dimension (group of variables in the article) |
| `escala` | scale of the test (original or log) |

## License

Data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Code: MIT (see `LICENSE`).
