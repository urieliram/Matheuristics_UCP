from   ctypes import util
from math import ceil
import os
import sys
import time
import pyomo.environ as pyo
import util
import numpy as np
from   pyomo.util.infeasible import log_infeasible_constraints
from   pyomo.opt import SolverStatus, TerminationCondition
import logging

class Solution:
    def __init__(self,model,env,executable,nameins='model',gap=0.0001,timelimit=300,tee=False,tofiles=False,lpmethod=0,
                 cutoff=1e+75,emphasize=1,exportLP=False,option=''):
        self.model      = model
        self.nameins    = nameins     ## name of instance 
        self.env        = env         ## enviroment  
        self.executable = executable  ## ruta donde encontramos el ejecutable CPLEX 
        self.tee        = tee         ## True = activate log of CPLEX
        self.gap        = gap         ## relative gap in CPLEX
        self.timelimit  = timelimit   ## max time in CPLEX
        self.tofiles    = tofiles     ## True = send to csv file the solution value of U,V,W,P,R exporta la solución a un formato .dat
        self.lpmethod   = lpmethod    ## 0=Automatic; 1,2= Primal and dual simplex; 3=Sifting; 4=Barrier, 5=Concurrent (Dual,Barrier, and Primal in opportunistic parallel mode; Dual and Barrier in deterministic parallel mode)
        self.cutoff     = cutoff      ## Agrega una cota superior factible, apara yudar a descartar nodos del árbol del B&B
        self.emphasize  = emphasize   ## Emphasize optimality=1(default);  feasibility=2.
        self.exportLP   = exportLP    ## True si se exporta el modelo a formato LP y MPS
        self.gg         = len(model.G)
        self.tt         = len(model.T)
        self.S          = model.S
        self.gap_       = 1e+75       ## relative gap calculated with #|bestbound-bestinteger|/(1e-10+|bestinteger|)
        self.fail       = False
        self.z_exact    = 1e+75
        self.option     = option
               
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
    def getSolverTime(self):
        return self.solvertime
   
    def solve_problem(self):  
                
        exist = os.path.exists(self.executable)   
        if exist:
            solver = pyo.SolverFactory('cplex',executable=self.executable) 
            ## executable='/home/uriel/cplex1210/cplex/bin/x86-64_linux/cplex'
        else:
            solver = pyo.SolverFactory('cplex')

        ## https://www.ibm.com/docs/en/icos/20.1.0?topic=parameters-upper-cutoff
        if self.cutoff != 1e+75:
            solver.options['mip tolerances uppercutoff'] = self.cutoff
        
        ## https://www.ibm.com/docs/en/icos/12.8.0.0?topic=parameters-algorithm-continuous-linear-problems
        ##https://www.ibm.com/docs/en/icos/12.8.0.0?topic=cplex-list-parameters
        solver.options['lpmethod'                      ] = self.lpmethod         
        solver.options['mip tolerances mipgap'         ] = self.gap  
        solver.options['timelimit'                     ] = self.timelimit 
        solver.options['emphasis mip'                  ] = self.emphasize
        
        ## para mostrar la solución en un formato propio
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
        
        t_o = time.time() 
        
        ## Envía el problema de optimización al solver
        if self.option=='Hard' or self.option=='lbc1' or self.option=='lbc2' or self.option=='Hard2':
            result = solver.solve(self.model,tee=self.tee,logfile='logfile'+self.option+self.nameins+'.log',warmstart=True)
        else:
            result = solver.solve(self.model,tee=self.tee,logfile='logfile'+self.option+self.nameins+'.log')
        #result.write()  
        self.solvertime = time.time() - t_o
                
        try:
            pyo.assert_optimal_termination(result)
        except Exception as e:
            print(e)
                            
        # model.obj.pprint()     # Print the objetive function
        # model.demand.pprint()  # Print constraint
        # model.reserve.pprint() # Print constraint
        # model.display()        # Print the optimal solution

        if (result.solver.status == SolverStatus.ok) and (result.solver.termination_condition == TerminationCondition.optimal):
            self.fail = False
            
        elif result.solver.termination_condition == TerminationCondition.infeasible:
            ##https://stackoverflow.com/questions/51044262/finding-out-reason-of-pyomo-model-infeasibility
            self.fail = True
            #print ("!!! Infeasible solution ... wait to unfeasible.log")            
            #log_infeasible_constraints(self.model,log_expression=True, log_variables=True)           
            #logging.basicConfig(filename='unfeasible.log', encoding='utf-8', level=logging.INFO)
            #sys.exit("!!! Unfortunately, the program has stopped.") 
        elif (result.solver.termination_condition == TerminationCondition.maxTimeLimit):
            print (">>> The maximum time limit has been reached.")
            self.fail = False

        else:
            print ("!!! Something else is wrong",str(result.solver)) 
            self.fail = True

        if self.fail == False:
            
            ## |bestbound-bestinteger|/(1e-10+|bestinteger|)
            __data = result.Problem._list
            LB = __data[0].lower_bound
            UB = __data[0].upper_bound
            self.gap_ = abs(LB - UB) /(1e-10 + abs(UB)) 
            
            ## Inizialize variables making a empty-solution with all generators in cero
            self.Uu     = [[0 for i in range(self.tt)] for j in range(self.gg)]
            self.V      = [[0 for i in range(self.tt)] for j in range(self.gg)]
            self.W      = [[0 for i in range(self.tt)] for j in range(self.gg)]
            self.P      = [[0 for i in range(self.tt)] for j in range(self.gg)]
            self.R      = [[0 for i in range(self.tt)] for j in range(self.gg)]            
            self.delta  = [[0 for i in range(self.tt)] for j in range(self.gg)]
                
            ## Tranformación especial para variable delta de (g,t,s) a (g,t) 
            for g in range(0, self.gg):
                for t in range(0, self.tt):
                    position = 0
                    for s in range(0, len(self.model.S[g+1])):
                        position = position + 1
                        if self.model.delta[(g+1,t+1,s+1)].value != None and self.model.delta[(g+1,t+1,s+1)].value == 1:
                            self.delta[g][t] = position
                            #self.delta[g][t] = self.delta[g][t] + self.model.delta[(g+1,t+1,s+1)].value
                
            ## Almacena solución entera
            for t in range(self.tt):
                for g in range(self.gg):
                    self.Uu[g][t] = round(self.model.u[(g+1, t+1)].value,5)
                    self.V [g][t] = round(self.model.v[(g+1, t+1)].value,5)
                    self.W [g][t] = round(self.model.w[(g+1, t+1)].value,5)
                    self.P [g][t] = round(self.model.p[(g+1, t+1)].value,5)
                    self.R [g][t] = round(self.model.r[(g+1, t+1)].value,5)
                        
            if self.tofiles == True:
                self.send_to_File()            
                
            ## Imprimimos las posibles variables 'u' que podrían no sean enteras.
            self.count_U_no_int()    
                            
            self.z_exact = self.model.obj.expr()   
            
        return self.z_exact, self.gap_
    
          
    def send_to_File(self,letra=""):     
        util.sendtofilesolution(self.Uu    ,"U_"   + self.nameins + letra +".csv")
        util.sendtofilesolution(self.V     ,"V_"   + self.nameins + letra +".csv")
        util.sendtofilesolution(self.W     ,"W_"   + self.nameins + letra +".csv")
        util.sendtofilesolution(self.P     ,"P_"   + self.nameins + letra +".csv")
        util.sendtofilesolution(self.R     ,"R_"   + self.nameins + letra +".csv")
        util.sendtofilesolution(self.delta ,"del_" + self.nameins + letra +".csv")
        
        file = open(self.nameins + letra + '.dat', 'w')
        file.write('z:%s\n' % (pyo.value(self.model.obj)))
        file.write('g,t,u,v,w,p\n') 
            
        for g in range(0, self.gg):
            for t in range(0, self.tt):
                file.write('%s,%s,%s,%s,%s,%s\n' %
                ( int(t), int(g), ceil(self.model.u[(g+1, t+1)].value),ceil(self.model.v[(g+1, t+1)].value),ceil(self.model.w[(g+1, t+1)].value), util.trunc(self.model.p[(g+1, t+1)].value,4)))

        # file.write('TIME,s,sR\n')
        # for t in range(1, self.tt+1):
        #     file.write('%s,%s,%s,\n' %
        #     (int(t), self.model.sn[t].value, self.model.sR[t].value))
                
        self.model.pprint(file)
        file.close()
                
        return 0
    
    
    ## En esta función seleccionamos el conjunto de variables Uu que quedarán en uno para ser fijadas posteriormente.
    def select_binary_support_Uu(self,optional=''):
        SB_Uu         = []  
        No_SB_Uu      = []
        lower_Pmin_Uu = []
        
        ## Almacena la solución entera
        UuxP = [[0 for i in range(self.tt)] for j in range(self.gg)]
        
        ## [Harjunkoski2021]
        if optional == 'LR':
            for t in range(self.tt):
                for g in range(self.gg):
                    UuxP[g][t] = self.P[g][t] * self.Uu[g][t]
                    
                    ## Aquí se enlistan los valores de 'u' que serán fijados.
                    ## El criterio para fijar es el propuesto por [Harjunkoski2021] de multiplicar la potencia 
                    ## por valores de 'u' y evaluar que sean mayores al límite operativo mínimo.
                    if UuxP[g][t] >= self.model.Pmin[g+1]:
                        SB_Uu.append([g,t])
                    else:
                        ## Vamos a guardar las variables que quedaron abajo del minimo pero diferentes de cero,
                        ## podriamos decir que este grupo de variables son <intentos de asignación>.
                        ## >>> Éste valor puede ser usado para definir el parámetro k en el LBC. <<<                   
                        if (UuxP[g][t] != 0):
                            lower_Pmin_Uu.append([g,t])
                        No_SB_Uu.append([g,t])  
                        
        if optional != 'LR':
            for t in range(self.tt):
                for g in range(self.gg):
                    if self.Uu[g][t] == 1:
                        SB_Uu.append([g,t])
                    if self.Uu[g][t] == 0:
                        No_SB_Uu.append([g,t])
                        
                    
        suma = len(SB_Uu) + len(No_SB_Uu)
        print('|Uu       |SB_Uu      |No_SB_Uu  |lower_Pmin_Uu|')   
        print('|',suma,'   |   ',len(SB_Uu),'   |   ',len(No_SB_Uu),'   |   ',len(lower_Pmin_Uu),' |',)   
                       
        return SB_Uu, No_SB_Uu, lower_Pmin_Uu
    
    
    def update_lower_Pmin_Uu(self,lower_Pmin_Uu_o,tag):
    ## Esta función actualiza las variables en cero que siguen quedando en el conjunto B.
        lower_Pmin_Uu = []
        ceros=0
        try:
            for i in lower_Pmin_Uu_o:
                if self.Uu[i[0]][i[1]] == 0:
                    ceros=ceros+1
                    lower_Pmin_Uu.append(i)
            print(tag,'update lower_Pmin_Uu (#0) ->',ceros)  
            
        except Exception as e:
            xx = 1 
            print('>>> Hubo un error en <update_lower_Pmin_Uu>')            
        return lower_Pmin_Uu
    
    
    def cuenta_ceros_a_unos(self,SB_Uu_o,No_SB_Uu_o,lower_Pmin_Uu_o,tag):
    ## Esta función cuenta aquellos elementos que han cambiado de estado de cero a uno
        try:
            uno_a_cero=0
            for i in SB_Uu_o:
                if self.Uu[i[0]][i[1]] == 0:
                    #print(i)
                    uno_a_cero=uno_a_cero+1
            print(tag,'SB_Uu    1->0',uno_a_cero)
            cero_a_uno=0
            for i in No_SB_Uu_o:
                if self.Uu[i[0]][i[1]] == 1:
                    #print(i)
                    cero_a_uno=cero_a_uno+1
            print(tag,'No_SB_Uu 0->1',cero_a_uno)
            cero_a_uno=0
            for i in lower_Pmin_Uu_o:
                if self.Uu[i[0]][i[1]] == 1:
                    #print(i)
                    cero_a_uno=cero_a_uno+1
            print(tag,'lower_Pmin_Uu  0->1',cero_a_uno)  
            
        except Exception as e:
            xx = 1 
            #print('>>> Hubo un error en <cuenta_ceros_a_unos>')
        return 0
    
    
    def count_U_no_int(self):   
        Uu_no_int = []   
        for t in range(self.tt):
            for g in range(self.gg):                
                if self.Uu[g][t] != 1 and self.Uu[g][t] != 0:
                    Uu_no_int.append([g,t,self.Uu[g][t]])    
        if len(Uu_no_int) != 0:
            if self.option=='relax':
                print(self.option+" Numero de No binarios en la solución ---> solution.Uu_no_int=",len(Uu_no_int))   
            else:
                print(self.option+" >>> WARNING se han encontrado No binarios en la solución ---> solution.Uu_no_int=",len(Uu_no_int),Uu_no_int)   
        return 0
    
    
    ## En esta función comparamos dos soluciones variable por variable.
    def compare(self,sol2):
        npArray1 = np.array([self.Uu])
        npArray2 = np.array([sol2.Uu])
        print(npArray1) 
        print(npArray2) 
        comparison = npArray1 == npArray2
        equal_arrays = comparison.all() 
        print('Uu equal_arrays  =',equal_arrays)        
        out_num = np.subtract(npArray1, npArray2) 
        print ("Uu Difference of two input number : ",type(out_num), out_num) 
        