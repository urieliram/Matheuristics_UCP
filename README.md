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
Características de las instancias Knueven2021 Datos obtenidos a partir de datos reales de mercados eléctricos de USA.

|GROUP           |INST  (n)       |GEN   (G)       |PERIOD   (T)   |FILES (uc_XX)   |
| :------------- | -------------: | -------------: |-------------: |-------------:  |
|rts_gmlc        | 12             |  73            |  168*         | (45-56)        |
|ca              | 20             |  610           |  168*         | (1-20)         |
|ferc            | 12             |  934           |  168*         | (21-24),(37-44)|
|ferc(2)         | 12             |  978           |  168*         | (25-36)        |
*El npumero de periodos fue modificado a 168 equivalente a 7 días, para calcular weekeen se usó un factor de 0.8

Características de las instancias Kazarlis
Estas instancias tienen una alta simetría, por lo que tardan en resolverse un poco más que otras instancias mas cercanas a las de la realidad.

|GROUP           |INST  (n)       |GEN   (G)       |PERIOD   (T)   |FILES (uc_XX)   |
| :------------- | -------------: | -------------: |-------------: |-------------:  |
|   x7day_small  | 10             |  28 to 54      | 168           | (061-070)      |90%
|   x7day_large  | 10             |  132 to 187    | 168           | (071-080)      |90%
|   x10gen_small | 10             |  280 to 540    | 24            | (081-090)      |
|   x10gen_large | 10             |  1320 to 1870  | 24            | (091-100)       |


Otras instancias creadas a partir de datos de Kazarlis son:
|GROUP              |INST  (n)       |GEN   (G)       |PERIOD   (T)   |FILES (uc_XX)   |
| :-------------    | -------------: | -------------: |-------------: |-------------:  |
|   x7day_medium    | 30             |  60 to 131     | 168           | (101-131)      |90%
|   x7day_large(b)  | 10             |  135 to 156    | 168           | (132-140)      |90%
|   x7day_large(c)  | 10             |  185 to 242    | 168           | (141-152)      |90%

Otras instancias que son usadas para validar el modelo son:

> - uc_57 morales_espania2013,Section_III_D,example of one_day. TABLE IX morales-españa2013
> - uc_58 morales_espania2013,Section_III_D,example of five days. TABLE VII morales-españa2013
> - uc_59 morales_espania2013,Template of eight generators. TABLE VII morales-españa2013


## Ligas
[On Mixed-Integer Programming Formulations for the Unit Commitment Problem, Knueven2020](https://pubsonline.informs.org/doi/10.1287/ijoc.2019.0944).

[Matheuristics for Speeding Up the Solution of the Unit Commitment Problem, Harjunkoski2021](https://ieeexplore.ieee.org/document/9640029).

[A genetic algorithm solution to the unit commitment problem](https://ieeexplore.ieee.org/document/485989)

