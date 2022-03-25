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
      
instancia = 'uc_52.json'       ## Infactible !!!  
  
instancia = 'uc_6.json'        ## ejemplos regulares 5,6    
instancia = 'uc_2.json'        ## ejemplos dificiles 2,3,4     
instancia = 'uc_3.json'        ## ejemplos dificiles 2,3,4   
instancia = 'uc_54.json'               
instancia = 'uc_53.json'       ## ejemplo de 'delta' relajado diferente de uno  
instancia = 'uc_47.json'       ## ejemplo sencillo  
instancia = 'archivox.json'    ## ejemplos sencillo 
instancia = 'anjos.json'       ## ejemplo de juguete
instancia = 'uc_45.json'       ## ejemplo de batalla

## Cragamos parámetros de configuración desde archivo <config>
ambiente, ruta, executable, timelimit, gap = util.config_env()
z_lp = 0;  z_milp = 0; z_milp2 = 0; z_hard = 0; t_harduvwdel=0; z_soft = 0; z_softcut = 0; z_lbc = 0
t_lp = 0;  t_milp = 0; t_milp2 = 0; t_hard = 0; t_harduvwdel=0; t_soft = 0; t_softcut = 0; t_lbc = 0;
nU_no_int = 0;  n_Uu_no_int = 0;  n_Uu_1_0 = 0;  k = 0; ns = 0

t_harduvw = 0; z_harduvw = 0;

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

## Si ya tenemos un resultado previo:
precargado, z_milp, z_hard, t_milp, t_hard = util.resultados_lp_milp(instancia,ambiente,gap,timelimit)


## --------------------------------- MILP ---------------------------------------------

## Solve as a MILP
if 1 == 1: # and precargado == False  
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,nameins=instancia[0:4])
    sol_milp = Solution(model=model, nameins=instancia[0:4], env=ambiente, executable=executable, gap=gap, timelimit=timelimit,
                        tee  = False, tofiles = True, exportLP = False, exportFile=True)
    z_milp = sol_milp.solve_problem()
    t_milp = time.time() - t_o
    print("t_milp = ", round(t_milp,1), "z_milp = ", round(z_milp,1))


## --------------------------------- MILP + Inequal ----------------------------------------

## Solve as a MILP with inequality
if 1 == 1: # and precargado == False  
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,option='Ineq',nameins=instancia[0:4])
    sol_milp2 = Solution(model=model, nameins=instancia[0:4], env=ambiente, executable=executable, gap=gap, timelimit=timelimit,
                         tee  = False, tofiles = False, exportLP = False, exportFile=False)
    z_milp2 = sol_milp2.solve_problem()
    t_milp2 = time.time() - t_o
    print("t_milp2 = ", round(t_milp2,1), "z_milp2 = ", round(z_milp2,1))


## --------------------------------- LINEAR RELAXATION -----------------------------------------

## Relax as LP and solve it
if 1 == 1:
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,option='relax',nameins=instancia[0:4])
    sol_lp   = Solution(model=model, env=ambiente, executable=executable, nameins=instancia[0:4], gap=gap, timelimit=timelimit,
                        tee  = False, tofiles = False, exportFile=False)
    z_lp = sol_lp.solve_problem() 
    t_lp = time.time() - t_o
    print("t_lp = ", round(t_lp,1), "z_lp = ", round(z_lp,1))
    
    
## --------------------------------- SELECTION VARIABLES TO FIX -----------------------------------------

    ## Seleccionamos las variables que serán fijadas, se requiere correr antes <linear relaxation>
    ## fixed_Uu     variables que Si serán fijadas a 1.
    ## No_fixed_Uu  variables que No serán fijadas.
    ## lower_Pmin   variables en que la potencia Pmin del generador fue menor a la mínima y No serán fijadas.
    fixed_Uu, No_fixed_Uu, lower_Pmin = sol_lp.select_fixed_variables_Uu()
    
    ## Variables delta a fijar.
    fixed_delta, No_fixed_delta = sol_lp.select_fixed_variables_delta()
        
    ## Variables "V" y "W" a fijar.
    fixed_V, No_fixed_V, fixed_W, No_fixed_W = sol_lp.select_fixed_variables_VW()
              
              
## --------------------------------- HARD-FIXING (only Uu) ---------------------------------------------

# HARD-FIXING solution and solve the sub-MILP.
if 1 == 1: # or precargado == False  
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,option='Hard',fixed_Uu=fixed_Uu,fixed_V=fixed_V,fixed_W=fixed_W,nameins=instancia[0:4])
    sol_hard = Solution(model=model, env=ambiente, executable=executable, nameins=instancia[0:4], gap=gap, timelimit=timelimit,
                        tee  = False, tofiles = False)
    z_hard = sol_hard.solve_problem()
    t_hard = time.time() - t_o + t_lp
    print("t_hard = ", round(t_hard,1), "z_hard = ", round(z_hard,1))
    
    
## --------------------------------- HARD-FIXING U,V,W---------------------------------------------

# HARD-FIXING solution and solve the sub-MILP.
if 1 == 1: # or precargado == False
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,option='harduvwdel',fixed_Uu=fixed_Uu,fixed_V=fixed_V,fixed_W=fixed_W,fixed_delta=[],nameins=instancia[0:4])
    sol_harduvw = Solution(model=model, env=ambiente, executable=executable, nameins=instancia[0:4], gap=gap, timelimit=timelimit,
                              tee  = False, tofiles = False)
    z_harduvw = sol_harduvw.solve_problem()
    t_harduvw = time.time() - t_o + t_lp
    print("t_hardUVW = ", round(t_harduvw,1), "z_hardUVW = ", round(z_harduvw,1))


## --------------------------------- HARD-FIXING U,V,W y delta---------------------------------------------

# HARD-FIXING solution and solve the sub-MILP.
if 1 == 1: # or precargado == False
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,option='harduvwdel',fixed_Uu=fixed_Uu,fixed_V=fixed_V,fixed_W=fixed_W,fixed_delta=fixed_delta,nameins=instancia[0:4])
    sol_harduvwdel = Solution(model=model, env=ambiente, executable=executable, nameins=instancia[0:4], gap=gap, timelimit=timelimit,
                              tee  = False, tofiles = False)
    z_harduvwdel = sol_harduvwdel.solve_problem()
    t_harduvwdel = time.time() - t_o + t_lp
    print("t_hardUVWdel = ", round(t_harduvwdel,1), "z_hardUVWdel = ", round(z_harduvwdel,1))


## --------------------------------- SOFT-FIXING ---------------------------------------------
        
## SOFT-FIXING solution and solve the sub-MILP. (Versión sin actualizar el cut-off)
if 1 == 0:
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,option='Soft',fixed_Uu=fixed_Uu,nameins=instancia[0:4])
    sol_soft = Solution(model=model, env=ambiente, executable=executable, nameins=instancia[0:4], gap=gap, timelimit=timelimit,
                        tee  = False, tofiles = False)
    z_soft = sol_soft.solve_problem() 
    t_soft = time.time() - t_o + t_lp
    print("t_soft = ", round(t_soft,1), "z_soft = ", round(z_soft,1))
    ## Imprimimos las posibles variables 'u' que podrían no sean enteras.
    nU_no_int, n_Uu_no_int , n_Uu_1_0 = sol_soft.count_U_no_int()
    

## --------------------------------- SOFT FIX + CUT-OFF --------------------------------------
        
## SOFT FIX + CUT-OFF solution and solve the sub-MILP (it is using cutoff = z_hard).
## Use 'Soft+pmin' if the lower subset of Uu-Pmin will be considered.
if 1 == 1:
    t_o = time.time() 
    model,xx    = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,option='Soft+pmin',fixed_Uu=fixed_Uu,nameins=instancia[0:4])
    sol_softcut = Solution(model=model, env=ambiente, executable=executable, nameins=instancia[0:4], gap=gap, cutoff=z_hard, timelimit=timelimit,
                            tee = False, tofiles = False)
    z_softcut = sol_softcut.solve_problem() 
    t_softcut = time.time() - t_o + t_hard ## t_hard (ya incluye el tiempo de lp)
    print("t_soft+cut = ", round(t_softcut,4), "z_soft+cut = ", round(z_softcut,1))
    ## Imprimimos las posibles variables 'u' que podrían no sean enteras.
    nU_no_int, n_Uu_no_int , n_Uu_1_0 = sol_softcut.count_U_no_int()

## --------------------------------- LOCAL BRANCHING CUTS ------------------------------------

## Include the LOCAL BRANCHING CUT to the solution and solve the sub-MILP (it is using cutoff=z_hard).
 # PENDIENTE
if 1 == 0:     
    t_o = time.time()   
    k   = len(lower_Pmin) # El valor de intentos de asignación está siendo usado para definir el parámetro k en el LBC. 
    model,ns = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,option='LBC+pmin',fixed_Uu=fixed_Uu,No_fixed_Uu=No_fixed_Uu,
                        k=k, lower_Pmin=lower_Pmin, nameins=instancia[0:4])
    sol_lbc  = Solution(model=model, env=ambiente, executable=executable, nameins=instancia[0:4], gap=gap, cutoff=z_hard, timelimit=timelimit,
                         tee = False, tofiles = False)
    z_lbc = sol_lbc.solve_problem() 
    t_lbc = time.time() - t_o + t_hard ## t_hard (ya incluye el tiempo de lp)
    print("t_lbc = ", round(t_lbc,1), "z_lbc = ", round(z_lbc,1),)
    # Imprimimos las posibles variables 'u' que podrían no sean enteras en la solución.
    nU_no_int, n_Uu_no_int , n_Uu_1_0 = sol_lbc.count_U_no_int()    
        
    # \todo{Verificar que las restricciones de arranque que usan delta en la formulación, se encontraron variables con valor None en la solución}
    
    # \todo{subir el gap de 0.001 a 0.0001 implica un esfuerzo computacional mucho mayor}
    # \todo{Calcular el tamaño del slack del subset Sbarra}
    # \todo{Reducir tiempo de búsqueda o iteraciones en el solver}
    # \todo{Cambiar valor de k en nuevas iteraciones con una búsqueda local (un LBC completo de A.Lodi)}
    # \todo{Hacer un VNS o un VND con movimientos definidos con las variables}
    # \todo{Un movimiento en la búsqueda local puede ser cambiar la asignación del costo de arranque en un periodo adelante o atras para algunos generadores} 
    # \todo{ Otro mivimiento puede ser fijar todas las variables relacionadas a un generador.}
            
    # \todo{EVALUAR SI NOS CONVIENE O NO INCLUIR LOS INTENTOS DE ASIGNACIÓN}}  
    # \todo{Podrian disminuirse el tamaño de las variables soft de 90% al 95%}
    
    # \todo{Podrian fijarse otras variables además de Uu como U,V,W o delta}
    # \todo{Podríamos usar reglas parecidas al paper de Todosijevic para fijar V,W a partir de Uu}
    # \todo{Podrian fijarse todas las variables (u,v,w y delta) relacionadas con los generadores que se escogen para ser fijados}
    # \todo{Aplicar corte. numero de 1´s de las variables de arranque 'V' en un horizonte deben ser igual al número de 1's en la variable delta}
    
    # \todo{Hacer un KS completo de Guastaroba}
    # \todo{Probar tamaños del n_kernel (!!! al parecer influye mucho en el tiempo de búsqueda)}  
    # \todo{Podrian intentarse un KS puro fijando todas las variables (u,v,w y delta) relacionadas con los generadores que se escogen para ser fijados}
    # \todo{Un KS relajando y fijando grupos de variables a manera de buckets}
    # \todo{Usar la solución factible hard como warm-start a otros métodos}  
      
    # \todo{Verificar por qué la instancia uc_52.json es infactible ???}
    # \todo{Revisar factibilidad de la solución}
    
    # \todo{Evaluar el efecto de la cota obtenida del hard-fix} FUNCIONA
    
## --------------------------------- KERNEL SEARCH WITH + HARD-CUT-OFF -------------------

## La versión básica de KS consiste en relajar la formulacion y a partir de ello sacar 
## las variables del kernel y de los buckets, después de manera iterativa se resulven los 
## SUB-MILP´S "restringidos" mas pequeños.
## KS solution and solve the sub-MILP (it is using cutoff = z_hard).
## Use 'Soft+pmin' (lower subset of Uu-Pmin)  as the first and unique bucket to consider
## Use relax the integrality variable Uu.
 
 # PENDIENTE
if 1 == 0:
    t_o = time.time() 
    model,xx    = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,option='KS',fixed_Uu=fixed_Uu,nameins=instancia[0:4])
    sol_ks = Solution(model=model, env=ambiente, executable=executable, nameins=instancia[0:4], gap=gap, cutoff=z_hard, timelimit=timelimit,
                           tee  = False, tofiles = False)
    z_ks = sol_ks.solve_problem() 
    t_ks = time.time() - t_o + t_hard ## t_hard (ya incluye el tiempo de lp)
    print("t_ks= ", round(t_ks,4), "z_ks = ", round(z_ks,1), "n_fixed_Uu = ", len(fixed_Uu))
    ## Imprimimos las posibles variables 'u' que podrían no sean enteras.
    nU_no_int, n_Uu_no_int , n_Uu_1_0 = sol_ks.count_U_no_int()
    

## --------------------------------- RESULTS -------------------------------------------

## Append a list as new line to an old csv file using as log, the first line of the file as shown.
## 'ambiente,localtime,instancia,T,G,gap,timelimit,z_lp,z_hard,z_harduvw,z_harduvwdel,z_milp,z_soft,z_soft+cut,z_lbc,t_lp,t_hard,t_harduvw,t_harduvwdel,t_milp,t_soft,t_soft+cut,t_lbc,gapabs_z_lbc-z_milp,n_fixU,nU_no_int,n_Uu_no_int,n_Uu_1_0,k,bin_sup,comment'
comment = 'hard-FIXING U,V,W,delta, Soft+pmin,LBC+pmin'
row = [ambiente,localtime,instancia,len(T),len(G),gap,timelimit,
       round(z_lp,1),round(z_hard,1),round(z_harduvw,1),round(z_harduvwdel,1),round(z_milp,1),round(z_milp2,1),round(z_soft,1),round(z_softcut,1),round(z_lbc,1),
       round(t_lp,1),round(t_hard,1),round(t_harduvw,1),round(t_harduvwdel,1),round(t_milp,1),round(t_milp2,1),round(t_soft,1),round(t_softcut,1),round(t_lbc,1),
       round(((z_milp-z_softcut)/z_milp)*100,4),len(fixed_Uu),nU_no_int,n_Uu_no_int,n_Uu_1_0,k,ns,comment]
util.append_list_as_row('stat.csv',row)