## --------------------------------------------------------------------------------
## File: main.py
## A math-heuristic to Tight and Compact Unit Commitment Problem 
## Developers: Uriel Iram Lezama Lope
## Purpose: Programa principal de un modelo de UC
## Description: Lee una instancia de UCP y la resuelve. 
## Para correr el programa usar el comando "python3 main.py anjos.json yalma"
## Desde script en linux test.sh "sh test.sh"
## --------------------------------------------------------------------------------
from pickle import TRUE
import pandas as pd
import time
import sys
import uc_Co
import util
import reading
from   solution import Solution
import time

#util.ETL_Coplex_Log('logfileMilp.log')

instancia = 'uc_03.json'       ## ejemplos dificiles 2,3,4  
instancia = 'uc_06.json'       ## ejemplos regulares 5,6 
instancia = 'uc_21.json'       ## ejemplos dificiles 2,3,4 
instancia = 'uc_22.json'       ## ejemplo dificil  

instancia = 'uc_42.json'       ## ejemplo dificil 
instancia = 'uc_44.json'       ## ejemplo dificil 
#instancia = 'uc_50.json'       ## ejemplo sencillo       [1 abajo,milp factible]   
#instancia = 'uc_51.json'       ## ejemplo sencillo  
#instancia = 'uc_53.json'       ## ejemplo de 'delta' relajado diferente de uno  
#instancia = 'uc_54.json'       ## ejemplo sencillo  
#instancia = 'uc_55.json'       ## ejemplo sencillo  
#instancia = 'uc_56.json'       ## ejemplo sencillo 
#instancia = 'uc_46.json'       ## ejemplo sencillo       [49 abajo,MILP infactible]

instancia = 'anjos.json'        ## ejemplo de juguete
instancia = 'morales_ejemplo_III_D.json'  ## 
#instancia = 'dirdat_18.json'   ## analizar infactibilidad 
#instancia = 'dirdat_21.json'   ## analizar infactibilidad 
#instancia = 'dirdat_26.json'   ## analizar infactibilidad 
#instancia = 'dirdat_2.json'    ## analizar infactibilidad
#instancia = 'output.json'      ## 
instancia = 'uc_47.json'        ## ejemplo sencillo      

instancia = 'mem_01.json'       ## MEM (PENDIENTE)

instancia = 'uc_02.json'        ## ejemplos dificiles 2,3,4   

instancia = 'uc_49.json'        ## ejemplo sencillo        [1 abajo,milp factible]  De_0=3317.97

instancia = 'uc_60.json'       ## 

## Cargamos parámetros de configuración desde archivo <config>
ambiente, ruta, executable, timeheu, timemilp, gap, k, iterpar = util.config_env()

z_lp=0; z_milp=0; z_hard=0; z_hard2=0; z_ks=0; z_lbc8=0; z_lbc1=0; z_=0; z_lbc0=0;
t_lp=0; t_milp=0; t_hard=0; t_hard2=0; t_ks=0; t_lbc8=0; t_lbc1=0; t_=0; t_lbc0=0;
g_lp=0; g_milp=0; g_hard=0; g_hard2=0; g_ks=0; g_lbc8=0; g_lbc1=0; g_=0; g_lbc0=0; 
ns=0; nU_no_int=0; n_Uu_no_int=0; n_Uu_1_0=0;
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

print(localtime,'  Solving ---> ---> --->',instancia)

## Lee instancia de archivo .json con formato de [Knueven2020]
G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,Pb,Cb,C,mpc,Cs,Tunder,names = reading.reading(ruta+instancia)

## Lista de Parámetros 
## fix      =  'Soft'  fixes the solution in a soft fashion (dominio flotante ente 0 y 1); 
##          ...'Hard'  fixes the solution in a hard fashion (enteras fijadas a 1); (something like relax and fix);
##          ...'LBC'   using Local Branching Constraint.
##          ...'relax' relax the problem as LP and solve it
## tee      =  True si se quiere ver el log del solver.
## ...por completar/actualizar...

## --------------------------------------- LINEAR RELAXATION ---------------------------------------------
## Relax as LP and solve it
if False:
    t_o = time.time() 
    model,xy = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='relax',nameins=instancia[0:5],mode="Tight")
    sol_lp   = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,timelimit=timeheu,
                        tee=False,tofiles=False,emphasize=emph,exportLP=False,option='relax')
    z_lp,g_lp = sol_lp.solve_problem() 
    t_lp      = time.time() - t_o
    print("t_lp= ",round(t_lp,1),"z_lp= ",round(z_lp,1))
    
    
## ------------------------------------ SELECTION VARIABLES TO FIX ---------------------------------------
    ## Seleccionamos las variables que serán fijadas, se requiere correr antes <linear relaxation>
    ## SB_Uu         variables que SI serán fijadas a 1. (Soporte binario)
    ## No_SB_Uu      variables que NO serán fijadas.
    ## lower_Pmin_Uu variables en que el producto Pmin*Uu de [Harjunkoski2021] fue menor a la potencia mínima del generador Pmin y NO serán fijadas.
    ## lower_Pmin_Uu  >>> Éste valor podría ser usado para definir el parámetro k en el LBC o en un KS <<<  
    SB_Uu, No_SB_Uu, lower_Pmin_Uu = sol_lp.select_binary_support_Uu('LR')


## ----------------------------------- HARD-FIXING (only Uu) ---------------------------------------------
## HARD-FIXING (only Uu) solution and solve the sub-MILP. (Require run the LP)
if False: 
    t_o = time.time()
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='Hard',SB_Uu=SB_Uu,lower_Pmin_Uu=lower_Pmin_Uu,nameins=instancia[0:5],mode="Tight")
    sol_hard = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,timelimit=timeheu,
                        tee=False,emphasize=emph,tofiles=False,option='Hard')
    z_hard,g_hard  = sol_hard.solve_problem()
    t_hard         = time.time() - t_o + t_lp
    print("t_hard= ",round(t_hard,1),"z_hard= ",round(z_hard,1),"g_hard= ",round(g_hard,5) )
    
    ## ES MUY IMPORTANTE GUARDAR LAS VARIABLES 'Uu=1'(SB_Uu2) DE LA PRIMERA SOLUCIÓN FACTIBLE 'Hard'.
    ## ASI COMO LAS 'Uu=0' (No_SB_Uu2) 
    ## Este es el primer - Soporte Binario Factible Entero-
    SB_Uu2, No_SB_Uu2, xx = sol_hard.select_binary_support_Uu('')    
    lower_Pmin_Uu2 = sol_hard.update_lower_Pmin_Uu(lower_Pmin_Uu,'Hard')
    sol_hard.cuenta_ceros_a_unos(SB_Uu, No_SB_Uu, lower_Pmin_Uu,'Hard')
        

## --------------------------------------- LOCAL BRANCHING 0 ------------------------------------------
## Include the LOCAL BRANCHING CUT to the solution and solve the sub-MILP (it is using cutoff=z_hard).
## UnitInterval 'Uu'
## The first iteration of LB 
if False:
    SB_Uu3 = SB_Uu2.copy()
    No_SB_Uu3 = No_SB_Uu2.copy()
    lower_Pmin_Uu3 = lower_Pmin_Uu2.copy()   
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='lbc0',SB_Uu=SB_Uu3,No_SB_Uu=No_SB_Uu3,lower_Pmin_Uu=lower_Pmin_Uu3,nameins=instancia[0:5],mode="Tight")
    sol_lbc0 = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,cutoff=z_hard,timelimit=timeheu,
                        tee=False,emphasize=emph,tofiles=False,option='lbc0')
    z_lbc0,g_lbc0 = sol_lbc0.solve_problem()
    t_lbc0         = time.time() - t_o + t_hard ## t_hard ya incluye el tiempo de lp
    print("t_lbc0= ",round(t_lbc0,1),"z_lbc0= ",round(z_lbc0,1),"g_lbc0= ",round(g_lbc0,5) )
    
    sol_lbc0.update_lower_Pmin_Uu(lower_Pmin_Uu2,'lbc0')
    sol_lbc0.cuenta_ceros_a_unos(SB_Uu2, No_SB_Uu2, lower_Pmin_Uu2,'lbc0')

      
## --------------------------------------- LOCAL BRANCHING 1 ------------------------------------------
## LBC COUNTINOUS VERSION without soft-fixing
## Include the LOCAL BRANCHING CUT to the solution and solve the sub-MILP (it is using cutoff=z_hard).
if False:
    SB_Uu3 = SB_Uu2.copy()
    No_SB_Uu3 = No_SB_Uu2.copy()
    lower_Pmin_Uu3 = lower_Pmin_Uu2.copy()
    t_o = time.time() 
    t_max = timemilp
    iter  = 0
    flag  = 1
    result_iter = []
    cutoff=z_hard
    while 1==1:
        if flag == 0:
            cutoff=1e+75
        model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='lbc1',SB_Uu=SB_Uu3,No_SB_Uu=No_SB_Uu3,lower_Pmin_Uu=lower_Pmin_Uu3,k=k,nameins=instancia[0:5],mode="Tight",flag=flag)
        sol_lbc1 = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,cutoff=cutoff,timelimit=timeheu,
                            tee=False,emphasize=emph,tofiles=False,option='lbc1')
        z_lbc1,g_lbc1 = sol_lbc1.solve_problem()
        cutoff = z_lbc1        
        flag = sol_lbc1.cuenta_ceros_a_unos(SB_Uu3, No_SB_Uu3, lower_Pmin_Uu3,'lbc1')
        
        SB_Uu3, No_SB_Uu3, xx = sol_lbc1.select_binary_support_Uu('')    
        lower_Pmin_Uu3 = sol_lbc1.update_lower_Pmin_Uu(lower_Pmin_Uu3,'lbc1')
        iter = iter + 1
        result_iter.append((round(time.time()-t_o+ t_hard,1),z_lbc1)) 
        print("iter:"+str(iter)+" t_lbc1= ",round(time.time()-t_o+t_hard,1),"z_lbc1= ",round(z_lbc1,1),"g_lbc1= ",round(g_lbc1,5) )
        if (iter==iterpar) or (time.time()-t_o+t_hard>=t_max):
            break
        
    t_lbc1 = time.time() - t_o + t_hard ## t_hard ya incluye el tiempo de LP
    for item in result_iter:
        print(item[0],',',item[1])
      
## --------------------------------------- LOCAL BRANCHING 2 ------------------------------------------
## LBC INTEGER VERSION OF Uu without soft-fixing
## Include the LOCAL BRANCHING CUT to the solution and solve the sub-MILP (it is using cutoff=z_hard).
if False:
    SB_Uu3 = SB_Uu2.copy()
    No_SB_Uu3 = No_SB_Uu2.copy()
    lower_Pmin_Uu3 = lower_Pmin_Uu2.copy()
    for iter in range(10):
        t_o = time.time() 
        model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='lbc2',SB_Uu=SB_Uu3,No_SB_Uu=No_SB_Uu3,lower_Pmin_Uu=lower_Pmin_Uu3,nameins=instancia[0:5],mode="Tight")
        sol_lbc2 = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,cutoff=z_hard,timelimit=timeheu,
                            tee=False,emphasize=emph,tofiles=False,option='lbc2')
        z_lbc2,g_lbc2 = sol_lbc2.solve_problem()
        t_lbc2         = time.time() - t_o + t_hard ## t_hard ya incluye el tiempo de lp
        print("iter:"+str(iter)+" t_lbc2= ",round(t_lbc2,1),"z_lbc2= ",round(z_lbc2,1),"g_lbc2= ",round(g_lbc2,5) )
        
        sol_lbc2.cuenta_ceros_a_unos(SB_Uu3, No_SB_Uu3, lower_Pmin_Uu3,'lbc2')
        SB_Uu3, No_SB_Uu3, xx = sol_hard.select_binary_support_Uu('')    
        lower_Pmin_Uu3 = sol_lbc2.update_lower_Pmin_Uu(lower_Pmin_Uu3,'lbc2')
        
                    
## --------------------------------------- LOCAL BRANCHING 8 ------------------------------------------
## Include the LOCAL BRANCHING CUT to the solution and solve the sub-MILP (it is using cutoff=z_hard).
## Binary 'Uu'
if False:
    SB_Uu3 = SB_Uu2.copy()
    No_SB_Uu3 = No_SB_Uu2.copy()
    lower_Pmin_Uu3 = lower_Pmin_Uu2.copy()   
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='lbc8',SB_Uu=SB_Uu3,No_SB_Uu=No_SB_Uu3,lower_Pmin_Uu=lower_Pmin_Uu3,nameins=instancia[0:5],mode="Tight")
    sol_lbc8 = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,cutoff=z_hard,timelimit=timeheu,
                        tee=False,emphasize=emph,tofiles=False,option='lbc8')
    z_lbc8,g_lbc8 = sol_lbc8.solve_problem()
    t_lbc8         = time.time() - t_o + t_hard ## t_hard ya incluye el tiempo de lp
    print("t_lbc8= ",round(t_lbc8,1),"z_lbc8= ",round(z_lbc8,1),"g_lbc8= ",round(g_lbc8,5) )
    
    sol_lbc8.update_lower_Pmin_Uu(lower_Pmin_Uu2,'lbc8')
    sol_lbc8.cuenta_ceros_a_unos(SB_Uu2, No_SB_Uu2, lower_Pmin_Uu2,'lbc8')

## ---------------------------------------------- MILP ----------------------------------------------------------
## Solve as a MILP
if True: 
    t_o = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option=None,nameins=instancia[0:5],mode="Tight")
    sol_milp = Solution(model=model,nameins=instancia[0:5],env=ambiente,executable=executable,gap=gap,timelimit=timemilp,
                          tee=False,tofiles=False,emphasize=emph,exportLP=False,option='Milp')
    z_milp,g_milp = sol_milp.solve_problem()
    t_milp        = time.time() - t_o
    print("t_milp= ",round(t_milp,1),"z_milp= ",round(z_milp,1),"g_milp= ",round(g_milp,5))#,"total_costo_arr=",model.total_cSU.value


## --------------------------------------- CALCULATE MARGINAL COST Uu ------------------------------------
## Fix values of binary variables to get dual variables and solve it again
## https://pascua.iit.comillas.edu/aramos/openSDUC.py

# PENDIENTE... DESPUES ORDENAREMOS POR COSTO MARGINAL DE U PARA ELEGIR CANDIDATOS DE LOS BUCKETS
if False: 
    t_o = time.time() 
    t_max = timemilp
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option=None,nameins=instancia[0:5],mode="Tight")
    sol_milp = Solution(model=model,nameins=instancia[0:5],env=ambiente,executable=executable,gap=gap,timelimit=timemilp,
                          tee=False,tofiles=False,emphasize=emph,exportLP=False,option='AllFixed')
    z_milp,g_milp = sol_milp.solve_problem()
    t_milp        = time.time() - t_o
    print("t_milp= ",round(t_milp,1),"z_milp= ",round(z_milp,1),"g_milp= ",round(g_milp,5))#,"total_costo_arr=",model.total_cSU.value
    

    ## PENDIENTES
    # \todo{Agregar must-run} 
    # \todo{Incluir datos hidro de instancias en México} 
    # \todo{Incluir restricciones de generadores hidro} 
    # \todo{Crear instancias sintéticas a partir de morales-españa2013} 
    
    ## PRUEBAS                    
    # \todo{Probar con diferentes calidades de primera solución factible,(podríamos usar Pure Variable-fixing)}
    # \todo{Probar el efecto de la cota obtenida del hard-fix} 
    # \todo{Encontrar la primer solución factible del CPLEX}
    # \todo{Probar experimentalmente que fijar otras variables enteras además de Uu no impacta mucho}      
    # \todo{Considerar no usar nada de Hard, ni cut-off, ni Soporte Binario.}
    # \todo{Probar cambiar el valor de k en nuevas iteraciones con una búsqueda local (un LBC completo de A.Lodi)}        
    # \todo{Probar modificar el tamaño de las variables soft-fix de 90% al 95%}
    # \todo{probar que SI conviene incluir los intentos de asignación en las variables soft-fix }
    # \todo{Probar configuración feasibility vs optimality en el Solver )} 
    # \todo{Usar la solución factible hard como warm-start a otros métodos} 

    ## IDEAS    
    # \todo{Un KS relajando y fijando grupos de variables a manera de buckets}
    # \todo{Modificar el emphasis en el solver}
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
    # \todo{Verificar por qué la instancia uc_52.json es infactible}
    # \todo{Verificar que las restricciones de arranque que usan delta en la formulación, se encontraron variables con valor None en la solución}
    # \todo{Fijar la solución entera y probar factibilidad} 
    
## --------------------------------- KERNEL SEARCH WITH + HARD-CUT-OFF -------------------
# \todo{Hacer un mix de KS de Guastaroba con LB de A.Lodi}
## La versión básica de KS consiste en relajar la formulacion y a partir de ello sacar 
## las variables del kernel y de los buckets, después de manera iterativa se resulven los 
## SUB-MILP´S "restringidos" mas pequeños.
## KS solution and solve the sub-MILP (it is using cutoff = z_hard).
## Use 'Soft+pmin' (lower subset of Uu-Pmin)  as the first and unique bucket to consider
## Use relax the integrality variable Uu.

 # KS (EN DESARROLLO)
if False:
    SB_Uu3 = SB_Uu2.copy()                 # ESTE SERÁ EL KERNEL
    No_SB_Uu3 = No_SB_Uu2.copy()
    lower_Pmin_Uu3 = lower_Pmin_Uu2.copy() # ESTE LO DIVIDIREMOS EN BUCKETS
    t_o = time.time()    
    iter  = 0
    flag  = 1
    result_iter = []
    cutoff=z_hard
    while 1==1:
        model,xx    = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='KS',SB_Uu=SB_Uu,nameins=instancia[0:5],mode="Tight")
        sol_ks = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,cutoff=cutoff,timelimit=timeheu,
                            tee=False,emphasize=emph,tofiles=False)
        z_ks,g_ks= sol_ks.solve_problem()    
        cutoff = z_ks
        result_iter.append((round(time.time()-t_o,1),z_ks)) 
        print("iter:"+str(iter)+" t_ks= ",round(time.time()-t_o+t_hard,1),"z_ks= ",round(z_ks,1),"g_ks= ",round(g_ks,5) )
        
        flag = sol_ks.cuenta_ceros_a_unos(SB_Uu3, No_SB_Uu3, lower_Pmin_Uu3,'ks')
        SB_Uu3, No_SB_Uu3, xx = sol_lbc1.select_binary_support_Uu('')    
        
    t_ks = time.time() - t_o + t_hard ## t_hard (ya incluye el tiempo de LP)
    print("t_ks= ", round(t_ks,4), "z_ks= ", round(z_ks,1), "n_SB_Uu= ", len(SB_Uu))


## --------------------------------- RESULTS -------------------------------------------
## Append a list as new line to an old csv file using as log, the first line of the file as shown.
## 'ambiente,localtime,instancia,T,G,gap,emphasize,timelimit,z_lp,z_hard,z_milp,z_milp2,z_soft,z_softpmin,z_softcut,z_softcut2,z_softcut3,z_lbc,
#                                                       t_lp,t_hard,t_milp,t_milp2,t_soft,t_softpmin,t_softcut,t_softcut2,t_softcut3,t_lbc,
#                                                       n_fixU,nU_no_int,n_Uu_no_int,n_Uu_1_0,k,bin_sup,comment'
comment = '(Incluimos costo de apagado) Validacion de lbc1[0,1] y lbc2[Binary], buscando el óptimo entre SB y B.'
row = [ambiente,localtime,instancia,len(T),len(G),gap,emph,timeheu,timemilp,
    round(z_lp,1),round(z_milp,1),round(z_hard,1),round(z_,1),round(z_,1),round(z_lbc8,1),round(z_lbc1,1),round(z_,1),round(z_lbc0,1),
    round(t_lp,1),round(t_milp,1),round(t_hard,1),round(t_,1),round(t_,1),round(t_lbc8,1),round(t_lbc1,1),round(t_,1),round(t_lbc0,1),
                  round(g_milp,8),round(g_hard,8),round(g_,8),round(g_,8),round(g_lbc8,8),round(g_lbc1,8),round(g_,8),round(g_lbc0,8),
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
#     model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='Soft0',SB_Uu=SB_Uu2,No_SB_Uu=No_SB_Uu2,lower_Pmin_Uu=lower_Pmin_Uu2,nameins=instancia[0:5],mode="Tight")
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
#     model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='Soft5',SB_Uu=SB_Uu2,No_SB_Uu=No_SB_Uu2,lower_Pmin_Uu=lower_Pmin_Uu2,nameins=instancia[0:5],mode="Tight")
#     sol_soft5 = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,cutoff=z_hard,timelimit=timeheu,
#                         tee=False,emphasize=emph,tofiles=False,option='Soft5')
#     z_soft5,g_soft5 = sol_soft5.solve_problem()
#     t_soft5         = time.time() - t_o + t_hard ## t_hard ya incluye el tiempo de lp
#     print("t_soft5= ",round(t_soft5,1),"z_soft5= ",round(z_soft5,1),"g_soft5= ",round(g_soft5,5) )
    
#     lower_Pmin_Uu0  = sol_soft5.update_lower_Pmin_Uu(lower_Pmin_Uu2,'Soft5')
#     sol_soft5.cuenta_ceros_a_unos(SB_Uu2, No_SB_Uu2, lower_Pmin_Uu2,'Soft5')
    
#     bb3,vari = Extract().extract('logfile'+'Soft5'+instancia[0:5]+'.log',t_hard=t_hard)

    
## ---------------------------------------- MILP2 with Inequality ------------------------------------------------
## Solve the MILP2 with valid inequality 
# if 1 == 0: 
#     t_o = time.time() 
#     model,xx  = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='Milp2',nameins=instancia[0:5],mode="Tight")
#     sol_milp2 = Solution(model=model,nameins=instancia[0:5],env=ambiente,executable=executable,gap=gap,timelimit=timemilp,
#                            tee=False,tofiles=False,emphasize=emph,exportLP=False,option='Milp2')
#     z_milp2,g_milp2 = sol_milp2.solve_problem()
#     t_milp2         = time.time() - t_o
#     print("t_milp2= ",round(t_milp2,1),"z_milp2= ",round(z_milp2,1),"g_milp2= ",round(g_milp2,5)) #"total_costo_arr=",model.total_cSU.value



## ---------------------------------- PURE SOFT-FIXING (only Uu) -----------------------------------------
## SOFTP-FIXING (only Uu) solution and solve the sub-MILP without cut-off and Binary support calculated by Hard-Fix
## Sin cut-off del HF
## Usa el LR->BS y LR->B 
# if 1 == 0:
#     t_o = time.time() 
#     model,xx  = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='Softp',SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,lower_Pmin_Uu=lower_Pmin_Uu,nameins=instancia[0:5],mode="Tight")
#     sol_softp = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,timelimit=timeheu,
#                         tee=False,emphasize=emph,tofiles=False,option='Softp')
#     z_softp,g_softp = sol_softp.solve_problem()
#     t_softp         = time.time() - t_o + t_lp
#     print("t_softp= ",round(t_softp,1),"z_softp= ",round(z_softp,1),"g_softp= ",round(g_softp,5))    
#     #sol_softp.update_lower_Pmin_Uu(lower_Pmin_Uu2,'Softp')
#     sol_softp.cuenta_ceros_a_unos(SB_Uu2, No_SB_Uu2,lower_Pmin_Uu2,'Softp')


## ------------------------------- SOFT4-FIXING (only Uu) + CUT ------------------------------------------
## SOFT4-FIXING (only Uu) solution and solve the sub-MILP.
## Se aplica la restricción de n_subset=90% al Soporte Binario (Titulares)
# if 1 == 0:
#     t_o = time.time() 
#     model,xx  = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='Soft4',SB_Uu=SB_Uu2,No_SB_Uu=No_SB_Uu2,lower_Pmin_Uu=lower_Pmin_Uu2,nameins=instancia[0:5],mode="Tight")
#     sol_soft4 = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,cutoff=z_hard,timelimit=timeheu,
#                         tee=False,emphasize=emph,tofiles=False,option='Soft4')
#     z_soft4,g_soft4 = sol_soft4.solve_problem()
#     t_soft4         = time.time() - t_o + t_hard ## t_hard ya incluye el tiempo de lp
#     print("t_soft4= ",round(t_soft4,1),"z_soft4= ",round(z_soft4,1),"g_soft4= ",round(g_soft4,5) )
    
#     #sol_soft4.update_lower_Pmin_Uu(lower_Pmin_Uu2,'Soft4')
#     sol_soft4.cuenta_ceros_a_unos(SB_Uu2, No_SB_Uu2, lower_Pmin_Uu2,'Soft4')

    
## -------------------------------- SOFT7-FIXING (only Uu) ---------------------------------------------
## SOFT7-FIXING (only Uu) solution and solve the sub-MILP.
## Se aplica la restricción de n_subset=90% al Soporte Binario obtenido por el Hard Fixing
## Sin cut-off del HF
# if 1 == 0:
#     t_o = time.time() 
#     model,xx  = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='Soft7',SB_Uu=SB_Uu2,No_SB_Uu=No_SB_Uu2,lower_Pmin_Uu=lower_Pmin_Uu2,nameins=instancia[0:5],mode="Tight")
#     sol_soft7 = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,timelimit=timeheu,
#                         tee=False,emphasize=emph,tofiles=False,option='Soft7')
#     z_soft7,g_soft7 = sol_soft7.solve_problem()
#     t_soft7         = time.time() - t_o + t_hard ## t_hard ya incluye el tiempo de lp
#     print("t_soft7= ",round(t_soft7,1),"z_soft7= ",round(z_soft7,1),"g_soft7= ",round(g_soft7,5) )
    
#     #sol_soft7.update_lower_Pmin_Uu(lower_Pmin_Uu,'Soft7')
#     sol_soft7.cuenta_ceros_a_unos(SB_Uu, No_SB_Uu, lower_Pmin_Uu,'Soft7')

