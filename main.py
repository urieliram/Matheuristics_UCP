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
import time
import sys
import uc_Co
import util
import pyomo.environ as pyo
from   pyomo.util.infeasible import log_infeasible_constraints
from   pyomo.opt import SolverStatus, TerminationCondition
import reading
import outfiles

## Instances features
## GROUP     #INST  #GEN PERIOD FILES
##            n      G     T    uc_XX
## rts_gmlc   12     73    48   (45-56)
## ca         20    610    48   (1-20)
## ferc       12    934    48   (21-24),(37-44)
## ferc(2)    12    978    48   (25-36)

instancia = 'uc_45 - copia.json'
instancia = 'archivox.json'

instancia = 'anjos.json'
ruta      = 'instances/'
ambiente  = 'localPC'
if ambiente == 'yalma':
    if len(sys.argv) != 3:
        print("!!! Something went wrong, try something like: $python3 main.py uc_45.json yalma")
        print("archivo:  ", sys.argv[1])
        print("ambiente: ", sys.argv[2])
        sys.exit()
    ambiente = sys.argv[2]
    instancia = sys.argv[1]

localtime = time.asctime(time.localtime(time.time()))

## Append a list as new line to an old csv file
row_file = [localtime,instancia]
util.append_list_as_row('solution.csv', row_file)
print(localtime, ' ',   'solving json --->', instancia)

##Lee instancia de archivo .json con formato Knueven2020
G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,Pb,C,mpc,Cs,Tmin,names = reading.reading(ruta+instancia)

## -----------------  Caso de ejemplo de anjos.json  --------------------------
#G        = [1, 2, 3]
#T        = [1, 2, 3, 4, 5, 6]
#L        = {1: [1, 2, 3], 2: [1, 2, 3], 3: [1, 2, 3, 4]}
#S        = {1: [1, 2, 3], 2: [1, 2, 3], 3: [1, 2, 3, 4]}
#Pmax     = {1: 300.0, 2: 200.0, 3: 100.0}
#Pmin     = {1: 80, 2: 50, 3: 30}
#TU       = {1: 3, 2: 2, 3: 1}
#TD       = {1: 2, 2: 2, 3: 2}
#De       = {1: 240, 2: 250, 3: 200, 4: 170, 5: 230, 6: 190}
#R        = {1: 10, 2: 10, 3: 10, 4: 10, 5: 10, 6: 10}
#u_0      = {1: 1, 2: 0, 3: 0}
#D        = {1: 0, 2: 0, 3: 0}
#U        = {1: 2, 2: 0, 3: 0}
#SU       = {1: 100, 2: 70, 3: 40}
#SD       = {1: 80, 2: 50, 3: 30}
#RU       = {1: 50, 2: 60, 3: 70}
#RD       = {1: 30, 2: 40, 3: 50}
#pc_0     = {1: 40, 2: 0, 3: 0}
#mpc      = {1: 400.0, 2: 750.0, 3: 900.0}
#Pb       = {(1, 1): 80, (1, 2): 150, (1, 3): 300, (2, 1): 50, (2, 2): 100, (2, 3): 200, (3, 1): 30, (3, 2): 50, (3, 3): 70, (3, 4): 100}   
#C        = {(1, 1): 5.0, (1, 2): 5.0, (1, 3): 5.0, (2, 1): 15.0, (2, 2): 15.0, (2, 3): 15.0, (3, 1): 30.0, (3, 2): 30.0, (3, 3): 30.0, (3, 4): 30.0}
#Cs       = {(1, 1): 800.0, (1, 2): 800.0, (1, 3): 800.0, (2, 1): 500.0, (2, 2): 500.0, (2, 3): 500.0, (3, 1): 25.0, (3, 2): 250.0, (3, 3): 
#500.0, (3, 4): 1000.0}
#Tmin     = {(1, 1): 2, (1, 2): 3, (1, 3): 4, (2, 1): 2, (2, 2): 3, (2, 3): 4, (3, 1): 2, (3, 2): 3, (3, 3): 4, (3, 4): 5}
#fixShedu = False
#relax    = False
#ambiente = 'localPC'
## ----------------------------------  o  -------------------------------------

z_exact  = 0
t_o      = time.time()  ## Start of the calculation time count.
fixShedu = False        ## True si se fija la solución entera, False, si se desea resolver de manera exacta.
relax    = False        ## True si se relaja la solución entera, False, si se desea resolver de manera entera.
model    = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,
                    Pb,C,Cs,Tmin,names,fixShedu,relax,ambiente)

## Create the solver interface and solve the model
# solver = pyo.SolverFactory('glpk')
# solver = pyo.SolverFactory('cbc')
# https://www.ibm.com/docs/en/icos/12.8.0.0?topic=parameters-relative-mip-gap-tolerance
solver = pyo.SolverFactory('cplex')
if ambiente == "localPC":
    solver = pyo.SolverFactory('cplex')
if ambiente == "yalma": 
    solver = pyo.SolverFactory('cplex', executable='/home/uriel/cplex1210/cplex/bin/x86-64_linux/cplex')
solver.options['mip tolerances mipgap'] = 0.1  
#solver.options['mip tolerances absmipgap'] = 200
solver.options['timelimit'] = 300

## para mostrar una solución en un formato propio
## https://developers.google.com/optimization/routing/cvrp
## para editar un Lp en pyomo
## https://stackoverflow.com/questions/54312316/pyomo-model-lp-file-with-variable-values
    
## write LP file
#model.write()             ## To write the model into a file using .nl format
#filename = os.path.join(os.path.dirname(__file__), 'model.lp')
#model.write(filename, io_options={'symbolic_solver_labels': True})
#model.write(filename = str('model') + ".mps", io_options = {"symbolic_solver_labels":True})
#print(solver.ExportModelAsLpFormat(False).replace('\\', '').replace(',_', ','), sep='\n')
  
## Envía el problema de optimización al solver
res = solver.solve(model, tee=False) ## timelimit=10; tee=True(para ver log)
    
try:
    pyo.assert_optimal_termination(res)
except:
    print("An exception occurred")
        
file = open("modeluc.dat", "w")
file.write('z: %s \n' % (pyo.value(model.obj)))
file.write('g, t,\t u,\t v,\t w, \t p \n')       

#for g in range(0, len(G)):
#    file.write('%s, %s, \t %s \n' % (int(g), 0, u_0[g] ))

for t in range(0, len(T)):
    for g in range(0, len(G)):
        file.write('%s, %s,\t %s,\t  %s,\t  %s,\t %s \n' %
        (int(g), int(t), int(model.u[(g+1, t+1)].value),int(model.v[(g+1, t+1)].value),int(model.w[(g+1, t+1)].value), model.p[(g+1, t+1)].value))

file.write('TIME,\t s \t sR \n')
for t in range(1, len(T)+1):
    file.write('%s, \t%s,\t %s,\t \n' %
    (int(t), model.sn[t].value, model.sR[t].value))

# model.obj.pprint()     # Print the objetive function
# model.demand.pprint()  # Print constraint
# model.reserve.pprint()
# model.display()        # Print the optimal solution     
# z = pyo.value(model.obj)
model.pprint(file)
file.close()
    
##https://stackoverflow.com/questions/51044262/finding-out-reason-of-pyomo-model-infeasibility
log_infeasible_constraints(model)

##https://pyomo.readthedocs.io/en/stable/working_models.html
if (res.solver.status == SolverStatus.ok) and (res.solver.termination_condition == TerminationCondition.optimal):
    print ("this is feasible and optimal")
elif res.solver.termination_condition == TerminationCondition.infeasible:
    print (">>> do something about it? or exit?")
else:
    print ("something else is wrong",str(res.solver))  ## Something else is wrong

#log_infeasible_constraints(model)
z_exact = model.obj.expr()
#t_exact = time.time() - t_o
print("z_exact = ", z_exact)
#print("t_exact = ", t_exact)

gg = len(G)
tt = len(T)
## Inizialize variables making a empty-solution with all generators in cero
Uu = [[0 for x in range(tt)] for y in range(gg)]
V  = [[0 for x in range(tt)] for y in range(gg)]
W  = [[0 for x in range(tt)] for y in range(gg)]
P  = [[0 for x in range(tt)] for y in range(gg)]
R  = [[0 for x in range(tt)] for y in range(gg)]

## ALMACENA SOLUCIÓN ENTERA
for t in range(tt):
    for g in range(gg):
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