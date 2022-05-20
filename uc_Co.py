## --------------------------------------------------------------------------------
## File: uc_Co.py
## Developers: Uriel Iram Lezama Lope
## Purpose: UC "Compact" model introduced by Knueven2020b
## Description:
## Objetive               (69)
## Up-time/down-time      (2), (3), (4), (5)       'garver_3bin_vars',
##                                                 'rajan_takriti_UT_DT',
## Generation limits      (17), (20), (21)         'MLR_generation_limits',
##                                                 'garver_power_vars',
##                                                 'garver_power_avail_vars',
## Ramp limits            (35), (36)               'damcikurt_ramping',
## Piecewise production   (42), (43), (44)         'Garver1962',
## Start-up cost          (54), (55), (56)         'MLR_startup_costs',
## System constraints     (67)
## --------------------------------------------------------------------------------
import math
import pyomo.environ as pyo
from   pyomo.environ import *

def uc(G,T,L,S,Pmax,Pmin,UT,DT,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tunder,option='None',
       fixed_Uu=[],No_fixed_Uu=[],lower_Pmin_Uu=[],percent_lbc=90,k=20,nameins='model'):
               
    n_subset   = 0 ## Número de variables que podrían moverse en el Sub-milp (Binary support)

    model      = pyo.ConcreteModel(nameins)    
    model.G    = pyo.Set(initialize = G)
    model.T    = pyo.Set(initialize = T)  
    model.L    = pyo.Set(model.G, initialize = L) 
    model.S    = pyo.Set(model.G, initialize = S) 
    
    model.Pmax = pyo.Param(model.G , initialize = Pmax , within = Any)
    model.Pmin = pyo.Param(model.G , initialize = Pmin , within = Any)
    model.UT   = pyo.Param(model.G , initialize = UT   , within = Any)
    model.DT   = pyo.Param(model.G , initialize = DT   , within = Any)
    model.De   = pyo.Param(model.T , initialize = De   , within = Any)
    model.R    = pyo.Param(model.T , initialize = R    , within = Any)
    model.u_0  = pyo.Param(model.G , initialize = u_0  , within = Any)
    model.D    = pyo.Param(model.G , initialize = D    , within = Any)
    model.U    = pyo.Param(model.G , initialize = U    , within = Any)
    model.SU   = pyo.Param(model.G , initialize = SU   , within = Any)
    model.SD   = pyo.Param(model.G , initialize = SD   , within = Any)
    model.RU   = pyo.Param(model.G , initialize = RU   , within = Any)
    model.RD   = pyo.Param(model.G , initialize = RD   , within = Any)
    model.pc_0 = pyo.Param(model.G , initialize = pc_0 , within = Any) 
    model.mpc  = pyo.Param(model.G , initialize = mpc  , within = Any)
    # model.c    = pyo.Param(model.G , initialize = {1:5,2:15,3:30}    ,within = Any)
    # model.cU   = pyo.Param(model.G , initialize = {1:800,2:500,3:250},within = Any)
       
    CLP = 999999999999.0 #penalty cost for failing to meet or exceeding load ($/megawatt-hour (MWh)).
    CRP = 999999999999.0 #penalty cost for failing to meet reserve requirement
    
    ##  Defined index to compute the per-generator, per-time, and segment period production costs.
    def index_G_T_Lg(m):
        return ((g,t,l) for g in m.G for t in m.T for l in range(1,len(m.L[g])+1))
    model.indexGTLg = Set(initialize=index_G_T_Lg, dimen=3)
    
    ##  Defined index to compute the per-generator, and segment period production costs.
    def index_G_Lg(m):
        return ((g,l) for g in m.G for l in range(1,len(m.L[g])+1))
    model.indexGLg = Set(initialize=index_G_Lg, dimen=2)
    
    ##  Defined index to compute the per-generator, per-time, and  start-up segment cost variable.
    def index_G_T_Sg(m):
        return ((g,t,s) for g in m.G for t in m.T for s in range(1,len(m.S[g])+1)) ##CHECAR SI REQUIERE +1
    model.indexGTSg = Set(initialize=index_G_T_Sg, dimen=3)    
    
    ##  Defined index to compute the per-generator, and start-up segment cost variable.
    def index_G_Sg(m):
        return ((g,s) for g in m.G for s in range(1,len(m.S[g])+1)) ##CHECAR SI REQUIERE +1
    model.indexGSg = Set(initialize=index_G_Sg, dimen=2)
    
    if(option == 'relax'): #Si se desea relajar las variables enteras como continuas
        model.u     = pyo.Var( model.G , model.T , within = UnitInterval)   ## UnitInterval: floating point values in the interval [0,1]
        model.v     = pyo.Var( model.G , model.T , within = UnitInterval)   
        model.w     = pyo.Var( model.G , model.T , within = UnitInterval)   
        model.delta = pyo.Var( model.indexGTSg,    within = UnitInterval)   
    else:        
        model.u     = pyo.Var( model.G , model.T , within = Binary)
        model.v     = pyo.Var( model.G , model.T , within = Binary)
        model.w     = pyo.Var( model.G , model.T , within = Binary)
        model.delta = pyo.Var( model.indexGTSg,    within = Binary) 

    model.p         = pyo.Var( model.G , model.T , bounds = (0.0,99999.0))
    model.pb        = pyo.Var( model.G , model.T , bounds = (0.0,99999.0))
    model.pbc       = pyo.Var( model.G , model.T , bounds = (0.0,99999.0))  ## pbarra' (capacidad máxima de salida con reserva arriba del m.Pmin)
    model.pc        = pyo.Var( model.G , model.T , bounds = (0.0,99999.0))  ## p' (potencia de salida arriba del m.Pmin)
    model.r         = pyo.Var( model.G , model.T , bounds = (0.0,99999.0))  ## reserve in general without specific timing
    model.cp        = pyo.Var( model.G , model.T , bounds = (0.0,9999999.0))
    model.cSU       = pyo.Var( model.G , model.T , bounds = (0.0,9999999.0))
    model.cSD       = pyo.Var( model.G , model.T , bounds = (0.0,9999999.0))
    model.snplus    = pyo.Var( model.T ,           bounds = (0.0,9999999.0)) ##surplus demand
    model.snminus   = pyo.Var( model.T ,           bounds = (0.0,9999999.0)) ##surplus demand
    model.sn        = pyo.Var( model.T ,           bounds = (0.0,9999999.0)) ##surplus demand
    model.sR        = pyo.Var( model.T ,           bounds = (0.0,9999999.0)) ##surplus reserve         
    model.pl        = pyo.Var(model.indexGTLg,     bounds = (0.0,99999.0))   ## within=UnitInterval UnitInterval == [0,1]   
    model.total_cSU = pyo.Var( bounds = (0.0,999999999999.0))                  ## Acumula total
    
    model.Pb   = pyo.Param(model.indexGLg, initialize = Pb,   within = Any)
    model.C    = pyo.Param(model.indexGLg, initialize = C,    within = Any)
    model.Cs   = pyo.Param(model.indexGSg, initialize = Cs,   within = Any)
    model.Tunder = pyo.Param(model.indexGSg, initialize = Tunder, within = Any)
    
    ## model.mut2.pprint()        ## For entire Constraint List
    ## print(model.mut2[1].expr)  ## For only one index of Constraint List
    ## print(model.mdt2[3].expr)  ## For only one index of Constraint List
    ## model.u.set_values(dict)
    ## model.u.set_values({(1,3): 1}) ##ojo este no fija
    ## https://pyomo.readthedocs.io/en/stable/working_models.html
    ## model.u[3,1].fix(0)
    ## model.u.fix(0)
    
    def obj_rule(m): 
    #   return sum(m.cp[g,t] + m.cSU[g,t] * m.v[g,t] + m.mpc[g] * m.u[g,t] for g in m.G for t in m.T) \ #Costo sin piecewise
        #return sum(m.cp[g,t] + m.cSU[g,t] * 1        + m.mpc[g] * m.u[g,t] for g in m.G for t in m.T) \
        return m.total_cSU + sum( m.cp[g,t]           + m.mpc[g] * m.u[g,t] for g in m.G for t in m.T) \
            #  + 0 
            #  + sum(m.sR[t]   * CLP                                         for t in m.T) \
            #  + sum(m.sn[t]   * CRP                                         for t in m.T) 
    #        + sum(m.cU[g] * m.v[g,t] + m.c[g] * m.p[g,t] for g in m.G for t in m.T) 
    model.obj = pyo.Objective(rule = obj_rule)


    ## -----------------------------TOTAL COSTOS ARRANQUE------------------------------------------  
    def total_cSU_rule(m):  ## 
        return m.total_cSU == sum( m.cSU[g,t] * 1 for g in m.G for t in m.T)
    model.total_cSU_ = pyo.Constraint(rule = total_cSU_rule)    
    
    
    ## -----------------------------GARVER------------------------------------------  

    def logical_rule(m,g,t):    # logical eq.(2)
        if t == 1:
            return m.u[g,t] - m.u_0[g]   == m.v[g,t] - m.w[g,t]
        else:
            return m.u[g,t] - m.u[g,t-1] == m.v[g,t] - m.w[g,t]
    model.logical = pyo.Constraint(model.G,model.T,rule = logical_rule)
    
    
    ## ----------------------------POWER EQUALS------------------------------------  

    def pow_igual_rule(m,g,t):  ## iguala p a pc eq.(12)
        return m.p[g,t] == m.pc[g,t] + m.Pmin[g] * m.u[g,t]
    model.pow_igual = pyo.Constraint(model.G,model.T, rule = pow_igual_rule)    

    def pow_igual_rule2(m,g,t): ## iguala pb a pcb eq.(13)
        return m.pb[g,t] == m.pbc[g,t] + m.Pmin[g] * m.u[g,t]
    model.pow_igual2 = pyo.Constraint(model.G,model.T, rule = pow_igual_rule2)    

    def pow_igual_rule3(m,g,t): ## iguala pb a pcb eq.(14)
        return m.pbc[g,t] == m.pc[g,t] + m.r[g,t]
    model.pow_igual3 = pyo.Constraint(model.G,model.T, rule = pow_igual_rule3)

    def pow_igual_rule4(m,g,t): ## iguala pb a pcb eq.(15)
        return m.pb[g,t] == m.p[g,t] + m.r[g,t]
    model.pow_igual4 = pyo.Constraint(model.G,model.T, rule = pow_igual_rule4)    

    def pow_igual_rule5(m,g,t): ## pow_pow eq.(16)
        return m.p[g,t] <= m.pb[g,t] 
    model.pow_igual5 = pyo.Constraint(model.G,model.T, rule = pow_igual_rule5)    

    def pow_igual_rule6(m,g,t): ## pow_pow eq.(17)
        return m.pc[g,t] <= m.pbc[g,t]
    model.pow_igual6 = pyo.Constraint(model.G,model.T, rule = pow_igual_rule6)    


    ## ------------------------------START-UP AND SHUT-DOWN RAMPS---------------------------------   

    def sdsu_ramp_rule20(m,g,t):          ## eq.(20) 
        if m.UT[g] > 1 and t < len(m.T):  ## :g ∈ G>1
            return m.pc[g,t] + m.r[g,t] <= (m.Pmax[g]-m.Pmin[g])*m.u[g,t] \
                - (m.Pmax[g]-m.SU[g])*m.v[g,t] - (m.Pmax[g]-m.SD[g])*m.w[g,t+1]
        else:
            return pyo.Constraint.Skip    
    model.sdsu_ramp_rule20 = pyo.Constraint(model.G,model.T, rule = sdsu_ramp_rule20)

    def su_ramp_rule21a(m,g,t):           ## eq.(21a)
        if m.UT[g] == 1:                  ## :g ∈ G1
            return m.pc[g,t] + m.r[g,t] <= (m.Pmax[g]-m.Pmin[g])*m.u[g,t] - (m.Pmax[g]-m.SU[g])*m.v[g,t]
        else:
            return pyo.Constraint.Skip    
    model.su_ramp_rule21a = pyo.Constraint(model.G,model.T, rule = su_ramp_rule21a)        
    
    def sd_ramp_rule21b(m,g,t):           # eq.(21b)
        if m.UT[g] == 1 and t < len(m.T): # :g ∈ G>1
            return m.pc[g,t] + m.r[g,t] <= (m.Pmax[g]-m.Pmin[g])*m.u[g,t] - (m.Pmax[g]-m.SD[g])*m.w[g,t+1]
        else:
            return pyo.Constraint.Skip    
    model.sd_ramp_rule21b = pyo.Constraint(model.G,model.T, rule = sd_ramp_rule21b)
    
    
    ## -------------------------------LIMITS & RAMPS------------------------------------------   
        
    def up_ramp_rule35(m,g,t):          ## ramp-up eq.(35)
        if t == 1:
            return m.pc[g,t] - (m.pc_0[g]) <= (m.SU[g]-m.Pmin[g]-m.RU[g])*m.v[g,t] + m.RU[g]*m.u[g,t]
        else:
            return m.pc[g,t] - m.pc[g,t-1]  <= (m.SU[g]-m.Pmin[g]-m.RU[g])*m.v[g,t] + m.RU[g]*m.u[g,t]
    model.up_ramp_rule35 = pyo.Constraint(model.G,model.T, rule = up_ramp_rule35)   

    def down_ramp_rule36(m,g,t):        ## ramp-down eq.(36) 
        if t == 1:
            return (m.pc_0[g])  - m.pc[g,t] <= (m.SD[g]-m.Pmin[g]-m.RD[g])*m.w[g,t] + m.RD[g]*m.u_0[g]
        else:
            return m.pc[g,t-1] - m.pc[g,t] <= (m.SD[g]-m.Pmin[g]-m.RD[g])*m.w[g,t] + m.RD[g]*m.u[g,t-1]
    model.down_ramp_rule36 = pyo.Constraint(model.G,model.T, rule = down_ramp_rule36)


    ## -------------------------------DEMAND & RESERVE----------------------------------------   
 
    def demand_rule65(m,t):                      ## demand eq.(65)
        # return sum( m.p[g,t] for g in m.G ) + m.sn[t]  == m.De[t] 
        return sum( m.p[g,t] for g in m.G ) + 0  == m.De[t] 
    model.demand_rule65 = pyo.Constraint(model.T, rule = demand_rule65)
    
    # def demand_rule66a(m,t):                      ## holguras o excesos en la demanda eq.(66a)
    #      return m.sn[t] == m.snplus[t] - m.snminus[t]  
    # model.demand_rule66a = pyo.Constraint(model.T, rule = demand_rule66a)

    def demand_rule67(m,t):                      ## demand + reserve eq.(67)
        # return sum( m.pb[g,t] for g in m.G ) + m.sR[t] >= m.De[t] + m.R[t] 
        return sum( m.pb[g,t] for g in m.G ) + 0 >= m.De[t] + m.R[t] 
    model.demand_rule67 = pyo.Constraint(model.T, rule = demand_rule67)

    def demand_reserve(m,t):                      ## reserve
        # return sum( m.r[g,t] for g in m.G) + m.sR[t] >= m.R[t] 
        return sum( m.r[g,t] for g in m.G) + 0 >= m.R[t] 
    model.demand_reserve = pyo.Constraint(model.T, rule = demand_reserve)


    ## --------------------------------MINIMUM UP/DOWN TIME---------------------------------------

    def mut_rule(m,g,t):  ## minimum-up time eq.(4)
        if t >= value(m.UT[g]):
            return sum( m.v[g,i] for i in range(t-value(m.UT[g])+1,t+1)) <= m.u[g,t]        
        else:
            return pyo.Constraint.Skip
    model.mut = pyo.Constraint(model.G, model.T, rule = mut_rule)    

    def mdt_rule(m,g,t): ## minimum-down time eq.(5)
        if t >= value(m.DT[g]):
            return sum( m.w[g,i] for i in range(t-value(m.DT[g])+1,t+1)) <= 1 - m.u[g,t] 
        else:
            return pyo.Constraint.Skip
    model.mdt = pyo.Constraint(model.G, model.T, rule = mdt_rule)
        
    def mdt_rule2(m,g): ## enforce the minimum-down time eq.(3b)
        minimo = min( value(D[g]),len(m.T) )
        if minimo > 0:
            return sum( m.u[g,i] for i in range(1,minimo+1)) == 0
        else: 
            return pyo.Constraint.Skip        
    model.mdt2 = pyo.Constraint(model.G, rule = mdt_rule2)
        
    def mut_rule2(m,g):  ## enforce the minimum-up time eq.(3a)
        minimo = min( value(m.U[g]) , len(m.T) )
        if minimo > 0:
            return sum( m.u[g,i] for i in range(1,minimo+1) ) == int(minimo)
        else: 
            return pyo.Constraint.Skip
    model.mut2 = pyo.Constraint(model.G, rule = mut_rule2)
    
    
    ## ----------------------------PIECEWISE OFFER-------------------------------------------   
    
    def Piecewise_offer42(m,g,t,l):  ## piecewise offer eq.(42)
        if l > 1:
            return m.pl[g,t,l] <= (m.Pb[g,l]-m.Pb[g,l-1]) * m.u[g,t]
        else: 
            return pyo.Constraint.Skip
    model.Piecewise_offer42 = pyo.Constraint(model.indexGTLg, rule = Piecewise_offer42)
    
    def Piecewise_offer43(m,g,t):  ## piecewise offer eq.(43)
        return sum(m.pl[g,t,l] for l in range(1,value(len(m.L[g]))+1)) == m.pc[g,t]                                        
    model.Piecewise_offer43 = pyo.Constraint(model.G,model.T, rule = Piecewise_offer43)
    
    def Piecewise_offer44(m,g,t):  ## piecewise offer eq.(44)
        return sum(m.C[g,l] * m.pl[g,t,l] for l in range(1,value(len(m.L[g]))+1)) == m.cp[g,t]                                       
    model.Piecewise_offer44 = pyo.Constraint(model.G,model.T, rule = Piecewise_offer44)
    
    
    ## ----------------------------VARIABLE START-UP COST-------------------------------------------     
    
    def Start_up_cost54(m,g,t,s):  ##  start-up cost eq.(54)   #CHECAR A MANO !!!! 
        #if s < value(len(m.S[g])) #and t >= m.Tunder[g,s+1]:  #CHECAR A MANO !!!! 
        if s < value(len(m.S[g]))   and t >= m.Tunder[g,s+1]:  #CHECAR A MANO !!!! 
            # print('s=',s,'t=',t)
            return m.delta[g,t,s] <= sum(m.w[g,t-i] for i in range(m.Tunder[g,s],m.Tunder[g,s+1]))  #CHECAR A MANO !!!! 
        else:
            return pyo.Constraint.Skip                                   
    model.Start_up_cost54 = pyo.Constraint(model.indexGTSg, rule = Start_up_cost54)

    def Start_up_cost57(m,g,t):  ##  start-up cost eq.(57)
        return m.v[g,t] >= sum(m.delta[g,t,s] for s in range(1,value(len(m.S[g])) )) 
    model.Start_up_cost57 = pyo.Constraint(model.G,model.T, rule = Start_up_cost57)
            
    def Start_up_cost58(m,g,t):  ##  start-up cost eq.(58)
        return m.cSU[g,t] == m.Cs[g,value(len(m.S[g]))]*m.v[g,t] - sum(((m.Cs[g,value(len(S[g]))]-m.Cs[g,s])*m.delta[g,t,s]) for s in range(1,value(len(m.S[g]))  ))  
    model.Start_up_cost58 = pyo.Constraint(model.G,model.T, rule = Start_up_cost58)   
    
    ## ---------------------------- Inequality related with 'delta' and 'v' ------------------------------------------
    
    if option == 'Milp2':    
        def Start_up_cost_desigualdad_Uriel(m,g):  ##  start-up cost eq.(54)(s < value(len(m.S[g])) and t >= m.Tunder[g,s+1]):
            return sum(m.v[g,t] for t in m.T) == sum(m.delta[g,t,s] for s in range(1,value(len(m.S[g]))+1) for t in m.T)  
        model.Start_up_cost_desigualdad_Uriel = pyo.Constraint(model.G,rule = Start_up_cost_desigualdad_Uriel)
    

    ## ---------------------------- HARD VARIABLE FIXING ------------------------------------------
    
    ## Si se desea usar la solución fix y calcular un sub-MILP.
    if option == 'Hard':    
        for f in fixed_Uu: 
            model.u[f[0]+1,f[1]+1].fix(1)  ## Hard fixing
                        
            
    ## ---------------------------- SOFT0 FIXING ------------------------------------------
    
    ## Relajamos la restricción de integralidad de las variables Uu candidatas a 1 en la relajación lineal
    if(option == 'Soft0' or option == 'Soft4' or option == 'Soft5'):    
        for f in No_fixed_Uu:
            model.u[f[0]+1,f[1]+1].fix(0)                ## Hard fixing to '0' those elements outside of Sopport Binary      
              
        for f in fixed_Uu:  
            model.u[f[0]+1,f[1]+1].domain = UnitInterval ## We remove the integrality constraint of the Binary Support 
            
        for f in lower_Pmin_Uu:
            model.u[f[0]+1,f[1]+1].unfix()               ## Unfixing
            model.u[f[0]+1,f[1]+1].domain = UnitInterval ## Soft-fixing I
            
        ## Adding a new restriction.  
        ## https://pyomo.readthedocs.io/en/stable/working_models.html
        ## Soft-fixing II
        model.cuts = pyo.ConstraintList()
        n_subset   = math.ceil((percent_lbc/100) * len(fixed_Uu))
        expr       = 0        
        
        if option != 'Soft5':       ## Sin ninguna restricción de n_subset=90%     
            if option == 'Soft0':   ## Se hace n_subset=90% solo a al Soporte Binario    
                for f in fixed_Uu:      
                    expr += model.u[f[0]+1,f[1]+1]
            if option == 'Soft4':  ## Se hace n_subset=90% al Soporte Binario (Titulares) y a Candidatos (la banca) identificados en LR
                for f in lower_Pmin_Uu:   
                    expr += model.u[f[0]+1,f[1]+1]  ## New constraint soft.                        
            model.cuts.add(expr >= n_subset)        ## Adding a new restriction.  


    ## ---------------------------- SOFT VARIABLE FIXING ------------------------------------------

    # ## Si se desea usar la solución fix y calcular un sub-MILP.
    # if(option == 'Soft' or option == 'Soft2' or option == 'Soft3'): 

    #     for f in fixed_Uu:  
    #         model.u[f[0]+1,f[1]+1].domain = UnitInterval  ## Soft-fixing I                

    #     ## Adding a new restriction.  
    #     ## https://pyomo.readthedocs.io/en/stable/working_models.html
    #     ## Soft-fixing II
    #     model.cuts = pyo.ConstraintList()
    #     n_subset   = math.ceil( (percent_lbc/100) * len(fixed_Uu))
    #     expr       = 0
        
    #     for f in fixed_Uu:      
    #         expr += model.u[f[0]+1,f[1]+1]
        
    #     if(option == 'Soft2' or option == 'Soft3'):
    #         # \todo{DEMOSTRAR QUE NOS CONVIENE RELAJAR LOS INTENTOS DE ASIGNACIÓN EN EL SOFT-FIXING}
    #         for f in lower_Pmin_Uu: 
    #             model.u[f[0]+1,f[1]+1].domain = UnitInterval ## Soft-fixing
    #         for f in lower_Pmin_Uu:      
    #             expr += model.u[f[0]+1,f[1]+1]               ## New constraint soft.                        
    #     model.cuts.add(expr >= n_subset)                     ## Adding a new restriction.  
    #     #print('Soft: number of variables Uu that could be outside  the n_subset (',100-percent_lbc,'%): ', len(fixed_Uu)-n_subset)

    # if(option == 'Soft3'):   
    #     print('Soft3 -estoy fijando a <0>: No_fixed_Uu - lower_Pmin_Uu =',len(No_fixed_Uu),'-',len(lower_Pmin_Uu))
    #     for f in No_fixed_Uu:
    #         model.u[f[0]+1,f[1]+1].fix(0)  ## Hard fixing to 0
    #     for f in lower_Pmin_Uu:
    #         model.u[f[0]+1,f[1]+1].unfix()   ## Unfixing
                

    ## ---------------------------- LOCAL BRANCHING CONSTRAINT ------------------------------------------
    
    ## Define a neighbourhood with LBC.
    if(option == 'LBC' or option == 'LBC+pmin'):
                
        for f in fixed_Uu: 
            model.u[f[0]+1,f[1]+1].domain = UnitInterval ## Soft-fixing I        
            
        ## Soft fixing III
        model.cuts = pyo.ConstraintList()
        n_subset   = math.ceil((percent_lbc/100) * len(fixed_Uu)) 
        expr       = 0
         
        for f in fixed_Uu:      
            expr += model.u[f[0]+1,f[1]+1]               ## New constraint soft.
            
        if(option == 'LBC+pmin'):  
            # \todo{EVALUAR SI NOS CONVIENE O NO RELAJAR LOS INTENTOS DE ASIGNACIÓN EN EL SOFT-FIXING}
            for f in lower_Pmin_Uu: 
                model.u[f[0]+1,f[1]+1].domain = UnitInterval ## Soft-fixing
            for f in lower_Pmin_Uu:      
                expr += model.u[f[0]+1,f[1]+1]               ## New constraint soft.             
        model.cuts.add(expr >= n_subset)                     ## Adding a new restriction. 
           
        #print('LBC: number of variables Uu that must be into the n_subset (',percent_lbc,'%): ', n_subset)
        print('LBC: number of variables Uu that must be outside the n_subset (',100-percent_lbc,'%): ', len(fixed_Uu)-n_subset)
        
        ## Local branching constraint
        expr = 0        
        for f in fixed_Uu:                                  ## Cuenta los cambios de 1 --> 0  
            expr += 1 - model.u[f[0]+1,f[1]+1] 
        for f in No_fixed_Uu:                               ## Cuenta los cambios de 0 --> 1
            expr +=     model.u[f[0]+1,f[1]+1]            
        model.cuts.add(expr <= k)                           ## Adding a new restrictions (lbc). 
        
    ## Termina y regresa el modelo MILP
    return model , n_subset



    ## ---------------------------- HARD VARIABLE FIXING (deprecared) ------------------------------------------    
    # ## Si se desea usar la solución fix y calcular un sub-MILP.
    # if(option == 'Hard'):    
    #     for f in fixed_Uu: 
    #         model.u[f[0]+1,f[1]+1].fix(1)  ## Hard fixing
    # if(option == 'HardUVWdelta'):   (deprecared)         
    #     for f in fixed_Uu: 
    #         model.u[f[0]+1,f[1]+1].fix(1)  ## Hard fixing
    #     for f in fixed_V: 
    #         model.v[f[0]+1,f[1]+1].fix(1)  ## Hard fixing
    #     for f in fixed_W: 
    #          model.w[f[0]+1,f[1]+1].fix(1) ## Hard fixing   
    #     for f in fixed_delta: 
    #          model.delta[f[0],f[1],f[2]].fix(0) ## Hard fixing   