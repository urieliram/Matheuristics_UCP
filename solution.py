import pyomo.environ as pyo
import outfiles
from   pyomo.util.infeasible import log_infeasible_constraints
from   pyomo.opt import SolverStatus, TerminationCondition

# import copy
# import pyomo as pyo
# from egret.models.unit_commitment import solve_unit_commitment
# from egret.model_library.unit_commitment.uc_model_generator import UCFormulation, generate_model
# from datetime import date
# from datetime import datetime
# from timeit import timeit
# from pyomo.core.base import piecewise
# from pyomo.core.base.boolean_var import ScalarBooleanVar
# from pyomo.util.infeasible import log_infeasible_constraints

class Solution:
    def __init__(self,model,nameins,env,gap,time,tee,tofile):
        self.model    = model
        self.nameins  = nameins  ## name of instance 
        self.env      = env      ## enviroment  
        self.tee      = tee      ## True = activate log of CPLEX
        self.gap      = gap      ## relative gap in CPLEX
        self.time     = time     ## max time in CPLEX
        self.tofile   = tofile   ## True = send to csv file the solution value of U,V,W,P,R 
        self.gg       = len(model.G)
        self.tt       = len(model.T)
       
    def getModel(self):
        return self.model
   
    def solve_problem(self):  
        ## Create the solver interface and solve the model
        # https://www.ibm.com/docs/en/icos/12.8.0.0?topic=parameters-relative-mip-gap-tolerance
        solver = pyo.SolverFactory('cplex') #'glpk', 'cbc'
        if self.env == "localPC":
            solver = pyo.SolverFactory('cplex')
        if self.env == "yalma": 
            solver = pyo.SolverFactory('cplex', executable='/home/uriel/cplex1210/cplex/bin/x86-64_linux/cplex')
        solver.options['mip tolerances mipgap'] = self.gap  
        #solver.options['mip tolerances absmipgap'] = 200
        solver.options['timelimit'] = self.time

        #https://www.ibm.com/docs/en/icos/12.8.0.0?topic=parameters-algorithm-continuous-linear-problems
        #solver.options['lpmethod'] = 1

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
        result = solver.solve(self.model, tee=self.tee) ## timelimit=10; tee=True(para ver log)
            
        try:
            pyo.assert_optimal_termination(result)
        except Exception as e:
            print("!!! An exception occurred")
            print(e)
                
        file = open("modeluc.dat", "w")
        file.write('z: %s \n' % (pyo.value(self.model.obj)))
        file.write('g, t,\t u,\t v,\t w, \t p \n')       

        #for g in range(0, len(G)):
        #    file.write('%s, %s, \t %s \n' % (int(g), 0, u_0[g] ))

        for t in range(0, self.tt):
            for g in range(0, self.gg):
                file.write('%s, %s,\t %s,\t  %s,\t  %s,\t %s \n' %
                (int(g), int(t), int(self.model.u[(g+1, t+1)].value),int(self.model.v[(g+1, t+1)].value),int(self.model.w[(g+1, t+1)].value), self.model.p[(g+1, t+1)].value))

        file.write('TIME,\t s \t sR \n')
        for t in range(1, self.tt+1):
            file.write('%s, \t%s,\t %s,\t \n' %
            (int(t), self.model.sn[t].value, self.model.sR[t].value))

        # model.obj.pprint()     # Print the objetive function
        # model.demand.pprint()  # Print constraint
        # model.reserve.pprint() # Print constraint
        # model.display()        # Print the optimal solution     
        # z = pyo.value(model.obj)

        #model.pprint(file)
        #file.close()

        ##https://pyomo.readthedocs.io/en/stable/working_models.html
        if (result.solver.status == SolverStatus.ok) and (result.solver.termination_condition == TerminationCondition.optimal):
            print ("This is feasible and optimal")
        elif result.solver.termination_condition == TerminationCondition.infeasible:
            ##https://stackoverflow.com/questions/51044262/finding-out-reason-of-pyomo-model-infeasibility
            log_infeasible_constraints(self.model)
            print (">>> infeasible solution, do something about it? or exit?")
        else:
            print ("something else is wrong",str(result.solver))  ## Something else is wrong

        if self.tofile == True:
            self.send_to_File()
            
        z_exact = self.model.obj.expr()
        return z_exact
    
    
      
    def send_to_File(self):       
        ## Inizialize variables making a empty-solution with all generators in cero
        Uu = [[0 for x in range(self.tt)] for y in range(self.gg)]
        V  = [[0 for x in range(self.tt)] for y in range(self.gg)]
        W  = [[0 for x in range(self.tt)] for y in range(self.gg)]
        P  = [[0 for x in range(self.tt)] for y in range(self.gg)]
        R  = [[0 for x in range(self.tt)] for y in range(self.gg)]
        ## ALMACENA SOLUCIÓN ENTERA
        for t in range(self.tt):
            for g in range(self.gg):
                Uu[g][t] = int(self.model.u[(g+1, t+1)].value)
                V [g][t] = int(self.model.v[(g+1, t+1)].value)
                W [g][t] = int(self.model.w[(g+1, t+1)].value)
                P [g][t] = int(self.model.p[(g+1, t+1)].value)
                R [g][t] = int(self.model.r[(g+1, t+1)].value)
                #print(g, t, (model.u[(g, t)].value), (model.v[(g, t)].value), (model.w[(g, t)].value), model.p[(g, t)].value)
        outfiles.sendtofilesolution(Uu,"U_" + self.nameins[0:5] + ".csv")
        outfiles.sendtofilesolution(V ,"V_" + self.nameins[0:5] + ".csv")
        outfiles.sendtofilesolution(W ,"W_" + self.nameins[0:5] + ".csv")
        outfiles.sendtofilesolution(P ,"P_" + self.nameins[0:5] + ".csv")
        outfiles.sendtofilesolution(R ,"R_" + self.nameins[0:5] + ".csv")
        return 0