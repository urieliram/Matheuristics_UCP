# Un método Mate-heurístico para resolver UC.
---
+ [Introducción](#introduccion)
+ [Implementación](#implementación)
  * [Clases](#clases)
+ [Pruebas](#pruebas)
  * [Instancias](#instancias)
+ [Ligas](#ligas)
---

## Introducción
El principal componente de este método es un modelo MILP fuerte y compacto **A Tight and Compact MILP** basado en [Knueven2020](https://pubsonline.informs.org/doi/10.1287/ijoc.2019.0944).

## Implementación


### Clases


## Pruebas


### Instancias
Características de las instancias Knueven2021

|GROUP           |INST  (n)       |GEN   (G)       |PERIOD   (T)   |FILES (uc_XX)   |
| :------------- | -------------: | -------------: |-------------: |-------------:  |
|rts_gmlc        | 12             |  73            |  48           | (45-56)        |
| ca             | 20             |  610           |  48           | (1-20)         |
|ferc            | 12             |  934           |  48           | (21-24),(37-44)|
|ferc(2)         | 12             |  978           |  48           | (25-36)        |

Características de las instancias Morales-españa2013 
Estas instancias tienen una alta simetría, por lo que tardan en resolverse un poco más que otras instancias mas cercanas a las de la realidad.

|GROUP           |INST  (n)       |GEN   (G)       |PERIOD   (T)   |FILES (uc_XX)   |
| :------------- | -------------: | -------------: |-------------: |-------------:  |
|   x7day_small  | 10             |  28 to 54      | 168           | (61-70)        |
|   x7day_large  | 10             |  132 to 187    | 168           | (71-80)        |
|   x10gen_small | 10             |  280 to 540    | 24            | (81-90)        |
|   x10gen_large | 10             |  1320 to 1870  | 24            | (91-100)       |

Otras instancias usadas para validar el modelo son:

> - uc_57 morales_espania2013,Section_III_D,example of one_day. TABLE IX morales-españa2013
> - uc_58 morales_espania2013,Section_III_D,example of five days. TABLE VII morales-españa2013
> - uc_59 morales_espania2013,Template of eight generators. TABLE VII morales-españa2013


## Ligas
[On Mixed-Integer Programming Formulations for the Unit Commitment Problem, Knueven2020](https://pubsonline.informs.org/doi/10.1287/ijoc.2019.0944).

[Matheuristics for Speeding Up the Solution of the Unit Commitment Problem, Harjunkoski2021](https://ieeexplore.ieee.org/document/9640029).


