## -------------------  >)|°> UriSoft© <°|(<  -------------------
## File: main.py
## A math-heuristic to Tight and Compact Unit Commitment Problem 
## Developers: Uriel Iram Lezama Lope
## Purpose: Programa principal de un modelo de UC
## Description: Lee una instancia de UCP y la resuelve. 
## Para correr el programa usar el comando 'python3 main.py anjos.json yalma'
## Desde script en linux test.sh 'sh test.sh'
## <º)))>< ¸.·´¯`·.´¯`·.¸¸.·´¯`·.¸¸.·´¯`·.´¯`·.¸¸.·´¯`·.¸ ><(((º>
import gc
import time
import sys
import uc_Co
import util
import reading
import time
import numpy as np
from   math     import floor
from   solution import Solution
from   copy import deepcopy 

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

instancia = 'uc_02.json'        ## ejemplos dificiles 2,3,4   
instancia = 'mem_01.json'       ## MEM (PENDIENTE)
instancia = 'anjos.json'        ## ejemplo de juguete
instancia = 'morales_ejemplo_III_D.json'  ## 
#instancia = 'dirdat_18.json'   ## analizar infactibilidad 
#instancia = 'dirdat_21.json'   ## analizar infactibilidad 
#instancia = 'dirdat_26.json'   ## analizar infactibilidad 
#instancia = 'dirdat_2.json'    ## analizar infactibilidad
#instancia = 'output.json'      ##     

instancia = 'uc_97.json'       ## 
instancia = 'uc_01.json'       ##

instancia = 'uc_47.json'       ## ejemplo sencillo  
instancia = 'uc_70.json'       ## 

instancia = 'uc_58.json'       ## prueba demostrativa excelente en mi PC 

## Cargamos parámetros de configuración desde archivo <config>
## Emphasize balanced=0 (default); feasibility=1; optimality=2;
## symmetry automatic=-1; symmetry low level=1
ambiente, ruta, executable, timeheu, timemilp, emph, symmetry, gap, k, iterstop = util.config_env()
x = 1e+75
z_lp=x; z_milp=x; z_hard=x; z_hard3=x; z_ks=x; z_lbc1=x; z_lbc2=x; z_lbc3=x; z_check=x; z_lbc0=x; z_=0;
t_lp=0; t_milp=0; t_hard=0; t_hard3=0; t_ks=0; t_lbc1=0; t_lbc2=0; t_lbc3=0; t_check=0; t_lbc0=0; t_=0;
g_lp=x; g_milp=x; g_hard=x; g_hard3=x; g_ks=x; g_lbc1=x; g_lbc2=x; g_lbc3=x; g_check=x; g_lbc0=x; g_=x;
ns=0; nU_no_int=0; n_Uu_no_int=0; n_Uu_1_0=0;
SB_Uu=[];  No_SB_Uu=[];  lower_Pmin_Uu=[];  Vv=[];  Ww=[];  delta=[];
SB_Uu3=[]; No_SB_Uu3=[]; lower_Pmin_Uu3=[]; Vv3=[]; Ww3=[]; delta3=[];
comment = 'Here it writes a message to the stat.csv results file' 

if ambiente == 'yalma':
    if len(sys.argv) != 3:
        print('!!! Something went wrong, try write something like: $python3 main.py uc_54.json yalma')
        print('archivo :', sys.argv[1])
        print('ambiente:', sys.argv[2])
        sys.exit()
    instancia = sys.argv[1]
    ambiente  = sys.argv[2]

localtime = time.asctime(time.localtime(time.time()))

print(localtime,'Solving ---> ---> ---> ---> --->',instancia)

## Lee instancia de archivo .json con formato de [Knueven2020]
G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,Pb,Cb,C,mpc,Cs,Tunder,names = reading.reading(ruta+instancia)


## --------------------------------------- LINEAR RELAXATION ---------------------------------------------
## Relax as LP and solve it

if True:
    t_o        = time.time() 
    model,xy   = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='relax',nameins=instancia[0:5],mode='Tight')
    sol_lp     = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,timelimit=timeheu,
                           tee=False,tofiles=False,emphasize=emph,exportLP=False,option='relax')
    z_lp, g_lp = sol_lp.solve_problem() 
    t_lp       = time.time() - t_o
    print('t_lp= ',round(t_lp,1),'z_lp= ',round(z_lp,1))


## ------------------------------------ SELECTION VARIABLES TO FIX ---------------------------------------

    ## Seleccionamos las variables que serán fijadas. Es requisito correr antes <linear relaxation>
    ## SB_Uu         variables que SI serán fijadas a 1. (Soporte binario)
    ## No_SB_Uu      variables que NO serán fijadas.
    ## lower_Pmin_Uu variables en las que el producto de Pmin*Uu de [Harjunkoski2021] fue menor a la potencia mínima del generador Pmin y NO serán fijadas.
    ## lower_Pmin_Uu  >>> Éste valor podría ser usado para definir el parámetro k en el LBC o buckets en un KS <<<  
    SB_Uu, No_SB_Uu, lower_Pmin_Uu, Vv, Ww, delta = sol_lp.select_binary_support_Uu('LR')
    del sol_lp
    gc.collect()

## ----------------------------------- HARD-FIXING 3 (only Uu) ---------------------------------------------
## HARD-FIXING 3 (only Uu) solution and solve the sub-MILP. (Require run the LP)

if True: 
    t_o       = time.time()
    lbheur    = 'no'
    model,xx  = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='Hard3',
                        SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,lower_Pmin_Uu=lower_Pmin_Uu,nameins=instancia[0:5],mode='Tight')
    sol_hard3 = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],gap=gap,timelimit=timeheu,
                        tee=False,emphasize=emph,lbheur=lbheur,symmetry=symmetry,tofiles=False,option='Hard3')
    z_hard3, g_hard3 = sol_hard3.solve_problem()
    g_hard3  = sol_hard3.igap(z_lp,z_milp)
    t_hard3  = time.time() - t_o + t_lp
    
    ## ES MUY IMPORTANTE GUARDAR LAS VARIABLES 'Uu=1'(SB_Uu3) DE LA PRIMERA SOLUCIÓN FACTIBLE 'Hard3'.
    ## ASI COMO LAS VARIABLES 'Uu=0' (No_SB_Uu3) 
    ## Este es el primer - Soporte Binario Entero Factible-
    SB_Uu3, No_SB_Uu3, xx, Vv3, Ww3, delta3 = sol_hard3.select_binary_support_Uu('Hard3')    
    lower_Pmin_Uu3 = sol_hard3.update_lower_Pmin_Uu(lower_Pmin_Uu,'Hard3')
    #sol_hard3.cuenta_ceros_a_unos( SB_Uu, No_SB_Uu, lower_Pmin_Uu,'Hard3')    

    print('t_hard3= ',round(t_hard3,1),'z_hard3= ',round(z_hard3,1),'g_hard3= ',round(g_hard3,5) )
    del sol_hard3
    gc.collect()
    ## NO OLVIDES COMENTAR TUS PRUEBAS ¸.·´¯`·.´¯`·.¸¸.·´¯`·.¸><(((º>
comment    = 'Integrality GAP'

k_original = k


## --------------------------------------- LOCAL BRANCHING 1 ------------------------------------------
## LBC COUNTINOUS VERSION without soft-fixing
## Include the LOCAL BRANCHING CUT to the solution and solve the sub-MILP (it is using cutoff=z_hard).

if True:    
    Vv             = deepcopy(Vv3)
    Ww             = deepcopy(Ww3)
    delta          = deepcopy(delta3)
    SB_Uu          = deepcopy(SB_Uu3)
    No_SB_Uu       = deepcopy(No_SB_Uu3)
    lower_Pmin_Uu  = deepcopy(lower_Pmin_Uu3)
    t_o            = time.time() 
    t_net          = timemilp - t_hard3
    t_res          = timemilp - t_hard3
    cutoff         = z_hard3
    incumbent      = z_hard3
    z_old          = z_hard3
    improve        = True    
    timeover       = False
    iter           = 1
    saved          = [SB_Uu,No_SB_Uu,Vv,Ww,delta]
    rightbranches  = []
    char           = ''
    fish           = ')'
    letter         = ['','_a','_b','_c','_d','_e','_f','_g','_h','_i','_j','_k','_l','_m','_n','_o','_p','_q','_r','_s','_t','_u','_v','_w','_x','_y','_z']
    result_iter    = []
    result_iter.append((t_hard3,z_hard3))
    print('\t')
        
    while True:
        if (iter==iterstop) or (time.time() - t_o >= t_net):
            break
        lbheur   = 'no'
        char     = ''
        
        if improve == False:
            cutoff=1e+75
                 
        timeheu1  = min(t_res,timeheu)
        model, xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='lbc1',
                            SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,lower_Pmin_Uu=lower_Pmin_Uu,V=Vv,W=Ww,delta=delta,
                            percent_soft=90,k=k,nameins=instancia[0:5],mode='Tight',improve=improve,timeover=timeover,rightbranches=rightbranches)
        sol_lbc1  = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],letter=letter[iter],gap=gap,cutoff=cutoff,timelimit=timeheu1,
                            tee=False,emphasize=emph,lbheur=lbheur,symmetry=symmetry,tofiles=False,option='lbc1')
        z_lbc1,g_lbc1 = sol_lbc1.solve_problem()
        
        #sol_lbc1.cuenta_ceros_a_unos(SB_Uu, No_SB_Uu, lower_Pmin_Uu,'lbc1') ## Compara contra la última solución
        
        gap_iter = abs((z_lbc1 - z_old) / z_old) * 100 ## Percentage
        improve = False
        if z_lbc1 < incumbent :                        ## Update solution
            incumbent  = z_lbc1
            cutoff     = z_lbc1
            # saved      = [SB_Uu,No_SB_Uu,Vv,Ww,delta]
            char       = '***'
            g_lbc1     = sol_lbc1.igap(z_lp,z_lbc1)
            if gap_iter > gap:
                improve = True

        result_iter.append((round(time.time() - t_o + t_hard3,1),z_lbc1))
        z_old = z_lbc1 ## Guardamos la z de la solución anterior
          
        print('<°|'+fish+'>< iter:'+str(iter)+' t_lbc1= ',round(time.time()-t_o+t_hard3,1),'z_lbc1= ',round(z_lbc1,1),char ) #,'g_lbc1= ',round(g_lbc1,5)
        print('\t')       
        fish = fish + ')'  
        
        ## Aqui se prepara la nueva iteracion ...  
        timeover == False       
        if improve == False:   
            if sol_lbc1.timeover == True or sol_lbc1.nosoluti == True or sol_lbc1.infeasib == True:                     
                if sol_lbc1.timeover == True:   
                    print('k=[k/2] Time limit reach without improve: shrinking the neighborhood  ...  >(°> . o O')
                else:
                    print('k=[k/2] No solution/infeasible: shrinking the neighborhood  ...  >(°> . o O')
                k = floor(k/2)  
                timeover == True         
            else:              
                print('Going out from a local optimum  ...  >>+*+*+*+*+*+|°>')
                SB_Uu, No_SB_Uu, xx, Vv, Ww, delta = sol_lbc1.select_binary_support_Uu('lbc1')  
                lower_Pmin_Uu = sol_lbc1.update_lower_Pmin_Uu(lower_Pmin_Uu,'lbc1') 
                rightbranches.append([SB_Uu,No_SB_Uu,lower_Pmin_Uu])
                fish = ')'
        else: ## Mejora la solución
            SB_Uu, No_SB_Uu, xx, Vv, Ww, delta = sol_lbc1.select_binary_support_Uu('lbc1')  
            lower_Pmin_Uu = sol_lbc1.update_lower_Pmin_Uu(lower_Pmin_Uu,'lbc1')
            saved         = [SB_Uu,No_SB_Uu,Vv,Ww,delta] ## Update solution
            
                    
        t_res = t_net - time.time() + t_o 
        print('lbc1','tiempo restante:',t_res)
        
        del sol_lbc1
        gc.collect()
        iter  = iter + 1
         
    t_lbc1 = time.time() - t_o + t_hard3  ## t_hard3 ya incluye el tiempo de LP
    z_lbc1 = incumbent    
    for item in result_iter:
        print(item[0],',',item[1])    
    result_iter = np.array(result_iter)
    np.savetxt('iterLBC1'+instancia[0:5]+'.csv', result_iter, delimiter=',')
        
k = k_original
    
## ---------------------------------------------- CHECK FEASIBILITY (LBC1)----------------------------------------------------------

if  True: 
    print('Revisando factibilidad de la solucion con z_lbc1=', z_lbc1 )
    t_o       = time.time() 
    model,xx  = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='Check',
                        SB_Uu=saved[0],No_SB_Uu=saved[1],V=saved[2],W=saved[3],delta=saved[4],nameins=instancia[0:5],mode='Tight')
    sol_check = Solution(model=model,nameins=instancia[0:5],env=ambiente,executable=executable,gap=gap,timelimit=timemilp,
                         tee=False,tofiles=False,emphasize=emph,symmetry=symmetry,exportLP=False,option='Check')
    z_check, g_check = sol_check.solve_problem()
    t_check          = time.time() - t_o
    print('t_check= ',round(t_check,1),'z_check= ',round(z_check,4),'g_check= ',round(g_check,4))
    del sol_check
    gc.collect()
        
## --------------------------------------- LOCAL BRANCHING 2 ------------------------------------------
## LBC COUNTINOUS VERSION without soft-fixing
## Include the LOCAL BRANCHING CUT to the solution and solve the sub-MILP (it is using cutoff=z_hard).

if  True:    
    Vv             = deepcopy(Vv3)
    Ww             = deepcopy(Ww3)
    delta          = deepcopy(delta3)
    SB_Uu          = deepcopy(SB_Uu3)
    No_SB_Uu       = deepcopy(No_SB_Uu3)
    lower_Pmin_Uu  = deepcopy(lower_Pmin_Uu3)
    t_o            = time.time() 
    t_net          = timemilp - t_hard3
    t_res          = timemilp - t_hard3
    cutoff         = z_hard3
    incumbent      = z_hard3
    z_old          = z_hard3
    improve        = True    
    timeover       = False
    iter           = 1
    saved          = [SB_Uu,No_SB_Uu,Vv,Ww,delta]
    rightbranches  = []
    char           = ''
    fish           = ')'
    letter         = ['','_a','_b','_c','_d','_e','_f','_g','_h','_i','_j','_k','_l','_m','_n','_o','_p','_q','_r','_s','_t','_u','_v','_w','_x','_y','_z']
    result_iter    = []
    result_iter.append((t_hard3,z_hard3))
    print('\t')
        
    while True:
        if (iter==iterstop) or (time.time()-t_o >= t_net):
            break
        lbheur   = 'no'
        char     = ''
        
        if improve == False:
            cutoff=1e+75
        
        timeheu1  = min(t_res,timeheu)      
        model, xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='lbc2',
                            SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,lower_Pmin_Uu=lower_Pmin_Uu,V=Vv,W=Ww,delta=delta,
                            percent_soft=90,k=k,nameins=instancia[0:5],mode='Tight',improve=improve,timeover=timeover,rightbranches=rightbranches)
        sol_lbc2  = Solution(model=model,env=ambiente,executable=executable,nameins=instancia[0:5],letter=letter[iter],gap=gap,cutoff=cutoff,timelimit=timeheu1,
                            tee=False,emphasize=emph,lbheur=lbheur,symmetry=symmetry,tofiles=False,option='lbc2')
        z_lbc2,g_lbc2 = sol_lbc2.solve_problem()
        
        #sol_lbc2.cuenta_ceros_a_unos(SB_Uu, No_SB_Uu, lower_Pmin_Uu,'lbc2') ## Compara contra la última solución
        
        gap_iter = abs((z_lbc2 - z_old)/z_old) * 100 ## Percentage
        improve = False
        if z_lbc2 < incumbent :                      ## Update solution
            incumbent  = z_lbc2
            cutoff     = z_lbc2
            #saved      = [SB_Uu,No_SB_Uu,Vv,Ww,delta]
            char       = '***'
            g_lbc2     = sol_lbc2.igap(z_lp,z_lbc2)
            if gap_iter > gap:
                improve = True
            
        result_iter.append((round(time.time()-t_o+t_hard3,1),z_lbc2))
        z_old = z_lbc2 ## Guardamos la solución anterior
          
        print('<°|'+fish+'>< iter:'+str(iter)+' t_lbc2= ',round(time.time()-t_o+t_hard3,1),'z_lbc2= ',round(z_lbc2,1),char ) #,'g_lbc2= ',round(g_lbc2,5)
        print('\t')       
        fish = fish + ')'  
        
        ## Aquí se prepara la nueva iteracion ...  
        timeover == False       
        if improve == False:   
            if sol_lbc2.timeover == True or sol_lbc2.nosoluti == True or sol_lbc2.infeasib == True:                     
                if sol_lbc2.timeover == True:   
                    print('k=[k/2] Time limit reach without improve: shrinking the neighborhood  ...  >(°> . o O')
                else:
                    print('k=[k/2] No solution/infeasible: shrinking the neighborhood  ...  >(°> . o O')
                k = floor(k/2)  
                timeover == True         
            else:              
                print('Going out from a local optimum    ...    >>+*+*+*+*+*+|°>')
                SB_Uu, No_SB_Uu, xx, Vv, Ww, delta = sol_lbc2.select_binary_support_Uu('lbc2')  
                lower_Pmin_Uu = sol_lbc2.update_lower_Pmin_Uu(lower_Pmin_Uu,'lbc2') 
                rightbranches.append([SB_Uu,No_SB_Uu,lower_Pmin_Uu])
                fish = ')'
        else: ## Mejora la solución
            SB_Uu, No_SB_Uu, xx, Vv, Ww, delta = sol_lbc2.select_binary_support_Uu('lbc2')  
            lower_Pmin_Uu = sol_lbc2.update_lower_Pmin_Uu(lower_Pmin_Uu,'lbc2') 
            saved         = [SB_Uu,No_SB_Uu,Vv,Ww,delta] ## Update solution

        t_res = t_net - time.time() + t_o 
        print('lbc2 ','tiempo restante:',t_res)
        
        del sol_lbc2
        gc.collect()
        iter = iter + 1

    t_lbc2 = time.time() - t_o + t_hard3  ## t_hard3 ya incluye el tiempo de LP
    z_lbc2 = incumbent    
    for item in result_iter:
        print(item[0],',',item[1])    
    result_iter = np.array(result_iter)
    np.savetxt('iterLBC2'+instancia[0:5]+'.csv', result_iter, delimiter=',')
    

## ---------------------------------------------- CHECK FEASIBILITY (LBC2)----------------------------------------------------------

if  True: 
    print('Revisando factibilidad de la solucion con z_lbc2=', z_lbc2 )
    t_o       = time.time() 
    model,xx  = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='Check',
                        SB_Uu=saved[0],No_SB_Uu=saved[1],V=saved[2],W=saved[3],delta=saved[4],nameins=instancia[0:5],mode='Tight')
    sol_check = Solution(model=model,nameins=instancia[0:5],env=ambiente,executable=executable,gap=gap,timelimit=timemilp,
                         tee=False,tofiles=False,emphasize=emph,symmetry=symmetry,exportLP=False,option='Check')
    z_check,g_check = sol_check.solve_problem()
    t_check         = time.time() - t_o
    print('t_check= ',round(t_check,1),'z_check= ',round(z_check,4),'g_check= ',round(g_check,4))
    
             
## ---------------------------------------------- MILP ----------------------------------------------------------
## Solve as a MILP

if  False: 
    symmetrydefault = -1 
    cutoff   = 1e+75 
    lbheur   = 'no'      
    t_o      = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='Milp',nameins=instancia[0:5],mode='Tight')
    sol_milp = Solution(model=model,nameins=instancia[0:5],env=ambiente,executable=executable,gap=gap,cutoff=cutoff,symmetry=symmetrydefault,timelimit=timemilp,
                          tee=False,tofiles=False,emphasize=emph,lbheur=lbheur,exportLP=False,option='Milp')
    z_milp, g_milp = sol_milp.solve_problem()
    t_milp         = time.time() - t_o
    print('t_milp= ',round(t_milp,1),'z_milp= ',round(z_milp,1),'g_milp= ',round(g_milp,5))


## ( EN DESARROLLO ... )

## --------------------------------- KERNEL SEARCH WITH + HARD-CUT-OFF -------------------
# \todo{Hacer un mix de KS de Guastaroba con LB de A.Lodi}
## La versión básica de KS consiste en relajar la formulacion y a partir de ello sacar 
## las variables del kernel y de los buckets, después de manera iterativa se resulven los 
## SUB-MILP´S 'restringidos' mas pequeños.
## KS solution and solve the sub-MILP (it is using cutoff = z_hard).
## Use 'Soft+pmin' (lower subset of Uu-Pmin)  as the first and unique bucket to consider
## Use relax the integrality variable Uu.

## --------------------------------------- CALCULATE REDUCED COST Uu ------------------------------------
## Fix values of binary variables to get rc variables and solve it again
## https://pascua.iit.comillas.edu/aramos/openSDUC.py

if  False:
    Vv             = deepcopy(Vv3)
    Ww             = deepcopy(Ww3)
    delta          = deepcopy(delta3)
    SB_Uu          = deepcopy(SB_Uu3)
    No_SB_Uu       = deepcopy(No_SB_Uu3)
    lower_Pmin_Uu  = deepcopy(lower_Pmin_Uu3)
    saved          = [SB_Uu,No_SB_Uu,Vv,Ww,delta]
    t_o      = time.time() 
    model,xx = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,mpc,Pb,Cb,C,Cs,Tunder,names,option='RC',
                        SB_Uu=saved[0],No_SB_Uu=saved[1],V=saved[2],W=saved[3],delta=saved[4],nameins=instancia[0:5],mode='Tight')
    sol_rc = Solution(model=model,nameins=instancia[0:5],env=ambiente,executable=executable,gap=gap,timelimit=timemilp,
                         tee=False,tofiles=False,emphasize=emph,symmetry=symmetry,exportLP=False,option='RC')
    z_rc,g_rc = sol_rc.solve_problem()
    t_rc         = time.time() - t_o
    
    sol_rc.cuenta_ceros_a_unos(SB_Uu, No_SB_Uu, lower_Pmin_Uu,'RC') ## Compara contra la última solución
    SB_Uu, No_SB_Uu, xx, Vv, Ww, delta = sol_rc.select_binary_support_Uu('lbc2')  
    lower_Pmin_Uu = sol_rc.update_lower_Pmin_Uu(lower_Pmin_Uu,'RC') 

    ## Ordenaremos los costos reducidos para elegir los candidatos de los buckets
    rc = []
    i  = 0
    for c in No_SB_Uu: 
        rc.append(( i , model.rc[model.u[c[0],c[1]]],c[0],c[1] ))
        i = i + 1
        
    rc.sort(key=lambda tup: tup[1], reverse=False)
    print(rc)    

    print('t_rc= ',round(t_rc,1),'z_rc= ',round(z_rc,4),'g_rc= ',round(g_rc,4))


    ## PENDIENTES
    # \todo{Incluir datos hidro de instancias en México} 
    # \todo{Incluir restricciones de generadores hidro}  
    # \todo{Verificar por qué la instancia mem_01.json es infactible}
    
    ## PRUEBAS                    
    # \todo{Probar experimentalmente que fijar otras variables enteras además de Uu no impacta mucho}         
    # \todo{Probar modificar el tamaño de las variables soft-fix de 90% al 95%}
    # \todo{Probar configuración enfasis feasibility vs optimality en el Solver )} 

    ## IDEAS    
    # \todo{probar que SI conviene incluir los intentos de asignación en las variables soft-fix }
    # \todo{Un KS relajando y fijando grupos de variables a manera de buckets}
    # \todo{Un movimiento en la búsqueda local puede ser cambiar la asignación del costo de arranque en un periodo adelante o atras para algunos generadores} 
    # \todo{Podríamos usar reglas parecidas al paper de Todosijevic para fijar V,W a partir de Uu}
    # \todo{Podrian fijarse todas las variables (u,v,w y delta) relacionadas con los generadores que se escogen para ser fijados}
    # \todo{Hacer un VNS o un VND con movimientos definidos con las variables}

    ## DESCARTES  
    # \todo{Calcular el tamaño del slack del subset Sbarra -Soporte binario-}
    # \todo{Probar tamaños del n_kernel (!!! al parecer influye mucho en el tiempo de búsqueda)} 
    # \todo{Agregar must-run} 
    # \todo{Encontrar la primer solución factible del CPLEX}
    
    
    ## TERMINADAS
    # \todo{Considerar no usar nada de Hard, ni cut-off, ni Soporte Binario.}
    # \todo{Probar cambiar el valor de k en nuevas iteraciones con una búsqueda local (un LBC completo de A.Lodi)}    
    # \todo{Usar la solución factible hard como warm-start} 
    # \todo{Probar el efecto de la cota obtenida del hard-fix} 
    # \todo{Probar con diferentes calidades de primera solución factible,(podríamos usar Pure Variable-fixing)}
    # \todo{Revisar la desigualdad válida. El numero de 1´s de las variables de arranque 'V' en un horizonte deben ser igual al número de 1's en la variable delta}
    # \todo{Comparar soluciones entre si en variables u,v,w y delta}
    # \todo{Verificar que las restricciones de arranque que usan delta en la formulación, se encontraron variables con valor None en la solución}
    # \todo{Fijar la solución entera y probar factibilidad} 
    # \todo{Crear instancias sintéticas a partir de morales-españa2013} 
    
    

## --------------------------------- RESULTS -------------------------------------------
## Append a list as new line to an old csv file using as log, the first line of the file as shown.
## 'ambiente,localtime,instancia,T,G,gap,emphasize,timelimit,z_lp,z_hard,z_milp,z_milp2,z_soft,z_softpmin,z_softcut,z_softcut2,z_softcut3,z_lbc,
#                                                       t_lp,t_hard,t_milp,t_milp2,t_soft,t_softpmin,t_softcut,t_softcut2,t_softcut3,t_lbc,
#                                                       n_fixU,nU_no_int,n_Uu_no_int,n_Uu_1_0,k,bin_sup,comment'


row = [ambiente,localtime,instancia,len(T),len(G),gap,emph,timeheu,timemilp,
    round(z_lp,1),round(z_milp,1),round(z_hard,1),round(z_hard3,1),round(z_lbc1,1),round(z_lbc2,1),round(z_lbc3,1),round(z_,1),round(z_,1),
    round(t_lp,1),round(t_milp,1),round(t_hard,1),round(t_hard3,1),round(t_lbc1,1),round(t_lbc2,1),round(t_lbc3,1),round(t_,1),round(t_,1),
                  round(g_milp,8),round(g_hard,8),round(g_hard3,8),round(g_lbc1,8),round(g_lbc2,8),round(g_lbc3,8),round(g_,8),round(g_,8),
                  k,ns,comment] #round(((z_milp-z_milp2)/z_milp)*100,6)
util.append_list_as_row('stat.csv',row)

print(localtime,'terminé instancia ...´¯`·...·´¯`·.. ><(((º> ',instancia)

exit()

