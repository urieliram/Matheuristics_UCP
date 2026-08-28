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
from    math     import floor, ceil, log
from    copy     import deepcopy 
from    solution import Solution
from    os       import path

## Instancia por omision; solo se usa cuando config.con no pide el ambiente 'yalma',
## porque en ese caso el nombre llega por linea de comandos (ver mas abajo).
## Instancias chicas utiles para validar: uc_057 (un dia), uc_058 (tres dias), uc_059 (cinco dias).
nameins = 'uc_061.json'

## symmetry breaking: Automatic =-1 Turn off=0 ; moderade=1 ; extremely aggressive=5
## Emphasize balanced=0; feasibility=1; optimality=2; symmetry automatic=-1; symmetry low level=1
    
## Cargamos parámetros de configuración desde archivo <config>
ambiente,ruta,executable,timelp,timeconst,timefull,emphasizeMILP,symmetryMILP,lbheurMILP,strategyMILP, \
diveMILP,heuristicfreqMILP,numericalMILP,tolfeasibilityMILP,toloptimalityMILP,     \
emphasizeHEUR,symmetryHEUR,lbheurHEUR,strategyHEUR,gap,k,iterstop, \
Hard3,Harjk,MILP2,lbc1,lbc2,lbc3,lbc4,KS,MILP = util.config_env() 

timeconst_original = timeconst
e                  = 1E+75

## Valores iniciales de los resultados que terminan en la fila de stat.csv.
## 'e' marca "sin incumbente"; los tiempos arrancan en cero.
z_lp=e; z_milp=e; z_milp2=0; z_harjk=e; z_hard3=e; z_lbc1=e; z_lbc2=e; z_lbc3=e; z_lbc4=e; z_ks=0; z_=0
t_lp=0; t_milp=0; t_milp2=0; t_harjk=0; t_hard3=0; t_lbc1=0; t_lbc2=0; t_lbc3=0; t_lbc4=0; t_ks=0; t_=0
g_lp=e; g_milp=e; g_milp2=e; g_harjk=e; g_hard3=e; g_lbc1=e; g_lbc2=e; g_lbc3=e; g_lbc4=e; g_ks=e; g_=e
lb_milp=0; lb_best=0; lb_milp2=0

## Parametros de CPLEX REALMENTE aplicados a SM1 (columnas *MILP de stat.csv).
## El bloque MILP no pasa emphasize/symmetry/lbheur, asi que rigen los defaults de
## Solution.__init__ y no los valores de config.con. Se leen del objeto Solution para
## que el log siga al codigo si algun dia se descomentan. 'na' = SM1 no se ejecuto.
eff_emphasizeMILP='na'; eff_symmetryMILP='na'; eff_strategyMILP='na'; eff_lbheurMILP='na'
SB_Uu =[]; No_SB_Uu =[]; lower_Pmin_Uu =[]; Vv =[]; Ww =[]; delta =[]
SB_Uu3=[]; No_SB_Uu3=[]; lower_Pmin_Uu3=[]; Vv3=[]; Ww3=[]; delta3=[]
comment = 'Here it writes a message to the stat.csv results file' 

if ambiente == 'yalma':
    if len(sys.argv) != 3:
        print('!!! Something went wrong, try write something like: $python3 main.py uc_54.json yalma')
        print('archivo :', sys.argv[1])
        print('ambiente:', sys.argv[2])
        sys.exit()
    nameins  = sys.argv[1]
    ambiente = sys.argv[2]

## Identificador de la instancia sin extension ('uc_057.json' -> 'uc_057').
## Nombra los logs de CPLEX y los archivos solHard3_a/b_<insid>.csv de recuperacion.
insid = nameins[0:6]

localtime = time.asctime(time.localtime(time.time()))

scope = ''       ## '' = T&C Unit Commitment Model

print(localtime,'Solving <'+scope+'> model ---> ---> ---> --->',nameins)

## Lee instancia de archivo .json con formato de [Knueven2020]
instance = reading.reading(ruta+nameins)

## DEF CHECK FEASIABILITY OF SOLUTION
def checkSol(option,z_,SB_Uux,No_SB_Uux,Vvx,Wwx,deltax,*,dual=False,label=''):
    print('Checking solution feasibility: '+option+'_'+label+'=', z_ )
    t_o       = time.time() 
    model,__  = uc_Co.uc(instance,option='Check',SB_Uu=SB_Uux,No_SB_Uu=No_SB_Uux,V=Vvx,W=Wwx,delta=deltax,
                         nameins=insid,mode='Tight',scope=scope)
    sol_check = Solution(model=model,nameins=insid,env=ambiente,executable=executable,gap=gap,timelimit=timefull,
                         tee=False,tofiles=False,exportLP=False,option='Check',scope=scope,dual=dual)
    z_check, g_check = sol_check.solve_problem()
    t_check          = time.time() - t_o
    print(option,': t_check= ',round(t_check,1),'z_check= ',round(z_check,4),'g_check= ',round(g_check,8))
    # SB_Uu, No_SB_Uu, __, Vv, Ww, delta = sol_check.select_binary_support_Uu('g_check')        
    return z_check


def reduced_costs(model, No_SB_Uu):
    """Costos reducidos de las Uu no fijadas, ordenados de menor a mayor.

    Devuelve tuplas (indice, costo_reducido, g, t). El mismo bloque estaba copiado
    literalmente en LBC4 y en Kernel Search.
    """
    rc = [(i, model.rc[model.u[f[0]+1, f[1]+1]], f[0], f[1]) for i, f in enumerate(No_SB_Uu)]
    rc.sort(key=lambda tup: tup[1], reverse=False)
    return rc

## ------------------------------------- LOCAL BRANCHING (LBC1-LBC4) ----------------------------------
## Los cuatro metodos de local branching compartian el mismo controlador, copiado cuatro veces
## (626 lineas, 57% del archivo). Solo diferian en dos banderas y en el preambulo de costos
## reducidos de LBC4; la diferencia algoritmica real vive en uc_Co.uc(), que ramifica por 'option'.
##
##   LBC1  soft-fixing + lista restringida de candidatos (Harjunkoski)
##   LBC2  version entera, sin soft-fixing
##   LBC3  todas las variables "U=0" dentro del corte
##   LBC4  soft-fixing + lista restringida por costo reducido
def run_local_branching(tag, softfix_after_solve, use_reduced_costs=False):
    """Ejecuta un metodo de local branching y devuelve (z, t, g, x_incumbent).

    tag                            nombre del metodo; se pasa tal cual como 'option' a uc_Co.uc().
    softfix_after_solve            valor que toma 'softfix' despues del primer solve (LBC1/LBC4: True).
    use_reduced_costs              LBC4: resuelve un RC previo y usa los candidatos de costo
                                   reducido negativo como lower_Pmin_Uu.
    """
    print('\n' + tag + ' starts')
    t_o            = time.time()
    Vv             = deepcopy(Vv3)
    Ww             = deepcopy(Ww3)
    delta          = deepcopy(delta3)
    SB_Uu          = deepcopy(SB_Uu3)
    No_SB_Uu       = deepcopy(No_SB_Uu3)
    lower_Pmin_Uu  = deepcopy(lower_Pmin_Uu3)
    t_net          = timefull - t_hard3
    t_res          = timefull - t_hard3
    cutoff         = e
    bestUB         = e
    diversify      = False
    first          = True
    softfix        = False
    rhs            = e                     ## Arrancamos con una vecindad gigante
    n_iter         = 1
    z              = e
    g              = e
    x_             = [SB_Uu, No_SB_Uu, lower_Pmin_Uu]
    x_incumbent    = [SB_Uu, No_SB_Uu, Vv, Ww, delta, lower_Pmin_Uu]
    rightbranches  = []
    leftbranch     = []
    result_iter    = [(t_hard3, z_hard3)]
    char           = ''

    if use_reduced_costs:
        ## Costos reducidos: candidatos con rc <= 0 sustituyen a lower_Pmin_Uu
        model, __ = uc_Co.uc(instance,option='RC',SB_Uu=x_incumbent[0],No_SB_Uu=x_incumbent[1],V=x_incumbent[2],W=x_incumbent[3],delta=x_incumbent[4],
                             nameins=insid,mode='Tight',scope=scope)
        sol_rc    = Solution(model=model,nameins=insid,env=ambiente,executable=executable,gap=gap,timelimit=t_net,
                             emphasize=emphasizeHEUR,symmetry=symmetryHEUR,lbheur=lbheurHEUR,strategy=strategyHEUR,
                             tee=False,tofiles=False,exportLP=False,rc=True,option='RC',scope=scope)
        z_rc, g_rc = sol_rc.solve_problem()
        print('lb4: z_rc= ', round(z_rc,4))
        rc = reduced_costs(model, No_SB_Uu)
        lower_Pmin_Uu = deepcopy([(f[2],f[3]) for f in rc if f[1] <= 0])

    while True:
        if (n_iter == iterstop) or (time.time() - t_o >= t_net):
            break
        char = ''

        timeres1 = min(t_res, timeconst)

        if rhs < e:
            leftbranch = [[x_[0],x_[1],x_[2],rhs]]
        if first:
            timeres1 = 100

        model, __ = uc_Co.uc(instance,option=tag,SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,lower_Pmin_Uu=lower_Pmin_Uu,V=Vv,W=Ww,delta=delta,
                             percent_soft=90,k=rhs,nameins=insid,mode='Tight',scope=scope,
                             rightbranches=rightbranches,leftbranch=leftbranch,softfix=softfix,)
        sol       = Solution(model=model,env=ambiente,executable=executable,nameins=insid,letter=util.getLetter(n_iter-1),
                             gap=gap,cutoff=cutoff,timelimit=timeres1,emphasize=emphasizeHEUR,symmetry=symmetryHEUR,
                             lbheur=lbheurHEUR,strategy=strategyHEUR,
                             tee=False,tofiles=False,option=tag,scope=scope)
        z, g      = sol.solve_problem()
        softfix   = softfix_after_solve

        rightbranches = util.delete_tabu(rightbranches)

        if sol.optimal:
            if rhs >= e:
                print('Optimal Solution :-)')
                print('<°|--< iter:'+str(n_iter)+' t_'+tag+'= ',round(time.time()-t_o+t_hard3,1),'z_'+tag+'= ',round(z,1),char,'g_'+tag+'= ',round(g,8) )
                bestUB        = z
                SB_Uu, No_SB_Uu, __, Vv, Ww, delta = sol.select_binary_support_Uu(tag)
                lower_Pmin_Uu = sol.update_lower_Pmin_Uu(lower_Pmin_Uu, tag)
                x_incumbent   = [SB_Uu,No_SB_Uu,Vv,Ww,delta,lower_Pmin_Uu]
                g             = util.igap(lb_best, z)
                char          = '*+*+*'
                break
            rightbranches.append([x_[0],x_[1],x_[2],rhs])   ## SB_Uu,No_SB_Uu,lower_Pmin_Uu,k
            leftbranch    = []
            diversify     = False
            first         = False
            cutoff        = z          ## era 'cuttoff' (typo): la cota superior nunca se actualizaba
            rhs           = k
            SB_Uu, No_SB_Uu, __, Vv, Ww, delta = sol.select_binary_support_Uu(tag)
            lower_Pmin_Uu = sol.update_lower_Pmin_Uu(lower_Pmin_Uu, tag)
            x_            = [SB_Uu, No_SB_Uu, lower_Pmin_Uu]

        if sol.infeasib:
            if rhs >= e:
                break
            rightbranches.append([x_[0],x_[1],x_[2],rhs])   ## SB_Uu,No_SB_Uu,lower_Pmin_Uu
            leftbranch = []
            if diversify:
                cutoff = e
                first  = True
            rhs = rhs + ceil(k/2)
            print('Infeasible problem: k = k+[k/2]=', rhs)
            diversify = True

        if sol.timeover:
            if rhs < e:
                leftbranch = []
                if not first:
                    rightbranches.append([x_[0],x_[1],x_[2],0])   ## Δ(x_,x) ≥ 1 restriccion tabu

            gap_iter = abs((z - bestUB) / bestUB) * 100         ## Porcentaje de mejora
            if z < bestUB and gap_iter > gap:                   ## Actualizamos la solucion
                bestUB      = z
                x_incumbent = [SB_Uu,No_SB_Uu,Vv,Ww,delta,lower_Pmin_Uu]
                g           = util.igap(lb_best, z)
                char        = '***'
            else:
                diversify   = False
            first         = False
            cutoff        = z
            rhs           = k
            SB_Uu, No_SB_Uu, __, Vv, Ww, delta = sol.select_binary_support_Uu(tag)
            lower_Pmin_Uu = sol.update_lower_Pmin_Uu(lower_Pmin_Uu, tag)
            x_            = [SB_Uu, No_SB_Uu, lower_Pmin_Uu]

        if sol.nosoluti:
            if diversify:
                leftbranch = []
                rightbranches.append([x_[0],x_[1],x_[2],0])   ## Δ(x_,x) ≥ 1 restriccion tabu
                first      = True
                cutoff     = e
                rhs        = rhs + ceil(k/2)
                print('No solution found + diversify: k = k+[k/2]=', rhs)
            else:
                leftbranch = []
                rhs        = rhs - ceil(k/2)
                print('No solution found: k = k-[k/2]=', rhs)
            diversify = True

        result_iter.append((round(time.time() - t_o + t_hard3,1), z))

        print('<°|--< iter:'+str(n_iter)+' t_'+tag+'= ',round(time.time()-t_o+t_hard3,1),'z_'+tag+'= ',round(z,1),char,'g_'+tag+'= ',round(g,8) )
        print('\t')

        t_res = t_net - time.time() + t_o
        print(tag+':','remaining time:',t_res)

        del sol, model
        gc.collect()
        n_iter = n_iter + 1

    t = time.time() - t_o + t_hard3
    z = bestUB
    ## Rescate del gap: dentro del ciclo cada iteracion hace 'z, g = sol.solve_problem()',
    ## asi que g queda con el gap del ULTIMO subproblema y no con el del incumbente que
    ## se reporta. Se recalcula aqui contra bestUB; si no hubo incumbente se respeta el
    ## centinela 'e' que marca "sin solucion".
    if z < e:
        g = util.igap(lb_best, z)
    print(tag+' results')
    for item in result_iter:
        print(item[0],',',item[1])
    print(tag+' end')

    checkSol('z_'+tag, z, x_incumbent[0],x_incumbent[1],x_incumbent[2],x_incumbent[3],x_incumbent[4], label=tag)
    return z, t, g, x_incumbent

if  Hard3:
    ## ----------------------------------------------- RECOVERED SOLUTION ---------------------------------------------
    ## Load LR and Hard3 storaged solutions
    if path.exists('solHard3_a_'+insid+'.csv') == True and path.exists('solHard3_b_'+insid+'.csv') == True:
        t_lp,z_lp,t_hard3,z_hard3,SB_Uu3,No_SB_Uu3,lower_Pmin_Uu3,Vv3,Ww3,delta3 = util.loadSolution('Hard3',insid) 
        print('Recovered solution ---> ','z_hard3= ',round(z_hard3,1))
        print('Recovered solution ---> ','t_hard3= ',round(t_hard3,1))
        z_hard3 = checkSol('Hard3 (recovered)',z_hard3,SB_Uu3,No_SB_Uu3,Vv3,Ww3,delta3,label='hard3(rec)') ## Check feasibility
        g_hard3 = util.igap(z_lp,z_hard3) 
        lb_best = max(z_lp,lb_best)
    
    ## ----------------------------------------------- LINEAR RELAXATION ---------------------------------------------
    ## Relax as LP and solve it  
    ## lpmethod=Barrier (4)0=Automatic; 1,2= Primal and dual simplex; 3=Sifting; 4=Barrier, 5=Concurrent (Dual,Barrier, and Primal in opportunistic parallel mode; Dual and Barrier in deterministic parallel mode)
    else:
        t_o        = time.time() 
        model,__   = uc_Co.uc(instance,option='LR',nameins=insid,mode='Tight',scope=scope)
        sol_lp     = Solution(model=model,env=ambiente,executable=executable,nameins=insid,gap=gap,timelimit=timelp,lpmethod=0,
                              tee=False,tofiles=False,exportLP=False,option='LR',scope=scope)
        z_lp, g_lp = sol_lp.solve_problem() 
        t_lp       = time.time() - t_o
        print('t_lp= ',round(t_lp,1))
        print('z_lp= ',round(z_lp,1))
        
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
                            nameins=insid,mode='Tight',scope=scope)
        sol_hard3 = Solution(model=model,env=ambiente,executable=executable,nameins=insid,gap=gap,timelimit=timeconst,
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
        checkSol('Hard3',z_hard3,SB_Uu3,No_SB_Uu3,Vv3,Ww3,delta3,label='hard3') ## Check feasibility
        print('t_hard3= ',round(t_hard3,1))
        print('z_hard3= ',round(z_hard3,1))
        print('g_hard3= ',round(g_hard3,8))
        del sol_hard3
        gc.collect()
        util.saveSolution(t_lp,z_lp,t_hard3,z_hard3,SB_Uu3,No_SB_Uu3,lower_Pmin_Uu3,Vv3,Ww3,delta3,'Hard3',insid)
      
    ## ------------------------------------- HARJUNKOSKI ---------------------------------------------
    ## HARJUNKOSKI's rule solution and solve the sub-MILP. (Require run the LP)
if  Harjk:    
    t_o       = time.time()
    model,__  = uc_Co.uc(instance,option='Harjk',SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,lower_Pmin_Uu=lower_Pmin_Uu,
                         nameins=insid,mode='Tight',scope=scope)
    sol_harjk = Solution(model=model,env=ambiente,executable=executable,nameins=insid,gap=gap,timelimit=timeconst,
                        emphasize=emphasizeHEUR,symmetry=symmetryHEUR,lbheur=lbheurHEUR,strategy=strategyHEUR,
                        tee=False,tofiles=False,option='Harjk',scope=scope)     
    try:
        z_harjk, g_harjk = sol_harjk.solve_problem()
        t_harjk  = time.time() - t_o + t_lp   ## <<< --- t_harjk ** INCLUYE EL TIEMPO DE LP **
        g_harjk  = util.igap(lb_best,z_harjk)         
        SB_Uujk, No_SB_Uujk, __, Vvjk, Wwjk, deltajk = sol_harjk.select_binary_support_Uu('Harjk')    
        checkSol('Harjk',z_harjk,SB_Uujk,No_SB_Uujk,Vvjk,Wwjk,deltajk,label='harjk') ## Check feasibility
        del SB_Uujk,No_SB_Uujk,Vvjk,Wwjk,deltajk
    except Exception as err:
        print('>>> No solution Harjk:', repr(err))
    print('t_harjk= ',round(t_harjk,1))
    print('z_harjk= ',round(z_harjk,1))
    print('g_harjk= ',round(g_harjk,8))
    del sol_harjk
    gc.collect()

## ---------------------------------------- MILP2 -----------------------------------------------------
## Solve as a MILP2 from a initial solution (MILP2 + Hard3)
if  MILP2: 
    print('\nMILP2 starts') 
    t_o      = time.time()
    t_res    = timefull - t_hard3
    model,__ = uc_Co.uc(instance,option='Milp2',SB_Uu=SB_Uu3,No_SB_Uu=No_SB_Uu3,V=Vv3,W=Ww3,delta=delta3,
                        nameins=insid,mode='Tight',scope=scope)
    sol_milp2 = Solution(model=model,nameins=insid,env=ambiente,executable=executable,
                        emphasize=emphasizeHEUR,symmetry=symmetryHEUR,lbheur=lbheurHEUR,strategy=strategyHEUR,
                        gap=gap,timelimit=t_res,tee=False,tofiles=False,
                        exportLP=False,option='Milp2',scope=scope)
    z_milp2, g_milp2 = sol_milp2.solve_problem()
    t_milp2          = time.time() - t_o + t_hard3
        
    ## Actualizamos el tiempo de las heurísticas al que ocupó el MILP (si es que encontró un óptimo o terminó por tiempo)
    #timefull = t_milp2
    try:
        lb_milp2  = sol_milp2.lower_bound
    except Exception as err:
        temp = 0 #print(err)
    print('t_milp2= ' ,round(t_milp2, 1))
    print('z_milp2= ' ,round(z_milp2, 1))
    print('g_milp2= ' ,round(g_milp2, 8))
    print('lb_milp2= ',round(lb_milp2,8))

## --------------------------------------- LOCAL BRANCHING 1-4 ----------------------------------------
## LBC1 continua con soft-fixing y lista restringida de candidatos (Harjunkoski).
if  lbc1:
    z_lbc1, t_lbc1, g_lbc1, x_incumbent = run_local_branching(
        'lbc1', softfix_after_solve=True)


## LBC2 version binaria, sin soft-fixing, usando candidatos P_min.
if  lbc2:
    z_lbc2, t_lbc2, g_lbc2, x_incumbent = run_local_branching(
        'lbc2', softfix_after_solve=False)


## LBC3 version continua, sin soft-fixing y sin candidatos P_min.
if  lbc3:
    z_lbc3, t_lbc3, g_lbc3, x_incumbent = run_local_branching(
        'lbc3', softfix_after_solve=False)


## LBC4 continua con soft-fixing y lista restringida por costo reducido.
if  lbc4:
    z_lbc4, t_lbc4, g_lbc4, x_incumbent = run_local_branching(
        'lbc4', softfix_after_solve=True,  use_reduced_costs=True)

## Use relax the integrality variable Uu.
if  KS:
    print('\nstarts KS')
    Vv          = deepcopy(Vv3)
    Ww          = deepcopy(Ww3)
    delta       = deepcopy(delta3)
    SB_Uu       = deepcopy(SB_Uu3)
    No_SB_Uu    = deepcopy(No_SB_Uu3)
    saved       = [SB_Uu,No_SB_Uu,Vv,Ww,delta]

    t_o         = time.time() 
    incumbent   =  z_hard3
    cutoff      =  z_hard3 # e 
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
                                 nameins=insid,mode='Tight',scope=scope)
            sol_rc    = Solution(model=model,nameins=insid,env=ambiente,executable=executable,gap=gap,timelimit=timefull,
                                emphasize=emphasizeHEUR,symmetry=symmetryHEUR,lbheur=lbheurHEUR,strategy=strategyHEUR,
                                tee=False,tofiles=False,exportLP=False,rc=True,option='RC',scope=scope)
            z_rc,g_rc = sol_rc.solve_problem() 
            t_rc      = time.time() - t_1
            print('KS t_rc= ',round(t_rc,1),'z_rc= ',round(z_rc,4))      
            
            ## ----------------------------- SECOND PHASE ----------------------------------------------
            ##  Defining buckets 
            rc = reduced_costs(model, No_SB_Uu)   ## ordenados por costo reducido ascendente
            
            ##  Definimos el número de buckets 
            n = floor(1 + 3.322 * log(len(No_SB_Uu)))  ## Sturges rule  log=lognatural
            print('KS Number of buckets n =', n)    
            len_i  = ceil(len(No_SB_Uu) / n)
            pos_i  = 0
            k_     = [0]    
            for i in range(len_i,len(No_SB_Uu),len_i+1):
                k_.append( i )
            k_[-1] = len(No_SB_Uu)
            #print( k_ )
            
            cutoff      = incumbent # e !!!
            iter_bk     = 0
            ## n viene de la regla de Sturges, pero el numero de buckets que realmente se
            ## construyeron es len(k_)-1 y puede ser menor: para 62 variables Sturges da n=14
            ## mientras que k_ solo tiene 10 fronteras, y el bucle desbordaba k_[iter_bk+1]
            ## con IndexError. Solo ocurria en instancias chicas; con ~500 variables ambos
            ## numeros coinciden, por eso las corridas grandes nunca lo vieron.
            ## Tampoco se reutiliza el nombre 'iterstop', que es un parametro global de config.con.
            ks_iterstop = min(n - 2, len(k_) - 1)
            char        = ''
            kernel      = deepcopy(SB_Uu)
            
            ## Recontabilizamos el tiempo
            t_res               = max(0,( timefull - t_hard3) - (time.time() - t_o))
            timeconst           = t_res / n
            max_without_improve = 7   ## cambio 22 de enero 2023
            without_improve     = 0    ## cambio 22 de enero 2023
            last_z_ks           = 0
            while True: 
                t_res = max(0,( timefull - t_hard3 ) - (time.time() - t_o))
                if iter_bk >= ks_iterstop or t_res <= 0 or without_improve > max_without_improve:
                    print('KS Salí ciclo interno')
                    break

                timeconst1  = min(t_res,timeconst)      
                bucket      = rc[k_[iter_bk]:k_[iter_bk + 1]] 
                print('bucket',util.getLetter(iter),'[',k_[iter_bk],':',k_[iter_bk + 1],']' )      
                
                try:
                    ##  Resolvemos el kernel con cada uno de los buckets
                    model,__   = uc_Co.uc(instance,option='KS',kernel=kernel,bucket=bucket,nameins=insid,mode='Tight',scope=scope)
                    sol_ks     = Solution(model=model,env=ambiente,executable=executable,nameins=insid,letter=util.getLetter(iter),gap=gap,cutoff=cutoff,timelimit=timeconst1,
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
                
                    ######################################################### cambio 22 de enero 2023
                    if z_ks == last_z_ks:
                        without_improve=without_improve+1
                    else:
                        print(without_improve)
                        without_improve=0
                    last_z_ks = z_ks
                    ######################################################### cambio 22 de enero 2023
                
                except Exception as err:
                    print('>>> No solution found:', repr(err))
                    result_iter.append((round(time.time()-t_o+t_hard3,1), e))
                finally:    
                    iter_bk = iter_bk + 1
                    
                print('\t')       
                    
                t_res = max(0,( timefull - t_hard3 ) - (time.time() - t_o))
                print('KS ','tiempo restante:',util.trunc(t_res,1))
                
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
    ## Mismo rescate que en local branching: cada bucket sobrescribe (z_ks,g_ks) con el
    ## retorno de solve_problem(), de modo que un bucket sin solucion dejaba g_ks=1e+75
    ## junto a un z_ks bueno en la fila de stat.csv.
    if z_ks < e:
        g_ks = util.igap(lb_best, z_ks)
    print('KS results')
    for item in result_iter:
        print(item[0],',',item[1])
    print('KS end')
    
    checkSol('z_ks',z_ks,SB_Uu,No_SB_Uu,Vv,Ww,delta,label='ks') ## Check feasibility (KS)


## ---------------------------------------- MILP -----------------------------------------------------
## Solve as a MILP
if  MILP:  
    try:
        print('\nMILP starts')
        #fpheurMILP   = 1     ## Do not generate flow path cuts=-1 ; Automatic=0(CPLEX choose); moderately =1; aggressively=2
        #rinsheurMILP = 50    ## Automatic=0 (CPLEX choose); None: do not apply RINS heuristic=-1;  Frequency to apply RINS heuristic=Any positive integer 
        t_o      = time.time() 
        model,__ = uc_Co.uc(instance,option='Milp',nameins=insid,mode='Tight',scope=scope)
        sol_milp = Solution(model=model,nameins=insid,env=ambiente,executable=executable,
                            gap=gap,timelimit=timefull,tee=False,tofiles=False,strategy=strategyMILP,                                         
                            exportLP=False,option='Milp',scope=scope)
                            # emphasize=emphasizeMILP,symmetry=symmetryMILP,lbheur=lbheurMILP,
                            # dive=diveMILP,heuristicfreq=heuristicfreqMILP,numerical=numericalMILP,
                            # tolfeasibility=tolfeasibilityMILP,toloptimality=toloptimalityMILP,   
                            # fpheur=fpheurMILP, rinsheur=rinsheurMILP,  
                            
        eff_emphasizeMILP = sol_milp.emphasize   ## lo que de verdad recibe CPLEX
        eff_symmetryMILP  = sol_milp.symmetry
        eff_strategyMILP  = sol_milp.strategy
        eff_lbheurMILP    = sol_milp.lbheur

        z_milp, g_milp = sol_milp.solve_problem()
        t_milp         = time.time() - t_o
        try:
            lb_milp  = sol_milp.lower_bound
        except Exception as err:
            temp = 0 #print(err)
            
        lb_best  = max(0,lb_milp)
        g_milp   = util.igap(lb_best,z_milp)
    except Exception as err:
        print('!!! Error, something went wrong in MILP:', repr(err))
    print('t_milp=  ',round(t_milp,1))
    print('z_milp=  ',round(z_milp,1))
    print('g_milp=  ',round(g_milp,8))
    print('lb_milp= ',round(lb_milp,8))

    ## PENDIENTES         
    # \todo{Exportar los Costos reducidos ordenados de LR y comparar contra los lower_Pmin_Uu, se esperan coincidencias}

    ## PRUEBAS                
    # \todo{probar estadísticamente que SI conviene incluir los intentos de asignación en las variables soft-fix }
    # \todo{Probar experimentalmente que fijar otras variables enteras V,W,DELTA no impacta mucho en la solución}         
    # \todo{Probar empiricamente tamaños del n_kernel (!!! al parecer influye mucho en el tiempo de búsqueda)} 

    ## IDEAS        
    # \todo{Hacer un Tabu search con las LBC}
    # \todo{Un KS con buckets de tamaños no iguales usando optimal binning}       
    # \todo{APROVECHAR las infactibilidades de KS para encontrar cotas inferiores}  
    # \todo{Incluir restricciones de generadores hidro}          
    # \todo{Un KS relajando y fijando grupos de variables a manera de buckets en generadores agrupados geogràficamente}          
    # \todo{Probar modificar el tamaño de las variables soft-fix de 90% a: 95% y 85%}
    # \todo{Hacer un VNS o un VND con movimientos definidos con las LBC}
    # \todo{Probar configuración enfasis feasibility vs optimality en el Solver )} 

    ## DESCARTES                    
    # \todo{Probar cambiar el valor de k en nuevas iteraciones con una búsqueda local (un LBC completo de A.Lodi)}   
    # \todo{Un movimiento en la búsqueda local puede ser cambiar la asignación del costo de arranque en un periodo adelante o atras para algunos generadores} 
    # \todo{Podrian fijarse todas las variables (u,v,w y delta) relacionadas con los generadores que se escogen para ser fijados}
    # \todo{Podríamos usar reglas parecidas al paper de Todosijevic para fijar V,W a partir de Uu}
    # \todo{Calcular el tamaño del slack del subset BS (Soporte binario)}
    # \todo{Agregar must-run} 
    
    ## TERMINADAS            
    # \todo{Curar instancias Morales y Knueven (cambiar limites pegados y agregar piecewise cost)}   
    # \todo{probar iniciar el solver solo con la solución inicial del constructivo Hard3}
    # \todo{Encontrar la primer solución factible del CPLEX}
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
    # Se usará en un futuro para saber que restriccciones están activas
    # SB_Uu, No_SB_Uu, __, Vv, Ww, delta = sol_milp.select_binary_support_Uu('Milp0') 
    # model,__  = uc_Co.uc(instance,option='FixSol',SB_Uu=SB_Uu,No_SB_Uu=No_SB_Uu,V=Vv,W=Ww,delta=delta,
    #                      nameins=insid,mode='Tight',scope=scope)
    # sol_fix   = Solution(model=model,env=ambiente,executable=executable,nameins=insid,gap=gap,timelimit=timeconst,
    #                       tee=False,tofiles=False,exportLP=False,option='FixSol',scope=scope,dual=True)
    # z_fix, g_fix = sol_fix.solve_problem() 
    # print('z_fix= ',round(z_fix,4))
    
    # for t in model.T:
    #     print(model.dual[ model.demand_rule65[t] ],model.dual[ model.demand_rule67[t] ])


    
## NO OLVIDES COMENTAR TUS PRUEBAS ¸.·´¯`·.´¯`·.¸¸.·´¯`·.¸><(((º>
comment    = 'Pruebas TC&UC'

## --------------------------------- RESULTS -------------------------------------------
## Append a list as new line to an old csv file using as log, the first line of the file as shown.

## Las columnas emphasizeMILP/symmetryMILP/strategyMILP/lbheurMILP registran los
## parametros EFECTIVOS de SM1 (leidos del objeto Solution), no los de config.con.
## ambiente,localtime,nameins,T,G,gap,timeconst,timefull,z_lp,z_milp,z_milp2,z_harjk,z_hard3,z_lbc1,z_lbc2,z_lbc3,z_lbc4,z_ks,z_,t_lp,t_milp,t_milp2,t_harjk,t_hard3,t_lbc1,t_lbc2,t_lbc3,t_lbc4,t_ks,t_,lb_milp,g_milp,g_milp2,g_harjk,g_hard3,g_lbc1,g_lbc2,g_lbc3,g_lbc4,g_ks,g_,lb_milp2,k,emphasizeMILP,symmetryMILP,strategyMILP,lbheurMILP,emphasizeHEUR,symmetryHEUR,strategyHEUR,lbheurHEUR,comment
row = [ambiente,localtime,nameins,len(instance[1]),len(instance[0]),gap,timeconst_original,timefull,
    round(z_lp,   1),round(z_milp,1),round(z_milp2,1),round(z_harjk,1),round(z_hard3,1),round(z_lbc1,1),round(z_lbc2,1),round(z_lbc3,1),round(z_lbc4,1),round(z_ks,1),round(z_,1),
    round(t_lp,   1),round(t_milp,1),round(t_milp2,1),round(t_harjk,1),round(t_hard3,1),round(t_lbc1,1),round(t_lbc2,1),round(t_lbc3,1),round(t_lbc4,1),round(t_ks,1),round(t_,1),
    round(lb_milp,1),round(g_milp,8),round(g_milp2,8),round(g_harjk,8),round(g_hard3,8),round(g_lbc1,8),round(g_lbc2,8),round(g_lbc3,8),round(g_lbc4,8),round(g_ks,8),round(g_,8),
                                     round(lb_milp2,1),k,eff_emphasizeMILP,eff_symmetryMILP,eff_strategyMILP,eff_lbheurMILP,emphasizeHEUR,symmetryHEUR,strategyHEUR,lbheurHEUR,comment] 
util.append_list_as_row('stat.csv',row)
message='terminé instancia ...´¯`·...·´¯`·.. ><(((º> '+nameins
print(localtime,message)

sys.exit()

