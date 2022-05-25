import numpy as np
import pandas as pd
from   Extract import Extract
import matplotlib.pyplot as plt
import sys
import util

## --------------------------------- GRAFICAS -------------------------------------------


instancia = 'archivox.json'    ## ejemplo sencillo
instancia = 'uc_45.json'       ## ejemplo de batalla  

## Cargamos parámetros de configuración desde archivo <config>
ambiente, ruta, executable, timeheu, timemilp, gap = util.config_env()
if ambiente == 'yalma':
    if len(sys.argv) != 2:
        print("!!! Something went wrong, try write something like: $python3 ploting.py uc_02")
        print("archivo :", sys.argv[1])
        sys.exit()
    instancia = sys.argv[1]

print('logfile'+'Milp'+instancia[0:5]+'.log')
bb2,vari = Extract().extract('logfile'+'Hard'+instancia[0:5]+'.log') 
bb3,vari = Extract().extract('logfile'+'Softp'+instancia[0:5]+'.log') 
bb1,vari = Extract().extract('logfile'+'Milp'+instancia[0:5]+'.log')    
Extract().plot_four_in_one(bb1,bb2,bb3,'MILP','Hard-fix','Soft-fix',instancia[0:5])


bb1,vari = Extract().extract('logfile'+'Softp'+instancia[0:5]+'.log')   
bb2,vari = Extract().extract('logfile'+'Soft4'+instancia[0:5]+'.log') 
bb3,vari = Extract().extract('logfile'+'Soft7'+instancia[0:5]+'.log')  
Extract().plot_four_in_one(bb1,bb2,bb3,'Softp','Soft4','Soft7',instancia[0:5])