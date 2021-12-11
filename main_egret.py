from egret.parsers.pglib_uc_parser import create_ModelData


from pyomo.environ import *
from pyomo.opt import results
# from pyomo.opt.results import solver
# from pyomo.util.infeasible import log_infeasible_constraints
# from pyomo.opt import SolverStatus, TerminationCondition
from egret.models.unit_commitment import solve_unit_commitment
from egret.model_library.unit_commitment.uc_model_generator import UCFormulation, generate_model
from datetime import date
from datetime import datetime
from timeit import timeit
import util
import time
import sys

## GROUP     #INST  #GEN PERIOD FILES
##            n      G     T    uc_XX
## rts_gmlc   12     73    48   (45-56)
## ca         20    610    48   (1-20)
## ferc       12    934    48   (21-24),(37-44)
## ferc(2)    12    978    48   (25-36)

instancia = 'archivox.json'
instancia = 'anjos.json'
ruta      = 'instances/'
ambiente  = 'thinkpad'
if ambiente == 'yalma':
    if len(sys.argv) != 3:
        print("!!! Something went wrong, try something like: $python3 main_egret.py uc_45.json yalma")
        print("archivo:  ", sys.argv[1])
        print("ambiente: ", sys.argv[2])
        sys.exit()
    ambiente = sys.argv[2]
    instancia = sys.argv[1]

localtime = time.asctime(time.localtime(time.time()))

##ruta = '/home/uriel/GIT/UCVNS/ucvns/'
md = create_ModelData(ruta+instancia)

## Append a list as new line to an old csv file
row_file = [localtime,instancia]
util.append_list_as_row('solution.csv', row_file)
print(localtime, ' ', 'solving --->', instancia)

def create_my_unit_commitment_model(model_data,relaxed=False,**kwargs):
    my_uc_formulation = UCFormulation(  \
## Get the formulation from Compact of Knueven (2020)
       status_vars = 'garver_3bin_vars',  \
       power_vars = 'garver_power_vars', \
       reserve_vars = 'garver_power_avail_vars', \
       generation_limits ='MLR_generation_limits',   \
       ramping_limits = 'damcikurt_ramping',  \
       production_costs = 'HB_production_costs',  \
       uptime_downtime = 'rajan_takriti_UT_DT',  \
       startup_costs = 'MLR_startup_costs',  \
       network_constraints = 'copperplate_power_flow')   
    #      
## Get the formulation from Carrion and Arroyo (2006)
    #    status_vars = 'CA_1bin_vars',  \
    #    power_vars = 'basic_power_vars',  \
    #    reserve_vars = 'CA_power_avail_vars',  \
    #    generation_limits = 'CA_generation_limits',  \
    #    ramping_limits = 'CA_ramping_limits',  \
    #    production_costs = 'CA_production_costs',  \
    #    uptime_downtime = 'CA_UT_DT',  \
    #    startup_costs = 'CA_startup_costs',  \
    #    network_constraints = 'copperplate_power_flow')  \
    #
## Other formulation.
    #    status_vars = 'garver_3bin_vars', \
    #    power_vars = 'garver_power_vars', \
    #    reserve_vars = 'MLR_reserve_vars', \
    #    generation_limits = 'pan_guan_gentile_KOW_generation_limits', \
    #    ramping_limits = 'damcikurt_ramping', \
    #    production_costs = 'KOW_production_costs_super_tight', \
    #    uptime_downtime = 'rajan_takriti_UT_DT_2bin', \
    #    startup_costs = 'KOW_startup_costs', \
    #    network_constraints = 'ptdf_power_flow')
    return generate_model(model_data, my_uc_formulation, relax_binaries=relaxed, **kwargs)


t_o = time.time()  ## Start of the calculation time count
print('SOLVING COMPACT-KNUEVEN MODEL')
md_sol = solve_unit_commitment(md,'cplex',mipgap=0.001,timelimit=7000,uc_model_generator=create_my_unit_commitment_model)

print('Objective value:', md_sol.data['system']['total_cost'])

#log_infeasible_constraints(model)
z_exact = md_sol.obj.expr()
t_exact = time.time() - t_o
print("z_exact = ", z_exact)
print("t_exact = ", t_exact)

# ## write the solution to an Egret *.json file
# md_sol.write(os.path.join(this_module_path, 'solution.json'))
# print('Wrote solution to solution.json' )


row_file = [localtime, instancia,  round(z_exact,1), round(t_exact,2) ]  # data to csv
util.append_list_as_row('stat.dat', row_file)


