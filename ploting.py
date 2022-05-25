import numpy as np
import pandas as pd
from   Extract import Extract
import matplotlib.pyplot as plt
import sys
import util

## --------------------------------- GRAFICAS -------------------------------------------

instancia = 'uc_02.json'       ## ejemplo de batalla 

instancia = 'uc_56.json'       ## ejemplo de batalla  
instancia = 'uc_55.json'       ## ejemplo de batalla  
instancia = 'uc_54.json'       ## ejemplo de batalla  
instancia = 'uc_53.json'       ## ejemplo de batalla  
instancia = 'uc_51.json'       ## ejemplo de batalla  
instancia = 'uc_50.json'       ## ejemplo de batalla  
instancia = 'uc_49.json'       ## ejemplo de batalla  
instancia = 'uc_48.json'       ## ejemplo de batalla  
instancia = 'uc_47.json'       ## ejemplo de batalla  
instancia = 'uc_46.json'       ## ejemplo de batalla  
instancia = 'uc_45.json'       ## ejemplo de batalla  
instancia = 'archivox.json'    ## ejemplo sencillo

## Cargamos parámetros de configuración desde archivo <config>
ambiente, ruta, executable, timeheu, timemilp, gap = util.config_env()
if ambiente == 'yalma':
    if len(sys.argv) != 2:
        print("!!! Something went wrong, try write something like: $python3 ploting.py uc_02")
        print("archivo :", sys.argv[1])
        sys.exit()
    instancia = sys.argv[1]

##Recordar que el pibite es el tercer dataframe bb3
print('Ploting '+instancia[0:5]+'.log')
bb1,vari = Extract().extract('logfile'+'Milp'+instancia[0:5]+'.log')  
bb2,vari = Extract().extract('logfile'+'Hard'+instancia[0:5]+'.log') 
bb3,vari = Extract().extract('logfile'+'Soft7'+instancia[0:5]+'.log')   
Extract().plot_four_in_one(bb1,bb2,bb3,'Milp','Hard','Soft7',instancia[0:5],id='a')

bb1,vari = Extract().extract('logfile'+'Hard2'+instancia[0:5]+'.log') 
bb2,vari = Extract().extract('logfile'+'Hard3'+instancia[0:5]+'.log') 
bb3,vari = Extract().extract('logfile'+'Hard'+instancia[0:5]+'.log')    
Extract().plot_four_in_one(bb1,bb2,bb3,'Hard2','Hard3','Hard',instancia[0:5],id='a')


# bb1,vari = Extract().extract('logfile'+'Softp'+instancia[0:5]+'.log')   
# bb2,vari = Extract().extract('logfile'+'Soft4'+instancia[0:5]+'.log') 
# bb3,vari = Extract().extract('logfile'+'Soft7'+instancia[0:5]+'.log')  
# Extract().plot_four_in_one(bb1,bb2,bb3,'Softp','Soft4','Soft7',instancia[0:5],id='b')