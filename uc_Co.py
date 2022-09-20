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
## Piecewise production   (50)                     'Hua and Baldick 2017',
## Start-up cost          (54), (55), (56)         'MLR_startup_costs',
## System constraints     (67)
##  
## (Alternative) Piecewise production   (42), (43), (44)         'Garver1962',
## --------------------------------------------------------------------------------

import time
import pyomo.environ as pyo
from   pyomo.environ import *
from   math import floor ,ceil

def uc(G,T,L,S,Pmax,Pmin,UT,DT,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,CR,Pb,Cb,C,Cs,Tunder,names,option='None',
       kernel=[],bucket=[],SB_Uu=[],No_SB_Uu=[],lower_Pmin_Uu=[],V=[],W=[],delta=[],
       percent_soft=90,k=20,nameins='model',mode="Compact",improve=True,timeover=False,rightbranches=[],):
                      
    t_o = time.time()
    inside90   = 0 ## Número de variables que podrían moverse en el Sub-milp (Binary support)

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
    model.p_0  = pyo.Param(model.G , initialize = p_0  , within = Any) 
    model.CR   = pyo.Param(model.G , initialize = CR   , within = Any) #cost of generator g running and operating at minimum production
    # model.c    = pyo.Param(model.G , initialize = {1:5,2:15,3:30}    ,within =Any)
    # model.cU   = pyo.Param(model.G , initialize = {1:800,2:500,3:250},within = Any)
       
    
    CLP = 1000.0 #penalty cost for failing to meet or exceeding load ($/megawatt-hour (MWh)).
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
    
    if(option == 'relax' or option == 'RC'): #Si se desea relajar las variables enteras como continuas
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
    model.mpc       = pyo.Var( model.G , model.T , bounds = (0.0,9999999.0))
    # model.snplus    = pyo.Var( model.T ,           bounds = (0.0,9999999.0)) ##surplus demand
    # model.snminus   = pyo.Var( model.T ,           bounds = (0.0,9999999.0)) ##surplus demand
    model.sn        = pyo.Var( model.T ,           bounds = (0.0,9999999.0)) ##surplus demand
    model.sR        = pyo.Var( model.T ,           bounds = (0.0,9999999.0)) ##surplus reserve         
    model.pl        = pyo.Var(model.indexGTLg,     bounds = (0.0,99999.0))   ## within=UnitInterval UnitInterval == [0,1]   
    model.total_cSU = pyo.Var( bounds = (0.0,999999999999.0))                ## Acumula total prendidos
    model.total_cSD = pyo.Var( bounds = (0.0,999999999999.0))                ## Acumula total apagados
    model.total_cEN = pyo.Var( bounds = (0.0,999999999999.0))                ## Acumula total energia
    model.total_cMP = pyo.Var( bounds = (0.0,999999999999.0))               ## Acumula total CR
    model.total_MPC = pyo.Var( bounds = (0.0,999999999999.0))               ## Acumula total MPC

    model.Pb     = pyo.Param(model.indexGLg, initialize = Pb,     within = Any)
    model.Cb     = pyo.Param(model.indexGLg, initialize = Cb,     within = Any)
    model.C      = pyo.Param(model.indexGLg, initialize = C,      within = Any)
    model.Cs     = pyo.Param(model.indexGSg, initialize = Cs,     within = Any)
    model.Tunder = pyo.Param(model.indexGSg, initialize = Tunder, within = Any)
    
    ## model.mut2.pprint()        ## For entire Constraint List
    ## print(model.mut2[1].expr)  ## For only one index of Constraint List
    ## print(model.mdt2[3].expr)  ## For only one index of Constraint List
    ## model.u.set_values(dict)
    ## model.u.set_values({(1,3): 1}) ## OJO este no sirve , no fija !!!
    ## https://pyomo.readthedocs.io/en/stable/working_models.html
    ## model.u[3,1].fix(0)
    ## model.u.fix(0)
    
    def obj_rule(m): 
        return  + m.total_cSU \
                + m.total_cEN \
                + m.total_cMP \
                + m.total_MPC \
                + sum(m.sn[t]   * CLP                    for t in m.T) 
            #   + sum(m.sR[t]   * CRP                    for t in m.T) \
            #   + m.total_cSD\
    model.obj = pyo.Objective(rule = obj_rule)

    ## -----------------------------TOTAL COSTOS VACIO------------------------------------------  
    def total_cMP_rule(m):  ## to account CR cost
        return m.total_cMP == sum( m.CR[g] * m.u[g,t] for g in m.G for t in m.T)
    model.total_cMP_ = pyo.Constraint(rule = total_cMP_rule)    
    
    ## -----------------------------TOTAL COSTOS ENERGIA------------------------------------------  
    def total_cEN_rule(m):  ## to account energy cost
        return m.total_cEN == sum( m.cp[g,t] for g in m.G for t in m.T)
    model.total_cEN_ = pyo.Constraint(rule = total_cEN_rule)    
        
    ## -----------------------------TOTAL COSTOS ARRANQUE------------------------------------------  
    def total_cSU_rule(m):  ## to account starts cost
        return m.total_cSU == sum( m.cSU[g,t] * 1 for g in m.G for t in m.T)
    model.total_cSU_ = pyo.Constraint(rule = total_cSU_rule)   
    
    ## -----------------------------TOTAL MINIMUM PRODUCTION COST------------------------------------------  
    def total_MPC_rule(m):  ## to account minumum production cost
        return m.total_MPC == sum( m.mpc[g,t] * 1 for g in m.G for t in m.T)
    model.total_MPC_ = pyo.Constraint(rule = total_MPC_rule)   
    
    ## -----------------------------TOTAL COSTOS APAGADO------------------------------------------  
    # def total_cSD_rule(m):  ## to account for stoppages cost
    #     return m.total_cSD == sum( m.cSD[g,t] * 1 for g in m.G for t in m.T)
    # model.total_cSD_ = pyo.Constraint(rule = total_cSD_rule)
      
    
    ## -----------------------------GARVER------------------------------------------  

    def logical_rule(m,g,t):    ## logical eq.(2)
        if t == 1:
            return m.u[g,t] - m.u_0[g]   == m.v[g,t] - m.w[g,t]
        else:
            return m.u[g,t] - m.u[g,t-1] == m.v[g,t] - m.w[g,t]
    model.logical = pyo.Constraint(model.G,model.T,rule = logical_rule)
    
    
    ## ----------------------------POWER EQUALS------------------------------------  

    def pow_igual_rule(m,g,t):  ## iguala p a pc eq.(12)
        return m.p[g,t] == m.pc[g,t] + m.Pmin[g] * m.u[g,t]
    model.pow_igual = pyo.Constraint(model.G,model.T, rule = pow_igual_rule)    

    def pow_igual_rule2(m,g,t): ## iguala pb a pbc eq.(13)
        return m.pb[g,t] == m.pbc[g,t] + m.Pmin[g] * m.u[g,t]
    model.pow_igual2 = pyo.Constraint(model.G,model.T, rule = pow_igual_rule2)    

    def pow_igual_rule3(m,g,t): ## iguala pbc a pc eq.(14)
        return m.pbc[g,t] == m.pc[g,t] + m.r[g,t]
    model.pow_igual3 = pyo.Constraint(model.G,model.T, rule = pow_igual_rule3)

    def pow_igual_rule4(m,g,t): ## iguala pb a p eq.(15)
        return m.pb[g,t] == m.p[g,t] + m.r[g,t]
    model.pow_igual4 = pyo.Constraint(model.G,model.T, rule = pow_igual_rule4)    

    def pow_igual_rule5(m,g,t): ## pow_pow eq.(16)
        return m.p[g,t] <= m.pb[g,t] 
    model.pow_igual5 = pyo.Constraint(model.G,model.T, rule = pow_igual_rule5)    

    def pow_igual_rule6(m,g,t): ## pow_pow2 eq.(17)
        return m.pc[g,t] <= m.pbc[g,t]
    model.pow_igual6 = pyo.Constraint(model.G,model.T, rule = pow_igual_rule6)    
    
    def Piecewise_offer44b(m,g,t):  ## piecewise offer eq.(44b)
        return m.pc[g,t] <= ( m.Pmax[g] - m.Pmin[g] ) * m.u[g,t]                                       
    model.Piecewise_offer44b = pyo.Constraint(model.G,model.T, rule = Piecewise_offer44b)


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
    
    ## -------------------------------GENERATION LIMITS (Tight)------------------------------------------ 

    if mode == "Tight":
        TRU = []; TRD = []; TRU.append(-1); TRD.append(-1)
        for g in G:
            TRU.append(floor((model.Pmax[g]-model.SU[g])/model.RU[g]))
            TRD.append(floor((model.Pmax[g]-model.SU[g])/model.RD[g]))                

        def su_sd_rule23a(m,g,t):                      ## eq.(23a)
            if m.UT[g] == 1 and m.SU[g] != m.SD[g] and t<len(m.T):    ## :g ∈ G1
                return m.pc[g,t] + m.r[g,t] <= (m.Pmax[g]-m.Pmin[g])*m.u[g,t] - (m.Pmax[g]-m.SU[g])*m.v[g,t] \
                    -max(0,m.SU[g]-m.SD[g])*m.w[g,t+1] 
            else:
                return pyo.Constraint.Skip    
        model.su_sd_rule23a = pyo.Constraint(model.G,model.T, rule = su_sd_rule23a)   
         
        def su_sd_rule23b(m,g,t):                      ## eq.(23b)
            if m.UT[g] == 1 and m.SU[g] != m.SD[g] and t<len(m.T):    ## :g ∈ G1
                return m.pc[g,t] + m.r[g,t] <= (m.Pmax[g]-m.Pmin[g])*m.u[g,t] - (m.Pmax[g]-m.SD[g])*m.w[g,t+1] \
                    -max(0,m.SD[g]-m.SU[g])*m.v[g,t] 
            else:
                return pyo.Constraint.Skip    
        model.su_sd_rule23b = pyo.Constraint(model.G,model.T, rule = su_sd_rule23b) 
        
        def up_ramp_rule38(m,g,t):  ## eq.(38) upper bounds based on the ramp-up and shutdown trajectory of the generator: Pan and Guan (2016)
            if t < len(m.T):
                expr = 0
                for i in range(0,min(m.UT[g]-2+1,TRU[g]+1)):
                    if t-i > 0:
                        expr += (m.Pmax[g]-m.SU[g]-i*m.RU[g])*m.v[g,t-i]                    
                ## expr=sum((m.Pmax[g]-m.SU[g]-i*m.RU[g])*m.v[g,t-i] for i in range(0,min(m.UT[g]-2+1,TRU[g]+1)))                
                return m.pb[g,t] <= m.Pmax[g]*m.u[g,t] - (m.Pmax[g]-m.SD[g])*m.w[g,t+1] - expr
            else:
                return pyo.Constraint.Skip
        model.up_ramp_rule38 = pyo.Constraint(model.G,model.T, rule = up_ramp_rule38)   
        
        ##40
        ##41
    
    ## -------------------------------LIMITS & RAMPS------------------------------------------   
        
    def up_ramp_rule35(m,g,t):          ## ramp-up eq.(35)
        if t == 1:
            return m.pbc[g,t] - max(0,m.p_0[g]-m.Pmin[g]) <= (m.SU[g]-m.Pmin[g]-m.RU[g])*m.v[g,t] + m.RU[g]*m.u[g,t]
        else:
            return m.pbc[g,t] - m.pc[g,t-1]  <= (m.SU[g]-m.Pmin[g]-m.RU[g])*m.v[g,t] + m.RU[g]*m.u[g,t]
    model.up_ramp_rule35 = pyo.Constraint(model.G,model.T, rule = up_ramp_rule35)   

    def down_ramp_rule36(m,g,t):        ## ramp-down eq.(36) 
        if t == 1:
            return max(0,m.p_0[g]-Pmin[g])   - m.pc[g,t] <= (m.SD[g]-m.Pmin[g]-m.RD[g])*m.w[g,t] + m.RD[g]*m.u_0[g]
        else:
            return m.pc[g,t-1] - m.pc[g,t] <= (m.SD[g]-m.Pmin[g]-m.RD[g])*m.w[g,t] + m.RD[g]*m.u[g,t-1]
    model.down_ramp_rule36 = pyo.Constraint(model.G,model.T, rule = down_ramp_rule36)
    

    ## -------------------------------DEMAND & RESERVE----------------------------------------   
 
    def demand_rule65(m,t):                      ## demand eq.(65)
        ##return sum( m.p[g,t] for g in m.G ) +  m.sn[t]  == m.De[t] 
        return sum( m.p[g,t] for g in m.G )  + 0  == m.De[t] 
    model.demand_rule65 = pyo.Constraint(model.T, rule = demand_rule65)
    
    # def demand_rule66a(m,t):                      ## holguras o excesos en la demanda eq.(66a)
    #     return m.sn[t] == m.snplus[t] - m.snminus[t]  
    # model.demand_rule66a = pyo.Constraint(model.T, rule = demand_rule66a)

    def demand_rule67(m,t):                      ## demand + reserve eq.(67)
        ##return sum( m.pb[g,t] for g in m.G ) +  m.sn[t] >= m.De[t] + m.R[t] 
        return sum( m.pb[g,t] for g in m.G )   +  0       >= m.De[t] + m.R[t] 
    model.demand_rule67 = pyo.Constraint(model.T, rule = demand_rule67)

    def reserve_rule68(m,t):                      ## reserve eq.(68)
        ## return sum( m.r[g,t] for g in m.G) + m.sR[t] >= m.R[t] 
        return sum( m.r[g,t] for g in m.G)    + 0       >= m.R[t] 
    model.reserve_rule68 = pyo.Constraint(model.T, rule = reserve_rule68)


    ## --------------------------------MINIMUM UP/DOWN TIME---------------------------------------

    def mut_rule(m,g,t):  ## minimum-up time eq.(4)
        if t >= m.UT[g]:
            return sum( m.v[g,i] for i in range(t-value(m.UT[g])+1,t+1)) <= m.u[g,t]        
        else:
            return pyo.Constraint.Skip
    model.mut = pyo.Constraint(model.G, model.T, rule = mut_rule)    

    def mdt_rule(m,g,t): ## minimum-down time eq.(5)
        if t >= m.DT[g]:
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
    
    ## (Enforce) the initial Minimum Up/Down Times fixing the initial periods U[g] and D[g] 
    ## Tight and Compact MILP Formulation for the Thermal Unit Commitment Problem
    ## Germán Morales-España, Jesus M. Latorre, and Andrés Ramos
    for g in model.G: 
        for t in model.T: 
            if t <= U[g]+D[g]:
                model.u[g,t].fix(model.u_0[g])
                    
    
    ## ----------------------------PIECEWISE OFFER-------------------------------------------   
    
    if mode == "Compact" and False:
        def Piecewise_offer51(m,g,t,l):  ## piecewise offer eq.(51)
            if l == 1:                
                #return pyo.Constraint.Skip   
                return m.cp[g,t] >= m.Cb[g,l]*m.p[g,t] + (m.C[g,l] - m.Cb[g,l]*m.Pmin[g])*m.u[g,t]
            if l >= 2:
                return m.cp[g,t] >= m.Cb[g,l]*m.p[g,t] + (m.Cb[g,l-1] - m.Cb[g,l]*m.Pb[g,l-1])*m.u[g,t]
        model.Piecewise_offer51 = pyo.Constraint(model.indexGTLg, rule = Piecewise_offer51)
    
    if  mode == "Compact" and False: 
        def Piecewise_offer51(m,g,t,l):  ## piecewise offer eq.(51)
            if l == 1:   
                x0 = 0  # m.Pmin[g]     ## PowerGenerationPiecewisePoints
                x1 = m.Pmin[g] #m.Pb[g,l-1]
                y0 = 0                  ## Production_cost
                y1 = m.C[g,l] * 60
                slope = (y1 - y0)/ (x1 - x0) 
                intercept = -slope*x0 + y0
                print('l=',l,'slope',slope,'intercept',intercept)
                return m.cp[g,t] >= slope*m.pc[g,t] + intercept*m.u[g,t] 
            if l >= 2:
                x0 = m.Pb[g,l-1]         ## PowerGenerationPiecewisePoints
                x1 = m.Pb[g,l]
                y0 = m.C[g,l-1] * 60     ## Production_cost
                y1 = m.C[g,l] * 60
                slope = (y1 - y0)  / (x1 - x0) 
                intercept = -slope*x0 + y0
                print('l=',l,'slope',slope,'intercept',intercept)
                return m.cp[g,t] >= slope*m.pc[g,t] + intercept*m.u[g,t] 
                   
        #PowerGeneratedAboveMinimum =? pc
        model.Piecewise_offer51 = pyo.Constraint(model.indexGTLg, rule = Piecewise_offer51)
        
        def _production_cost_function(m, g, t, i):
            return m.TimePeriodLengthHours * m.PowerGenerationPiecewiseCostValues[g,t][i]
       
    
    if mode == "Tight" and True:  ##  Garver 1962
        def Piecewise_offer42(m,g,t,l):  ## piecewise offer eq.(42)
            if l == 1:
                return m.pl[g,t,l] <= (m.Pb[g,l]-m.Pmin[g] ) * m.u[g,t]
            if l > 1:
                return m.pl[g,t,l] <= (m.Pb[g,l]-m.Pb[g,l-1] ) * m.u[g,t]
        model.Piecewise_offer42 = pyo.Constraint(model.indexGTLg, rule = Piecewise_offer42)
        
        def Piecewise_offer43(m,g,t):   ## piecewise offer eq.(43)
            return sum(m.pl[g,t,l] for l in range(1,value(len(m.L[g]))+1)) == m.pc[g,t]                                        
        model.Piecewise_offer43 = pyo.Constraint(model.G,model.T, rule = Piecewise_offer43)
        
        def Piecewise_offer44(m,g,t):   ## piecewise offer eq.(44)
            return sum(m.C[g,l] * m.pl[g,t,l] for l in range(1,value(len(m.L[g]))+1)) == m.cp[g,t]                                       
        model.Piecewise_offer44 = pyo.Constraint(model.G,model.T, rule = Piecewise_offer44)
        
        def Piecewise_mpc(m,g,t):   ## minimum production cost
            try:
                return m.C[g,1] * m.Pmin[g] * m.u[g,t] == m.mpc[g,t]          
            except:
                if t==1:
                    print('<Piecewise_mpc> name...',names[g]) 
                return pyo.Constraint.Skip
                                       
        model.Piecewise_mpc = pyo.Constraint(model.G,model.T, rule = Piecewise_mpc)
        
        
    if mode == "Tight" and True:  ##  Knueven et al. (2018b)          
        ## Tightened the bounds on pl(t)->(43),(44) with the start-up 
        ## and shutdown variables using the start-up and shutdown ramp:
        Cv = []
        Cw = []
        for g in G:
            auxv=[]
            auxw=[]
            for l in L[g]:
                a=0       
                if Pb[g,l] <= SU[g]:
                   a=0     
                if l==1 : ## Case Pb[g,l=0] = Pmin[g]
                    if Pmin[g] < SU[g] and SU[g] < Pb[g,l]:
                        a=Pb[g,l]-SU[g]   
                    if Pmin[g] >= SU[g]:
                        a=Pb[g,l]-Pmin[g]  
                if l!=1:
                    if Pb[g,l-1] < SU[g] and SU[g] < Pb[g,l]:
                        a=Pb[g,l]-SU[g]   
                    if Pb[g,l-1] >= SU[g]:
                        a=Pb[g,l]-Pb[g,l-1]  
                auxv.append(a)
                b=0 
                if Pb[g,l] <= SD[g]:
                   b=0    
                if l==1: ## Case Pb[g,0] = Pmin[g]
                    if Pmin[g] < SD[g] and SD[g] < Pb[g,l]:
                        b=Pb[g,l]-SD[g]   
                    if Pmin[g] >= SD[g]:
                        b=Pb[g,l]-Pmin[g]  
                if l!=1: 
                    if  Pb[g,l-1] < SD[g] and SD[g] < Pb[g,l]:
                        b=Pb[g,l]-SD[g]   
                    if  Pb[g,l-1] >= SD[g]:
                        b=Pb[g,l]-Pb[g,l-1]  
                auxw.append(b)
                #print('g,l',g,l)
            Cv.append(auxv)
            Cw.append(auxw)
            
        def Piecewise_offer46(m,g,t,l):  ## piecewise offer eq.(46)  Knueven et al. (2018b)      
            if m.UT[g] > 1:
                if l == 1:  ## Case Pb[g,l=0] = Pmin[g]
                    if t < len(m.T):
                        return m.pl[g,t,l] <= (m.Pb[g,l]- m.Pmin[g] )*m.u[g,t] - Cv[g-1][l-1]*m.v[g,t] - Cw[g-1][l-1]*m.w[g,t+1]
                    if t == len(m.T):
                        return m.pl[g,t,l] <= (m.Pb[g,l]- m.Pmin[g] )*m.u[g,t] - Cv[g-1][l-1]*m.v[g,t] - 0
                if l > 1:
                    if t < len(m.T):
                        return m.pl[g,t,l] <= (m.Pb[g,l]-m.Pb[g,l-1])*m.u[g,t] - Cv[g-1][l-1]*m.v[g,t] - Cw[g-1][l-1]*m.w[g,t+1]
                    if t == len(m.T):
                        return m.pl[g,t,l] <= (m.Pb[g,l]-m.Pb[g,l-1])*m.u[g,t] - Cv[g-1][l-1]*m.v[g,t] - 0
            else: ## UT[g] == 1
                return pyo.Constraint.Skip         
        model.Piecewise_offer46 = pyo.Constraint(model.indexGTLg, rule = Piecewise_offer46)
        
        def Piecewise_offer47a(m,g,t,l):  ## piecewise offer eq.(47a)  Knueven et al. (2018b)     
            if m.UT[g]==1:
                if l == 1:  ## Case Pb[g,0] = Pmin[g]
                    return m.pl[g,t,l] <= (m.Pb[g,l]-m.Pmin[g]  )*m.u[g,t] - Cv[g-1][l-1]*m.v[g,t] 
                if l > 1:
                    return m.pl[g,t,l] <= (m.Pb[g,l]-m.Pb[g,l-1])*m.u[g,t] - Cv[g-1][l-1]*m.v[g,t]
            else:
                return pyo.Constraint.Skip                 
        model.Piecewise_offer47a = pyo.Constraint(model.indexGTLg, rule = Piecewise_offer47a)
        
        def Piecewise_offer47b(m,g,t,l):  ## piecewise offer eq.(47b)  Knueven et al. (2018b)     
            if m.UT[g]==1:
                if l == 1:  ## Case Pb[g,0] = Pmin[g]
                    if t < len(m.T):
                        return m.pl[g,t,l] <= (m.Pb[g,l]-m.Pmin[g]  )*m.u[g,t] - Cw[g-1][l-1]*m.w[g,t+1]
                    if t == len(m.T):
                        return m.pl[g,t,l] <= (m.Pb[g,l]-m.Pmin[g]  )*m.u[g,t] - 0
                if l > 1:
                    if t < len(m.T):
                        return m.pl[g,t,l] <= (m.Pb[g,l]-m.Pb[g,l-1])*m.u[g,t] - Cw[g-1][l-1]*m.w[g,t+1]
                    if t == len(m.T):
                        return m.pl[g,t,l] <= (m.Pb[g,l]-m.Pb[g,l-1])*m.u[g,t] - 0                       
            else:
                return pyo.Constraint.Skip                 
        model.Piecewise_offer47b = pyo.Constraint(model.indexGTLg, rule = Piecewise_offer47b)
        
        def Piecewise_offer48a(m,g,t,l):  ## piecewise offer eq.(48a)  Knueven et al. (2018b)     
            if m.UT[g]==1 and SU[g]!=SD[g]:
                posit = max(0,Cv[g-1][l-1] - Cw[g-1][l-1])      
                if l == 1:  ## Case Pb[g,l=0] = Pmin[g]
                    if t < len(m.T):         
                        return m.pl[g,t,l] <= (m.Pb[g,l]- m.Pmin[g] )*m.u[g,t] - Cv[g-1][l-1]*m.v[g,t] - posit*m.w[g,t+1]
                    if t == len(m.T):  
                        return pyo.Constraint.Skip                   
                if l > 1:  ## Caso general 
                    if t < len(m.T):   
                        return m.pl[g,t,l] <= (m.Pb[g,l]-m.Pb[g,l-1])*m.u[g,t] - Cv[g-1][l-1]*m.v[g,t] - posit*m.w[g,t+1]
                    if t == len(m.T):    
                        return pyo.Constraint.Skip  
            else:
                return pyo.Constraint.Skip                 
        model.Piecewise_offer48a = pyo.Constraint(model.indexGTLg, rule = Piecewise_offer48a)       
                        
        # VALIDAR EXPERIMENTALMENTE
        def Piecewise_offer48b(m,g,t,l):  ## piecewise offer eq.(48b)  Knueven et al. (2018b)     
            if m.UT[g]==1 and SU[g]!=SD[g]:
                posit = max(0,Cw[g-1][l-1] - Cv[g-1][l-1]) 
                if l == 1:  ## Case Pb[g,l=0] = Pmin[g]
                    if t < len(m.T):              
                        return m.pl[g,t,l] <= (m.Pb[g,l]-m.Pmin[g]  )*m.u[g,t] - Cw[g-1][l-1]*m.w[g,t+1] - posit*m.v[g,t]
                    if t == len(m.T):
                        return pyo.Constraint.Skip                     
                if l > 1: ## Caso general 
                    if t < len(m.T):             
                        return m.pl[g,t,l] <= (m.Pb[g,l]-m.Pb[g,l-1])*m.u[g,t] - Cw[g-1][l-1]*m.w[g,t+1] - posit*m.v[g,t]
                    if t == len(m.T):   
                        return pyo.Constraint.Skip                                 
            else:
                return pyo.Constraint.Skip                 
        model.Piecewise_offer48b = pyo.Constraint(model.indexGTLg, rule = Piecewise_offer48b)               
    
    
    ## ----------------------------SIMPLE COST PRODUCTION-------------------------------------------   
    if False:
        def simple_cost(m,g,t):   
            return m.C[g,1] * m.p[g,t] == m.cp[g,t]                                            
        model.simple_cost = pyo.Constraint(model.G,model.T, rule = simple_cost)
        
    
    ## ----------------------------VARIABLE START-UP COST-------------------------------------------     
    
    def Start_up_cost54(m,g,t,s):  ##  start-up cost eq.(54)   Checar and t >= m.Tunder[g,s+1]:------------------- 
        if s != len(m.S[g]) and t >= m.Tunder[g,s+1]:  
            return m.delta[g,t,s] <= sum(m.w[g,t-i] for i in range(m.Tunder[g,s],m.Tunder[g,s+1])) 
        else:
            return pyo.Constraint.Skip                                   
    model.Start_up_cost54 = pyo.Constraint(model.indexGTSg, rule = Start_up_cost54)
    
    if True: ## Morales-España et al. (2013a):
        def Start_up_cost55(m,g,t):  ##  start-up cost eq.(55)
            return m.v[g,t] == sum(m.delta[g,t,s] for s in range(1,len(m.S[g])+1)) 
        model.Start_up_cost55 = pyo.Constraint(model.G,model.T, rule = Start_up_cost55)
         
        def Start_up_cost56(m,g,t):  ##  start-up cost eq.(56)
            return m.cSU[g,t] == sum((m.Cs[g,s]*m.delta[g,t,s]) for s in range(1,len(m.S[g])+1))  
        model.Start_up_cost56 = pyo.Constraint(model.G,model.T, rule = Start_up_cost56)   
        
    else:  ## delta projection suggested by Knueven 2020       
        def Start_up_cost57(m,g,t):  ##  start-up cost eq.(57)
            return m.v[g,t] >= sum(m.delta[g,t,s] for s in range(1,len(m.S[g]) )) 
        model.Start_up_cost57 = pyo.Constraint(model.G,model.T, rule = Start_up_cost57)
                
        def Start_up_cost58(m,g,t):  ##  start-up cost eq.(58)
            return m.cSU[g,t] == m.Cs[g,len(m.S[g])]*m.v[g,t] - sum(((m.Cs[g,len(S[g])]-m.Cs[g,s])*m.delta[g,t,s]) for s in range(1,len(m.S[g]) ))  
        model.Start_up_cost58 = pyo.Constraint(model.G,model.T, rule = Start_up_cost58)   
        
    
    ## Initial Startup (t=0)Type required by MLR and Knueven from
    ## "Tight and Compact MILP Formulation for the Thermal Unit Commitment Problem",
    ## Germán Morales-España, Jesus M. Latorre, and Andrés Ramos.  
       
    for g in range(1,len(G)+1): 
        for t in range(1,len(T)+1): 
            for s in range(1,len(S[g])): 
                if TD_0[g]>=2:
                    if t < model.Tunder[g,s+1]:
                        if t > max(model.Tunder[g,s+1]-TD_0[g],1):
                            model.delta[g,t,s].fix(0)
                            # print('fix delta:',g,t,s)


    ## ---------------------------- Inequality related with 'delta' and 'v' ------------------------------------------

    if option == 'Milp2':
        def Start_up_cost_desigualdad_Uriel(m,g):  ##  start-up cost eq.(54)(s < value(len(m.S[g])) and t >= m.Tunder[g,s+1]):
            return sum(m.v[g,t] for t in m.T) == sum(m.delta[g,t,s] for s in range(1,value(len(m.S[g]))+1) for t in m.T)  
        model.Start_up_cost_desigualdad_Uriel = pyo.Constraint(model.G,rule = Start_up_cost_desigualdad_Uriel)
        

    ## ---------------------------- LOCAL BRANCHING CONSTRAINT LBC 1 (SOFT-FIXING)------------------------------------------    
    ## Define a neighbourhood with LBC1.
    
    if(option == 'lbc1'):
                  
        for f in No_SB_Uu:   
            model.u[f[0]+1,f[1]+1].domain = UnitInterval    ## We remove the integrality constraint of the Binary Support 
            if improve == True:          
                model.u[f[0]+1,f[1]+1] = 0                  ## Hints
        for f in SB_Uu:  
            model.u[f[0]+1,f[1]+1].domain = UnitInterval    ## We remove the integrality constraint of the Binary Support 
            if improve == True:          
                model.u[f[0]+1,f[1]+1] = 1                  ## Hints
            
        ## Hints para iniciar desde la última solución válida
        #if improve ==True:
        for g in range(len(G)):
            for t in range(len(T)):
                model.v[g+1,t+1] = V[g][t]                  ## Hints
                model.w[g+1,t+1] = W[g][t]                  ## Hints
                if delta[g][t]  != 0:
                    model.delta[g+1,t+1,delta[g][t]] = 1    ## Hints
                    
        model.cuts = pyo.ConstraintList()
        
        # Soft-fixing: adding a new restriction 
        if True:
            ## https://pyomo.readthedocs.io/en/stable/working_models.html
            inside90   = ceil((percent_soft/100) * (len(SB_Uu))) #-len(lower_Pmin_Uu)
            expr       = 0        
            ## Se hace inside90 = 90% solo a el - Soporte Binario -  
            for f in SB_Uu:
                expr += model.u[f[0]+1,f[1]+1]
            model.cuts.add(expr >= inside90)
            print(option,'variables Uu that SB_Uu=1 <= inside90  =', inside90)
            # outside90 = len(SB_Uu)-inside90
            # print(option,'variables Uu that SB_Uu=0 <= outside90 =', outside90)
            
        
        ## Local Branching Constraint (LBC)     
        if True:            
            ## Adding a new restrictions LEFT-BRANCH  <°|((><
            if improve == True or (timeover==True and improve == False) : 
                print('Adding  1  left-branch: ∑lower_Pmin_Uu + ∑SB_Uu ≤',k)                
                expr = 0      
                for f in SB_Uu:                             ## Cuenta los cambios de 1 --> 0  
                    expr += 1 - model.u[f[0]+1,f[1]+1] 
                for f in lower_Pmin_Uu :  # No_SB_Uu        ## Cuenta los cambios de 0 --> 1 
                    expr +=     model.u[f[0]+1,f[1]+1]              
                model.cuts.add(expr <= k)      
        
            ## Adding a new restrictions RIGHT-BRANCH  >>++++++++|°> . o O
            print('Adding ',len(rightbranches),' right-branches:  ∑lower_Pmin_Uu + ∑SB_Uu ≥',k,'+ 1')
            for cut in rightbranches:
                expr = 0      
                ## cut[1]=No_SB_Uu   cut[2]=lower_Pmin_Uu  cut[0]=SB_Uu   
                for f in cut[0]:  ## NUNCA SE MUEVE         ## Cuenta los cambios de 1 --> 0  
                    expr += 1 - model.u[f[0]+1,f[1]+1] 
                for f in cut[2]:  # cut[1]                  ## Cuenta los cambios de 0 --> 1 
                    expr +=     model.u[f[0]+1,f[1]+1] 
                model.cuts.add(expr >= k + 1)
                
                
                
    ## ---------------------------- LOCAL BRANCHING CONSTRAINT LBC2 (INTEGER VERSION)------------------------------------------    
    ## Define a neighbourhood with LBC2.
       
    if(option == 'lbc2'):
                  
        for f in No_SB_Uu:   
            model.u[f[0]+1,f[1]+1].domain = Binary    ## We remove the integrality constraint of the Binary Support 
            if improve == True:          
                model.u[f[0]+1,f[1]+1] = 0            ## Hints
        for f in SB_Uu:  
            model.u[f[0]+1,f[1]+1].domain = Binary    ## We remove the integrality constraint of the Binary Support 
            if improve == True:          
                model.u[f[0]+1,f[1]+1] = 1            ## Hints
            
        ## Hints para iniciar desde la última solución válida
        #if improve == True:
        for g in range(len(G)):
            for t in range(len(T)):
                model.v[g+1,t+1] = V[g][t]                  ## Hints
                model.w[g+1,t+1] = W[g][t]                  ## Hints
                if delta[g][t]  != 0:
                    model.delta[g+1,t+1,delta[g][t]] = 1    ## Hints
        
        model.cuts = pyo.ConstraintList()
        
        ## Local Branching Constraint (LBC) 
        if True:            
            ## Adding a new restrictions LEFT-BRANCH  <°|((><
            if improve == True or (timeover==True and improve == False) : 
                print('Adding  1  left-branch: ∑lower_Pmin_Uu  + ∑SB_Uu ≤',k)                
                expr = 0      
                for f in SB_Uu:                             ## Cuenta los cambios de 1 --> 0  
                    expr += 1 - model.u[f[0]+1,f[1]+1] 
                for f in lower_Pmin_Uu :  # No_SB_Uu        ## Cuenta los cambios de 0 --> 1 
                    expr +=     model.u[f[0]+1,f[1]+1]              
                model.cuts.add(expr <= k)      
        
            ## Adding a new restrictions RIGHT-BRANCH  >>++++++++|°> . o O
            print('Adding ',len(rightbranches),' right-branches:  ∑lower_Pmin_Uu  + ∑SB_Uu ≥',k,'+ 1')
            for cut in rightbranches:
                expr = 0      
                ## cut[1]=No_SB_Uu   cut[2]=lower_Pmin_Uu  cut[0]=SB_Uu   
                for f in cut[0]:  ## NUNCA SE MUEVE         ## Cuenta los cambios de 1 --> 0  
                    expr += 1 - model.u[f[0]+1,f[1]+1] 
                for f in cut[2]:  # cut[1]                  ## Cuenta los cambios de 0 --> 1 
                    expr +=     model.u[f[0]+1,f[1]+1] 
                model.cuts.add(expr >= k + 1)
                

    ## ---------------------------- HARD VARIABLE FIXING I  ------------------------------------------
    ## 
    if option == 'Hard':
        for f in SB_Uu:
            model.u[f[0]+1,f[1]+1].fix(1)                   ## Hard fixing
        for f in No_SB_Uu: 
            model.u[f[0]+1,f[1]+1] = 0                      ## Hints
        for f in lower_Pmin_Uu:
            model.u[f[0]+1,f[1]+1] = 0                      ## Hints
            
            
    ## ---------------------------- HARD VARIABLE FIXING III------------------------------------------
    ##     
    if option == 'Hard3':
        for f in SB_Uu:       
            model.u[f[0]+1,f[1]+1] = 1                      ## Hints   
        for f in No_SB_Uu: 
            model.u[f[0]+1,f[1]+1].fix(0)                   ## Hard fixing
        for f in lower_Pmin_Uu:
            model.u[f[0]+1,f[1]+1].unfix()    
            model.u[f[0]+1,f[1]+1] = 0                      ## Hints
     
     
    ## ---------------------------- CHECK FEASIABILITY ------------------------------------------
    ## 

    if option == 'Check':  
        
        # model.u.fix(0)
        # model.delta.fix(0) ***???!!!
        for f in SB_Uu: 
            model.u[f[0]+1,f[1]+1].domain = Binary 
            model.u[f[0]+1,f[1]+1].fix(1)                   ## Hard fixing
        for f in No_SB_Uu: 
            model.u[f[0]+1,f[1]+1].domain = Binary 
            model.u[f[0]+1,f[1]+1].fix(0)                   ## Hard fixing
        for g in range(0,len(model.G)):
            for t in range(0,len(model.T)):
                model.v[g+1,t+1].domain   = Binary 
                model.v[g+1,t+1].fix( V[g][t] )             ## Hard fixing
                model.w[g+1,t+1].domain   = Binary 
                model.w[g+1,t+1].fix( W[g][t] )             ## Hard fixing
                if delta[g][t] != 0:
                    model.delta[g+1,t+1,delta[g][t]].domain = Binary 
                    model.delta[g+1,t+1,delta[g][t]].fix(1) ## Hard fixing

                                
    ## ---------------------------- REDUCED COST ------------------------------------------
    ## 

    if option == 'RC':                             
        for f in SB_Uu: 
            # model.u[f[0]+1,f[1]+1].fix(1)                   ## Hard fixing
            model.u[f[0]+1,f[1]+1].setlb(1.0)                 ## Fix upper bound
                                
                    
    ## ---------------------------- KERNEL SEARCH ------------------------------------------
    ##
    if option == 'KS':    
        model.u.fix(0)                                      ## Hard fixing
        for f in kernel: 
            model.u[f[0]+1,f[1]+1].unfix()  
            model.u[f[0]+1,f[1]+1] = 1                      ## Hints
        for f in bucket: 
            model.u[f[2]+1,f[3]+1].unfix()                  ## Hard fixing
            model.u[f[2]+1,f[3]+1] = 0                      ## Hints
            
        model.cuts = pyo.ConstraintList()
        expr       = 0      
        for f in bucket:                                    ## Cuenta los elementos del bucket
            expr += model.u[f[2]+1,f[3]+1] 
        model.cuts.add(expr >= 1)      
        
    ## ---------------------------- Termina y regresa el modelo MILP ------------------------------------------

    ##print(option,'Pyomo model has been built <uc_Co.uc> --->',time.time()-t_o) 
    
    return model, inside90

