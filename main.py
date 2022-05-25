## --------------------------------------------------------------------------------
## File: main.py
## A math-heuristic to Tight and Compact Unit Commitment Problem 
## Developers: Uriel Iram Lezama Lope
## Purpose: Programa principal de un modelo de UC
## Description: Lee una instancia de UCP y la resuelve. 
## Para correr el programa usar el comando "python3 main.py anjos.json yalma"
## Desde script en linux test.sh "sh test.sh"
## --------------------------------------------------------------------------------
import pandas as pd
import time
import sys
import uc_Co
import util
import reading
from   solution import Solution
import matplotlib.pyplot as plt

#util.ETL_Coplex_Log('logfileMilp.log')

instancia = 'uc_52.json'       ## analizar infactibilidad
instancia = 'uc_02.json'       ## ejemplos dificiles 2,3,4     
instancia = 'uc_03.json'       ## ejemplos dificiles 2,3,4   
instancia = 'uc_54.json'               
instancia = 'uc_53.json'       ## ejemplo de 'delta' relajado diferente de uno  
instancia = 'anjos.json'       ## ejemplo de juguete
instancia = 'uc_45.json'       ## ejemplo de batalla  
instancia = 'uc_22.json'       ## ejemplo dificil  
instancia = 'uc_47.json'       ## ejemplo sencillo   
instancia = 'uc_06.json'       ## ejemplos regulares 5,6
instancia = 'archivox.json'    ## ejemplo sencillo

## Cargamos parámetros de configuración desde archivo <config>
ambiente, ruta, executable, timeheu, timemilp, gap = util.config_env()
z_lp=0; z_milp=0; z_milp2=0; z_hard=0; z_soft7=0; z_soft4=0; z_soft5=0; z_softp=0; z_lbc=0;
t_lp=0; t_milp=0; t_milp2=0; t_hard=0; t_soft7=0; t_soft4=0; t_soft5=0; t_softp=0; t_lbc=0;
g_lp=0; g_milp=0; g_milp2=0; g_hard=0; g_soft7=0; g_soft4=0; g_soft5=0; g_softp=0; g_lbc=0; 
k=0; ns=0; nU_no_int=0; n_Uu_no_int=0; n_Uu_1_0=0;
SB_Uu=[]

emph = 0 ## Emphasize balanced=0 (default); feasibility=1; optimality=2;

if ambiente == 'yalma':
    if len(sys.argv) != 3:
        print("!!! Something went wrong, try write something like: $python3 main.py uc_54.json yalma")
        print("archivo :", sys.argv[1])
        print("ambiente:", sys.argv[2])
        sys.exit()
    ambiente  = sys.argv[2]
    instancia = sys.argv[1]

localtime = time.asctime(time.localtime(time.time()))

print(localtime,'Solving --->',instancia)

## Lee instancia de archivo .json con formato de [Knueven2020]
G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,Pb,C,mpc,Cs,Tunder,names = reading.reading(ruta+instancia)

## Lista de Parámetros
## relax    =  True    if the integer solution is relaxed.
## fix      =  'Soft'  fixes the solution in a soft fashion (dominio flotante ente 0 y 1); 
##          ...'Hard'  fixes the solution in a hard fashion (enteras fijadas a 1); (something like relax and fix);
##          ...'LBC'   using Local Branching Constraint.
##          ...'relax' relax the problem as LP and solve it
## tee      =  True si se quiere ver el log del solver.
## lpmethod =  0 : 0=Automatic; 1,2= Primal and dual simplex; 3=Sifting; 4=Barrier, 5=Concurrent 

## Si ya tenemos un resultado previo: 
#precargado, z_milp, z_hard, t_milp, t_hard = util.resultados_lp_milp(instancia,ambiente,gap,timelimit)


## --------------------------------- LINEAR RELAXATION -----------------------------------------

## Relax as LP and solve it
if 1 == 1:
    t_o = time.time() 
    model,xy = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tunder,option='relax',nameins=instancia[0:5])
    sol_lp   = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,timelimit=timeheu,
                          tee=False,tofiles=False,emphasize=emph,exportLP=False,option='relax')
    z_lp,g_lp = sol_lp.solve_problem() 
    t_lp      = time.time() - t_o
    print("t_lp= ",round(t_lp,1),"z_lp= ",round(z_lp,1))
    
    
## --------------------------------- SELECTION VARIABLES TO FIX -----------------------------------------

    ## Seleccionamos las variables que serán fijadas, se requiere correr antes <linear relaxation>
    ## SB_Uu       variables que SI serán fijadas a 1. (Soporte binario)
    ## No_SB_Uu    variables que NO serán fijadas.
    ## lower_Pmin_Uu  variables en que el producto Pmin*Uu  fue menor a la potencia mínima del generador Pmin y No serán fijadas.
    SB_Uu, No_SB_Uu, lower_Pmin_Uu = sol_lp.select_binary_support_Uu('LR')


## --------------------------------- HARD-FIXING (only Uu) ---------------------------------------------

## HARD-FIXING (only Uu) solution and solve the sub-MILP. (Require run the LP)
if 1 == 1: 
    t_o = time.time() 
    timehard = timeheu / 3
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tunder,option='Hard',SB_Uu=SB_Uu,nameins=instancia[0:5])
    sol_hard = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,timelimit=timehard,
                        tee=False,emphasize=emph,tofiles=False,option='Hard')
    z_hard,g_hard  = sol_hard.solve_problem()
    t_hard         = time.time() - t_o + t_lp
    print("t_hard= ",round(t_hard,1),"z_hard= ",round(z_hard,1),"g_hard= ",round(g_hard,5) )
    
    ## Almacenamos la solución de Uu.
    ## ES MUY IMPORTANTE GUARDAR LAS VARIABLES 'Uu=0' (No_SB_Uu2) Y 'Uu=1'(SB_Uu2) DE LA PRIMERA SOLUCIÓN FACTIBLE 'Hard'.
    ## Este es el primer - Soporte Binario Factible -
    SB_Uu2, No_SB_Uu2, xx = sol_hard.select_binary_support_Uu('NotLR')    
    lower_Pmin_Uu2 = sol_hard.update_lower_Pmin_Uu(lower_Pmin_Uu,'Hard')
    sol_hard.cuenta_ceros_a_unos(SB_Uu, No_SB_Uu, lower_Pmin_Uu,'Hard')
    

## --------------------------------- SOFT4-FIXING (only Uu) + CUT ---------------------------------------------

## SOFT4-FIXING (only Uu) solution and solve the sub-MILP.
## Se aplica la restricción de n_subset=90% al Soporte Binario (Titulares)
if 1 == 1:
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tunder,option='Soft4',SB_Uu=SB_Uu2,No_SB_Uu=No_SB_Uu2,lower_Pmin_Uu=lower_Pmin_Uu2,nameins=instancia[0:5])
    sol_soft4 = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,cutoff=z_hard,timelimit=timeheu,
                        tee=False,emphasize=emph,tofiles=False,option='Soft4')
    z_soft4,g_soft4 = sol_soft4.solve_problem()
    t_soft4         = time.time() - t_o + t_hard ## t_hard ya incluye el tiempo de lp
    print("t_soft4= ",round(t_soft4,1),"z_soft4= ",round(z_soft4,1),"g_soft4= ",round(g_soft4,5) )
    
    lower_Pmin_Uu0  = sol_soft4.update_lower_Pmin_Uu(lower_Pmin_Uu2,'Soft4')
    sol_soft4.cuenta_ceros_a_unos(SB_Uu2, No_SB_Uu2, lower_Pmin_Uu2,'Soft4')
    

## ----------------------------------- PURE SOFT-FIXING (only Uu) ----------------------------------------------

## SOFTP-FIXING (only Uu) solution and solve the sub-MILP without cut-off and Binary support calculated by Hard-Fix
## Sin cut-off del HF
if 1 == 1:
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tunder,option='Softp',SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,lower_Pmin_Uu=lower_Pmin_Uu,nameins=instancia[0:5])
    sol_softp = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,timelimit=timeheu,
                        tee=False,emphasize=emph,tofiles=False,option='Softp')
    z_softp,g_softp = sol_softp.solve_problem()
    t_softp         = time.time() - t_o + t_lp
    print("t_softp= ",round(t_softp,1),"z_softp= ",round(z_softp,1),"g_softp= ",round(g_softp,5))    
    lower_Pmin_Uu0  = sol_softp.update_lower_Pmin_Uu(lower_Pmin_Uu2,'Softp')
    sol_softp.cuenta_ceros_a_unos(SB_Uu2, No_SB_Uu2,lower_Pmin_Uu2,'Softp')
     

## --------------------------------- SOFT7-FIXING (only Uu) ---------------------------------------------

## SOFT7-FIXING (only Uu) solution and solve the sub-MILP.
## Se aplica la restricción de n_subset=90% al Soporte Binario obtenido por el Hard Fixing
## Sin cut-off del HF
if 1 == 1:
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tunder,option='Soft7',SB_Uu=SB_Uu2,No_SB_Uu=No_SB_Uu2,lower_Pmin_Uu=lower_Pmin_Uu2,nameins=instancia[0:5])
    sol_soft7 = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,timelimit=timeheu,
                        tee=False,emphasize=emph,tofiles=False,option='Soft7')
    z_soft7,g_soft7 = sol_soft7.solve_problem()
    t_soft7         = time.time() - t_o + t_hard ## t_hard ya incluye el tiempo de lp
    print("t_soft7= ",round(t_soft7,1),"z_soft7= ",round(z_soft4,1),"g_soft7= ",round(g_soft7,5) )
    
    lower_Pmin_Uu0  = sol_soft7.update_lower_Pmin_Uu(lower_Pmin_Uu,'Soft7')
    sol_soft7.cuenta_ceros_a_unos(SB_Uu, No_SB_Uu, lower_Pmin_Uu,'Soft7')
    

## ---------------------------------------------- MILP ----------------------------------------------------------

## Solve as a MILP
if 1 == 1: 
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tunder,option=None,nameins=instancia[0:5])
    sol_milp = Solution(model=model,nameins=instancia[0:5],env=ambiente,executable=executable,gap=gap,timelimit=timemilp,
                          tee=False,tofiles=False,emphasize=emph,exportLP=False,option='Milp')
    z_milp,g_milp = sol_milp.solve_problem()
    t_milp        = time.time() - t_o
    print("t_milp= ",round(t_milp,1),"z_milp= ",round(z_milp,1),"g_milp= ",round(g_milp,5))#,"total_costo_arr=",model.total_cSU.value
        
    
## ---------------------------------------- MILP2 with Inequality ------------------------------------------------

## Solve the MILP2 with valid inequality 
if 1 == 0: 
    t_o = time.time() 
    model,xx  = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tunder,option='Milp2',nameins=instancia[0:5])
    sol_milp2 = Solution(model=model,nameins=instancia[0:5],env=ambiente,executable=executable,gap=gap,timelimit=timemilp,
                           tee=False,tofiles=False,emphasize=emph,exportLP=False,option='Milp2')
    z_milp2,g_milp2 = sol_milp2.solve_problem()
    t_milp2         = time.time() - t_o
    print("t_milp2= ",round(t_milp2,1),"z_milp2= ",round(z_milp2,1),"g_milp2= ",round(g_milp2,5)) #"total_costo_arr=",model.total_cSU.value


## --------------------------------------- CALCULATE MARGINAL COST Uu ------------------------------------
## Fix values of binary variables to get dual variables and solve it again
if 1 == 0: 
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tunder,option=None,nameins=instancia[0:5])
    sol_milp = Solution(model=model,nameins=instancia[0:5],env=ambiente,executable=executable,gap=gap,timelimit=timemilp,
                          tee=False,tofiles=False,emphasize=emph,exportLP=False,option='AllFixed')
    z_milp,g_milp = sol_milp.solve_problem()
    t_milp        = time.time() - t_o
    print("t_milp= ",round(t_milp,1),"z_milp= ",round(z_milp,1),"g_milp= ",round(g_milp,5))#,"total_costo_arr=",model.total_cSU.value
    

## --------------------------------------- LOCAL BRANCHING CUTS ------------------------------------------

## Include the LOCAL BRANCHING CUT to the solution and solve the sub-MILP (it is using cutoff=z_hard).
# PENDIENTE ...
if 1 == 0:     
    t_o = time.time()   
    k   = len(lower_Pmin_Uu) # El valor de intentos de asignación está siendo usado para definir el parámetro k en el LBC. 
    model,ns = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tunder,option='LBC+pmin',SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,
                        k=k,lower_Pmin_Uu=lower_Pmin_Uu,nameins=instancia[0:5])
    sol_lbc  = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,cutoff=z_hard,timelimit=timeheu,
                          tee=False,emphasize=emph,tofiles=False,option='LBC+pmin')
    z_lbc = sol_lbc.solve_problem() 
    t_lbc = time.time() - t_o + t_hard ## t_hard (ya incluye el tiempo de lp    
    sol_lbc.cuenta_ceros_a_unos(SB_Uu, No_SB_Uu, lower_Pmin_Uu,'Soft+pmin+cut')
    
    ## PENDIENTES
    # \todo{Fijar la solución entera y probar factibilidad} 
    # \todo{Preparar las instancias del WEM de México} 
    # \todo{Verificar por qué la instancia uc_52.json es infactible}
    # \todo{Verificar que las restricciones de arranque que usan delta en la formulación, se encontraron variables con valor None en la solución}

    ## PRUEBAS                    
    # \Probar con diferentes calidadades de primera solución factible,(podríamos usar Pure Variable-fixing)
    # \Considerar no usar nada de Hard, ni cut-off, ni Soporte Binario.
    # \todo{Probar cambiar el valor de k en nuevas iteraciones con una búsqueda local (un LBC completo de A.Lodi)}        
    # \todo{Probar modificar el tamaño de las variables soft-fix de 90% al 95%}
    # \todo{Probar el efecto de la cota obtenida del hard-fix}
    # \todo{Probar experimentalmente que fijar otras variables enteras además de Uu no impacta mucho}       
    # \todo{probar que SI conviene incluir los intentos de asignación en las variables soft-fix }
    # \todo{Encontrar la primer solución factible del CPLEX}
    # \todo{Usar la solución factible hard como warm-start a otros métodos} 
    # \todo{Probar configuración feasibility vs optimality en el Solver )} 

    ## IDEAS    
    # \todo{Un KS relajando y fijando grupos de variables a manera de buckets}
    # \todo{Hacer un VNS o un VND con movimientos definidos con las variables}
    # \todo{Un movimiento en la búsqueda local puede ser cambiar la asignación del costo de arranque en un periodo adelante o atras para algunos generadores} 
    # \todo{Podríamos usar reglas parecidas al paper de Todosijevic para fijar V,W a partir de Uu}
    # \todo{Podrian fijarse todas las variables (u,v,w y delta) relacionadas con los generadores que se escogen para ser fijados}

    ## DESCARTES  
    # \todo{Calcular el tamaño del slack del subset Sbarra -Soporte binario-}
    # \todo{Probar tamaños del n_kernel (!!! al parecer influye mucho en el tiempo de búsqueda)} 
    
    ## TERMINADAS
    # \todo{Revisar la desigualdad válida. El numero de 1´s de las variables de arranque 'V' en un horizonte deben ser igual al número de 1's en la variable delta}
    # \todo{Comparar soluciones entre si en variables u,v,w y delta}
    
## --------------------------------- KERNEL SEARCH WITH + HARD-CUT-OFF -------------------
# \todo{Hacer un mix de KS de Guastarobacon LB de A.Lodi}
## La versión básica de KS consiste en relajar la formulacion y a partir de ello sacar 
## las variables del kernel y de los buckets, después de manera iterativa se resulven los 
## SUB-MILP´S "restringidos" mas pequeños.
## KS solution and solve the sub-MILP (it is using cutoff = z_hard).
## Use 'Soft+pmin' (lower subset of Uu-Pmin)  as the first and unique bucket to consider
## Use relax the integrality variable Uu.

 
 # PENDIENTE... 
if 1 == 0:
    t_o = time.time() 
    model,xx    = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tunder,option='KS',SB_Uu=SB_Uu,nameins=instancia[0:5])
    sol_ks = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,cutoff=z_hard,timelimit=timeheu,
                        tee=False,emphasize=emph,tofiles=False)
    z_ks = sol_ks.solve_problem() 
    t_ks = time.time() - t_o + t_hard ## t_hard (ya incluye el tiempo de lp)
    print("t_ks= ", round(t_ks,4), "z_ks= ", round(z_ks,1), "n_SB_Uu= ", len(SB_Uu))


## --------------------------------- RESULTS -------------------------------------------

## Append a list as new line to an old csv file using as log, the first line of the file as shown.
## 'ambiente,localtime,instancia,T,G,gap,emphasize,timelimit,z_lp,z_hard,z_milp,z_milp2,z_soft,z_softpmin,z_softcut,z_softcut2,z_softcut3,z_lbc,
#                                                       t_lp,t_hard,t_milp,t_milp2,t_soft,t_softpmin,t_softcut,t_softcut2,t_softcut3,t_lbc,
#                                                       n_fixU,nU_no_int,n_Uu_no_int,n_Uu_1_0,k,bin_sup,comment'
comment = 'Validacion de Soft0, Soft4 y Soft5. Se incorpora Soft-pure'
row = [ambiente,localtime,instancia,len(T),len(G),gap,emph,timeheu,timemilp,
    round(z_lp,1),round(z_hard,1),round(z_milp,1),round(z_milp2,1),round(z_soft7,1),round(z_soft4,1),round(z_soft5,1),round(z_softp,1),round(z_lbc,1),
    round(t_lp,1),round(t_hard,1),round(t_milp,1),round(t_milp2,1),round(t_soft7,1),round(t_soft4,1),round(t_soft5,1),round(t_softp,1),round(t_lbc,1),
                  round(g_hard,5),round(g_milp,5),round(g_milp2,5),round(g_soft7,5),round(g_soft4,5),round(g_soft5,5),round(g_softp,5),round(g_lbc,5),
                  k,ns,comment] #round(((z_milp-z_milp2)/z_milp)*100,6)
util.append_list_as_row('stat.csv',row)


## --------------------------------- ADICIONALES -------------------------------------------

    ## Compare two solutions 
    #sol_milp.compare(sol_milp2)
    # sol_milp2.send_to_File(letra="a")
            
    
## --------------------------------- SOFT0-FIXING (only Uu) + CUT --------------------------------------------

## SOFT0-FIXING (only Uu) solution and solve the sub-MILP.
## Sin ninguna restricción de del 90%.
# if 1 == 0:
#     t_o = time.time() 
#     model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tunder,option='Soft0',SB_Uu=SB_Uu2,No_SB_Uu=No_SB_Uu2,lower_Pmin_Uu=lower_Pmin_Uu2,nameins=instancia[0:5])
#     sol_soft0 = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,cutoff=z_hard,timelimit=timeheu,
#                         tee=False,emphasize=emph,tofiles=False,option='Soft0')
#     z_soft0,g_soft0 = sol_soft0.solve_problem()
#     t_soft0         = time.time() - t_o + t_hard ## t_hard ya incluye el tiempo de lp
#     print("t_soft0= ",round(t_soft0,1),"z_soft0= ",round(z_soft0,1),"g_soft0= ",round(g_soft0,5) )
    
#     lower_Pmin_Uu0  = sol_soft0.update_lower_Pmin_Uu(lower_Pmin_Uu2,'Soft0')
#     sol_soft0.cuenta_ceros_a_unos(SB_Uu2, No_SB_Uu2, lower_Pmin_Uu2,'Soft0')


## --------------------------------- SOFT5-FIXING (only Uu) + CUT ---------------------------------------------

## SOFT5-FIXING (only Uu) solution and solve the sub-MILP.
## Se aplica la restricción de n_subset=90% al Soporte Binario (Titulares) y a Candidatos (la banca) identificados en LR
# if 1 == 0: 
#     t_o = time.time() 
#     model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tunder,option='Soft5',SB_Uu=SB_Uu2,No_SB_Uu=No_SB_Uu2,lower_Pmin_Uu=lower_Pmin_Uu2,nameins=instancia[0:5])
#     sol_soft5 = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,cutoff=z_hard,timelimit=timeheu,
#                         tee=False,emphasize=emph,tofiles=False,option='Soft5')
#     z_soft5,g_soft5 = sol_soft5.solve_problem()
#     t_soft5         = time.time() - t_o + t_hard ## t_hard ya incluye el tiempo de lp
#     print("t_soft5= ",round(t_soft5,1),"z_soft5= ",round(z_soft5,1),"g_soft5= ",round(g_soft5,5) )
    
#     lower_Pmin_Uu0  = sol_soft5.update_lower_Pmin_Uu(lower_Pmin_Uu2,'Soft5')
#     sol_soft5.cuenta_ceros_a_unos(SB_Uu2, No_SB_Uu2, lower_Pmin_Uu2,'Soft5')
    
#     bb3,vari = Extract().extract('logfile'+'Soft5'+instancia[0:5]+'.log',t_hard=t_hard)

