# --------------------------------------------------------------------------------
# File: uc_Co.py
# Developers: Uriel Iram Lezama Lope
# Purpose: UC "Compact" model introduced by Knueven2020b
# Description:
# Objetive               (69)*
# Up-time/down-time      (2)*, (3)*, (4)*, (5)*   'garver_3bin_vars',
#                                                 'rajan_takriti_UT_DT',
# Generation limits      (17)*, (20)*, (21)*      'MLR_generation_limits',
#                                                 'garver_power_vars',
#                                                 'garver_power_avail_vars',
# Ramp limits            (35)*, (36)*             'damcikurt_ramping',
# Piecewise production   (50)*                    'HB_production_costs',
# Start-up cost          (54)*, (55)*, (56)*      'MLR_startup_costs',
# System constraints     (67)*
# --------------------------------------------------------------------------------
import pyomo.environ as pyo
from pyomo.environ import *

def uc(G,T,S,Piecewise,Pmax,Pmin,UT,DT,De,R,CR,u_0,U,D,SU,SD,RU,RD,pc_0,fixShedu,relax,ambiente):
    model = pyo.ConcreteModel(name="UC")
    
    model.S    = pyo.Set(initialize = S)
    model.G    = pyo.Set(initialize = G)
    model.T    = pyo.Set(initialize = T)
    
    model.Pmax = pyo.Param(model.G , initialize = Pmax,within=Any)
    model.Pmin = pyo.Param(model.G , initialize = Pmin,within=Any)
    model.UT   = pyo.Param(model.G , initialize = UT,within=Any)
    model.DT   = pyo.Param(model.G , initialize = DT,within=Any)
    model.De   = pyo.Param(model.T , initialize = De,within=Any)
    model.R    = pyo.Param(model.T , initialize = R,within=Any)
    model.CR   = pyo.Param(model.G , initialize = CR,within=Any)
    model.u_0  = pyo.Param(model.G , initialize = u_0,within=Any)
    model.D    = pyo.Param(model.G , initialize = D,within=Any)
    model.U    = pyo.Param(model.G , initialize = U,within=Any)
    model.SU   = pyo.Param(model.G , initialize = SU,within=Any)
    model.SD   = pyo.Param(model.G , initialize = SD,within=Any)
    model.RU   = pyo.Param(model.G , initialize = RU,within=Any)
    model.RD   = pyo.Param(model.G , initialize = RD,within=Any)
    model.pc_0  = pyo.Param(model.G , initialize = pc_0,within=Any)
    model.c    = pyo.Param(model.G , initialize = {1:5,2:15,3:30},within=Any)
    model.cU   = pyo.Param(model.G , initialize = {1:800,2:500,3:250},within=Any)
    CLP = 999999999999.0 #penalty cost for failing to meet or exceeding load ($/megawatt-hour (MWh)).
    CRP = 999999999999.0 #penalty cost for failing to meet reserve requirement
 
    if(relax == False): #Si se desea relajar las variables enteras como continuas
        model.u     = pyo.Var( model.G , model.T ,          within=Binary)
        model.v     = pyo.Var( model.G , model.T ,          within=Binary)
        model.w     = pyo.Var( model.G , model.T ,          within=Binary)
        model.delta = pyo.Var( model.G , model.T , model.S, within=Binary)
    
    else:        
        model.u     = pyo.Var( model.G , model.T ,          within=UnitInterval)
        model.v     = pyo.Var( model.G , model.T ,          within=UnitInterval)
        model.w     = pyo.Var( model.G , model.T ,          within=UnitInterval)
        model.delta = pyo.Var( model.G , model.T , model.S, within=UnitInterval)
    model.p         = pyo.Var( model.G , model.T , bounds=(0.0,99999.0))
    model.pb        = pyo.Var( model.G , model.T , bounds=(0.0,99999.0))
    model.pbc       = pyo.Var( model.G , model.T , bounds=(0.0,99999.0))   # pbarra' (capacidad máxima de salida con reserva arriba del m.Pmin)
    model.pc        = pyo.Var( model.G , model.T , bounds=(0.0,99999.0))   # p' (potencia de salida arriba del m.Pmin)
    model.r         = pyo.Var( model.G , model.T , bounds=(0.0,99999.0))   # reserve
    model.cp        = pyo.Var( model.G , model.T , bounds=(0.0,9999999.0))
    model.cSU       = pyo.Var( model.G , model.T , bounds=(0.0,9999999.0))
    model.cSD       = pyo.Var( model.G , model.T , bounds=(0.0,9999999.0))
    model.snplus    = pyo.Var( model.T ,           bounds=(0.0,9999999.0)) #surplus demand
    model.snminus   = pyo.Var( model.T ,           bounds=(0.0,9999999.0)) #surplus demand
    model.sn        = pyo.Var( model.T ,           bounds=(0.0,9999999.0)) #surplus demand
    model.sR        = pyo.Var( model.T ,           bounds=(0.0,9999999.0)) #surplus reserve    
   
    ## https://pyomo.readthedocs.io/en/stable/working_models.html
    # model.u[3,1].fix(0)
    # model.v[3,1].fix(0)
    # model.v[3,3].fix(0)
    # model.v[3,4].fix(0)
    # model.v[3,2].fix(0)
    # model.u[2,3].fix(0)
    # model.u[2,4].fix(0)
    # model.u[2,5].fix(0)
    # model.u[2,6].fix(0)

    # if(FixShedu == True): #Si se desea usar la solución fixed
    #     model.u.fix(0)
    #     model.u.set_values(Shedule_dict)

    def obj_rule(m): #Costo sin piecewise
        return sum(m.cp[g,t]                              for g in m.G for t in m.T) \
             + sum(m.CR[g] * m.u[g,t]                     for g in m.G for t in m.T) \
             + sum(m.sR[t] * CLP                                       for t in m.T) \
             + sum(m.sn[t] * CRP                                       for t in m.T) \
             + sum(m.cU[g] * m.v[g,t] + m.c[g] * m.p[g,t] for g in m.G for t in m.T) 
    model.obj = pyo.Objective(rule = obj_rule)

    # -----------------------------GARVER------------------------------------------  

    def logical_rule(m,g,t):    # logical eq.(2)
        if t == 1:
            return m.u[g,t] - m.u_0[g]   == m.v[g,t] - m.w[g,t]
        else:
            return m.u[g,t] - m.u[g,t-1] == m.v[g,t] - m.w[g,t]
    model.logical = pyo.Constraint(model.G,model.T,rule = logical_rule)
    
    # ----------------------------POWER EQUALS------------------------------------  

    def pow_igual_rule(m,g,t):  # iguala p a pc eq.(12)
        return m.p[g,t] == m.pc[g,t] + m.Pmin[g] * m.u[g,t]
    model.pow_igual = pyo.Constraint(model.G,model.T, rule = pow_igual_rule)    

    def pow_igual_rule2(m,g,t): # iguala pb a pcb eq.(13)
        return m.pb[g,t] == m.pbc[g,t] + m.Pmin[g] * m.u[g,t]
    model.pow_igual2 = pyo.Constraint(model.G,model.T, rule = pow_igual_rule2)    

    def pow_igual_rule3(m,g,t): # iguala pb a pcb eq.(14)
        return m.pbc[g,t] == m.pc[g,t] + m.r[g,t]
    model.pow_igual3 = pyo.Constraint(model.G,model.T, rule = pow_igual_rule3)

    def pow_igual_rule4(m,g,t): # iguala pb a pcb eq.(15)
        return m.pb[g,t] == m.p[g,t] + m.r[g,t]
    model.pow_igual4 = pyo.Constraint(model.G,model.T, rule = pow_igual_rule4)    

    def pow_igual_rule5(m,g,t): # pow_pow eq.(16)
        return m.p[g,t] <= m.pb[g,t] 
    model.pow_igual5 = pyo.Constraint(model.G,model.T, rule = pow_igual_rule5)    

    def pow_igual_rule6(m,g,t): # pow_pow eq.(17)
        return m.pc[g,t] <= m.pbc[g,t] 
    model.pow_igual6 = pyo.Constraint(model.G,model.T, rule = pow_igual_rule6)    

    # ------------------------------START-UP AND SHUT-DOWN RAMPS---------------------------------   

    def sdsu_ramp_rule20(m,g,t):          # eq.(20) 
        if m.UT[g] > 1 and t < len(m.T):  # :g ∈ G>1
            return m.pc[g,t] + m.r[g,t] <= (m.Pmax[g]-m.Pmin[g])*m.u[g,t] \
                - (m.Pmax[g]-m.SU[g])*m.v[g,t] - (m.Pmax[g]-m.SD[g])*m.w[g,t+1]
        else:
            return pyo.Constraint.Skip    
    model.sdsu_ramp_rule20 = pyo.Constraint(model.G,model.T, rule = sdsu_ramp_rule20)

    def su_ramp_rule21a(m,g,t):           # eq.(21a)
        if m.UT[g] == 1:                  # :g ∈ G1
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
    
    # -------------------------------LIMITS & RAMPS------------------------------------------   
    
    
    def up_ramp_rule35(m,g,t):          # ramp-up eq.(35)
        if t == 1:
            return m.pc[g,t] - (m.pc_0[g]) <= (m.SU[g]-m.Pmin[g]-m.RU[g])*m.v[g,t] + m.RU[g]*m.u[g,t]
        else:
            return m.pc[g,t] - m.pc[g,t-1]  <= (m.SU[g]-m.Pmin[g]-m.RU[g])*m.v[g,t] + m.RU[g]*m.u[g,t]
    model.up_ramp_rule35 = pyo.Constraint(model.G,model.T, rule = up_ramp_rule35)   

    def down_ramp_rule36(m,g,t):        # ramp-down eq.(36) 
        if t == 1:
            return (m.pc_0[g])  - m.pc[g,t] <= (m.SD[g]-m.Pmin[g]-m.RD[g])*m.w[g,t] + m.RD[g]*m.u_0[g]
        else:
            return m.pc[g,t-1] - m.pc[g,t] <= (m.SD[g]-m.Pmin[g]-m.RD[g])*m.w[g,t] + m.RD[g]*m.u[g,t-1]
    model.down_ramp_rule36 = pyo.Constraint(model.G,model.T, rule = down_ramp_rule36)

    # -------------------------------DEMAND & RESERVE----------------------------------------   
 
    def demand_rule65(m,t):                      # demand eq.(65)
        return sum( m.p[g,t] for g in m.G ) + m.sn[t]  == m.De[t] 
        # return sum( m.p[g,t] for g in m.G ) + 0  == m.De[t] 
    model.demand_rule65 = pyo.Constraint(model.T, rule = demand_rule65)
    
    def demand_rule66a(m,t):                      # holguras o excesos en la demanda eq.(66a)
         return m.sn[t] == m.snplus[t] - m.snminus[t]  
    model.demand_rule66a = pyo.Constraint(model.T, rule = demand_rule66a)

    def demand_rule67(m,t):                      # demand + reserve eq.(67)
        # return sum( m.pb[g,t] for g in m.G ) + m.sR[t] >= m.De[t] + m.R[t] 
        return sum( m.pb[g,t] for g in m.G ) + 0 >= m.De[t] + m.R[t] 
    model.demand_rule67 = pyo.Constraint(model.T, rule = demand_rule67)

    def demand_reserve(m,t):                      # reserve
        # return sum( m.r[g,t] for g in m.G) + m.sR[t] >= m.R[t] 
        return sum( m.r[g,t] for g in m.G) + 0 >= m.R[t] 
    model.demand_reserve = pyo.Constraint(model.T, rule = demand_reserve)

    # --------------------------------MINIMUM UP/DOWN TIME---------------------------------------

    def mut_rule(m,g,t):  # minimum-up time eq.(4)
        if t >= value(m.UT[g]):
            return sum( m.v[g,i] for i in range(t-value(m.UT[g])+1,t+1)) <= m.u[g,t]        
        else:
            return pyo.Constraint.Skip
    model.mut = pyo.Constraint(model.G,model.T, rule = mut_rule)
    
    print(model.mut[1,3].expr)  # For only one index of Constraint List
    print(model.mut[1,4].expr)  # For only one index of Constraint List
    print(model.mut[1,5].expr)  # For only one index of Constraint List
    print(model.mut[1,6].expr)  # For only one index of Constraint List

    def mdt_rule(m,g,t): # minimum-down time eq.(5)
        if t >= value(m.DT[g]):
            return sum( m.w[g,i] for i in range(t-value(m.DT[g])+1,t+1)) <= 1 - m.u[g,t] 
        else:
            return pyo.Constraint.Skip
    model.mdt = pyo.Constraint(model.G,model.T, rule = mdt_rule)
        
    print(model.mdt[1,2].expr)  # For only one index of Constraint List
    print(model.mdt[1,3].expr)  # For only one index of Constraint List
    print(model.mdt[1,4].expr)  # For only one index of Constraint List
    print(model.mdt[1,5].expr)  # For only one index of Constraint List
    print(model.mdt[1,6].expr)  # For only one index of Constraint List

    def mdt_rule2(m,g): # enforce the minimum-down time eq.(3b)
        minimo = min( value(D[g]),len(m.T) )
        if minimo > 0:
            return sum( m.u[g,i] for i in range(1,minimo+1)) == 0
        else: 
            return pyo.Constraint.Skip        
    model.mdt2 = pyo.Constraint(model.G, rule = mdt_rule2)
    
    #model.mdt2.pprint()         # For entire Constraint List
    #print(model.mdt2[3].expr)  # For only one index of Constraint List
    
    def mut_rule2(m,g):  # enforce the minimum-up time eq.(3a)
        minimo = min( value(m.U[g]) , len(m.T) )
        if minimo > 0:
            return sum( m.u[g,i] for i in range(1,minimo+1) ) == int(minimo)
        else: 
            return pyo.Constraint.Skip
    model.mut2 = pyo.Constraint(model.G, rule = mut_rule2)

    #model.mut2.pprint()       # For entire Constraint List
    #print(model.mut2[1].expr)  # For only one index of Constraint List
    
    # ----------------------------PIECEWISE-------------------------------------------   
    # # compute the per-generator, per-time period production costs. We'll do this by hand
    # def piecewise_production_costs_index_set_generator(model):
    #     return ((model.G,model.T,i) for g in G for t in T for i in range(len(Piecewise[g,t])-1))
    # model.PiecewiseProductionCostsIndexSet = Set(initialize=piecewise_production_costs_index_set_generator, dimen=3)
    
    # def _production_cost_function(model, g, t, i):
    #     return model.PowerGenerationPiecewiseCostValues[g,t][i]
    # def piecewise_rule(model,model.G,model.T,l):  # piecewise production costs
    #     # x0 = m.PowerGenerationPiecewisePoints[g,t][i]
    #     # x1 = m.PowerGenerationPiecewisePoints[g,t][i+1]
    #     # y0 = _production_cost_function(m,model.G,model.T,i)
    #     # y1 = _production_cost_function(m,model.G,model.T,i+1)
    #     # slope = (y1 - y0)/ (x1 - x0) 
    #     # intercept = -slope*x0 + y0
    #     slope = c[g]
    #     intercept = 0
    #     return model.cp[g,t] >= slope * model.p[g,t] + intercept * model.u[g,t] 
    # model.piecewise = Constraint(model.G,model.T,Piecewise, rule=piecewise_rule)
    # model.piecewise = pyo.Constraint(model.G,model.T, rule = piecewise_rule)

    # def piecewise_production_cost_rule(m, g, t, i):

    #     x0 = m.PowerGenerationPiecewisePoints[g,t][i]
    #     x1 = m.PowerGenerationPiecewisePoints[g,t][i+1]
    #     y0 = _production_cost_function(m,model.G,model.T,i)
    #     y1 = _production_cost_function(m,model.G,model.T,i+1)
    #     slope = (y1 - y0)/ (x1 - x0) 
    #     intercept = -slope*x0 + y0

    #     # this will be good regardless
    #     return m.ProductionCost[g,t] >= slope*m.PowerGeneratedAboveMinimum[g,t] + intercept*m.UnitOn[g,t]

    # model.ProductionCostConstr = Constraint(model.PiecewiseProductionCostsIndexSet, rule=piecewise_production_cost_rule)

    # _compute_total_production_cost(model)
    
    return model