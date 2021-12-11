## --------------------------------------------------------------------------------
## File: main.py
## Unit Commitment Problem 
## Developers: Uriel Iram Lezama Lope
## Purpose: Programa principal de un modelo de UC
## Description: Lee una instancia de UCP y la resuelve. 
## Para correr el programa usar el comando "python3 main.py anjos.json thinkpad"
## --------------------------------------------------------------------------------
# import copy
# import pyomo as pyo
# from egret.models.unit_commitment import solve_unit_commitment
# from egret.model_library.unit_commitment.uc_model_generator import UCFormulation, generate_model
# from datetime import date
# from datetime import datetime
# from timeit import timeit
# from pyomo.core.base import piecewise
# from pyomo.core.base.boolean_var import ScalarBooleanVar
# from pyomo.util.infeasible import log_infeasible_constraints

from egret.parsers.pglib_uc_parser import create_ModelData
import outfiles
import util
import time
import sys
import unit_commitment as UC

## GROUP     #INST  #GEN PERIOD FILES
##            n      G     T    uc_XX
## rts_gmlc   12     73    48   (45-56)
## ca         20    610    48   (1-20)
## ferc       12    934    48   (21-24),(37-44)
## ferc(2)    12    978    48   (25-36)

instancia = 'UC_45.json'
instancia = 'archivox.json'
instancia = 'anjos.json'
ruta      = 'instances/'
ambiente  = 'thinkpad'
if ambiente == 'yalma':
    if len(sys.argv) != 3:
        print("!!! Something went wrong, try something like: $python3 main.py uc_45.json yalma")
        print("archivo:  ", sys.argv[1])
        print("ambiente: ", sys.argv[2])
        sys.exit()
    ambiente = sys.argv[2]
    instancia = sys.argv[1]

localtime = time.asctime(time.localtime(time.time()))

##ruta = '/home/uriel/GIT/UCVNS/ucvns/'
md = create_ModelData(ruta+instancia)

## Append a list as new line to an old csv file
row_file = [localtime,instancia]
util.append_list_as_row('solution.csv', row_file)
print(localtime, ' ', 'solving --->', instancia)

## extracted from /home/uriel/Egret-main/egret/data/model_data.py
G     = 0      ## generators number
S     = {}     ## eslabones de costo variable de arranque
L     = {}     ## eslabones de costo en piecewise
pc    = []     ## piecewise cost
C     = {}     ## cost of segment of piecewise
Pb    = {}     ## power of segment of piecewise
De    = []     ## load
Re    = []     ## reserve_requirement
Pmin  = []     ## power min
Pmax  = []     ## power max
RU    = []     ## ramp_up_limit", "ramp_up_60min"
RD    = []     ## ramp_down_limit", "ramp_down_60min"
SU    = []     ## ramp_startup_limit", "startup_capacity"
SD    = []     ## ramp_shutdown_limit", "shutdown_capacity"
UT    = []     ## time_upminimum
DT    = []     ## time_down_minimum
D     = []     ## number of hours generator g is required to be off at t=1 (h).
U     = []     ## number of hours generator g is required to be on at t=1 (h).
p_0   = []     ## power_output_t0
pc_0  = []     ## power_output_t0
t_0   = []     ## tiempo que lleva en un estado (prendido(+) o apagado(-))
u_0   = []     ## ultimo estado de la unidad
mpc   = {}     ## cost of generator g running and operating at minimum production Pmin ($/h).
Tmin  = {}     ## lag   de cada escalón del conjunto S de la función de costo variable de arranque.
Cs    = {}     ## Costo de cada escalón del conjunto S de la función de costo variable de arranque.
Piecewise = [] ## piecewise cost
Startup   = [] ## start-up  cost

T = len(md.data['system']['time_keys'])  ## time periods

## To get the data from the generators
for i, gen in md.elements("generator", generator_type="thermal", in_service=True):  
    
    Piecewise.append(gen["p_cost"]["values"])
    lista=[]
    for j in range(1,len(Piecewise[G])+1):
        lista.append(j)   
    L[G+1] = lista
    
    Startup.append(gen["startup_cost"])
    lista=[]
    for j in range(1,len(Startup[G])+1):
        lista.append(j)  
    S[G+1] = lista
    
    Pmin.append(gen["p_min"])
    Pmax.append(gen["p_max"])
    RU.append(gen["ramp_up_60min"])
    RD.append(gen["ramp_down_60min"])
    SU.append(gen["startup_capacity"])
    SD.append(gen["shutdown_capacity"])
    UT.append(gen["min_up_time"])
    DT.append(gen["min_down_time"])
    t_0.append(gen["initial_status"])
    
    ## Caso prendido
    if t_0[G] > 0:
        u_0.append(1)
        aux = UT[G] - t_0[G]
        U.append(aux)
        D.append(0)
        
    ## Caso apagado
    if t_0[G] <= 0: 
        u_0.append(0)   
        aux = DT[G] + t_0[G]
        if aux <= 0:
            aux = 0
        U.append(0)
        D.append(aux) 

    p_0.append(gen["initial_p_output"])
    pc_0.append(max(0,gen["initial_p_output"]-gen["p_min"]))
    
    G = G + 1    

## Se extraen los diccionarios Pb y C de la lista de listas Piecewise    
k=0; n=0
for i in Piecewise:
    s=len(i)
    k=k+1
    n=0
    for j in i:
        n=n+1
        # print(k,",",n,",",s,",",j[0],",",j[1])
        Pb[k,n] = j[0]
        C[k,n]  = j[1]
        ## Se calcula el costo mínimo de operación 
        if n==1:
            mpc[k] = j[0]*j[1]
        
## Se extraen los diccionarios Tmin y Cs de la lista de listas Startup    
k=0; n=0
for i in Startup:
    s=len(i)
    k=k+1
    n=0
    for j in i:
        n=n+1
        # print(k,",",n,",",s,",",j[0],",",j[1])
        Tmin[k,n] = j[0]
        Cs[k,n]   = j[1]

#print(Piecewise)
# for i in range(len(Piecewise)):
#     for j in range(len(Piecewise[i])):
#         C.append(Piecewise[i][j])
#print(C)    
    
Re = md.data['system']['reserve_requirement']["values"]  ## reserve requierement

for obj, dem in md.elements("load"):   ## load demand
    De = dem["p_load"]["values"]

t_o = time.time()  ## Start of the calculation time count

# TODO{almacenar en una clase instancia todos los parametros de un modelo}
# instance = Instance()

# TODO{almacenar en una clase Solution}
# soluc = Solution()

## Inizialize variables making a empty-solution with all generators in cero
Uu = [[0 for x in range(T)] for y in range(G)]
V  = [[0 for x in range(T)] for y in range(G)]
W  = [[0 for x in range(T)] for y in range(G)]
P  = [[0 for x in range(T)] for y in range(G)]
R  = [[0 for x in range(T)] for y in range(G)]

z_exact = 0
t_o = time.time()  ## Start of the calculation time count
fixShedu = False   ## True si se fija   la solución entera Uu, False, si se desea resolver de manera exacta
relax = False      ## True si se relaja la solución entera Uu, False, si se desea resolver de manera entera
model = UC.solve(G,T,L,S,Piecewise,Pmax,Pmin,UT,DT,De,Re,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fixShedu,relax,ambiente)
 
#log_infeasible_constraints(model)
z_exact = model.obj.expr()
t_exact = time.time() - t_o
print("z_exact = ", z_exact)
print("t_exact = ", t_exact)

## ALMACENA SOLUCIÓN ENTERA
for t in range(T):
    for g in range(G):
        Uu[g][t] = int(model.u[(g+1, t+1)].value)
        V [g][t] = int(model.v[(g+1, t+1)].value)
        W [g][t] = int(model.w[(g+1, t+1)].value)
        P [g][t] = int(model.p[(g+1, t+1)].value)
        R [g][t] = int(model.r[(g+1, t+1)].value)
        #print(g, t, (model.u[(g, t)].value), (model.v[(g, t)].value), (model.w[(g, t)].value), model.p[(g, t)].value)

## Guarda en archivo csv la solución
outfiles.sendtofilesolution(Uu,"U_" + instancia[0:5] + ".csv")
outfiles.sendtofilesolution(V ,"V_" + instancia[0:5] + ".csv")
outfiles.sendtofilesolution(W ,"W_" + instancia[0:5] + ".csv")
outfiles.sendtofilesolution(P ,"P_" + instancia[0:5] + ".csv")
outfiles.sendtofilesolution(R ,"R_" + instancia[0:5] + ".csv")

# print('RELAXED')
# z_relax = 0
# t_o = time.time()  # Start of the calculation time count
# FixShedu = False   # True si se fija la solución entera U, False, si se desea resolver de manera exacta
# Relax = True       # True si se relaja la solución entera U, False, si se desea resolver de manera entera
# model = unit_commitment.solve(
#     N, T, c, Piecewise, pmax, pmin, TU, TD, De, Re, FixShedu, Relax, U, ambiente)
# z_relax = pyo.value(model.obj)
# t_relax = time.time() - t_o
# print("z_relax = ", z_relax)
# print("t_relax = ", t_relax)

## IMPRIME SOLUCIÓN RELAJADA
# for t in range(T):
#     for g in range(G):
#         #U[g][t] = int(model.u[(g, t)].value)
#         print(g, t, (model.u[(g, t)].value), (model.v[(g, t)].value), (model.w[(g, t)].value), model.p[(g, t)].value)

# z_fixed = float("inf")
# print('FIXED SOLUTION')
# FixShedu = True  # True si se fija la solución entera U, False, si se desea resolver de manera exacta
# Relax = False    # True si se relaja la solución entera U, False, si se desea resolver de manera entera
# model = unit_commitment.solve(
#     N, T, c, Piecewise, pmax, pmin, TU, TD, De, Re, FixShedu, Relax, U, ambiente)
# if model != None:
#     z_fixed = pyo.value(model.obj)
#     print("z = ", z_fixed)

## Guarda en archivo csv la solución Ugvns
#outfiles.sendtofileU(U,"Uconst_" + instancia + ".csv")
#outfiles.sendtofileTUTD(TU,TD,"timesTUTD_" + instancia + ".csv")

## Resultados GVNS
# print("z_fixed = ", z_fixed)

# Append a list as new line to an old csv file

row_file = [localtime, instancia, T, G, round(z_exact,1), round(t_exact,2) ]  # data to csv
util.append_list_as_row('stat.dat', row_file)