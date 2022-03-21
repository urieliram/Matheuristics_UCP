from   ctypes import util
import os
import pyomo.environ as pyo
import util
from   pyomo.util.infeasible import log_infeasible_constraints
from   pyomo.opt import SolverStatus, TerminationCondition
import os

class Solution:
    def __init__(self,model,env,executable,nameins='model',gap=0.001,timelimit=300,tee=False,tofiles=False,lpmethod=0,
                 cutoff=1e+75,exportLP=False,exportFile=False):
        self.model      = model
        self.nameins    = nameins     ## name of instance 
        self.env        = env         ## enviroment  
        self.executable = executable  ## ruta donde encontramos el ejecutable CPLEX 
        self.tee        = tee         ## True = activate log of CPLEX
        self.gap        = gap         ## relative gap in CPLEX
        self.timelimit  = timelimit   ## max time in CPLEX
        self.tofiles    = tofiles     ## True = send to csv file the solution value of U,V,W,P,R 
        self.lpmethod   = lpmethod    ## 0=Automatic; 1,2= Primal and dual simplex; 3=Sifting; 4=Barrier, 5=Concurrent (Dual,Barrier, and Primal in opportunistic parallel mode; Dual and Barrier in deterministic parallel mode)
        self.cutoff     = cutoff      ## Agrega una cota superior factible, apara yudar a descartar nodos del árbol del B&B
        
        self.exportFile = exportFile  ## True si se exporta la solución a un formato .dat
        self.exportLP   = exportLP    ## True si se exporta el modelo a formato LP y MPS
        self.gg         = len(model.G)
        self.tt         = len(model.T)
       
    def getModel(self):
        return self.model
    def getUu(self):
        return self.Uu
    def getV(self):
        return self.V
    def getW(self):
        return self.W
    def getP(self):
        return self.P
    def getR(self):
        return self.R
   
    def solve_problem(self):  
        ## Create the solver interface and solve the model
        # https://www.ibm.com/docs/en/icos/12.8.0.0?topic=parameters-relative-mip-gap-tolerance
        solver = pyo.SolverFactory('cplex') #'glpk', 'cbc'
        if self.env == "localPC":
            solver = pyo.SolverFactory('cplex')
        if self.env == "yalma": 
            solver = pyo.SolverFactory('cplex', executable=self.executable)
            #solver = pyo.SolverFactory('cplex', executable='/home/uriel/cplex1210/cplex/bin/x86-64_linux/cplex')
        solver.options['mip tolerances mipgap'] = self.gap  
        solver.options['timelimit'] = self.timelimit        
        
        #https://www.ibm.com/docs/en/icos/20.1.0?topic=parameters-upper-cutoff
        if self.cutoff != 1e+75:
            solver.options['mip tolerances uppercutoff'] = self.cutoff
        
        #https://www.ibm.com/docs/en/icos/12.8.0.0?topic=parameters-algorithm-continuous-linear-problems
        solver.options['lpmethod'] = self.lpmethod 
        
        #solver.options['mip tolerances absmipgap'] = 200
        
        ## Boosting Pyomo
        solver.options['Threads'] = int((os.cpu_count() + os.cpu_count())/2)
        
        ## para mostrar una solución en un formato propio
        ## https://developers.google.com/optimization/routing/cvrp
        ## para editar un LP en pyomo
        ## https://stackoverflow.com/questions/54312316/pyomo-model-lp-file-with-variable-values
            
            
        ## write LP file
        if self.exportLP == True:
            self.model.write()             ## To write the model into a file using .nl format
            filename = os.path.join(os.path.dirname(__file__), self.model.name+'.lp')
            self.model.write(filename, io_options={'symbolic_solver_labels': True})
            self.model.write(filename = self.model.name+'.mps', io_options = {"symbolic_solver_labels":True})
            #print(solver.ExportModelAsLpFormat(False).replace('\\', '').replace(',_', ','), sep='\n')
        
        ## Envía el problema de optimización al solver
        result = solver.solve(self.model, tee=self.tee) ## timelimit=10; tee=True (para ver log)
        #result.write()
        
        try:
            pyo.assert_optimal_termination(result)
        except Exception as e:
            print("!!! An exception occurred")
            print(e)
                
        if self.exportFile == True:    
            file = open(self.nameins + '.dat', 'w')
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
                
            self.model.pprint(file)
            file.close()

        # model.obj.pprint()     # Print the objetive function
        # model.demand.pprint()  # Print constraint
        # model.reserve.pprint() # Print constraint
        # model.display()        # Print the optimal solution     
        # z = pyo.value(model.obj)

        ##https://pyomo.readthedocs.io/en/stable/working_models.html
        # maxIterations= 2
        if (result.solver.status == SolverStatus.ok) and (result.solver.termination_condition == TerminationCondition.optimal):
            aux=1+1
            #print ("This is feasible and optimal")            
        elif result.solver.termination_condition == TerminationCondition.infeasible:
            ##https://stackoverflow.com/questions/51044262/finding-out-reason-of-pyomo-model-infeasibility
            log_infeasible_constraints(self.model)
            print ("!!! Infeasible solution, do something about it, or exit.")
        else:
            print ("Something else is wrong",str(result.solver))  ## Something else is wrong

        ## Inizialize variables making a empty-solution with all generators in cero
        self.Uu = [[0 for x in range(self.tt)] for y in range(self.gg)]
        self.V  = [[0 for x in range(self.tt)] for y in range(self.gg)]
        self.W  = [[0 for x in range(self.tt)] for y in range(self.gg)]
        self.P  = [[0 for x in range(self.tt)] for y in range(self.gg)]
        self.R  = [[0 for x in range(self.tt)] for y in range(self.gg)]
        ## Almacena solución entera
        for t in range(self.tt):
            for g in range(self.gg):
                self.Uu[g][t] = round(self.model.u[(g+1, t+1)].value,1)
                self.V [g][t] = round(self.model.v[(g+1, t+1)].value,1)
                self.W [g][t] = round(self.model.w[(g+1, t+1)].value,1)
                self.P [g][t] = round(self.model.p[(g+1, t+1)].value,1)
                self.R [g][t] = round(self.model.r[(g+1, t+1)].value,1)
                
        if self.tofiles == True:
            self.send_to_File()
                       
        z_exact = self.model.obj.expr()
        return z_exact
    
      
    def send_to_File(self):     
        util.sendtofilesolution(self.Uu,"U_" + self.nameins + ".csv")
        util.sendtofilesolution(self.V ,"V_" + self.nameins + ".csv")
        util.sendtofilesolution(self.W ,"W_" + self.nameins + ".csv")
        util.sendtofilesolution(self.P ,"P_" + self.nameins + ".csv")
        util.sendtofilesolution(self.R ,"R_" + self.nameins + ".csv")
        return 0
    
    
    ## En esta función seleccionamos el conjunto de variables que quedarán en uno para ser fijadas posteriormente.
    def select_fixed_variables_U(self):    
        fixed_Uu    = []  
        No_fixed_Uu = []
        lower_Pmin  = []
        
        UuP = [[0 for i in range(self.tt)] for j in range(self.gg)]
        ## Almacena solución entera
        for t in range(self.tt):
            for g in range(self.gg):
                UuP[g][t] = self.P[g][t] * self.Uu[g][t]
                
                ## Aquí se enlistan los valores de 'u' que serán fijados.
                ## El criterio para fijar es el de Harjunkoski2020 de multiplicar potencia por valores de 'u' 
                ## y evaluar que sean mayores al límite operativo mínimo.
                if UuP[g][t] >= self.model.Pmin[g+1]:
                    fixed_Uu.append([g,t,1])
                else:
                    ## Vamos a guardar las variables que quedaron abajo del minimo pero diferentes de cero,
                    ## podriamos decir que este grupo de variables son intentos de asignación.
                    ## Este valor puede ser usado para definir el parámetro k en el LBC.                    
                    if (UuP[g][t] != 0):
                        lower_Pmin.append([g,t,1])
                    No_fixed_Uu.append([g,t,0])
                    
                ## aquellas unidades que quedan en cero o menos, son fijadas a cero, INTENTO INFACTIBLE... sorry :-(.
                #elif UuP[g][t] <= 0:               
                #    fix_Uu.append([g,t,0])                
        
        return fixed_Uu, No_fixed_Uu, lower_Pmin
    
    def count_U_no_int(self):   
        Uu_no_int = []
        aux  = 0
        aux2 = 0
        ## Almacena solución entera
        for t in range(self.tt):
            for g in range(self.gg):
                
                if self.Uu[g][t] != 1 and self.Uu[g][t] != 0:
                    Uu_no_int.append([g,t,self.Uu[g][t]])
                    aux = aux + 1
                    
                if self.Uu[g][t] == 1 or self.Uu[g][t] == 0:
                    aux2 = aux2 + 1
                    
        print("Number of U_no_int=", Uu_no_int,", n_Uu_no_int=",aux," , n_Uu_1_0=",aux2)   
        return len(Uu_no_int), aux, aux2
    
        
        
        return t_lp, t_lp, z_lp, z_lp 

            
        