# Instrucciones para Agentes de IA - Proyecto UC (Unit Commitment)

## Descripción General del Proyecto
Implementación de un método mate-heurístico para resolver problemas de Unit Commitment (UC) utilizando MILP (Mixed-Integer Linear Programming). Basado en el modelo "Tight and Compact MILP" de [Knueven2020](https://pubsonline.informs.org/doi/10.1287/ijoc.2019.0944).

## Arquitectura Principal

### Componentes Clave
- **`main.py`**: Programa principal que ejecuta el flujo completo de solución (LP → Hard3 → Harjk → MILP2 → LBC1-4 → KS)
- **`uc_Co.py`**: Define el modelo matemático de optimización usando Pyomo (1217 líneas, ecuaciones 2-67)
- **`solution.py`**: Clase `Solution` que encapsula la solución de modelos con CPLEX
- **`reading.py`**: Lee instancias desde archivos JSON (formato Knueven2020)
- **`util.py`**: Utilidades (config, gap calculation, save/load solutions)
- **`config.con`**: Archivo CSV con parámetros de configuración del solver

### Flujo de Solución (Método Mate-heurístico de 2 Fases)

#### Fase de Construcción (Construction Phase)
1. **Linear Relaxation (LR)**: Relaja variables binarias a [0,1], resuelve LP para obtener cota inferior
2. **Hard3 (HARDUC)**: Método Relax & Fix que fija variables binarias según criterio:
   - Fija a 0: variables donde `ũ[g,t]·p̃[g,t] = 0` (no producen en LP)
   - Libera: resto de variables para que solver decida
   - Genera **RCL** (Restricted Candidate List): variables que cumplen `{u[g,t]: {ũ[g,t]·p̃[g,t] < Pmin} ∩ {ũ[g,t]·p̃[g,t]≠0}}`
3. **Harjk**: Implementación alternativa usando regla de Harjunkoski (fija a 1 donde `ũ[g,t]·p̃[g,t] ≥ Pmin`)

#### Fase de Mejora (Improvement Phase)
4. **MILP2**: Resuelve MILP completo desde solución inicial Hard3 con warm-start
5. **Local Branching (lbc1-4)**: 4 variantes de búsqueda local en árbol B&B (ver detalles abajo)
6. **KS (Kernel Search)**: Matheurística que divide espacio de búsqueda en kernel + buckets

## Estructura de Datos

### Instancias JSON
Ubicadas en `instances/`, formato Knueven2020 con campos:
- `time_periods`: Número de periodos T
- `demand`: Array de demanda por periodo
- `reserves`: Requerimientos de reserva
- `generators`: Lista con `Pmax`, `Pmin`, `UT`, `DT`, rampas (`RU`, `RD`, `SU`, `SD`), costos (`piecewise_production`, `startup`), etc.

### Variables Principales del Modelo
- `u[g,t]`: Binaria, generador g encendido en periodo t
- `v[g,t]`: Binaria, arranque (start-up) 
- `w[g,t]`: Binaria, apagado (shut-down)
- `p[g,t]`: Potencia de salida
- `r[g,t]`: Reserva asignada
- `delta[g,t,s]`: Variables de costo de arranque por segmento

### Opciones de Modelo (`option` en `uc_Co.uc()`)
- `'LR'` / `'RC'`: Variables binarias relajadas como continuas
- `'Hard3'`: Fija `SB_Uu` a 1, libera `No_SB_Uu`
- `'Harjk'`: Fijación según regla Harjunkoski
- `'Milp2'`: MILP con solución inicial
- `'lbc1'`-`'lbc4'`: Local branching con diferentes estrategias
- `'Check'`: Verificación de factibilidad

## Convenciones Importantes

### Manejo de Configuración
- **NO modificar directamente variables en `main.py`** (líneas 23-28 son para testing local)
- Configuración se carga desde `config.con` vía `util.config_env()`
- Parámetros CPLEX: `emphasizeMILP`, `symmetryMILP`, `lbheurMILP`, `gap`, `k` (neighborhood size para LBC)

### Ejecución
```bash
# Desde script (recomendado para batch)
sh test.sh

# Manual (requiere ambiente 'yalma')
python3 main.py uc_060.json yalma

# Verifica ejecutable CPLEX en config.con:
# executable,/opt/ibm/ILOG/CPLEX_Studio221/cplex/bin/x86-64_linux/cplex
```

### Nomenclatura de Resultados
- Logs: `Log_<instance>.log`, `logfile<Method>uc_<instance>[_<iter>].log`
- Soluciones guardadas: `solHard3_a_uc_<instance>.csv`, `solHard3_b_uc_<instance>.csv`
- Estadísticas: `stat.csv` (agregadas por `util.append_list_as_row()`)

### Variables "Binary Support" (BS)
- **`SB_Uu` (BS)**: Lista de tuplas (g,t) donde `u[g,t]=1` en la solución. Representa generadores encendidos
  - **Solo usa `u[g,t]`**, NO incluye `v[g,t]`, `w[g,t]`, `delta[g,t]` (variables dominantes según Paper)
  - Fijadas a 1 en heurísticas para explotar estructura del problema
- **`No_SB_Uu` (~BS)**: Tuplas donde `u[g,t]=0` (NO fijadas, candidatas a cambiar en búsqueda local)
- **`lower_Pmin_Uu` (RCL)**: Variables donde `Pmin·u < Pmin` del generador (regla Harjunkoski)
  - Forman **Restricted Candidate List** para LB1/LB4: `{u[g,t]: {ũ[g,t]·p̃[g,t] < Pmin} ∩ {ũ[g,t]·p̃[g,t]≠0}}`

## Patrones de Código

### Creación de Modelos
```python
# Siempre pasar instancia + opciones específicas
model, __ = uc_Co.uc(instance, option='Hard3', 
                     SB_Uu=SB_Uu, No_SB_Uu=No_SB_Uu,
                     nameins=nameins[0:6], mode='Tight', scope='')
```

### Solución con CPLEX
```python
sol = Solution(model=model, env=ambiente, executable=executable,
               nameins=nameins[0:6], gap=gap, timelimit=timeconst,
               emphasize=emphasizeHEUR, symmetry=symmetryHEUR,
               option='Hard3', scope='')
z, g = sol.solve_problem()  # Returns objetivo, gap
```

### Extracción de Soporte Binario
```python
SB_Uu, No_SB_Uu, __, Vv, Ww, delta = sol.select_binary_support_Uu('Hard3')
lower_Pmin_Uu = sol.update_lower_Pmin_Uu(lower_Pmin_Uu, 'Hard3')
```

## Errores Comunes

### ⚠️ No Ejecutar sin CPLEX
- Verificar `executable` en `config.con` existe antes de correr
- Script `comandos.sh` contiene **token de GitHub** (NO compartir, usar .gitignore)

### ⚠️ Tiempo vs Cálculo de Gap
- Tiempos `t_hard3`, `t_harjk` **incluyen** tiempo de LP (`t_lp`)
- Calcular gap correcto: `util.igap(lb_best, z_hard3)` NO `g_hard3` del solver

### ⚠️ Memoria en Instancias Grandes
- `del sol_<method>; gc.collect()` después de cada heurística
- Instancias grandes: ferc (934-978 generadores), ca (610 gen)

## Análisis y Visualización

### Jupyter Notebooks
- `Figures_TC_UC*.ipynb`: Generación de gráficas de resultados
- `Instances_gen.ipynb`: Generación de nuevas instancias
- `Simulation_LBC.ipynb`: Análisis de Local Branching

### Grupos de Instancias (ver README.md)
- **rts_gmlc**: uc_045-056 (73 gen, 168 periodos)
- **ca**: uc_001-020 (610 gen)
- **ferc**: uc_021-044 (934-978 gen)
- **Kazarlis**: uc_061-100 (alta simetría)

## Dependencias Externas
- **Pyomo**: Framework de modelado matemático
- **IBM CPLEX**: Solver MILP (requiere licencia)
- **numpy**, **pandas**: Manipulación de datos
- **matplotlib** (notebooks): Visualización

## Detalles de los Métodos Matemáticos

### Kernel Search (KS)
Matheurística que divide el espacio de búsqueda en dos componentes:

1. **Kernel (K)**: Variables `u[g,t]=1` en solución inicial (obtenida de HARDUC)
2. **Buckets (B_i)**: Resto de variables divididas en grupos según costos reducidos
   - Número de buckets: **Regla de Sturges**: `nbucks = 1 + 3.322·ln(|U|)`
   - Variables ordenadas descendentemente por reduced costs de LP con kernel fijado

**Algoritmo completo** (loop mientras `elapsed_time < t_total`):

**Fase de Inicialización**:
```python
cutoff = z*
K = {u[g,t]: u[g,t]=1 en x̄}  # Kernel desde solución inicial
Resolver LP fijando K a 1 → obtener reduced costs
U = {u[g,t] ∉ K}  # Variables fuera del kernel
nbucks = 1 + 3.322·ln(|U|)  # Regla de Sturges
U_desc = sort(U, by=reduced_costs, descending=True)
{B_i} = buildbuckets(U_desc, nbucks)  # Dividir en buckets
tl = (t_total - elapsed_time) / nbucks  # Tiempo por bucket
```

**Construcción de Buckets** (`buildbuckets(U_desc, nbucks)`):
```python
# Divide U_desc en nbucks subconjuntos aproximadamente iguales
n = |U_desc|
k = ⌊n / nbucks⌋  # Tamaño base de cada bucket
remainder = n mod nbucks  # Variables sobrantes
# Los primeros 'remainder' buckets reciben una variable extra
# Ejemplo: n=100, nbucks=7 → k=14, remainder=2
#   B_1: 15 vars, B_2: 15 vars, B_3-7: 14 vars cada uno
for i in 1..nbucks:
    size = k + (1 if remainder > 0 else 0)
    B_i = U_desc[start:start+size]
    start += size
    if remainder > 0: remainder -= 1
```

**Fase de Expansión** (para cada bucket `i=1..nbucks`):
```python
P^{K∪B_i} = fixing(0, ~B_i, P)  # Fija a 0 OTROS buckets
P^{K∪B_i} += {Σ(j∈B_i) u_j ≥ 1}  # Fuerza ≥1 variable del bucket entre
{stat, x̃, z̃} = solve(P^{K∪B_i}, cutoff, tl)
if stat == feasible and z̃ < z*:
    z* = z̃; cutoff = z̃; x* = x̃
    K = K ∪ {u[g,t] ∈ B_i: u[g,t]=1 en x̃}  # Actualiza kernel
```

**Reinicia** buckets si termina antes de tiempo total (diversificación)

### Local Branching (LB) - 4 Variantes

**Concepto base**: Exploración de vecindario `N(x̄,k)` usando corte de ramificación local:
```
Δ(x,x̄) = Σ(j∈BS)(1-u_j) + Σ(j∈~BS)(u_j) ≤ k
```
donde `k` es el tamaño del vecindario (parámetro en `config.con`)

**Diferencias entre variantes**:

- **LB1** (`lbc1`): 
  - Búsqueda local entre BS y **RCL** (NO todo ~BS)
  - **Soft-fixing**: `Σ(j∈BS) x̄_j·x_j ≥ 0.9·Σ(j∈BS) x̄_j` (mantiene 90% del BS)
  - **Relaja integralidad** de `u[g,t]` en BS (aprovecha que constraints `v`,`w` fuerzan valores binarios)
  
- **LB2** (`lbc2`):
  - Igual a LB1 pero **sin soft-fixing**
  - Mantiene `u[g,t]` binario en BS
  
- **LB3** (`lbc3`):
  - **Versión original de Fischetti2003**
  - Búsqueda entre BS y TODO ~BS (sin RCL)
  - Sin soft-fixing
  
- **LB4** (`lbc4`):
  - Igual a LB1 pero **RCL diferente**
  - RCL formado por variables con **costos reducidos negativos** (en vez de regla Harjunkoski)

**Constraints de LB** (ecuaciones del Paper):
```python
# Left-branch:  Δ(x,x̄) ≤ k
# Right-branch: Δ(x,x̄) ≥ k+1
# Tabu:         Δ(x,x̄) ≥ 1  (evita revisitar soluciones)
# Soft-fixing:  Σ(j∈BS) x̄_j·x_j ≥ 0.9·Σ(j∈BS) x̄_j  (solo LB1/LB4)
```

## Scope Extensions
- `scope=''`: Modelo básico UC (T&C de Knueven2020)
- `scope='POZ+EL'`: Incluye Prohibited Operating Zones + Elastic Loads (añade variables `l[d,t]`, `rco[b,t]`, etc.)

---

## ⚠️ Discrepancias entre Paper e Implementación

### Kernel Search (KS)
**✅ Implementado según paper**:
- Regla de Sturges para número de buckets: `n = ⌊1 + 3.322·ln(|U|)⌋` (línea 900 main.py)
- Ordenamiento por reduced costs descendente
- Constraint `Σ(j∈B_i) u_j ≥ 1` para forzar entrada al kernel (línea 933 uc_Co.py)
- Fijación a 0 de variables fuera del kernel y bucket actual

**⚠️ Diferencias**:
- **División de buckets**: Código usa `len_i = ceil(len(No_SB_Uu) / n)` con incremento `len_i+1`, NO implementa algoritmo `buildbuckets()` del paper que distribuye remainder equitativamente
- **Sin reinicio**: Código NO reinicia buckets después de completar todos (diversificación mencionada en paper)
- **Criterio de parada adicional**: `max_without_improve = 7` (línea 913) NO está en paper

### Local Branching (LB1-4)
**✅ Correctamente implementado**:
- **LB1**: Soft-fixing (90%) + RCL (lower_Pmin_Uu) + `u[g,t]` en UnitInterval (líneas 836-897 uc_Co.py)
- **LB2**: Sin soft-fixing + RCL + `u[g,t]` Binary (líneas 900-960)
- **LB3**: Sin soft-fixing + sin RCL (usa `No_SB_Uu` completo en cut[1]) + Binary (líneas 963-1024)
- **LB4**: Soft-fixing + RCL por reduced costs negativos + UnitInterval (líneas 1027-1091)
- Constraints left/right-branch y tabu implementadas correctamente

**⚠️ Diferencias menores**:
- Código comenta líneas de desactivar soft-fixing en ciertas condiciones (NO mencionado en paper)
- Ajuste dinámico de `k`: incrementa/decrementa `k/2` según infeasibility (NO en paper, solo menciona diversificación)

### HARDUC (Hard3)
**✅ Implementado según paper**:
- Fija a 0: `ũ[g,t]·p̃[g,t] = 0` en LP
- Libera: resto de variables (`SB_Uu` y `lower_Pmin_Uu`)
- RCL: `{u[g,t]: {ũ[g,t]·p̃[g,t] < Pmin} ∩ {ũ[g,t]·p̃[g,t]≠0}}`

### Harjunkoski (Harjk)
**✅ Implementado según paper**:
- Fija a 1: variables donde `ũ[g,t]·p̃[g,t] ≥ Pmin`

---
*Para ecuaciones específicas, consultar `uc_Co.py` (refs. a Knueven2020) o archivo `Paper` (algoritmos KS y LB)*
