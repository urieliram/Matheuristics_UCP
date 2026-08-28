# A Kernel Search Matheuristic for a Thermal Unit Commitment Problem

## Table of Contents
+ [Introduction](#introduction)
+ [Implementation](#implementation)
  * [Classes](#classes)
+ [Experiments](#experiments)
  * [Instances](#instances)
  * [Results](#results)
    - [Comparative Analysis of Optimization Methods](#comparative-analysis-of-optimization-methods)
    - [Key Findings](#key-findings)
    - [Discussion: Convergence Speed](#discussion-convergence-speed)
+ [Conclusion](#conclusion)
+ [Links](#links)
+ [Development](#development)
  * [Tests](#tests)
  * [Fixed bugs](#fixed-bugs)
  * [Start-up costs are missing from the model](#️-start-up-costs-are-missing-from-the-model)
  * [Open questions](#open-questions)
+ [Appendix](#appendix)

---

## 📖 Introduction

The Unit Commitment Problem (UCP) is a critical challenge in the electrical power systems operation schedule. It involves determining the optimal scheduling of power generation units over a specific time horizon, considering various constraints and objectives. This capsule delves into matheuristic methods, which combine mathematical optimization and heuristic search algorithms. Specifically, we will explore five matheuristic methods that utilize local branching techniques from Fischetti 2003 and kernel search from Angelini 2013. Also, we will be presenting an empirical evaluation comparing the performance of these methods with that of a solver. The assessment focuses on solving a challenging model near the convex vestibule, utilizing instances derived from the Morales-España 2013 dataset. Finally, we will delve into the characteristics of the UCP, discuss the application of matheuristic methods, and highlight their potential to provide efficient and high-quality solutions.

## 💻 Implementation

The code of the methods proposed is in [main.py](main.py). The results can be found in [Figures_TC_UC2.ipynb](Figures_TC_UC2.ipynb). The MILP model of UCP is in [uc_Co.py](uc_Co.py). The generator of instances is on [instances_gen.ipynb](instances_gen.ipynb). 

The main component of this method is a strong and compact MILP model **A Tight and Compact MILP** based on [Knueven2020](https://pubsonline.informs.org/doi/10.1287/ijoc.2019.0944).

## 🧪 Experiments
(Comparative Evaluation: Assessing Method Performance)

To evaluate the effectiveness of the proposed matheuristic methods, we conducted a comprehensive empirical evaluation. The evaluation employed a tight and compact model situated close to the convex hall, a challenging region of the search space. The model featured a limited number of variables and constraints, ensuring a rigorous test for the matheuristic methods.

To construct difficult instances for evaluation, we utilized instances derived from the Morales-Spain 2013 dataset. These instances are known for their complexity and provide a suitable benchmark for assessing the performance of the proposed methods.

### 🧪 Instances

The instances in JSON format are in the folder [instances/](instances/).

Estas instancias tienen una alta simetría, por lo que tardan en resolverse un poco más que otras instancias más cercanas a las de la realidad.

|GROUP           |INST  (n)       |GEN   (G)       |PERIOD   (T)   |FILES (uc_XX)   |
| :------------- | -------------: | -------------: |-------------: |-------------:  |
|   x7day_small  | 10             |  28 to 54      | 168           | (061-070)      |90%
|   x7day_large  | 10             |  132 to 187    | 168           | (071-080)      |90%
|   x7day_medium    | 30             |  60 to 131     | 168           | (101-131)      |90%
|   x7day_large(b)  | 10             |  135 to 156    | 168           | (132-140)      |90%
|   x7day_large(c)  | 10             |  185 to 242    | 168           | (141-152)      |90%

Other tiny instances to validate the model are:
> - uc_57 morales_espania2013,Section_III_D,example of one_day from TABLE IX Morales-españa2013.
> - uc_58 morales_espania2013,Section_III_D,example of five days from TABLE VII Morales-españa2013.
> - uc_59 morales_espania2013,Template of eight generators from TABLE VII Morales-españa2013.

### 📊 Results

The empirical evaluation yielded intriguing insights into the performance of the matheuristic methods. Four of the methods, based on local bifurcation techniques, showcased remarkable performance in capturing and exploiting local optima. By adapting the search process to the problem's characteristics, these methods demonstrated improved convergence and solution quality.

#### ⚖️ Comparative Analysis of Optimization Methods

This repository contains the analysis and comparison of various optimization methods applied to different instance groups under different time constraints.

#### 🏆 Key Findings

- **Best Initial Solution Provider**: The **HARDUC** method consistently found feasible solutions in all instance groups and provided the most accurate initial solutions.
- **Performance of KS Algorithm**:
  - Showed a **higher solution descent rate** than Local Branching (LB) methods but was **slower in solution finding**.
  - In some cases, KS remained in the first found solution without improvement (13.3% of large instances, 4.3% of total instances).
  - KS outperformed other methods for **large instances** (4000s & 7200s runtime).
- **Solver Performance**:
  - For **small instances (4000s runtime)**, no significant differences were found between KS, LB1, LB2, LB3, LB4, and the solver.
  - For **medium instances (4000s runtime)**, KS had the best results, followed by LB methods, outperforming the solver.
  - For **large instances (4000s & 7200s runtime)**, KS outperformed all other methods significantly.
  - **Providing an initial solution to the solver (SM2) often led to worse performance** than letting it run without one (SM1).

#### ⚡ Discussion: Convergence Speed

One of the most notable aspects of the KS method is its **fast initial convergence**. In the first iterations, KS was able to **quickly reduce the optimality gap**, significantly outperforming LB-based methods. However, as iterations progressed, **its convergence rate slowed down**, eventually reaching a state of **stagnation**, which is a common behavior in greedy algorithms.

- **Early-stage dominance**: KS finds an initial solution faster and improves it at a rapid pace.
- **Late-stage slowdown**: Unlike LB methods, KS loses momentum over time and struggles to continue improving.
- **Solver limitations**: While KS outperforms the solver in most cases, it sometimes fails to further refine its solution after a certain point.

Despite its **fast early convergence**, KS did not always utilize the initial solution provided by HARDUC, while LB methods consistently improved upon it. This suggests that **LB methods are more robust in long-term refinement**, whereas KS excels in **fast, early-stage improvements**.

## 🏆 Conclusion

- The **KS method** achieved the **lowest average optimality gap** and is the best approach for large instances.
- **Local Branching (LB) methods consistently improved the initial solution**, unlike KS, which sometimes stagnated.
- The **solver struggled with large instances**, and its performance was significantly affected when given an initial solution.
- **KS is ideal for problems requiring rapid early improvements**, but LB methods are preferable when longer optimization time is available.

For detailed results, refer to the statistical analysis in this link 🧑‍🏫 [Uriel I. Lezama](http://eprints.uanl.mx/26250/).. 🚀

## 🔗 Links
[On Mixed-Integer Programming Formulations for the Unit Commitment Problem, Knueven2020](https://pubsonline.informs.org/doi/10.1287/ijoc.2019.0944).

[Matheuristics for Speeding Up the Solution of the Unit Commitment Problem, Harjunkoski2021](https://ieeexplore.ieee.org/document/9640029).

[Tight and Compact MILP Formulation for the Thermal Unit Commitment Problem, Morales-españa2013](https://ieeexplore.ieee.org/document/6485014).

The complete results of this research can be found at 🧑‍🏫:

[U. I. Lezama-Lope. Efficient Methods for Solving Power System Operation Scheduling Challenges: The Thermal Unit Commitment Problem with Staircase Cost and the Very Short-term Load Forecasting Problem. PhD thesis, Universidad Autonoma de Nuevo Leon, Monterrey, Mexico, November 2023.](http://eprints.uanl.mx/26250/).

## 🛠️ Development

### Setup

```bash
pip install -r requirements-dev.txt
```

CPLEX is not installed by `pip` here: point the `executable` key of `config.con` at your own
CPLEX binary. `config.con` is versioned — without it `main.py` cannot start.

### Running

```bash
python3 main.py uc_057.json yalma      # single instance
sh test.sh                             # batch, see the loop at the top of the script
```

Results are appended as one row to `stat.csv`; the column order is documented in `main.py`
immediately above the `row = [...]` assembly. Each run also drops `logfile*.log` (CPLEX logs) and
`solHard3_a/b_<instance>.csv` in the working directory. Those `solHard3_*` files are a **warm-start
cache**: if they exist for an instance, the next run recovers that solution instead of re-solving
the LP relaxation and Hard3. Delete them to force a clean run.

### Tests

```bash
pytest                 # everything
pytest -m "not slow"   # skips the tests that need CPLEX (this is what CI runs)
```

`tests/test_model.py` pins the MILP itself: it exports the model `uc_Co.uc()` builds to LP with
symbolic labels and hashes it, so constraint count, constraint order, coefficients and variable
domains are all covered. That is the gate to refactor `uc_Co.py` behind — anything that moves the
model breaks the hash. Regenerate the digests deliberately with `python3 tests/regen_lp_digest.py`
after an intentional model change or a Pyomo upgrade.

`tests/test_regression.py` solves `uc_057` end to end and compares every non-timing column of the
resulting `stat.csv` row against `tests/data/golden_uc_057.csv`. That golden row was captured before
the code was cleaned up, so it is the guard that the refactor did not move any published number.
Regenerate it only when a change is *meant* to alter results.

### Fixed bugs

These were real defects found during the cleanup. Each is now covered by a test.

| Where | Bug | What changed |
| :---- | :-- | :----------- |
| `main.py`, LBC | `cuttoff = z_lbcN` — misspelled, so the intended `cutoff` was never updated in the "optimal but rhs < e" branch and CPLEX kept a stale upper cutoff on the next iteration | now assigns `cutoff` |
| `main.py`, LBC1 | `diversify = False` had been swallowed by a trailing comment, so LBC1 alone never reset diversification after a non-improving iteration | all four variants now reset it |
| `main.py`, Kernel Search | `iterstop` came from Sturges' *n*, but the number of bucket boundaries actually built (`len(k_)-1`) can be smaller, so `k_[iter_bk + 1]` overran with `IndexError`. Only bit small instances — at ~500 free variables the two numbers coincide, which is why the published large-instance runs never saw it | bound is `min(n - 2, len(k_) - 1)`; the loop counter no longer shadows the global `iterstop` |
| `util.py` | `delete_tabu` popped from the list it was iterating, so one of two adjacent tabu cuts survived and over-constrained the next LB iteration | rewritten as a list comprehension |
| `uc_Co.py` eq. (56) | registration of `Start_up_cost56` sat inside the rule after the `return`, so start-up costs were never priced (`sum(cSU) = 0` in every published run) | registered; objectives now include start-up cost (+0.2-0.4 %) |
| `uc_Co.py` (Startcost4) | `enforce2()` implementing the initial start-up-type rule was defined but never called | inlined as live `delta.fix(0)` at model build |
| `uc_Co.py` eq. (48b) | constraint registration sat outside `if mode == 'Tight'`, raising `NameError` under any other mode | moved inside the block (emitted model under Tight unchanged, verified by LP digest) |
| `reading.py` | `demand`/`reserves` aliased the parsed JSON and were appended to while being iterated; the loop also ran over `len(demand)` instead of the horizon, so `uc_059` (121 demands, 120 periods) died with `IndexError` | scales into fresh lists over `time_periods`; verified `De`/`R` byte-identical on 166 instances |
| `main.py`, LBC + KS | the reported gap was overwritten on every iteration by `z, g = sol.solve_problem()`, so `stat.csv` recorded the gap of the *last* subproblem, not of the incumbent that is reported next to it (`z_ks = 571490.7` beside `g_ks = 1e+75`) | both blocks recompute the gap against the returned incumbent; the `1e+75` sentinel is preserved when no incumbent was found |
| `main.py`, `stat.csv` | `g_milp2` was written with `round(...,1)` while every other gap uses 8 decimals, so a real gap of 0.0032 was logged as `0.0` | now 8 decimals like the rest |
| `main.py`, `stat.csv` | the `emphasizeMILP/symmetryMILP/strategyMILP/lbheurMILP` columns logged the `config.con` values, but SM1 does not pass `emphasize/symmetry/lbheur` — it runs on `Solution.__init__` defaults. The log claimed a parameterization that never reached CPLEX | the columns now record the *effective* parameters, read back from the `Solution` object so the log follows the code |
| `instances/uc_011.json` | committed as 0 bytes in its only commit; the data never existed in history | removed; `tests/test_util.py` now fails if any instance is empty or malformed |

On `uc_057` none of the LBC fixes change a single number — that instance converges in one iteration
through the `optimal -> break` path, so the corrected branches never execute. They will change the
search trajectory on instances that actually iterate, so **re-run any experiment whose conclusions
depend on LB1's diversification or on the tabu list**.

### Start-up costs: fixed 2026-08-25

Until 2026-08-25 the model **did not price start-up costs**: the registration of eq. (56) sat
inside its own rule function, after the `return`, so it never executed and the solver drove every
`cSU[g,t]` to zero. The companion initial-condition rule (Startcost4) lived in a function
`enforce2()` that was never called. Both are now active in `uc_Co.py`:

* `Start_up_cost56` is registered (`cSU = sum(Cs[s] * delta[s])`), so `total_cSU` in the objective
  is real money.
* (Startcost4) fixes `delta[g,t,s] = 0` in the initial periods where the pre-horizon downtime
  `TD_0` makes that start-up type impossible. Vacuous on the shipped dataset (every unit starts
  online, `TD_0 = 0`) but load-bearing for extensions with cold initial conditions; covered by
  `tests/test_util.py::test_startcost4_fixes_initial_delta_for_cold_units`.

Measured impact on `uc_057` (identical by two independent routes):

| | objective | starts | `sum(cSU)` |
| :-- | --: | --: | --: |
| before | 571490.66 | 5 | 0.00 |
| after | 573630.66 | 5 | 2140.00 |

On longer horizons the *schedule itself* moves (uc_058: 5.2 % of commitment cells, uc_059: 4.3 %,
uc_061: 15 % with starts dropping 62 → 56), so **any experiment whose conclusions depend on
objective values or commitment schedules needs a re-run**. The golden row
(`tests/data/golden_uc_057.csv`) and the LP digests (`tests/data/model_lp_sha256_uc_057.json`)
were regenerated on 2026-08-25; results in `stat.csv` rows dated before then were produced by the
old model. Stale `solHard3_*.csv` warm-start caches from the old model were deleted — never reuse
them across this boundary.

### Paper errata applied 2026-08-27

Where the code and `Paper_CAOR25_R1` disagreed, **the experiment was taken as the source of truth**
and the LaTeX was corrected to describe what actually ran:

| File | Was | Now |
| :--- | :-- | :-- |
| `3_MathModel.tex` (genlim3) | full two-sided trajectory bound on `p` with summations over both `T^RU` and `T^RD` | the implemented form: bound on `p-bar`, ramp-up summation capped at `min(UT-2, T^RU)`, shutdown as the single `w_{g,t+1}` term. Noted as a valid inequality, so the integer optimum is unaffected — only the relaxation strength |
| `5_ExpWork.tex` (both parameter tables) | `mip_tolerances_mipgap = 1e-5` | `1e-6`, the value in `config.con` and in all three 2023 `stat.csv` rows |
| `5_ExpWork.tex` (Table 2, Remaining) | `mip_strategy_heuristicfreq = 50` | row removed — `main.py` never forwards it, so CPLEX used its default |
| `5_ExpWork.tex` (Table 2, SM1) | symmetry not stated | `preprocessing_symmetry = -1` stated explicitly, plus a note that unlisted parameters kept CPLEX defaults |
| `5_ExpWork.tex` §Test2 | "each iteration has a time limit of 1200 s." | adds the 100 s cap that applies to the first subproblem and to every post-diversification restart |

Earlier errata (2026-08-25): `(relation3)`, the definition of `C^R`, the large-instance range
`141-163`, the 10 % reserve subset, and the ascending reduced-cost order in Algorithm 2 / `alg_ks`.

### Open questions

Not bugs with an obvious right answer — they need a call from whoever owns the experiments.
Entries marked **Decision** have already been settled and are kept here as the record of why.

* **KS bucket construction diverges from the paper's Algorithm 2 — accepted as-is.** `main.py` builds
  bucket boundaries with step `len_i+1`, yielding fewer, differently-sized buckets than the published
  `buildbuckets()` (for |U|=62: 10 buckets `[5,6,...,9]` vs 14 buckets `[5x6,4x8]`), sweeps at most
  `n-2` of them per pass, and stops after 7 non-improving buckets. **Decision (2026-08-27): the code
  stays as it is** — it is what produced the published results, and aligning it to Algorithm 2 would
  invalidate every KS number. Anyone extending KS should read `main.py`, not Algorithm 2, as the
  specification of what ran.
* **LB iteration limit: 1200 s (paper) vs `timeconst = 2000` (`config.con`).** `stat.csv` shows both
  values were used during the May 2023 campaign (`uc_155` at 1200, `uc_160`/`uc_163` at 2000), so the
  repository cannot settle which one governed the published tables. Needs the experiment owner's call
  before the paper's "1200 s." can be trusted or corrected.
* **`solution.py` calls `exit()`** inside its solver-status branch, so a library terminates the whole
  process instead of raising. It also discards incumbents when the status is not `ok`, so a timed-out
  run loses a perfectly good solution.

## 📎 Appendix


### Differences Mean Test Summary Between the Constructive Methods HARDUC and HGPS

| Null Hypothesis | Instances      | Test         | p-value | Decision |
|----------------|---------------|-------------|---------|----------|
| The means difference of the samples from the same distribution | x7day_small  | Mann-Whitney | 0.0002* | We reject H₀ and accept Hₐ: HARDUC's mean is less than HGPS's mean |
| The means difference of the samples from the same distribution | x7day_medium | Mann-Whitney | 0.0000* | We reject H₀ and accept Hₐ: HARDUC's mean is less than HGPS's mean |
| The means difference of the samples from the same distribution | x7day_large  | Mann-Whitney | 0.0000* | We reject H₀ and accept Hₐ: HARDUC's mean is less than HGPS's mean |

**Significance level: 0.05**



### Means Difference Statistical Test Summary (x7day_small) - 1 Hour

#### Means difference statistical test summary among all methods for instances from group x7day_small under a running time limit of 4000 seconds.

| Null Hypothesis | Test | p-value | Decision |
|----------------|------|---------|----------|
| SM1_1h-LB2_1h: There is no difference between the two population means | Mann-Whitney | 0.3779 | We fail to reject H₀ |
| SM1_1h-KS_1h: There is no difference between the two population means | T-test for two samples | 0.2725 | We fail to reject H₀ |
| SM1_1h-LB1_1h: There is no difference between the two population means | T-test for two samples | 0.2499 | We fail to reject H₀ |
| SM1_1h-LB4_1h: There is no difference between the two population means | T-test for two samples | 0.1737 | We fail to reject H₀ |
| SM1_1h-LB3_1h: There is no difference between the two population means | T-test for two samples | 0.1318 | We fail to reject H₀ |
| SM1_1h-SM2_1h: There is no difference between the two population means | T-test for two samples | 0.0888 | We fail to reject H₀ |
| LB2_1h-KS_1h: There is no difference between the two population means | Mann-Whitney | 0.5484 | We fail to reject H₀ |
| LB2_1h-LB1_1h: There is no difference between the two population means | Mann-Whitney | 0.4302 | We fail to reject H₀ |
| LB2_1h-LB4_1h: There is no difference between the two population means | Mann-Whitney | 0.2714 | We fail to reject H₀ |
| LB2_1h-LB3_1h: There is no difference between the two population means | Mann-Whitney | 0.2367 | We fail to reject H₀ |
| LB2_1h-SM2_1h: There is no difference between the two population means | Mann-Whitney | 0.1617 | We fail to reject H₀ |
| KS_1h-LB1_1h: There is no difference between the two population means | T-test for two samples | 0.492 | We fail to reject H₀ |
| KS_1h-LB4_1h: There is no difference between the two population means | T-test for two samples | 0.4016 | We fail to reject H₀ |
| KS_1h-LB3_1h: There is no difference between the two population means | T-test for two samples | 0.3336 | We fail to reject H₀ |
| KS_1h-SM2_1h: There is no difference between the two population means | T-test for two samples | 0.2923 | We fail to reject H₀ |
| LB1_1h-LB4_1h: There is no difference between the two population means | T-test for two samples | 0.4039 | We fail to reject H₀ |
| LB1_1h-LB3_1h: There is no difference between the two population means | T-test for two samples | 0.332 | We fail to reject H₀ |
| LB1_1h-SM2_1h: There is no difference between the two population means | T-test for two samples | 0.287 | We fail to reject H₀ |
| LB4_1h-LB3_1h: There is no difference between the two population means | T-test for two samples | 0.4211 | We fail to reject H₀ |
| LB4_1h-SM2_1h: There is no difference between the two population means | T-test for two samples | 0.3808 | We fail to reject H₀ |
| LB3_1h-SM2_1h: There is no difference between the two population means | T-test for two samples | 0.4675 | We fail to reject H₀ |

**Significance level: 0.05**




### Means Difference Statistical Test Summary (x7day_small) - 2 Hours

#### Means difference statistical test summary among all methods for instances from group x7day_small under a running time limit of 7200 seconds.

| Null Hypothesis | Test | p-value | Decision |
|----------------|------|---------|----------|
| SM1-LB2: There is no difference between the two population means | Mann-Whitney | 0.1584 | We fail to reject H₀ |
| SM1-LB1: There is no difference between the two population means | Mann-Whitney | 0.1396 | We fail to reject H₀ |
| SM1-LB4: There is no difference between the two population means | Mann-Whitney | 0.117 | We fail to reject H₀ |
| SM1-SM2: There is no difference between the two population means | T-test for two samples | *0.0362 | We reject H₀ and accept Hₐ: MILP's mean is less than MILP2's |
| SM1-KS: There is no difference between the two population means | T-test for two samples | 0.0501 | We fail to reject H₀ |
| SM1-LB3: There is no difference between the two population means | T-test for two samples | *0.0358 | We reject H₀ and accept Hₐ: MILP's mean is less than LB3's |
| LB2-LB1: There is no difference between the two population means | Mann-Whitney | 0.4569 | We fail to reject H₀ |
| LB2-LB4: There is no difference between the two population means | Mann-Whitney | 0.4143 | We fail to reject H₀ |
| LB2-SM2: There is no difference between the two population means | Mann-Whitney | 0.2326 | We fail to reject H₀ |
| LB2-KS: There is no difference between the two population means | Mann-Whitney | 0.4091 | We fail to reject H₀ |
| LB2-LB3: There is no difference between the two population means | Mann-Whitney | 0.2989 | We fail to reject H₀ |
| LB1-LB4: There is no difference between the two population means | Mann-Whitney | 0.4515 | We fail to reject H₀ |
| LB1-SM2: There is no difference between the two population means | Mann-Whitney | 0.2669 | We fail to reject H₀ |
| LB1-KS: There is no difference between the two population means | Mann-Whitney | 0.4623 | We fail to reject H₀ |
| LB1-LB3: There is no difference between the two population means | Mann-Whitney | 0.2896 | We fail to reject H₀ |
| LB4-SM2: There is no difference between the two population means | Mann-Whitney | 0.3036 | We fail to reject H₀ |
| LB4-KS: There is no difference between the two population means | Mann-Whitney | 0.4623 | We fail to reject H₀ |
| LB4-LB3: There is no difference between the two population means | Mann-Whitney | 0.3375 | We fail to reject H₀ |
| SM2-KS: There is no difference between the two population means | T-test for two samples | 0.3651 | We fail to reject H₀ |
| SM2-LB3: There is no difference between the two population means | T-test for two samples | 0.3434 | We fail to reject H₀ |
| KS-LB3: There is no difference between the two population means | T-test for two samples | 0.4909 | We fail to reject H₀ |

**Significance level: 0.05**


### Means Difference Statistical Test Summary (x7day_medium) - 1 Hour

#### Means difference statistical test summary among all methods for instances from group x7day_medium under a running time limit of 4000 seconds.

| Null Hypothesis | Test | p-value | Decision |
|----------------|------|---------|----------|
| KS_1h-LB2_1h: There is no difference between the two population means | Mann-Whitney | *0.0108 | We reject H₀ and accept Hₐ: KS_1h's mean is less than LB2_1h's |
| KS_1h-LB1_1h: There is no difference between the two population means | Mann-Whitney | *0.0031 | We reject H₀ and accept Hₐ: KS_1h's mean is less than LB1_1h's |
| KS_1h-LB4_1h: There is no difference between the two population means | Mann-Whitney | *0.0022 | We reject H₀ and accept Hₐ: KS_1h's mean is less than LB4_1h's |
| KS_1h-LB3_1h: There is no difference between the two population means | Mann-Whitney | *0.001 | We reject H₀ and accept Hₐ: KS_1h's mean is less than LB3_1h's |
| KS_1h-SM1_1h: There is no difference between the two population means | Mann-Whitney | *0.0 | We reject H₀ and accept Hₐ: KS_1h's mean is less than SM1_1h's |
| KS_1h-SM2_1h: There is no difference between the two population means | Mann-Whitney | *0.0 | We reject H₀ and accept Hₐ: KS_1h's mean is less than SM2_1h's |
| LB2_1h-LB1_1h: There is no difference between the two population means | Mann-Whitney | 0.2699 | We fail to reject H₀ |
| LB2_1h-LB4_1h: There is no difference between the two population means | Mann-Whitney | 0.2405 | We fail to reject H₀ |
| LB2_1h-LB3_1h: There is no difference between the two population means | Mann-Whitney | 0.1593 | We fail to reject H₀ |
| LB2_1h-SM1_1h: There is no difference between the two population means | Mann-Whitney | *0.0002 | We reject H₀ and accept Hₐ: LB2_1h's mean is less than SM1_1h's |
| LB2_1h-SM2_1h: There is no difference between the two population means | Mann-Whitney | *0.0002 | We reject H₀ and accept Hₐ: LB2_1h's mean is less than SM2_1h's |
| LB1_1h-LB4_1h: There is no difference between the two population means | Mann-Whitney | 0.4745 | We fail to reject H₀ |
| LB1_1h-LB3_1h: There is no difference between the two population means | Mann-Whitney | 0.3538 | We fail to reject H₀ |
| LB1_1h-SM1_1h: There is no difference between the two population means | Mann-Whitney | *0.0003 | We reject H₀ and accept Hₐ: LB1_1h's mean is less than SM1_1h's |
| LB1_1h-SM2_1h: There is no difference between the two population means | Mann-Whitney | *0.0003 | We reject H₀ and accept Hₐ: LB1_1h's mean is less than SM2_1h's |
| LB4_1h-LB3_1h: There is no difference between the two population means | Mann-Whitney | 0.3606 | We fail to reject H₀ |
| LB4_1h-SM1_1h: There is no difference between the two population means | Mann-Whitney | *0.0005 | We reject H₀ and accept Hₐ: LB4_1h's mean is less than SM1_1h's |
| LB4_1h-SM2_1h: There is no difference between the two population means | Mann-Whitney | *0.0004 | We reject H₀ and accept Hₐ: LB4_1h's mean is less than SM2_1h's |
| LB3_1h-SM1_1h: There is no difference between the two population means | Mann-Whitney | *0.0009 | We reject H₀ and accept Hₐ: LB3_1h's mean is less than SM1_1h's |
| LB3_1h-SM2_1h: There is no difference between the two population means | Mann-Whitney | *0.0005 | We reject H₀ and accept Hₐ: LB3_1h's mean is less than SM2_1h's |
| SM1_1h-SM2_1h: There is no difference between the two population means | Mann-Whitney | 0.2699 | We fail to reject H₀ |

**Significance level: 0.05**



### Means Difference Hypothesis Test Summary (x7day_medium)

#### Means difference statistical test summary among all methods for instances from group x7day_medium under a running time limit of 7200 seconds.

| Null Hypothesis | Test | p-value | Decision |
|----------------|------|---------|----------|
| KS-SM1: There is no difference between the two population means | Mann-Whitney | 0.3813 | We fail to reject H₀ |
| KS-LB1: There is no difference between the two population means | Mann-Whitney | *0.0165* | We reject H₀ and accept Hₐ: KS's mean less than LB1's |
| KS-LB4: There is no difference between the two population means | Mann-Whitney | *0.0125* | We reject H₀ and accept Hₐ: KS's mean less than LB4's |
| KS-LB2: There is no difference between the two population means | Mann-Whitney | *0.0131* | We reject H₀ and accept Hₐ: KS's mean less than LB2's |
| KS-LB3: There is no difference between the two population means | Mann-Whitney | *0.0012* | We reject H₀ and accept Hₐ: KS's mean less than LB3's |
| KS-SM2: There is no difference between the two population means | Mann-Whitney | *0.0* | We reject H₀ and accept Hₐ: KS's mean less than MILP2's |
| SM1-LB1: There is no difference between the two population means | Mann-Whitney | 0.061 | We fail to reject H₀ |
| SM1-LB4: There is no difference between the two population means | Mann-Whitney | 0.061 | We fail to reject H₀ |
| SM1-LB2: There is no difference between the two population means | Mann-Whitney | 0.0691 | We fail to reject H₀ |
| SM1-LB3: There is no difference between the two population means | Mann-Whitney | *0.0103* | We reject H₀ and accept Hₐ: MILP's mean less than LB3's |
| SM1-SM2: There is no difference between the two population means | Mann-Whitney | *0.0* | We reject H₀ and accept Hₐ: MILP's mean less than MILP2's |
| LB1-LB4: There is no difference between the two population means | Mann-Whitney | 0.4418 | We fail to reject H₀ |
| LB1-LB2: There is no difference between the two population means | Mann-Whitney | 0.5219 | We fail to reject H₀ |
| LB1-LB3: There is no difference between the two population means | Mann-Whitney | 0.1463 | We fail to reject H₀ |
| LB1-SM2: There is no difference between the two population means | Mann-Whitney | *0.0001* | We reject H₀ and accept Hₐ: LB1's mean less than MILP2's |
| LB4-LB2: There is no difference between the two population means | Mann-Whitney | 0.551 | We fail to reject H₀ |
| LB4-LB3: There is no difference between the two population means | T-test for two samples | 0.2583 | We fail to reject H₀ |
| LB4-SM2: There is no difference between the two population means | T-test for two samples | *0.0001* | We reject H₀ and accept Hₐ: LB4's mean less than MILP2's |
| LB2-LB3: There is no difference between the two population means | Mann-Whitney | 0.1638 | We fail to reject H₀ |
| LB2-SM2: There is no difference between the two population means | Mann-Whitney | *0.0002* | We reject H₀ and accept Hₐ: LB2's mean less than MILP2's |
| LB3-SM2: There is no difference between the two population means | Mann-Whitney | *0.0004* | We reject H₀ and accept Hₐ: LB3's mean less than MILP2's |

**Significance level: 0.05**



### Means Difference Hypothesis Test Summary (x7day_large)

#### Means difference statistical test summary among all methods for instances from group x7day_large under a running time limit of 4000 seconds.

| Null Hypothesis | Test | p-value | Decision |
|----------------|------|---------|----------|
| KS_1h-LB1_1h: There is no difference between the two population means | T-test for two samples | *0.0071* | We reject H₀ and accept Hₐ: KS_1h's mean less than LB1_1h's |
| KS_1h-LB2_1h: There is no difference between the two population means | T-test for two samples | *0.0038* | We reject H₀ and accept Hₐ: KS_1h's mean less than LB2_1h's |
| KS_1h-LB4_1h: There is no difference between the two population means | T-test for two samples | *0.0005* | We reject H₀ and accept Hₐ: KS_1h's mean less than LB4_1h's |
| KS_1h-LB3_1h: There is no difference between the two population means | Mann-Whitney | *0.0021* | We reject H₀ and accept Hₐ: KS_1h's mean less than LB3_1h's |
| KS_1h-SM1_1h: There is no difference between the two population means | Mann-Whitney | *0.0003* | We reject H₀ and accept Hₐ: KS_1h's mean less than SM1_1h's |
| KS_1h-SM2_1h: There is no difference between the two population means | Mann-Whitney | *0.0001* | We reject H₀ and accept Hₐ: KS_1h's mean less than SM2_1h's |
| LB1_1h-LB2_1h: There is no difference between the two population means | T-test for two samples | 0.2958 | We fail to reject H₀ |
| LB1_1h-LB4_1h: There is no difference between the two population means | T-test for two samples | 0.1441 | We fail to reject H₀ |
| LB1_1h-LB3_1h: There is no difference between the two population means | T-test for two samples | 0.1603 | We fail to reject H₀ |
| LB1_1h-SM1_1h: There is no difference between the two population means | Mann-Whitney | *0.0425* | We reject H₀ and accept Hₐ: LB1_1h's mean less than SM1_1h's |
| LB1_1h-SM2_1h: There is no difference between the two population means | T-test for two samples | *0.0033* | We reject H₀ and accept Hₐ: LB1_1h's mean less than SM2_1h's |
| LB2_1h-LB4_1h: There is no difference between the two population means | T-test for two samples | 0.3234 | We fail to reject H₀ |
| LB2_1h-LB3_1h: There is no difference between the two population means | T-test for two samples | 0.329 | We fail to reject H₀ |
| LB2_1h-SM1_1h: There is no difference between the two population means | Mann-Whitney | 0.1208 | We fail to reject H₀ |
| LB2_1h-SM2_1h: There is no difference between the two population means | T-test for two samples | *0.0155* | We reject H₀ and accept Hₐ: LB2_1h's mean less than SM2_1h's |
| LB4_1h-LB3_1h: There is no difference between the two population means | T-test for two samples | 0.4934 | We fail to reject H₀ |
| LB4_1h-SM1_1h: There is no difference between the two population means | Mann-Whitney | 0.2347 | We fail to reject H₀ |
| LB4_1h-SM2_1h: There is no difference between the two population means | T-test for two samples | *0.032* | We reject H₀ and accept Hₐ: LB4_1h's mean less than SM2_1h's |
| LB3_1h-SM1_1h: There is no difference between the two population means | Mann-Whitney | 0.1853 | We fail to reject H₀ |
| LB3_1h-SM2_1h: There is no difference between the two population means | T-test for two samples | *0.0408* | We reject H₀ and accept Hₐ: LB3_1h's mean less than SM2_1h's |
| SM1_1h-SM2_1h: There is no difference between the two population means | Mann-Whitney | 0.1208 | We fail to reject H₀ |

**Significance level: 0.05**



### Means Difference Hypothesis Test Summary (x7day_large)

#### Means difference statistical test summary among all methods for instances from group x7day_large under a running time limit of 7200 seconds.**

| Null Hypothesis | Test | p-value | Decision |
|----------------|------|---------|----------|
| KS-LB2: There is no difference between the two population means | Mann-Whitney | *0.0164 | We reject H₀ and accept Hₐ: KS's mean less than LB2's |
| KS-LB1: There is no difference between the two population means | Mann-Whitney | *0.0105 | We reject H₀ and accept Hₐ: KS's mean less than LB1's |
| KS-LB4: There is no difference between the two population means | Mann-Whitney | *0.0072 | We reject H₀ and accept Hₐ: KS's mean less than LB4's |
| KS-LB3: There is no difference between the two population means | Mann-Whitney | *0.0019 | We reject H₀ and accept Hₐ: KS's mean less than LB3's |
| KS-SM1: There is no difference between the two population means | Mann-Whitney | *0.0021 | We reject H₀ and accept Hₐ: KS's mean less than MILP's |
| KS-SM2: There is no difference between the two population means | Mann-Whitney | *0.0001 | We reject H₀ and accept Hₐ: KS's mean less than MILP2's |
| LB2-LB1: There is no difference between the two population means | T-test for two samples | 0.3812 | We fail to reject H₀ |
| LB2-LB4: There is no difference between the two population means | T-test for two samples | 0.2823 | We fail to reject H₀ |
| LB2-LB3: There is no difference between the two population means | T-test for two samples | 0.1417 | We fail to reject H₀ |
| LB2-SM1: There is no difference between the two population means | T-test for two samples | 0.0858 | We fail to reject H₀ |
| LB2-SM2: There is no difference between the two population means | T-test for two samples | *0.0012 | We reject H₀ and accept Hₐ: LB2's mean less than MILP2's |
| LB1-LB4: There is no difference between the two population means | T-test for two samples | 0.3952 | We fail to reject H₀ |
| LB1-LB3: There is no difference between the two population means | T-test for two samples | 0.2175 | We fail to reject H₀ |
| LB1-SM1: There is no difference between the two population means | T-test for two samples | 0.1337 | We fail to reject H₀ |
| LB1-SM2: There is no difference between the two population means | T-test for two samples | *0.0022 | We reject H₀ and accept Hₐ: LB1's mean less than MILP2's |
| LB4-LB3: There is no difference between the two population means | T-test for two samples | 0.2932 | We fail to reject H₀ |
| LB4-SM1: There is no difference between the two population means | T-test for two samples | 0.1826 | We fail to reject H₀ |
| LB4-SM2: There is no difference between the two population means | T-test for two samples | *0.0032 | We reject H₀ and accept Hₐ: LB4's mean less than MILP2's |
| LB3-SM1: There is no difference between the two population means | T-test for two samples | 0.3414 | We fail to reject H₀ |
| LB3-SM2: There is no difference between the two population means | T-test for two samples | *0.0101 | We reject H₀ and accept Hₐ: LB3's mean less than MILP2's |
| SM1-SM2: There is no difference between the two population means | T-test for two samples | *0.0290 | We reject H₀ and accept Hₐ: MILP's mean less than MILP2's |

**Significance level: 0.05**


