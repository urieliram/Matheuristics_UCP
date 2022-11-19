## -------------------  >)|°> UriSoft© <°|(<  -------------------
## File: main.py
## A math-heuristic to Tight and Compact Unit Commitment Problem 
## Developers: Uriel Iram Lezama Lope
## Purpose: Programa principal de un modelo de UC
## Description: Lee una instancia de UCP y la resuelve. 
## Para correr el programa usar el comando 'python3 main.py anjos.json yalma'
## Desde script en linux test.sh 'sh test.sh'
## <º)))>< ¸.·´¯`·.´¯`·.¸¸.·´¯`·.¸¸.·´¯`·.´¯`·.¸¸.·´¯`·.¸ ><(((º>
import  gc
import  time
import  sys
import  uc_Co
import  util
import  reading
import  time
import  numpy as np
from    math     import floor, ceil, log
from    copy     import deepcopy 
from    solution import Solution
from    os       import path

nameins = 'uc_060.json'       ## prueba demostrativa excelente en mi PC
nameins = 'uc_062.json'       ## prueba demostrativa excelente en mi PC 

nameins = 'uc_57_copy.json'   ## prueba demostrativa excelente en mi PC (MOR un dia)
nameins = 'uc_057.json'       ## prueba demostrativa excelente en mi PC (MOR un dia)
nameins = 'uc_58.json'        ## prueba demostrativa excelente en mi PC (MOR tres dias)
nameins = 'uc_059.json'       ## prueba demostrativa excelente en mi PC (MOR cinco dias)
nameins = 'uc_082.json'       ## prueba demostrativa excelente en mi PC (MOR cinco dias)

## symmetry breaking: Automatic =-1 Turn off=0 ; moderade=1 ; extremely aggressive=5
## Emphasize balanced=0; feasibility=1; optimality=2; symmetry automatic=-1; symmetry low level=1
    
## Cargamos parámetros de configuración desde archivo <config>
ambiente,ruta,executable,timeconst,timefull,emphasizeMILP,symmetryMILP,lbheurMILP,strategyMILP, \
diveMILP,heuristicfreqMILP,numericalMILP,tolfeasibilityMILP,toloptimalityMILP,     \
emphasizeHEUR,symmetryHEUR,lbheurHEUR,strategyHEUR,gap,k,iterstop, \
MILP,Hard3,Harjk,lbc1,lbc2,lbc3,KS,lbc4 = util.config_env() 
# diveMILP=2; heuristicfreqMILP=50;  numericalMILP='yes'; tolfeasibilityMILP=1.0000001e-09 ;toloptimalityMILP =1.0000001e-09

k_original         = k          ## Almacenamos el parámetro k de local branching
timeconst_original = timeconst
x                  = 1e+75

z_lp=x; z_milp=x; z_harjk=x; z_hard3=x; z_ks=x; z_lbc1=x; z_lbc2=x; z_lbc3=x; z_lbc4=x; z_feas=x; z_check=x; z_lbc0=x; z_ks=0; z_rks=0; z_=0;
t_lp=0; t_milp=0; t_harjk=0; t_hard3=0; t_ks=0; t_lbc1=0; t_lbc2=0; t_lbc3=0; t_lbc4=0; t_feas=0; t_check=0; t_lbc0=0; t_ks=0; t_rks=0; t_=0;
g_lp=x; g_milp=x; g_harjk=x; g_hard3=x; g_ks=x; g_lbc1=x; g_lbc2=x; g_lbc3=x; g_lbc4=x; g_feas=x; g_check=x; g_lbc0=x; g_ks=x; g_rks=x; g_=x;
lb_milp=0; lb_best=0;
ns=0; nU_no_int=0; n_Uu_no_int=0; n_Uu_1_0=0;
SB_Uu =[]; No_SB_Uu =[]; lower_Pmin_Uu =[]; Vv =[]; Ww =[]; delta =[];
SB_Uu3=[]; No_SB_Uu3=[]; lower_Pmin_Uu3=[]; Vv3=[]; Ww3=[]; delta3=[];
comment = 'Here it writes a message to the stat.csv results file' 

if ambiente == 'yalma':
    if len(sys.argv) != 3:
        print('!!! Something went wrong, try write something like: $python3 main.py uc_54.json yalma')
        print('archivo :', sys.argv[1])
        print('ambiente:', sys.argv[2])
        sys.exit()
    nameins  = sys.argv[1]
    ambiente = sys.argv[2]

localtime = time.asctime(time.localtime(time.time()))

scope = ''       ## Unit Commitment Model 

print(localtime,'Solving <'+scope+'> model ---> ---> ---> --->',nameins)

## Lee instancia de archivo .json con formato de [Knueven2020]
instance = reading.reading(ruta+nameins)

## DEF CHECK FEASIABILITY OF SOLUTION
def checkSol(option,z_,SB_Uux,No_SB_Uux,Vvx,Wwx,deltax,dual=False,label=''):
    print('Checking solution feasibility: '+option+'_'+label+'=', z_ )
    t_o       = time.time() 
    model,__  = uc_Co.uc(instance,option='Check',SB_Uu=SB_Uux,No_SB_Uu=No_SB_Uux,V=Vvx,W=Wwx,delta=deltax,
                         nameins=nameins[0:6],mode='Tight',scope=scope)
    sol_check = Solution(model=model,nameins=nameins[0:6],env=ambiente,executable=executable,gap=gap,timelimit=timefull,
                         tee=False,tofiles=False,exportLP=False,option='Check',scope=scope,dual=dual)
    z_check, g_check = sol_check.solve_problem()
    t_check          = time.time() - t_o
    print(option,': t_check= ',round(t_check,1),'z_check= ',round(z_check,4),'g_check= ',round(g_check,8))
    return model

## ---------------------------------------------- MILP ----------------------------------------------------------
## Solve as a MILP

if  MILP:  
    fpheurMILP   = 1     ## Do not generate flow path cuts=-1 ; Automatic=0(CPLEX choose); moderately =1; aggressively=2
    rinsheurMILP = 50    ## Automatic=0 (CPLEX choose); None: do not apply RINS heuristic=-1;  Frequency to apply RINS heuristic=Any positive integer 
    cutoff   = 1e+75 
    t_o      = time.time() 
    model,__ = uc_Co.uc(instance,option='Milp',nameins=nameins[0:6],mode='Tight',scope=scope)
    sol_milp = Solution(model=model,nameins=nameins[0:6],env=ambiente,executable=executable,
                        gap=gap,cutoff=cutoff,timelimit=timefull,tee=False,tofiles=False,
                        emphasize=emphasizeMILP,symmetry=symmetryMILP,lbheur=lbheurMILP,strategy=strategyMILP,
                        dive=diveMILP,heuristicfreq=heuristicfreqMILP,numerical=numericalMILP,
                        tolfeasibility=tolfeasibilityMILP,toloptimality=toloptimalityMILP,   
                        fpheur=fpheurMILP, rinsheur=rinsheurMILP,                                           
                        exportLP=False,option='Milp',scope=scope)
    z_milp, g_milp = sol_milp.solve_problem()
    t_milp         = time.time() - t_o
    
    ## Actualizamos el tiempo de las heurísticas al que ocupó el MILP (si es que encontró un óptimo o terminó por tiempo)
    timefull = t_milp
    try:
        lb_milp  = sol_milp.lower_bound
    except Exception as e:
        temp = 0 #print(e)
        
    lb_best  = max(0,lb_milp)
    g_milp   = util.igap(lb_best,z_milp)
    print('t_milp= ',round(t_milp,1),'z_milp= ',round(z_milp,1),'g_milp= ',round(g_milp,8))
      
if  Hard3:
    ## ----------------------------------------------- RECOVERED SOLUTION ---------------------------------------------
    ## Load LR and Hard3 storaged solutions
    if path.exists('solHard3_a_'+nameins[0:6]+'.csv') == True and path.exists('solHard3_b_'+nameins[0:6]+'.csv') == True:
        t_lp,z_lp,t_hard3,z_hard3,SB_Uu3,No_SB_Uu3,lower_Pmin_Uu3,Vv3,Ww3,delta3 = util.loadSolution('Hard3',nameins[0:6]) 
        g_hard3  = util.igap(z_lp,z_hard3) 
        print('Recovered solution ---> ','t_hard3= ',round(t_hard3,1),'z_hard3= ',round(z_hard3,1))
        checkSol('Hard3 (recovered)',z_hard3,SB_Uu3,No_SB_Uu3,Vv3,Ww3,delta3,'hard3(rec)') ## Check feasibility
        
        lb_best = max(z_lp,lb_best)
    
    ## ----------------------------------------------- LINEAR RELAXATION ---------------------------------------------
    ## Relax as LP and solve it
    else:
        t_o        = time.time() 
        model,__   = uc_Co.uc(instance,option='LR',nameins=nameins[0:6],mode='Tight',scope=scope)
        sol_lp     = Solution(model=model,env=ambiente,executable=executable,nameins=nameins[0:6],gap=gap,timelimit=timeconst,
                              tee=False,tofiles=False,exportLP=False,option='LR',scope=scope)
        z_lp, g_lp = sol_lp.solve_problem() 
        t_lp       = time.time() - t_o
        print('t_lp= ',round(t_lp,1),'z_lp= ',round(z_lp,1))
        
        lb_best = max(z_lp,lb_best)
        
    ## -------------------------------------------- SELECTION VARIABLES TO FIX ---------------------------------------
    ## Seleccionamos las variables que serán fijadas. Es requisito correr antes <linear relaxation>
    ## SB_Uu         variables que SI serán fijadas a 1. (Soporte binario)
    ## No_SB_Uu      variables que NO serán fijadas.
    ## lower_Pmin_Uu variables en las que el producto de Pmin*Uu de [Harjunkoski2021] 
    ##               es menor a la potencia mínima del generador Pmin.
        SB_Uu, No_SB_Uu, lower_Pmin_Uu, Vv, Ww, delta = sol_lp.select_binary_support_Uu('LR')
        del sol_lp
        gc.collect()
        
    ## ------------------------------------------- HARD-FIXING 3 (only Uu) ---------------------------------------------
    ## HARD-FIXING 3 (only Uu) solution and solve the sub-MILP. (Require run the LP)
        t_o       = time.time()
        model,__  = uc_Co.uc(instance,option='Hard3',SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,lower_Pmin_Uu=lower_Pmin_Uu,
                            nameins=nameins[0:6],mode='Tight',scope=scope)
        sol_hard3 = Solution(model=model,env=ambiente,executable=executable,nameins=nameins[0:6],gap=gap,timelimit=timeconst-t_lp,
                            tee=False,tofiles=False,option='Hard3',scope=scope,
                            emphasize=emphasizeHEUR,symmetry=symmetryHEUR,lbheur=lbheurHEUR,strategy=strategyHEUR)
        z_hard3, g_hard3 = sol_hard3.solve_problem()
        t_hard3  = time.time() - t_o + t_lp   ## <<< --- t_hard3 ** INCLUYE EL TIEMPO DE LP **
        g_hard3  = util.igap(lb_best,z_hard3) 
        
        ## ES MUY IMPORTANTE GUARDAR LAS VARIABLES 'Uu=1'(SB_Uu3) DE LA PRIMERA SOLUCIÓN FACTIBLE 'Hard3'.
        ## ASI COMO LAS VARIABLES 'Uu=0' (No_SB_Uu3) 
        ## Este es el primer - Soporte Binario Entero Factible-
        SB_Uu3, No_SB_Uu3, __, Vv3, Ww3, delta3 = sol_hard3.select_binary_support_Uu('Hard3')    
        lower_Pmin_Uu3 = sol_hard3.update_lower_Pmin_Uu(lower_Pmin_Uu,'Hard3')
        #sol_hard3.cuenta_ceros_a_unos( SB_Uu, No_SB_Uu, lower_Pmin_Uu,'Hard3') 
        checkSol('Hard3',z_hard3,SB_Uu3,No_SB_Uu3,Vv3,Ww3,delta3,'hard3') ## Check feasibility

        print('t_hard3= ',round(t_hard3,1),'z_hard3= ',round(z_hard3,1),'g_hard3= ',round(g_hard3,8) )
        del sol_hard3
        gc.collect()
        util.saveSolution(t_lp,z_lp,t_hard3,z_hard3,SB_Uu3,No_SB_Uu3,lower_Pmin_Uu3,Vv3,Ww3,delta3,'Hard3',nameins[0:6])
        

    ## ------------------------------------------- HARJUNKOSKI ---------------------------------------------
    ## HARJUNKOSKI's rule solution and solve the sub-MILP. (Require run the LP)
    
if  Harjk:    
    t_o       = time.time()
    model,__  = uc_Co.uc(instance,option='Harjk',SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,lower_Pmin_Uu=lower_Pmin_Uu,
                         nameins=nameins[0:6],mode='Tight',scope=scope)
    sol_harjk = Solution(model=model,env=ambiente,executable=executable,nameins=nameins[0:6],gap=gap,timelimit=timeconst-t_lp,
                        emphasize=emphasizeHEUR,symmetry=symmetryHEUR,lbheur=lbheurHEUR,strategy=strategyHEUR,
                        tee=False,tofiles=False,option='Harjk',scope=scope)
    z_harjk, g_harjk = sol_harjk.solve_problem()
    t_harjk  = time.time() - t_o + t_lp   ## <<< --- t_harjk ** INCLUYE EL TIEMPO DE LP **
    g_harjk  = util.igap(lb_best,z_harjk)         
    
    SB_Uujk, No_SB_Uujk, __, Vvjk, Wwjk, deltajk = sol_harjk.select_binary_support_Uu('Harjk')    
    checkSol('Harjk',z_harjk,SB_Uujk,No_SB_Uujk,Vvjk,Wwjk,deltajk,'harjk') ## Check feasibility
    del SB_Uujk,No_SB_Uujk,Vvjk,Wwjk,deltajk
    print('t_harjk= ',round(t_harjk,1),'z_harjk= ',round(z_harjk,1),'g_harjk= ',round(g_harjk,8) )
    del sol_harjk
    gc.collect()


## --------------------------------------- LOCAL BRANCHING 1 ------------------------------------------
## LBC COUNTINOUS VERSION with soft-fixing
## Include the LOCAL BRANCHING CUT to the solution and solve the sub-MILP (it is using cutoff=z_hard).
if  lbc1:    
    t_o            = time.time() 
    Vv             = deepcopy(Vv3)
    Ww             = deepcopy(Ww3)
    delta          = deepcopy(delta3)
    SB_Uu          = deepcopy(SB_Uu3)
    No_SB_Uu       = deepcopy(No_SB_Uu3)
    lower_Pmin_Uu  = deepcopy(lower_Pmin_Uu3)
    t_net          = timefull - t_hard3
    t_res          = timefull - t_hard3
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
    result_iter    = []
    result_iter.append((t_hard3,z_hard3))
    print('\t')
        
    while True:
        if (iter==iterstop) or (time.time() - t_o >= t_net):
            break
        char     = ''
        
        if improve == False:
            cutoff=1e+75
                 
        timeres1  = min(t_res,timeconst)
        model, __ = uc_Co.uc(instance,option='lbc1',SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,lower_Pmin_Uu=lower_Pmin_Uu,V=Vv,W=Ww,delta=delta,
                            percent_soft=90,k=k,nameins=nameins[0:6],mode='Tight',scope=scope,improve=improve,timeover=timeover,rightbranches=rightbranches)
        sol_lbc1  = Solution(model=model,env=ambiente,executable=executable,nameins=nameins[0:6],letter=util.getLetter(iter-1),gap=gap,cutoff=cutoff,timelimit=timeres1,
                            emphasize=emphasizeHEUR,symmetry=symmetryHEUR,lbheur=lbheurHEUR,strategy=strategyHEUR,
                            tee=False,tofiles=False,option='lbc1',scope=scope)
        z_lbc1,g_lbc1 = sol_lbc1.solve_problem()
        
        #sol_lbc1.cuenta_ceros_a_unos(SB_Uu, No_SB_Uu, lower_Pmin_Uu,'lbc1') ## Compara contra la última solución
        
        gap_iter = abs((z_lbc1 - z_old) / z_old) * 100 ## Percentage
        improve = False
        if z_lbc1 < incumbent :                        ## Update solution
            incumbent  = z_lbc1
            cutoff     = z_lbc1
            # saved      = [SB_Uu,No_SB_Uu,Vv,Ww,delta]
            char       = '***'
            g_lbc1     = util.igap(lb_best,z_lbc1)
            if gap_iter > gap:
                improve = True

        result_iter.append((round(time.time() - t_o + t_hard3,1),z_lbc1))
        z_old = z_lbc1 ## Guardamos la z de la solución anterior
          
        print('<°|'+fish+'>< iter:'+str(iter)+' t_lbc1= ',round(time.time()-t_o+t_hard3,1),'z_lbc1= ',round(z_lbc1,1),char,'g_lbc1= ',round(g_lbc1,8) ) #
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
                print('Leaving a local optimum ...  >>+*+*+*+*+*+|°>')
                SB_Uu, No_SB_Uu, __, Vv, Ww, delta = sol_lbc1.select_binary_support_Uu('lbc1')  
                lower_Pmin_Uu = sol_lbc1.update_lower_Pmin_Uu(lower_Pmin_Uu,'lbc1') 
                rightbranches.append([SB_Uu,No_SB_Uu,lower_Pmin_Uu])
                fish = ')'
        else: ## Mejora la solución
            SB_Uu, No_SB_Uu, __, Vv, Ww, delta = sol_lbc1.select_binary_support_Uu('lbc1')  
            lower_Pmin_Uu = sol_lbc1.update_lower_Pmin_Uu(lower_Pmin_Uu,'lbc1')
            saved         = [SB_Uu,No_SB_Uu,Vv,Ww,delta] ## Update solution
                    
        t_res = t_net - time.time() + t_o 
        print('lbc1','tiempo restante:',t_res)
        
        del sol_lbc1
        gc.collect()
        iter  = iter + 1
         
    t_lbc1 = time.time() - t_o + t_hard3  
    z_lbc1 = incumbent    
    for item in result_iter:
        print(item[0],',',item[1])    
    result_iter = np.array(result_iter)
    #np.savetxt('iterLBC1'+nameins[0:6]+'.csv', result_iter, delimiter=',')
    
    checkSol('z_lbc1',z_lbc1,SB_Uu,No_SB_Uu,Vv,Ww,delta,'lbc1') ## Check feasibility (LB1)
        
    k = k_original  ## Si es que LBC cambió el parámetro k

        
## --------------------------------------- LOCAL BRANCHING 2 ------------------------------------------
## LBC BINARY VERSION without soft-fixing and use P_min candidates
## Include the LOCAL BRANCHING CUT to the solution and solve the sub-MILP (it is using cutoff=z_hard).
if  lbc2:    
    t_o            = time.time() 
    Vv             = deepcopy(Vv3)
    Ww             = deepcopy(Ww3)
    delta          = deepcopy(delta3)
    SB_Uu          = deepcopy(SB_Uu3)
    No_SB_Uu       = deepcopy(No_SB_Uu3)
    lower_Pmin_Uu  = deepcopy(lower_Pmin_Uu3)
    t_net          = timefull - t_hard3
    t_res          = timefull - t_hard3
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
    result_iter    = []
    result_iter.append((t_hard3,z_hard3))
    print('\t')
        
    while True:
        if (iter==iterstop) or (time.time()-t_o >= t_net):
            break
        char     = ''
        
        if improve == False:
            cutoff=1e+75
        
        timeres1  = min(t_res,timeconst)      
        model, __ = uc_Co.uc(instance,option='lbc2',SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,lower_Pmin_Uu=lower_Pmin_Uu,V=Vv,W=Ww,delta=delta,
                            percent_soft=90,k=k,nameins=nameins[0:6],mode='Tight',scope=scope,improve=improve,timeover=timeover,rightbranches=rightbranches)
        sol_lbc2  = Solution(model=model,env=ambiente,executable=executable,nameins=nameins[0:6],letter=util.getLetter(iter-1),gap=gap,cutoff=cutoff,timelimit=timeres1,
                            emphasize=emphasizeHEUR,symmetry=symmetryHEUR,lbheur=lbheurHEUR,strategy=strategyHEUR,
                            tee=False,tofiles=False,option='lbc2',scope=scope)
        z_lbc2,g_lbc2 = sol_lbc2.solve_problem()
        
        #sol_lbc2.cuenta_ceros_a_unos(SB_Uu, No_SB_Uu, lower_Pmin_Uu,'lbc2') ## Compara contra la última solución
        
        gap_iter = abs((z_lbc2 - z_old)/z_old) * 100 ## Percentage
        improve = False
        if z_lbc2 < incumbent :                      ## Update solution
            incumbent  = z_lbc2
            cutoff     = z_lbc2
            #saved      = [SB_Uu,No_SB_Uu,Vv,Ww,delta]
            char       = '***'
            g_lbc2     = util.igap(lb_best,z_lbc2)
            if gap_iter > gap:
                improve = True
            
        result_iter.append((round(time.time()-t_o+t_hard3,1),z_lbc2))
        z_old = z_lbc2 ## Guardamos la solución anterior
          
        print('<°|'+fish+'>< iter:'+str(iter)+' t_lbc2= ',round(time.time()-t_o+t_hard3,1),'z_lbc2= ',round(z_lbc2,1),char,'g_lbc2= ',round(g_lbc2,8) ) #
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
                print('Leaving a local optimum     ...    >>+*+*+*+*+*+|°>')
                SB_Uu, No_SB_Uu, __, Vv, Ww, delta = sol_lbc2.select_binary_support_Uu('lbc2')  
                lower_Pmin_Uu = sol_lbc2.update_lower_Pmin_Uu(lower_Pmin_Uu,'lbc2') 
                rightbranches.append([SB_Uu,No_SB_Uu,lower_Pmin_Uu])
                fish = ')'
        else: ## Mejora la solución
            SB_Uu, No_SB_Uu, __, Vv, Ww, delta = sol_lbc2.select_binary_support_Uu('lbc2')  
            lower_Pmin_Uu = sol_lbc2.update_lower_Pmin_Uu(lower_Pmin_Uu,'lbc2') 
            saved         = [SB_Uu,No_SB_Uu,Vv,Ww,delta] ## Update solution

        t_res = t_net - time.time() + t_o 
        print('lbc2 ','tiempo restante:',t_res)
        
        del sol_lbc2
        gc.collect()
        iter = iter + 1

    t_lbc2 = time.time() - t_o + t_hard3  
    z_lbc2 = incumbent    
    for item in result_iter:
        print(item[0],',',item[1])    
    result_iter = np.array(result_iter)
    #np.savetxt('iterLBC2'+nameins[0:6]+'.csv', result_iter, delimiter=',')
    
    checkSol('z_lbc2',z_lbc2,SB_Uu,No_SB_Uu,Vv,Ww,delta,'lbc2') ## Check feasibility (LBC2)
    
    k = k_original  ## Si es que LBC cambió el parámetro k

        
## --------------------------------------- LOCAL BRANCHING 3 ------------------------------------------
## LBC COUNTINOUS VERSION without soft-fixing and not use P_min candidates
## Include the LOCAL BRANCHING CUT to the solution and solve the sub-MILP (it is using cutoff=z_hard).
if  lbc3:    
    t_o            = time.time() 
    Vv             = deepcopy(Vv3)
    Ww             = deepcopy(Ww3)
    delta          = deepcopy(delta3)
    SB_Uu          = deepcopy(SB_Uu3)
    No_SB_Uu       = deepcopy(No_SB_Uu3)
    lower_Pmin_Uu  = deepcopy(lower_Pmin_Uu3)
    t_net          = timefull - t_hard3
    t_res          = timefull - t_hard3
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
    result_iter    = []
    result_iter.append((t_hard3,z_hard3))
    print('\t')
        
    while True:
        if (iter==iterstop) or (time.time()-t_o >= t_net):
            break
        char     = ''
        
        if improve == False:
            cutoff=1e+75
        
        timeres1  = min(t_res,timeconst)      
        model, __ = uc_Co.uc(instance,option='lbc3',SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,lower_Pmin_Uu=lower_Pmin_Uu,V=Vv,W=Ww,delta=delta,
                            percent_soft=90,k=k,nameins=nameins[0:6],mode='Tight',scope=scope,improve=improve,timeover=timeover,rightbranches=rightbranches)
        sol_lbc3  = Solution(model=model,env=ambiente,executable=executable,nameins=nameins[0:6],letter=util.getLetter(iter-1),gap=gap,cutoff=cutoff,timelimit=timeres1,
                            emphasize=emphasizeHEUR,symmetry=symmetryHEUR,lbheur=lbheurHEUR,strategy=strategyHEUR,
                            tee=False,tofiles=False,option='lbc3',scope=scope)
        z_lbc3,g_lbc3 = sol_lbc3.solve_problem()
        
        #sol_lbc3.cuenta_ceros_a_unos(SB_Uu, No_SB_Uu, lower_Pmin_Uu,'lbc3') ## Compara contra la última solución
        
        gap_iter = abs((z_lbc3 - z_old)/z_old) * 100 ## Percentage
        improve = False
        if z_lbc3 < incumbent :                      ## Update solution
            incumbent  = z_lbc3
            cutoff     = z_lbc3
            #saved      = [SB_Uu,No_SB_Uu,Vv,Ww,delta]
            char       = '***'
            g_lbc3     = util.igap(lb_best,z_lbc3)
            if gap_iter > gap:
                improve = True
            
        result_iter.append((round(time.time()-t_o+t_hard3,1),z_lbc3))
        z_old = z_lbc3 ## Guardamos la solución anterior
          
        print('<°|'+fish+'>< iter:'+str(iter)+' t_lbc3= ',round(time.time()-t_o+t_hard3,1),'z_lbc3= ',round(z_lbc3,1),char,'g_lbc3= ',round(g_lbc3,8) ) #
        print('\t')       
        fish = fish + ')'  
        
        ## Aquí se prepara la nueva iteracion ...  
        timeover == False       
        if improve == False:   
            if sol_lbc3.timeover == True or sol_lbc3.nosoluti == True or sol_lbc3.infeasib == True:                     
                if sol_lbc3.timeover == True:   
                    print('k=[k/2] Time limit reach without improve: shrinking the neighborhood  ...  >(°> . o O')
                else:
                    print('k=[k/2] No solution/infeasible: shrinking the neighborhood  ...  >(°> . o O')
                k = floor(k/2)  
                timeover == True         
            else:              
                print('Leaving a local optimum     ...    >>+*+*+*+*+*+|°>')
                SB_Uu, No_SB_Uu, __, Vv, Ww, delta = sol_lbc3.select_binary_support_Uu('lbc3')  
                lower_Pmin_Uu = sol_lbc3.update_lower_Pmin_Uu(lower_Pmin_Uu,'lbc3') 
                rightbranches.append([SB_Uu,No_SB_Uu,lower_Pmin_Uu])
                fish = ')'
        else: ## Mejora la solución
            SB_Uu, No_SB_Uu, __, Vv, Ww, delta = sol_lbc3.select_binary_support_Uu('lbc3')  
            lower_Pmin_Uu = sol_lbc3.update_lower_Pmin_Uu(lower_Pmin_Uu,'lbc3') 
            saved         = [SB_Uu,No_SB_Uu,Vv,Ww,delta] ## Update solution

        t_res = t_net - time.time() + t_o 
        print('lbc3 ','tiempo restante:',t_res)
        
        del sol_lbc3
        gc.collect()
        iter = iter + 1

    t_lbc3 = time.time() - t_o + t_hard3  
    z_lbc3 = incumbent    
    for item in result_iter:
        print(item[0],',',item[1])    
    result_iter = np.array(result_iter)
    #np.savetxt('iterLBC2'+nameins[0:6]+'.csv', result_iter, delimiter=',')
    
    checkSol('z_lbc3',z_lbc3,SB_Uu,No_SB_Uu,Vv,Ww,delta,'lbc3') ## Check feasibility (LBC2)
    
    k = k_original  ## Si es que LBC cambió el parámetro k


## --------------------------------------- LOCAL BRANCHING 4 ------------------------------------------
## LBC COUNTINOUS VERSION without soft-fixing
## Include the LOCAL BRANCHING CUT to the solution and solve the sub-MILP (it is using cutoff=z_hard).

if  lbc4:    
    t_o            = time.time() 
    Vv             = deepcopy(Vv3)
    Ww             = deepcopy(Ww3)
    delta          = deepcopy(delta3)
    SB_Uu          = deepcopy(SB_Uu3)
    No_SB_Uu       = deepcopy(No_SB_Uu3)
    lower_Pmin_Uu  = deepcopy(lower_Pmin_Uu3)
    t_net          = timefull - t_hard3
    t_res          = timefull - t_hard3
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
    result_iter    = []
    result_iter.append((t_hard3,z_hard3))
    print('\t')
    
    ## Calculating reduced cost
    model,__  = uc_Co.uc(instance,option='RC',SB_Uu=saved[0],No_SB_Uu=saved[1],V=saved[2],W=saved[3],delta=saved[4],
                         nameins=nameins[0:6],mode='Tight',scope=scope)
    sol_rc    = Solution(model=model,nameins=nameins[0:6],env=ambiente,executable=executable,gap=gap,timelimit=t_net,
                         emphasize=emphasizeHEUR,symmetry=symmetryHEUR,lbheur=lbheurHEUR,strategy=strategyHEUR,
                         tee=False,tofiles=False,exportLP=False,rc=True,option='RC',scope=scope)
    z_rc,g_rc = sol_rc.solve_problem() 
    print('lb4 z_rc= ',round(z_rc,4))      
    
    ##  Colected candidates
    rc   = []
    i    = 0                    
    for f in No_SB_Uu: 
        ##        ( i , reduced_cost , g , t )
        rc.append(( i , model.rc[model.u[f[0]+1,f[1]+1]] , f[0] , f[1] ))
        i = i + 1    
    rc.sort(key=lambda tup:tup[1], reverse=False) ## Ordenamos las variables No_SB_Uu de acuerdo a sus costos reducidos 

    candidates = []
    for f in rc: 
        if f[1]<=0:
            candidates.append((f[2],f[3])) ## (g , t) 
    
    while True:
        if (iter==iterstop) or (time.time()-t_o >= t_net):
            break
        char     = ''
        
        if improve == False:
            cutoff=1e+75
        
        timeres1  = min(t_res,timeconst)      
        model, __ = uc_Co.uc(instance,option='lbc4',SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,lower_Pmin_Uu=candidates,V=Vv,W=Ww,delta=delta,
                            percent_soft=90,k=k,nameins=nameins[0:6],mode='Tight',scope=scope,improve=improve,timeover=timeover,rightbranches=rightbranches)
        sol_lbc4  = Solution(model=model,env=ambiente,executable=executable,nameins=nameins[0:6],letter=util.getLetter(iter-1),gap=gap,cutoff=cutoff,timelimit=timeres1,
                            emphasize=emphasizeHEUR,symmetry=symmetryHEUR,lbheur=lbheurHEUR,strategy=strategyHEUR,
                            tee=False,tofiles=False,option='lbc4',scope=scope)
        z_lbc4,g_lbc4 = sol_lbc4.solve_problem()
                
        gap_iter = abs((z_lbc4 - z_old)/z_old) * 100 ## Percentage
        improve = False
        if z_lbc4 < incumbent :                      ## Update solution
            incumbent  = z_lbc4
            cutoff     = z_lbc4
            #saved      = [SB_Uu,No_SB_Uu,Vv,Ww,delta]
            char       = '***'
            g_lbc4     = util.igap(lb_best,z_lbc4)
            if gap_iter > gap:
                improve = True
            
        result_iter.append((round(time.time()-t_o+t_hard3,1),z_lbc4))
        z_old = z_lbc4 ## Guardamos la solución anterior
          
        print('<°|'+fish+'>< iter:'+str(iter)+' t_lbc4= ',round(time.time()-t_o+t_hard3,1),'z_lbc4= ',round(z_lbc4,1),char,'g_lbc4= ',round(g_lbc4,8) ) #
        print('\t')       
        fish = fish + ')'  
        
        ## Aquí se prepara la nueva iteracion ...  
        timeover == False       
        if improve == False:   
            if sol_lbc4.timeover == True or sol_lbc4.nosoluti == True or sol_lbc4.infeasib == True:                     
                if sol_lbc4.timeover == True:   
                    print('k=[k/2] Time limit reach without improve: shrinking the neighborhood  ...  >(°> . o O')
                else:
                    print('k=[k/2] No solution/infeasible: shrinking the neighborhood  ...  >(°> . o O')
                k = floor(k/2)  
                timeover == True         
            else:              
                print('Leaving a local optimum     ...    >>+*+*+*+*+*+|°>')
                SB_Uu, No_SB_Uu, __, Vv, Ww, delta = sol_lbc4.select_binary_support_Uu('lbc4')  
                lower_Pmin_Uu = sol_lbc4.update_lower_Pmin_Uu(lower_Pmin_Uu,'lbc4') 
                rightbranches.append([SB_Uu,No_SB_Uu,lower_Pmin_Uu])
                fish = ')'
        else: ## Mejora la solución
            SB_Uu, No_SB_Uu, __, Vv, Ww, delta = sol_lbc4.select_binary_support_Uu('lbc4')  
            lower_Pmin_Uu = sol_lbc4.update_lower_Pmin_Uu(lower_Pmin_Uu,'lbc4') 
            saved         = [SB_Uu,No_SB_Uu,Vv,Ww,delta] ## Update solution

        t_res = t_net - time.time() + t_o 
        print('lbc4 ','tiempo restante:',t_res)
        
        del sol_lbc4
        gc.collect()
        iter = iter + 1

    t_lbc4 = time.time() - t_o + t_hard3  
    z_lbc4 = incumbent    
    for item in result_iter:
        print(item[0],',',item[1])    
    result_iter = np.array(result_iter)
    #np.savetxt('iterLBC2'+nameins[0:6]+'.csv', result_iter, delimiter=',')
    
    checkSol('z_lbc4',z_lbc4,SB_Uu,No_SB_Uu,Vv,Ww,delta,'lbc4') ## Check feasibility (LBC2)
    
    k = k_original  ## Si es que LBC cambió el parámetro k
    
    
## ---------------------------------  KERNEL SEARCH I ---------------------------------
##
## La versión básica de KS consiste en relajar la formulacion y a partir de ello sacar 
## las variables del kernel y de los buckets, después de manera iterativa se resulven los 
## SUB-MILP´S 'restringidos' mas pequeños.
## KS solution and solve the sub-MILP (it is using cutoff = z_hard).
## Use 'Soft+pmin' (lower subset of Uu-Pmin)  as the first and unique bucket to consider
## Use relax the integrality variable Uu.
if  KS:
    Vv          = deepcopy(Vv3)
    Ww          = deepcopy(Ww3)
    delta       = deepcopy(delta3)
    SB_Uu       = deepcopy(SB_Uu3)
    No_SB_Uu    = deepcopy(No_SB_Uu3)
    saved       = [SB_Uu,No_SB_Uu,Vv,Ww,delta]

    t_o         = time.time() 
    incumbent   =  z_hard3
    cutoff      =  z_hard3 # 1e+75 
    iter        =  0  
    sol_ks      =  []
    result_iter =  []
    result_iter.append((t_hard3 + time.time() - t_o, z_hard3))

    while True:
        ## --------------------------------------- CALCULATE REDUCED COSTS Uu ------------------------------------
        t_res = max(0,( timefull - t_hard3 ) - (time.time() - t_o))
        if t_res <= 0:
            print('KS Salí ciclo externo')
            break
        
        if  True:
            t_1 = time.time()
            model,__  = uc_Co.uc(instance,option='RC',SB_Uu=saved[0],No_SB_Uu=saved[1],V=saved[2],W=saved[3],delta=saved[4],
                                 nameins=nameins[0:6],mode='Tight',scope=scope)
            sol_rc    = Solution(model=model,nameins=nameins[0:6],env=ambiente,executable=executable,gap=gap,timelimit=timefull,
                                emphasize=emphasizeHEUR,symmetry=symmetryHEUR,lbheur=lbheurHEUR,strategy=strategyHEUR,
                                tee=False,tofiles=False,exportLP=False,rc=True,option='RC',scope=scope)
            z_rc,g_rc = sol_rc.solve_problem() 
            t_rc      = time.time() - t_1
            print('KS t_rc= ',round(t_rc,1),'z_rc= ',round(z_rc,4))      
            
            ## ----------------------------- SECOND PHASE ----------------------------------------------
            ##  Defining buckets 
            rc   = []
            i    = 0                    
            for f in No_SB_Uu: 
                ##        ( i , reduced_cost , g , t )
                rc.append(( i , model.rc[model.u[f[0]+1,f[1]+1]] , f[0] , f[1] ))
                i = i + 1    
            rc.sort(key=lambda tup:tup[1], reverse=False) ## Ordenamos las variables No_SB_Uu de acuerdo a sus costos reducidos 
            
            ##  Definimos el número de buckets 
            K = floor(1 + 3.322 * log(len(No_SB_Uu)))  ## Sturges rule
            print('KS Number of buckets K =', K)    
            len_i  = ceil(len(No_SB_Uu) / K)
            pos_i  = 0
            k_     = [0]    
            for i in range(len_i,len(No_SB_Uu),len_i+1):
                k_.append( i )
            k_[-1] = len(No_SB_Uu)
            #print( k_ )
            
            cutoff      = incumbent # 1e+75 !!!
            iter_bk     = 0
            iterstop    = K - 2
            char        = ''
            kernel      = deepcopy(SB_Uu)
            
            ## Recontabilizamos el tiempo
            t_res     = max(0,( timefull - t_hard3) - (time.time() - t_o))
            timeconst = t_res / K
            
            while True: 
                t_res = max(0,( timefull - t_hard3 ) - (time.time() - t_o))
                if iter_bk >= iterstop or t_res <= 0:
                    print('KS Salí ciclo interno')
                    break

                timeconst1  = min(t_res,timeconst)      
                bucket      = rc[k_[iter_bk]:k_[iter_bk + 1]] 
                print('bucket',util.getLetter(iter),'[',k_[iter_bk],':',k_[iter_bk + 1],']' )      
                
                try:
                    ##  Resolvemos el kernel con cada uno de los buckets
                    model,__   = uc_Co.uc(instance,option='KS',kernel=kernel,bucket=bucket,nameins=nameins[0:6],mode='Tight',scope=scope)
                    sol_ks     = Solution(model=model,env=ambiente,executable=executable,nameins=nameins[0:6],letter=util.getLetter(iter),gap=gap,cutoff=cutoff,timelimit=timeconst1,
                                          emphasize=emphasizeHEUR,symmetry=symmetryHEUR,lbheur=lbheurHEUR,strategy=strategyHEUR,
                                          tee=False,tofiles=False,option='KS',scope=scope)
                    z_ks, g_ks = sol_ks.solve_problem()
                    t_ks       = time.time() - t_o + t_hard3
                    kernel, No_SB_Uu, __, Vv, Ww, delta = sol_ks.select_binary_support_Uu('KS') 
                    
                    if z_ks < incumbent :                      ## Update solution
                        incumbent  = z_ks
                        cutoff     = z_ks
                        saved      = [kernel,No_SB_Uu,Vv,Ww,delta]
                        g_ks       = util.igap(lb_best,z_ks)
                        char       = '***'
                        
                    result_iter.append((round(time.time()-t_o+t_hard3,1), z_ks))
                    
                    g_ks    = util.igap(lb_best,z_ks) 
                    print('<°|>< iter:'+str(iter)+' t_ks= ',round(time.time()-t_o+t_hard3,1),'z_ks= ',round(z_ks,1),char,'g_ks= ',round(g_ks,8)) #
                except:
                    print('>>> No solution found')
                    result_iter.append((round(time.time()-t_o+t_hard3,1), 1e+75))
                finally:    
                    iter_bk = iter_bk + 1
                    
                print('\t')       
                    
                t_res = max(0,( timefull - t_hard3 ) - (time.time() - t_o))
                print('KS ','tiempo restante:',t_res)
                
                del sol_ks
                gc.collect()
                iter = iter + 1
                                
        Vv       = deepcopy(saved[2])
        Ww       = deepcopy(saved[3])
        delta    = deepcopy(saved[4])
        SB_Uu    = deepcopy(saved[0])
        No_SB_Uu = deepcopy(saved[1])

    t_ks = (time.time() - t_o) + t_hard3  
    z_ks = incumbent    
    for item in result_iter:
        print(item[0],',',item[1])
    result_iter = np.array(result_iter)
    #np.savetxt('iterKS'+nameins[0:6]+'.csv', result_iter, delimiter=',')
    
    checkSol('z_ks',z_ks,SB_Uu,No_SB_Uu,Vv,Ww,delta,'ks') ## Check feasibility (KS)
 
        
    ## PENDIENTES    
    # \todo{Exportar los Costos reducidos ordenados de LR y comparar contra los lower_Pmin_Uu, se esperan coincidencias}
    # \todo{Curar instancias Morales y Knueven (cambiar limites pegados y agregar piecewise cost)}

    ## PRUEBAS                    
    # \todo{Probar experimentalmente que fijar otras variables enteras además de Uu no impacta mucho}         
    # \todo{probar que SI conviene incluir los intentos de asignación en las variables soft-fix }
    # \todo{Probar tamaños del n_kernel (!!! al parecer influye mucho en el tiempo de búsqueda)} 

    ## IDEAS    
    # \todo{Un KS relajando y fijando grupos de variables a manera de buckets}    
    # \todo{Incluir datos hidro de instancias en México} 
    # \todo{Incluir restricciones de generadores hidro}      
    # \todo{Probar modificar el tamaño de las variables soft-fix de 90% al 95%}
    # \todo{Probar cambiar el valor de k en nuevas iteraciones con una búsqueda local (un LBC completo de A.Lodi)}    

    ## DESCARTES            
    # \todo{Verificar por qué la instancia mem_01.json es infactible}    
    # \todo{Un movimiento en la búsqueda local puede ser cambiar la asignación del costo de arranque en un periodo adelante o atras para algunos generadores} 
    # \todo{Hacer un VNS o un VND con movimientos definidos con las variables}
    # \todo{Podrian fijarse todas las variables (u,v,w y delta) relacionadas con los generadores que se escogen para ser fijados}
    # \todo{Podríamos usar reglas parecidas al paper de Todosijevic para fijar V,W a partir de Uu}
    # \todo{Calcular el tamaño del slack del subset Sbarra -Soporte binario-}
    # \todo{Agregar must-run} 
    # \todo{Encontrar la primer solución factible del CPLEX}
    
    ## TERMINADAS
    # \todo{Probar configuración enfasis feasibility vs optimality en el Solver )} 
    # \todo{Considerar no usar nada de Hard, ni cut-off, ni Soporte Binario.}
    # \todo{Usar la solución factible hard como warm-start} 
    # \todo{Probar el efecto de la cota obtenida del hard-fix} 
    # \todo{Probar con diferentes calidades de primera solución factible,(podríamos usar Pure Variable-fixing)}
    # \todo{Revisar la desigualdad válida. El numero de 1´s de las variables de arranque 'V' en un horizonte deben ser igual al número de 1's en la variable delta}
    # \todo{Comparar soluciones entre si en variables u,v,w y delta}
    # \todo{Verificar que las restricciones de arranque que usan delta en la formulación, se encontraron variables con valor None en la solución}
    # \todo{Fijar la solución entera y probar factibilidad} 
    # \todo{Crear instancias sintéticas a partir de kazarlis} 

    # ## ----------------------------- DUAL COST ----------------------------------------------
    
    # SB_Uu, No_SB_Uu, __, Vv, Ww, delta = sol_milp.select_binary_support_Uu('Milp0') 
    # model,__  = uc_Co.uc(instance,option='FixSol',SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,V=Vv,W=Ww,delta=delta,
    #                      nameins=nameins[0:6],mode='Tight',scope=scope)
    # sol_fix   = Solution(model=model,env=ambiente,executable=executable,nameins=nameins[0:6],gap=gap,timelimit=timeconst,
    #                       tee=False,tofiles=False,exportLP=False,option='FixSol',scope=scope,dual=True)
    # z_fix, g_fix = sol_fix.solve_problem() 
    # print('z_fix= ',round(z_fix,4))
    
    # for t in model.T:
    #     print(model.dual[ model.demand_rule65[t] ],model.dual[ model.demand_rule67[t] ])


    
## NO OLVIDES COMENTAR TUS PRUEBAS ¸.·´¯`·.´¯`·.¸¸.·´¯`·.¸><(((º>
comment    = 'Pruebas completas TC&UC'

## --------------------------------- RESULTS -------------------------------------------
## Append a list as new line to an old csv file using as log, the first line of the file as shown.

## ambiente,localtime,nameins,T,G,gap,timeconst,timefull,z_lp,z_milp,z_feas,z_harjk,z_hard3,z_lbc1,z_lbc2,z_lbc3,z_ks,t_lp,t_milp,t_feas,t_harjk,t_hard3,t_lbc1,t_lbc2,t_lbc3,t_ks,lb_milp,g_milp,g_feas,g_harjk,g_hard3,g_lbc1,g_lbc2,g_lbc3,g_ks,k,ns,emphasizeMILP,symmetryMILP,strategyMILP,lbheurMILP,emphasizeHEUR,symmetryHEUR,strategyHEUR,lbheurHEUR,comment
row = [ambiente,localtime,nameins,len(instance[1]),len(instance[0]),gap,timeconst_original,timefull,
    round(z_lp,   1),round(z_milp,1),round(z_feas,1),round(z_harjk,1),round(z_hard3,1),round(z_lbc1,1),round(z_lbc2,1),round(z_lbc3,1),round(z_ks,1),round(z_lbc4,1),
    round(t_lp,   1),round(t_milp,1),round(t_feas,1),round(t_harjk,1),round(t_hard3,1),round(t_lbc1,1),round(t_lbc2,1),round(t_lbc3,1),round(t_ks,1),round(t_lbc4,1),
    round(lb_milp,1),round(g_milp,8),round(g_feas,1),round(g_harjk,8),round(g_hard3,8),round(g_lbc1,8),round(g_lbc2,8),round(g_lbc3,8),round(g_ks,8),round(g_lbc4,8),
                  k,ns,emphasizeMILP,symmetryMILP,strategyMILP,lbheurMILP,emphasizeHEUR,symmetryHEUR,strategyHEUR,lbheurHEUR,comment] 
util.append_list_as_row('stat.csv',row)

print(localtime,'terminé instancia ...´¯`·...·´¯`·.. ><(((º> ',nameins)

exit()

