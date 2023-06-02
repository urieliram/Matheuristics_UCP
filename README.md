# Exploring Innovative Matheuristic Methods for Uniot commitment problem: A Comparative Evaluation.
---
+ [Introducción](#introduccion)
+ [Implementación](#implementación)
  * [Clases](#clases)
+ [Pruebas](#pruebas)
  * [Instancias](#instancias)
+ [Ligas](#ligas)
---

## Introducción
The Unit Commitment Problem (UCP) is a critical challenge in the electrical power systems operation schedule. It involves determining the optimal scheduling of power generation units over a specific time horizon, considering various constraints and objectives. This capsule delves into matheuristic methods, which combine mathematical optimization and heuristic search algorithms. Specifically, we will explore five matheuristic methods that utilize local bifurcation techniques from fischetti2003 and kernel search from Angelini 2013. Additionally, we will present an empirical evaluation comparing the performance of these methods with that of a solver. The evaluation focuses on solving a challenging model near the convex vestibule, utilizing instances derived from the Morales-Spain201 dataset. Finally, we will delve into the characteristics of the UCP, discuss the application of matheuristic methods, and highlight their potential to provide efficient and high-quality solutions.


## Implementación
The code of the methods proposed are in [main.py](main.py). The results can be found on [Figures_TC_UC2.ipynb](Figures_TC_UC2.ipynb). The MILP model of UCP is in [co_Co.py](co_Co.py). The generator of instances is on [instances_gen.ipynb](instances_gen.ipynb). 

El principal componente de este método es un modelo MILP fuerte y compacto **A Tight and Compact MILP** basado en [Knueven2020](https://pubsonline.informs.org/doi/10.1287/ijoc.2019.0944).

### Clases


## Assesment
(Comparative Evaluation: Assessing Method Performance)

To evaluate the effectiveness of the proposed matheuristic methods, we conducted a comprehensive empirical evaluation. The evaluation employed a tight and compact model situated close to the convex vestibule, a challenging region of the search space. The model featured a limited number of variables and constraints, ensuring a rigorous test for the matheuristic methods.

To construct difficult instances for evaluation, we utilized instances derived from the Morales-Spain201 dataset. These instances are known for their complexity and provide a suitable benchmark for assessing the performance of the proposed methods.

### Instancias
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
> - uc_57 morales_espania2013,Section_III_D,example of one_day from TABLE IX morales-españa2013.
> - uc_58 morales_espania2013,Section_III_D,example of five days from TABLE VII morales-españa2013.
> - uc_59 morales_espania2013,Template of eight generators from TABLE VII morales-españa2013.

### Resultados
The empirical evaluation yielded intriguing insights into the performance of the matheuristic methods. Four of the methods, based on local bifurcation techniques, showcased remarkable performance in capturing and exploiting local optima. By adapting the search process to the problem's characteristics, these methods demonstrated improved convergence and solution quality.




## Ligas
[On Mixed-Integer Programming Formulations for the Unit Commitment Problem, Knueven2020](https://pubsonline.informs.org/doi/10.1287/ijoc.2019.0944).

[Matheuristics for Speeding Up the Solution of the Unit Commitment Problem, Harjunkoski2021](https://ieeexplore.ieee.org/document/9640029).

[Tight and Compact MILP Formulation for the Thermal Unit Commitment Problem, Morales-españa2013](https://ieeexplore.ieee.org/document/6485014).

