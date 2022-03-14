## --------------------------------------------------------------------------------
## File: main.py
## Unit Commitment Problem 
## Developers: Uriel Iram Lezama Lope
## Purpose: Programa principal de un modelo de UC
## Description: Lee una instancia de UCP y la resuelve. 
## Para correr el programa usar el comando "python3 main.py anjos.json thinkpad"
## --------------------------------------------------------------------------------

import time
import sys

from pymysql import NULL
import uc_Co
import util
import reading
from   solution import Solution

instancia = 'uc_45 - copia.json'
instancia = 'archivox.json'      # z_milp0.1=292812718.45270145, z_lp0.1=279311866.4, z_milp0.001=283849653.53052485
instancia = 'anjos.json'         # z_milp=9700.0, z_lp=8328.7

ruta      = 'instances/'
ambiente  = 'localPC'
if ambiente == 'yalma':
    if len(sys.argv) != 3:
        print("!!! Something went wrong, try something like: $python3 main.py uc_45.json yalma")
        print("archivo:  ", sys.argv[1])
        print("ambiente: ", sys.argv[2])
        sys.exit()
    ambiente  = sys.argv[2]
    instancia = sys.argv[1]

localtime = time.asctime(time.localtime(time.time()))

print(localtime, 'solving --->', instancia)

## Lee instancia de archivo .json con formato de Knueven2020
G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,Pb,C,mpc,Cs,Tmin,names = reading.reading(ruta+instancia)

## Start of the calculation time count.
t_o = time.time() 

## fix   = True si se fija la solución entera.
## relax = True si se relaja la solución entera.
gap   = 0.001

## Solve as a MILP
model = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fix= False,relax= False)
sol   = Solution(model  = model,nameins=instancia,env=ambiente,gap=gap,time=300,
                 tee    = False,
                 tofile = True)
z_milp = sol.solve_problem()
t_milp = time.time() - t_o
print("z_milp = ", round(z_milp,1))
util.imprime_sol(model,sol)


## Relax as LP and solve
# model = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fix=False,relax=True)
# sol = Solution(model   = model,nameins=instancia,env=ambiente,gap=gap,time=300,
#                 tee    = False,
#                 tofile = True)
z_lp = 0 
# z_lp = sol.solve_problem() 
t_lp = time.time() - t_o
print("z_lp = ", round(z_lp,1))
# util.imprime_sol(model,sol)


## Fix solution and solve the subMILP
model = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fix=True,relax=False)
sol   = Solution(model  = model,nameins=instancia,env=ambiente,gap=gap,time=300,
                 tee    = False,
                 tofile = True)
z_sub = 0
z_sub = sol.solve_problem() 
t_sub = time.time() - t_o
print("z_sub = ", round(z_sub,1))
util.imprime_sol(model,sol)

## Append a list as new line to an old csv file using as log:  localtime,instancia,T,G,z_lp,t_lp,z_milp,t_milp,z_sub,t_sub,gap
row = [localtime,instancia,len(T),len(G),round(z_milp,1),round(t_milp,4),round(z_lp,1),round(t_lp,4),round(z_sub,1),round(t_sub,4),gap]  ## data to csv
util.append_list_as_row('stat.csv', row)