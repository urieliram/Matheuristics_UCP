## --------------------------------------------------------------------------------
## File: unit_commitment.py
## Developers: Uriel Iram Lezama Lope
## Purpose: Solve a Unit Commitment Problem
## Description: para ejecutar use: python3 main.py anjos.json thinkpad
##--------------------------------------------------------------------------------
# from   pyomo.opt import results
# from   pyomo.opt.results import solver
import pyomo.environ as pyo
from   pyomo.environ import *
from   pyomo.util.infeasible import log_infeasible_constraints
from   pyomo.opt import SolverStatus, TerminationCondition
import uc_Co

def solve(G1,T1,L,S,Piecewise,Pmax,Pmin,UT,DT,De,R,CR,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,fixShedu,relax,ambiente):  
            
    G = []
    T = []
    for g in range(1, G1+1):
        G.append(g)
    for t in range(1, T1+1):
        T.append(t)

    ## Aquí se pasa de una solución en arreglo "SOL" a una solución al diccionario "Shedule_dict"
    Shedule_dict = {}
    # for g in range(len(G)):
    #     for t in range(len(T)):
    #         Shedule_dict[g, t] = SOL[g][t]   
    # print("Shedule_dict")
    # print(Shedule_dict)

    ## Aqui se pasan de arreglos a diccionarios como los lee Pyomo
    Pmax_dict = dict(zip(G, Pmax))
    Pmin_dict = dict(zip(G, Pmin))
    TU_dict   = dict(zip(G, UT))
    TD_dict   = dict(zip(G, DT))
    De_dict   = dict(zip(T, De))
    R_dict    = dict(zip(T, R))
    CR_dict   = dict(zip(G, CR))
    u_0_dict  = dict(zip(G, u_0))
    U_dict    = dict(zip(G, U))
    D_dict    = dict(zip(G, D))
    U_dict    = dict(zip(G, U))
    SU_dict   = dict(zip(G, SU))
    SD_dict   = dict(zip(G, SD))
    RU_dict   = dict(zip(G, RU))
    RD_dict   = dict(zip(G, RD))
    pc_0_dict = dict(zip(G, pc_0))

    ## Create the Pyomo model
    model = uc_Co.uc(G,T,L,S,Piecewise,Pmax_dict,Pmin_dict,TU_dict,TD_dict,
                     De_dict,R_dict,CR_dict,u_0_dict,U_dict,D_dict,SU_dict,
                     SD_dict,RU_dict,RD_dict,pc_0_dict,mpc,Pb,C,Cs,Tmin,
                     fixShedu,relax,ambiente)
  
    ## Create the solver interface and solve the model
    # solver = pyo.SolverFactory('glpk')
    #solver = pyo.SolverFactory('cbc')
    #https://www.ibm.com/docs/en/icos/12.8.0.0?topic=parameters-relative-mip-gap-tolerance
    solver = pyo.SolverFactory('cplex')
    if ambiente == "thinkpad":
         solver = pyo.SolverFactory('cplex')
    if ambiente == "yalma":
        solver = pyo.SolverFactory('cplex', executable='/home/uriel/cplex1210/cplex/bin/x86-64_linux/cplex')
    solver.options['mip tolerances mipgap'] = 0.001  
    #solver.options['mip tolerances absmipgap'] = 200
    solver.options['timelimit'] = 300
    

    ## para mostrar una solución en un formato propio
    ## https://developers.google.com/optimization/routing/cvrp
    ## para editar un Lp en pyomo
    ## https://stackoverflow.com/questions/54312316/pyomo-model-lp-file-with-variable-values
    
    ## write LP file
    #model.write()             ## To write the model into a file using .nl format
    #filename = os.path.join(os.path.dirname(__file__), 'model.lp')
    #model.write(filename, io_options={'symbolic_solver_labels': True})
    #model.write(filename = str('model') + ".mps", io_options = {"symbolic_solver_labels":True})
    #print(solver.ExportModelAsLpFormat(False).replace('\\', '').replace(',_', ','), sep='\n')
  
    ## Envía el problema de optimización al solver
    res = solver.solve(model, tee=False) ## timelimit=10; tee=True(para ver log)
    
    try:
        pyo.assert_optimal_termination(res)
    except:
        print("An exception occurred")
        return None
        
    file = open("modeluc.txt", "w")
    file.write('z: %s \n' % (pyo.value(model.obj)))
    file.write('g, t,\t u,\t v,\t w, \t p \n')       

    for g in range(0, G1):
        file.write('%s, %s, \t %s \n' % (int(g), 0, u_0[g] ))

    for t in range(0, T1):
        for g in range(0, G1):
            file.write('%s, %s,\t %s,\t  %s,\t  %s,\t %s \n' %
                       (int(g), int(t), int(model.u[(g+1, t+1)].value),int(model.v[(g+1, t+1)].value),int(model.w[(g+1, t+1)].value), model.p[(g+1, t+1)].value))

    file.write('TIME,\t s \t sR \n')
    for t in range(1, T1+1):
        file.write('%s, \t%s,\t %s,\t \n' %
                   (int(t), model.sn[t].value, model.sR[t].value))

    # model.obj.pprint()     # Print the objetive function
    # model.demand.pprint()  # Print constraint
    # model.reserve.pprint()
    # model.display()        # Print the optimal solution     
    # z = pyo.value(model.obj)
    model.pprint(file)
    file.close()
    
    ##https://stackoverflow.com/questions/51044262/finding-out-reason-of-pyomo-model-infeasibility
    log_infeasible_constraints(model)

    ##https://pyomo.readthedocs.io/en/stable/working_models.html
    if (res.solver.status == SolverStatus.ok) and (res.solver.termination_condition == TerminationCondition.optimal):
        print ("this is feasible and optimal")
        return model
    elif res.solver.termination_condition == TerminationCondition.infeasible:
        print (">>> do something about it? or exit?")
        return None
    else:
        print ("something else is wrong",str(res.solver))  ## Something else is wrong
        return None
    

    
