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
import numpy as np 
import uc_Co
import util
import reading
from   solution import Solution

instancia = 'uc_45 - copia.json' # z_milp=283887541.8, z_lp=279360013.2, z_sub=283892029.8
instancia = 'archivox.json'      # z_milp=283849653.5, z_lp=279311866.4, z_sub=283854271.1
instancia = 'uc_5.json'          #  <<<---------- AQUI
instancia = 'anjos.json'         # z_milp=9650.0,      z_lp=8328.8,      z_sub=9700.0


ruta        = 'instances/'
ambiente    = 'localPC'
if ambiente == 'yalma':
    if len(sys.argv) != 3:
        print("!!! Something went wrong, try something like: $python3 main.py uc_45.json yalma")
        print("archivo:  ", sys.argv[1])
        print("ambiente: ", sys.argv[2])
        sys.exit()
    ambiente  = sys.argv[2]
    instancia = sys.argv[1]

localtime = time.asctime(time.localtime(time.time()))

print(localtime,'solving --->',instancia)

## Lee instancia de archivo .json con formato de Knueven2020
G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,Pb,C,mpc,Cs,Tmin,names = reading.reading(ruta+instancia)

## Lista de Parámetros
## relax = True si se relaja la solución entera.
## fix   = 'Soft',''Hard' si se fija la solución entera de manera suave (dominio continuo) o dura (enteras fijadas).
## tee   = True si se quiere ver el log del solver.
## lpmethod = 0 ## 0=Automatic; 1,2= Primal and dual simplex; 3=Sifting; 4=Barrier, 5 Concurrent 
gap       = 0.001
timelimit = 3000


## Relax as LP and solve
t_o = time.time() 
model  = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,relax=True,namemodel=instancia[0:4])
sol_lp = Solution(model = model, nameins=instancia, env=ambiente, gap=gap, timelimit=timelimit,
                  tee   = False, tofile = False)
z_lp = 0 
z_lp = sol_lp.solve_problem() 
t_lp = time.time() - t_o
print("t_lp = ", round(t_lp,4),"z_lp = ", round(z_lp,1))


## Seleccionamos las variables que serán fijadas.
fix_Uu = sol_lp.select_fixed_variables_U()


# HARD FIX solution and solve the sub-MILP.
t_o = time.time() 
model   = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fix='Hard',fix_Uu=fix_Uu,namemodel=instancia[0:4])
sol_hard = Solution(model = model, nameins=instancia, env=ambiente, gap=gap, timelimit=timelimit,
                    tee   = False, tofile = False)
z_hard = 0; z_hard = sol_hard.solve_problem() 
t_hard = time.time() - t_o
print("t_hard = ", round(t_hard,4),"z_hard = ", round(z_hard,1), "n_fix_Uu = ", len(fix_Uu))

        
## SOFT FIX solution and solve the sub-MILP.
t_o = time.time() 
model   = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fix='Soft',fix_Uu=fix_Uu,namemodel=instancia[0:4])
sol_soft = Solution(model = model, nameins=instancia, env=ambiente, gap=gap, timelimit=timelimit,
                    tee   = False, tofile = False)
z_soft = 0; z_soft = sol_soft.solve_problem() 
t_soft = time.time() - t_o
print("t_soft = ", round(t_soft,4),"z_soft = ", round(z_soft,1), "n_fix_Uu = ", len(fix_Uu))
#util.imprime_sol(model,sol_soft)


## Imprimimos las posibles variables 'u' que podrían no sean enteras.
sol_soft.print_U_no_int()


## Solve as a MILP
t_o = time.time() 
model    = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,namemodel=instancia[0:4])
sol_milp = Solution(model = model, nameins=instancia, env=ambiente, gap=gap, timelimit=timelimit,
                    tee   = False, tofile = False, export=True)
z_milp = 0 ; z_milp = sol_milp.solve_problem()
t_milp = time.time() - t_o
print("t_milp = ", round(t_milp,4),"z_milp = ", round(z_milp,1))
util.imprime_sol(model,sol_milp)
    

## Append a list as new line to an old csv file using as log:  
row = [localtime,instancia,len(T),len(G),gap,round(z_lp,1),round(z_milp,1),round(z_hard,1),round(z_soft,1),
                                             round(t_lp,4),round(t_milp,4),round(t_hard,4),round(t_soft,4), 
                                             round(z_soft-z_milp,1),len(fix_Uu)]
util.append_list_as_row('stat.csv', row)