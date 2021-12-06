# --------------------------------------------------------------------------------
# File: main.py
# Unit Commitment Problem 
# Developers: Uriel Iram Lezama Lope
# Purpose: Programa principal de un modelo de UC
# Description: Lee una instancia de UCP y la resuelve. 
# Para correr el programa usar el comando "python3 main.py anjos.json thinkpad"
# --------------------------------------------------------------------------------
import copy
import pyomo as pyo
from egret.parsers.pglib_uc_parser import create_ModelData
from egret.models.unit_commitment import solve_unit_commitment
from egret.model_library.unit_commitment.uc_model_generator import UCFormulation, generate_model

from datetime import date
from datetime import datetime
from timeit import timeit
from pyomo.core.base import piecewise

from pyomo.util.infeasible import log_infeasible_constraints
import routines
import util
import outfiles
import time
import sys
import time
import unit_commitment as UC

instancia = 'anjos.json'
ruta      = 'instances/'
ambiente  = 'thinkpad'
# if len(sys.argv) != 3:
#     print("!!! something went wrong, try something like: $python3 ksuc.py name_instance.json yalma")
#     print("!!! or: $python3 ksuc.py name_instance.json thinkpad")
#     print("archivo:  ", sys.argv[1])
#     print("ambiente: ", sys.argv[2])
#     sys.exit()
# ambiente = sys.argv[2]
# instancia = sys.argv[1]

localtime = time.asctime(time.localtime(time.time()))
#ruta = '/home/uriel/GIT/UCVNS/ucvns/'

md = create_ModelData(ruta+instancia)  # large instance
#md = create_ModelData('/home/uriel/GIT/UCVNS/ucvns/ca/Scenario400_reserves_5.json')
# md = create_ModelData('/home/uriel/GIT/UCVNS/ucvns/anjosmodificado.json')   # small instance

# Append a list as new line to an old csv file
# row_file = [localtime,instancia]
# util.append_list_as_row('solution.csv', row_file)
print(localtime, ' ', 'solving --->', instancia)

# /home/uriel/Egret-main/egret/data/model_data.py
G     = 0      # generators number
S     = []     # eslabones de costo variable de arranque
L     = {}     # eslabones de costo en piecewise
pc    = []     # piecewise cost
Piecewise = [] # piecewise cost
C     = []     # cost of segment of piecewise
Pb    = []     # power of segment of piecewise
De    = []     # load
Re    = []     # reserve_requirement
Pmin  = []     # power min
Pmax  = []     # power max
RU    = []     # ramp_up_limit", "ramp_up_60min"
RD    = []     # ramp_down_limit", "ramp_down_60min"
SU    = []     # ramp_startup_limit", "startup_capacity"
SD    = []     # ramp_shutdown_limit", "shutdown_capacity"
UT    = []     # time_upminimum
DT    = []     # time_down_minimum
D     = []     # number of hours generator g is required to be off at t=1 (h).
U     = []     # number of hours generator g is required to be on at t=1 (h).
p_0   = []     # power_output_t0
pc_0  = []     # power_output_t0
t_0   = []     # tiempo que lleva en un estado (prendido(+) o apagado(-))
u_0   = []     # ultimo estado de la unidad   
M     = []     # averange cost of priority list
CR    = []     # cost of generator g running and operating at minimum production P_g ($/h).


T = len(md.data['system']['time_keys'])  # time periods

# to get the data from the generators
j = 0
for i, gen in md.elements("generator", generator_type="thermal", in_service=True):        

    # S.update(gen["startup_cost"])
    S = range(1,len(S))
    ## egret/parser/pglib_uc_parser.py
    #gen["startup_cost"] = list( (s["lag"], s["cost"]) for s in gen["startup"] )
    #gen["p_cost"] = { "data_type":"cost_curve", "cost_curve_type":"piecewise", 
    #                            "values": list( (c["mw"], c["cost"]) for c in gen["piecewise_production"]) }
    
    Piecewise.append(gen["p_cost"]["values"])
    Pmin.append(gen["p_min"])
    Pmax.append(gen["p_max"])
    RU.append(gen["ramp_up_60min"])
    RD.append(gen["ramp_down_60min"])
    SU.append(gen["startup_capacity"])
    SD.append(gen["shutdown_capacity"])
    UT.append(gen["min_up_time"])
    DT.append(gen["min_down_time"])
    t_0.append(gen["initial_status"])
    
    ## prendido
    if t_0[G] > 0:
        u_0.append(1)
        aux = UT[G] - t_0[G]
        U.append(aux)
        D.append(0)
        
    ## apagado
    if t_0[G] <= 0: 
        u_0.append(0)   
        aux = DT[G] + t_0[G]
        if aux <= 0:
            aux = 0
        U.append(0)
        D.append(aux) 

    p_0.append(gen["initial_p_output"])
    pc_0.append(max(0,gen["initial_p_output"]-gen["p_min"]))

    CR.append(0.0) # todo{ dar un valor mas o menos real de instancias del MEM }
    G = G + 1    
    
L[1] = [1,2,3]
L[2] = [1,2,3,4]
L[3] = [1,2,3,4,5]  
#print(Piecewise)

# for i in range(len(Piecewise)):
#     for j in range(len(Piecewise[i])):
#         C.append(Piecewise[i][j])

# print(C)
    
    
Re = md.data['system']['reserve_requirement']["values"]  # reserve requierement

for obj, dem in md.elements("load"):   # load demand
    De = dem["p_load"]["values"]

t_o = time.time()  # Start of the calculation time count

# todo{almacenar en una clase instancia todos los parametros de un modelo}
# instance = Instance()

# todo{almacenar en una clase Solution}
# soluc = Solution()

# Inizialize variables making a empty-solution with all generators in cero
Uu = [[0 for x in range(T)] for y in range(G)]
V  = [[0 for x in range(T)] for y in range(G)]
W  = [[0 for x in range(T)] for y in range(G)]
P  = [[0 for x in range(T)] for y in range(G)]
R  = [[0 for x in range(T)] for y in range(G)]

z_exact = 0
t_o = time.time()  # Start of the calculation time count
fixShedu = False   # True si se fija la solución entera U, False, si se desea resolver de manera exacta
relax = False      # True si se relaja la solución entera U, False, si se desea resolver de manera entera
model = UC.solve(G,T,L,S,Piecewise,Pmax,Pmin,UT,DT,De,Re,CR,u_0,U,D,SU,SD,RU,RD,pc_0,fixShedu,relax,ambiente)
 
#log_infeasible_constraints(model)
z_exact = model.obj.expr()
t_exact = time.time() - t_o
print("z_exact = ", z_exact)
print("t_exact = ", t_exact)

# ALMACENA SOLUCIÓN ENTERA
for t in range(T):
    for g in range(G):
        Uu[g][t] = int(model.u[(g+1, t+1)].value)
        V [g][t] = int(model.v[(g+1, t+1)].value)
        W [g][t] = int(model.w[(g+1, t+1)].value)
        P [g][t] = int(model.p[(g+1, t+1)].value)
        R [g][t] = int(model.r[(g+1, t+1)].value)
        #print(g, t, (model.u[(g, t)].value), (model.v[(g, t)].value), (model.w[(g, t)].value), model.p[(g, t)].value)

# Guarda en archivo csv la solución
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
#     N, T, c, Piecewise, pmax, pmin, TU, TD, De, Re, CR, FixShedu, Relax, U, ambiente)
# z_relax = pyo.value(model.obj)
# t_relax = time.time() - t_o
# print("z_relax = ", z_relax)
# print("t_relax = ", t_relax)

# # IMPRIME SOLUCIÓN RELAJADA
# for t in range(T):
#     for g in range(G):
#         #U[g][t] = int(model.u[(g, t)].value)
#         print(g, t, (model.u[(g, t)].value), (model.v[(g, t)].value), (model.w[(g, t)].value), model.p[(g, t)].value)

# z_fixed = float("inf")
# print('FIXED SOLUTION')
# FixShedu = True  # True si se fija la solución entera U, False, si se desea resolver de manera exacta
# Relax = False    # True si se relaja la solución entera U, False, si se desea resolver de manera entera
# model = unit_commitment.solve(
#     N, T, c, Piecewise, pmax, pmin, TU, TD, De, Re, CR, FixShedu, Relax, U, ambiente)
# if model != None:
#     z_fixed = pyo.value(model.obj)
#     print("z = ", z_fixed)

# Guarda en archivo csv la solución Ugvns
#outfiles.sendtofileU(U,"Uconst_" + instancia + ".csv")
#outfiles.sendtofileTUTD(TU,TD,"timesTUTD_" + instancia + ".csv")

# # Resultados GVNS
# print("z_fixed = ", z_fixed)

# Append a list as new line to an old csv file

# row_file = [localtime, instancia, T, N, 
# round(z_exact,1), round(z_relax,1), round(z_fixed,1), t_exact ]  # data to csv
# util.append_list_as_row('stat.csv', row_file)