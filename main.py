## --------------------------------------------------------------------------------
## File: main.py
## Unit Commitment Problem 
## Developers: Uriel Iram Lezama Lope
## Purpose: Programa principal de un modelo de UC
## Description: Lee una instancia de UCP y la resuelve. 
## Para correr el programa usar el comando "python3 main.py anjos.json yalma"
## Desde script test.sh "sh test.sh"
## --------------------------------------------------------------------------------

import time
import sys
import numpy as np 
import uc_Co
import util
import reading
from   solution import Solution

instancia = 'uc_45 - copia.json' # z_milp=283887541.8, z_lp=279360013.2, z_sub=283892029.8
instancia = 'uc_5.json'          # 
instancia = 'anjos.json'         # z_milp=9650.0,      z_lp=8328.8,      z_sub=9700.0
instancia = 'archivox.json'      # z_milp=283849653.5, z_lp=279311866.4, z_sub=283854271.1

ruta        = 'instances/'
ambiente    = 'localPC' 
#ambiente    = 'yalma' ## Recordar cambiar este valor a 'yalma' para pruebas en ese servidor.

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

z_lp = 0;  z_milp = 0; z_hard = 0; z_soft = 0; z_softcut = 0; z_lbc = 0
t_lp = 0;  t_milp = 0; t_hard = 0; t_soft = 0; t_softcut = 0; t_lbc = 0
nU_no_int = 0;

## Lee instancia de archivo .json con formato de Knueven2020
G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,Pb,C,mpc,Cs,Tmin,names = reading.reading(ruta+instancia)

## Lista de Parámetros
## relax = True si se relaja la solución entera.
## fix   = 'Soft', 'Hard', 'LBC' si se fija la solución entera de manera suave (dominio continuo) o dura (enteras fijadas), o se usa Local Branchong Constraint
## tee   = True si se quiere ver el log del solver.
## lpmethod = 0 ## 0=Automatic; 1,2= Primal and dual simplex; 3=Sifting; 4=Barrier, 5 Concurrent 
gap       = 0.001
timelimit = 3000

## ------------------------ LINEAR RELAXATION -----------------------------------------

## Relax as LP and solve
if 1 == 1:
    t_o = time.time() 
    model  = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,relax=True,namemodel=instancia[0:4])
    sol_lp = Solution(model = model, nameins=instancia, env=ambiente, gap=gap, timelimit=timelimit,
                    tee   = False, tofile = False)
    z_lp = sol_lp.solve_problem() 
    t_lp = time.time() - t_o
    print("t_lp = ", round(t_lp,4),"z_lp = ", round(z_lp,1))

## ------------------------ SELECTION VARIABLES TO FIX -----------------------------------------

    ## Seleccionamos las variables que serán fijadas.
    fixed_Uu , No_fixed_Uu , abajo_Pmin = sol_lp.select_fixed_variables_U()
    
    print('generadores abajo_Pmin',abajo_Pmin)

## ------------------------------------- HARD FIX ---------------------------------------------

# HARD FIX solution and solve the sub-MILP.
if 1 == 1:
    t_o = time.time() 
    model   = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fix='Hard',fixed_Uu=fixed_Uu,namemodel=instancia[0:4])
    sol_hard = Solution(model = model, nameins=instancia, env=ambiente, gap=gap, timelimit=timelimit,
                        tee   = False, tofile = False)
    z_hard = sol_hard.solve_problem() 
    t_hard = time.time() - t_o
    print("t_hard = ", round(t_hard,4),"z_hard = ", round(z_hard,1), "n_fixed_Uu = ", len(fixed_Uu))

## ------------------------------------- SOFT FIX ---------------------------------------------
        
## SOFT FIX solution and solve the sub-MILP.
if 1 == 1:
    t_o = time.time() 
    model   = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fix='Soft',fixed_Uu=fixed_Uu,namemodel=instancia[0:4])
    sol_soft = Solution(model = model, nameins=instancia, env=ambiente, gap=gap, timelimit=timelimit,
                        tee   = False, tofile = False)
    z_soft = sol_soft.solve_problem() 
    t_soft = time.time() - t_o
    print("t_soft = ", round(t_soft,4),"z_soft = ", round(z_soft,1), "n_fixed_Uu = ", len(fixed_Uu))
    ## Imprimimos las posibles variables 'u' que podrían no sean enteras.
    nU_no_int = sol_soft.print_U_no_int()

## --------------------------------- SOFT FIX + CUT-OFF --------------------------------------
        
## SOFT FIX + CUT-OFF solution and solve the sub-MILP. (cutoff=z_hard)

if 1 == 1:
    t_o = time.time() 
    model   = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fix='Soft',fixed_Uu=fixed_Uu,namemodel=instancia[0:4])
    sol_softcut = Solution(model = model, nameins=instancia, env=ambiente, gap=gap, cutoff=z_hard, timelimit=timelimit,
                           tee   = False, tofile = False)
    z_softcut = sol_softcut.solve_problem() 
    t_softcut = time.time() - t_o
    print("t_softcut = ", round(t_softcut,4),"z_softcut = ", round(z_softcut,1), "n_fixed_Uu = ", len(fixed_Uu))
    ## Imprimimos las posibles variables 'u' que podrían no sean enteras.
    ##nU_no_int = sol_softcut.print_U_no_int()

## -------------------------------- LOCAL BRANCHING CUTS ------------------------------------

## LOCAL BRANCHING CUTS solution and solve the sub-MILP using (cutoff=z_hard)
if 1 == 1:
    t_o = time.time()   
    k   = abajo_Pmin
    model   = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fix='LBC',fixed_Uu=fixed_Uu,No_fixed_Uu=No_fixed_Uu,k=k,namemodel=instancia[0:4])
    sol_lbc = Solution(model = model, nameins=instancia, env=ambiente, gap=gap, cutoff=z_hard, timelimit=timelimit,
                         tee = True, tofile = False)
    z_lbc = sol_lbc.solve_problem() 
    t_lbc = time.time() - t_o
    print("t_lbc = ", round(t_lbc,4),"z_lbc = ", round(z_lbc,1), "n_fixed_Uu = ", len(fixed_Uu))
    util.imprime_sol(model,sol_lbc)
    # Imprimimos las posibles variables 'u' que podrían no sean enteras en la solución.
    #nU_no_int = sol_lbc.print_U_no_int()

## ----------------------------------------- MILP -----------------------------------------

## Solve as a MILP
if 1 == 1:
    t_o = time.time() 
    model    = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,namemodel=instancia[0:4])
    sol_milp = Solution(model = model, nameins=instancia, env=ambiente, gap=gap, timelimit=timelimit,
                        tee   = False, tofile = False, exportLP = False)
    z_milp = sol_milp.solve_problem()
    t_milp = time.time() - t_o
    print("t_milp = ", round(t_milp,4),"z_milp = ", round(z_milp,1))
    util.imprime_sol(model,sol_milp)

## ------------------------------------ RESULTS -------------------------------------------

## Append a list as new line to an old csv file using as log, the first line of the file as shown.
## 'localtime,instancia,T,G,gap,z_lp,z_milp,z_hard,z_soft,z_softcut,z_lbc,t_lp,t_milp,t_hard,t_soft,t_softcut,t_lbc,gap_soft_milp,n_fixU,nU_no_int,k'
row = [localtime,instancia,len(T),len(G),gap,round(z_lp,1),round(z_milp,1),round(z_hard,1),     round(z_soft,1),     round(z_softcut,1),     round(z_lbc,1),
                                             round(t_lp,4),round(t_milp,4),round(t_hard+t_lp,4),round(t_soft+t_lp,4),round(t_softcut+t_lp+t_hard,4),round(t_lbc+t_lp+t_hard,4),
                                             round(z_soft-z_milp,4),len(fixed_Uu),nU_no_int,k]
util.append_list_as_row('stat.csv', row)