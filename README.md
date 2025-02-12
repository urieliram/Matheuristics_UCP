# A Kernel Search Matheuristic for a Thermal Unit Commitment Problem
---
+ [Introducción](#introduccion)
+ [Implementación](#implementación)
  * [Clases](#clases)
+ [Pruebas](#pruebas)
  * [Instancias](#instancias)
+ [Links](#links)
+ + [Appendix](#appendix)
---

## Introducción
The Unit Commitment Problem (UCP) is a critical challenge in the electrical power systems operation schedule. It involves determining the optimal scheduling of power generation units over a specific time horizon, considering various constraints and objectives. This capsule delves into matheuristic methods, which combine mathematical optimization and heuristic search algorithms. Specifically, we will explore five matheuristic methods that utilize local branching techniques from Fischetti 2003 and kernel search from Angelini 2013. Also, we will be presenting an empirical evaluation comparing the performance of these methods with that of a solver. The assessment focuses on solving a challenging model near the convex vestibule, utilizing instances derived from the Morales-España 2013 dataset. Finally, we will delve into the characteristics of the UCP, discuss the application of matheuristic methods, and highlight their potential to provide efficient and high-quality solutions.


## Implementación
The code of the methods proposed is in [main.py](main.py). The results can be found in [Figures_TC_UC2.ipynb](Figures_TC_UC2.ipynb). The MILP model of UCP is in [co_Co.py](co_Co.py). The generator of instances is on [instances_gen.ipynb](instances_gen.ipynb). 

The main component of this method is a strong and compact MILP model **A Tight and Compact MILP** based on [Knueven2020](https://pubsonline.informs.org/doi/10.1287/ijoc.2019.0944).



## Assessment
(Comparative Evaluation: Assessing Method Performance)

To evaluate the effectiveness of the proposed matheuristic methods, we conducted a comprehensive empirical evaluation. The evaluation employed a tight and compact model situated close to the convex hall, a challenging region of the search space. The model featured a limited number of variables and constraints, ensuring a rigorous test for the matheuristic methods.

To construct difficult instances for evaluation, we utilized instances derived from the Morales-Spain 2013 dataset. These instances are known for their complexity and provide a suitable benchmark for assessing the performance of the proposed methods.

### Instances
The instances in JSON format are in the folder [instances/](instances/).

Estas instancias tienen una alta simetría, por lo que tardan en resolverse un poco más que otras instancias mas cercanas a las de la realidad.

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

### Results
The empirical evaluation yielded intriguing insights into the performance of the matheuristic methods. Four of the methods, based on local bifurcation techniques, showcased remarkable performance in capturing and exploiting local optima. By adapting the search process to the problem's characteristics, these methods demonstrated improved convergence and solution quality.




## Ligas
[On Mixed-Integer Programming Formulations for the Unit Commitment Problem, Knueven2020](https://pubsonline.informs.org/doi/10.1287/ijoc.2019.0944).

[Matheuristics for Speeding Up the Solution of the Unit Commitment Problem, Harjunkoski2021](https://ieeexplore.ieee.org/document/9640029).

[Tight and Compact MILP Formulation for the Thermal Unit Commitment Problem, Morales-españa2013](https://ieeexplore.ieee.org/document/6485014).

The complete results can be found at:



[U. I. Lezama-Lope. Efficient Methods for Solving Power System Operation Scheduling Challenges: The Thermal Unit Commitment Problem with Staircase Cost and the Very Short-term Load Forecasting Problem. PhD thesis, Universidad Autonoma de Nuevo Leon, Monterrey, Mexico, November 2023.](http://eprints.uanl.mx/26250/).


## Appendix


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


