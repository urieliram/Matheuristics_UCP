## --------------------------------------------------------------------------------
## File: main.py
## A math-heuristic to Tight and Compact Unit Commitment Problem 
## Developers: Uriel Iram Lezama Lope
## Purpose: Programa principal de un modelo de UC
## Description: Lee una instancia de UCP y la resuelve. 
## Para correr el programa usar el comando "python3 main.py anjos.json yalma"
## Desde script en linux test.sh "sh test.sh"
## --------------------------------------------------------------------------------
import time
import sys
import numpy as np 
import uc_Co
import util
import reading
from   solution import Solution

instancia = 'anjos.json'         
instancia = 'archivox.json'      
instancia = 'uc_55.json'         # !!! Instancia donde aparentemente z_lbc es menor que z_milp

ruta        = 'instances/'
ambiente    = 'localPC' 
ambiente    = 'yalma'            ## Activar esta línea para pruebas en el servidor 'yalma'.

if ambiente == 'yalma':
    if len(sys.argv) != 3:
        print("!!! Something went wrong, try write something like: $python3 main.py uc_54.json yalma")
        print("archivo : ", sys.argv[1])
        print("ambiente: ", sys.argv[2])
        sys.exit()
    ambiente  = sys.argv[2]
    instancia = sys.argv[1]

localtime = time.asctime(time.localtime(time.time()))

print(localtime,'Solving --->',instancia)

z_lp = 0;  z_milp = 0; z_hard = 0; z_soft = 0; z_softcut = 0; z_lbc = 0
t_lp = 0;  t_milp = 0; t_hard = 0; t_soft = 0; t_softcut = 0; t_lbc = 0; nU_no_int = 0;

## Lee instancia de archivo .json con formato de [Knueven2020]
G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,Pb,C,mpc,Cs,Tmin,names = reading.reading(ruta+instancia)

## Lista de Parámetros
## relax    =  True    if the integer solution is relaxed.
## fix      =  'Soft'  fixes the solution in a soft fashion (dominio flotante ente 0 y 1); 
##          ...'Hard'  fixes the solution in a hard fashion (enteras fijadas a 1); (something like relax and fix);
##          ...'LBC'   using Local Branching Constraint.
##          ...'relax' relax the problem as LP and solve it
## tee      =  True si se quiere ver el log del solver.
## lpmethod =  0 : 0=Automatic; 1,2= Primal and dual simplex; 3=Sifting; 4=Barrier, 5=Concurrent 
gap       = 0.001
timelimit = 2000

## Si ya tenemos un resultado previo:
precargado, z_milp, z_hard, t_milp, t_hard = util.resultados_lp_milp(instancia,ambiente,gap,timelimit)

## ----------------------------------------- MILP -----------------------------------------

## Solve as a MILP
if precargado == False:
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,nameins=instancia[0:4])
    sol_milp = Solution(model = model, nameins=instancia[0:4], env=ambiente, gap=gap, timelimit=timelimit,
                        tee   = False, tofiles = False, exportLP = False)
    z_milp = sol_milp.solve_problem()
    t_milp = time.time() - t_o
    print("t_milp = ", round(t_milp,1), "z_milp = ", round(z_milp,1))

## ------------------------ LINEAR RELAXATION -----------------------------------------

## Relax as LP and solve it
if 1 == 1:
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fix='relax',nameins=instancia[0:4])
    sol_lp   = Solution(model = model, env=ambiente, nameins=instancia[0:4], gap=gap, timelimit=timelimit,
                        tee   = False, tofiles = False)
    z_lp = sol_lp.solve_problem() 
    t_lp = time.time() - t_o
    print("t_lp = ", round(t_lp,1), "z_lp = ", round(z_lp,1))
    
## ------------------------ SELECTION VARIABLES TO FIX -----------------------------------------

    ## Seleccionamos las variables que serán fijadas, se requiere correr antes <linear relaxation>
    ## fixed_Uu    variables que Si serán fijadas a 1.
    ## No_fixed_Uu variables que No serán fijadas.
    ## lower_Pmin  variables en que la potencia Pmin del generador fue menor a la mínima y No serán fijadas.
    fixed_Uu , No_fixed_Uu , lower_Pmin = sol_lp.select_fixed_variables_U()
    
    print('generadores lower_Pmin', len(lower_Pmin))

## ------------------------------------- HARD-FIXING ---------------------------------------------

# HARD-FIXING solution and solve the sub-MILP.
if precargado == False:
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fix='Hard',fixed_Uu=fixed_Uu,nameins=instancia[0:4])
    sol_hard = Solution(model = model, env=ambiente, nameins=instancia[0:4], gap=gap, timelimit=timelimit,
                        tee   = False, tofiles = False)
    z_hard = sol_hard.solve_problem()
    t_hard = time.time() - t_o + t_lp
    print("t_hard = ", round(t_hard,1), "z_hard = ", round(z_hard,1), "n_fixed_Uu = ", len(fixed_Uu))

## ------------------------------------- SOFT-FIXING ---------------------------------------------
        
## SOFT-FIXING solution and solve the sub-MILP.
if 1 == 1:
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fix='Soft',fixed_Uu=fixed_Uu,nameins=instancia[0:4])
    sol_soft = Solution(model = model, env=ambiente, nameins=instancia[0:4], gap=gap, timelimit=timelimit,
                        tee   = False, tofiles = False)
    z_soft = sol_soft.solve_problem() 
    t_soft = time.time() - t_o + t_lp
    print("t_soft = ", round(t_soft,1), "z_soft = ", round(z_soft,1), "n_fixed_Uu = ", len(fixed_Uu))
    ## Imprimimos las posibles variables 'u' que podrían no sean enteras.
    nU_no_int, n_Uu_no_int , n_Uu_1_0 = sol_soft.count_U_no_int()
    

## --------------------------------- SOFT FIX + CUT-OFF --------------------------------------
        
## SOFT FIX + CUT-OFF solution and solve the sub-MILP (it is using cutoff = z_hard).
## Use 'Soft+pmin' if the lower subset of Uu-Pmin will be considered.
if 1 == 1:
    t_o = time.time() 
    model,xx    = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fix='Soft+pmin',fixed_Uu=fixed_Uu,nameins=instancia[0:4])
    sol_softcut = Solution(model = model, env=ambiente, nameins=instancia[0:4], gap=gap, cutoff=z_hard, timelimit=timelimit,
                           tee   = False, tofiles = False)
    z_softcut = sol_softcut.solve_problem() 
    t_softcut = time.time() - t_o + t_hard ## t_hard (ya cuenta el tiempo de lp)
    print("t_soft+cut = ", round(t_softcut,4), "z_soft+cut = ", round(z_softcut,1), "n_fixed_Uu = ", len(fixed_Uu))
    ## Imprimimos las posibles variables 'u' que podrían no sean enteras.
    nU_no_int, n_Uu_no_int , n_Uu_1_0 = sol_softcut.count_U_no_int()

## -------------------------------- LOCAL BRANCHING CUTS ------------------------------------

## Include the LOCAL BRANCHING CUT to the solution and solve the sub-MILP (it is using cutoff=z_hard).
if 1 == 1: 
    
    t_o = time.time()   
    k   = len(lower_Pmin) # El valor de intentos de asignación está siendo usado para definir el parámetro k en el LBC. 
    model,ns = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fix='LBC+pmin',fixed_Uu=fixed_Uu,No_fixed_Uu=No_fixed_Uu,
                        k=k, lower_Pmin=lower_Pmin, nameins=instancia[0:4])
    sol_lbc  = Solution(model = model, env=ambiente, nameins=instancia[0:4], gap=gap, cutoff=z_hard, timelimit=timelimit,
                          tee = False, tofiles = False)
    z_lbc = sol_lbc.solve_problem() 
    t_lbc = time.time() - t_o + t_hard ## t_hard (ya cuenta el tiempo de lp)
    print("t_lbc = ", round(t_lbc,1), "z_lbc = ", round(z_lbc,1), "n_fixed_Uu = ", len(fixed_Uu))
    # Imprimimos las posibles variables 'u' que podrían no sean enteras en la solución.
    nU_no_int, n_Uu_no_int , n_Uu_1_0 = sol_lbc.count_U_no_int()    
    
    # \todo{Calcular el tamaño del slack del subset Sbarra}
    # \todo{Evaluar el efecto de la cota obtenida del hard-fix}
    # \todo{Revisar factibilidad de la solución}
    # \todo{Reducir tiempo de búsqueda o iteraciones en el solver}
    # \todo{Cambiar valor de k en nuevas iteraciones}
    # \todo{Probar tamaños del n_kernel (!!! al parecer influye mucho en el tiempo de búsqueda)}  
    # \todo{EVALUAR SI NOS CONVIENE O NO INCLUIR LOS INTENTOS DE ASIGNACIÓN}}    
    # \todo{Verificar por que la instancia uc_52.json es infactible ???}

## ------------------------------------ RESULTS -------------------------------------------

## Append a list as new line to an old csv file using as log, the first line of the file as shown.
## 'ambiente,localtime,instancia,T,G,gap,timelimit,z_lp,z_hard,z_milp,z_soft,z_soft+cut,z_lbc,t_lp,t_hard,t_milp,t_soft,t_soft+cut,t_lbc,gapabs_z_lbc-z_milp,n_fixU,nU_no_int,n_Uu_no_int,n_Uu_1_0,k,bin_sup,comment'
comment = 'Soft+pmin,LBC+pmin'
row = [ambiente,localtime,instancia,len(T),len(G),gap,timelimit,
       round(z_lp,1),round(z_hard     ,1),round(z_milp,1),round(z_soft,1),round(z_softcut,1),round(z_lbc,1),
       round(t_lp,1),round(t_hard+t_lp,1),round(t_milp,1),round(t_soft,1),round(t_softcut,1),round(t_lbc,1),
       round(z_lbc-z_milp,4),len(fixed_Uu),nU_no_int,n_Uu_no_int,n_Uu_1_0,k,ns,comment]
util.append_list_as_row('stat.csv', row)