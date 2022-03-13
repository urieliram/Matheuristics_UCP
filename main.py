## --------------------------------------------------------------------------------
## File: main.py
## Unit Commitment Problem 
## Developers: Uriel Iram Lezama Lope
## Purpose: Programa principal de un modelo de UC
## Description: Lee una instancia de UCP y la resuelve. 
## Para correr el programa usar el comando "python3 main.py anjos.json thinkpad"
## --------------------------------------------------------------------------------

import time
import sys
import uc_Co
import util
import reading
from   solution import Solution

## Instances features
## GROUP     #INST  #GEN PERIOD FILES
##            n      G     T    uc_XX
## rts_gmlc   12     73    48   (45-56)
## ca         20    610    48   (1-20)
## ferc       12    934    48   (21-24),(37-44)
## ferc(2)    12    978    48   (25-36)

instancia = 'uc_45 - copia.json'
instancia = 'archivox.json'      # z_milp0.1=292812718.45270145, z_lp0.1=279311866.4, z_milp0.001=283849653.53052485
instancia = 'anjos.json'         # z_milp=9700.0, z_lp=8328.7

ruta      = 'instances/'
ambiente  = 'localPC'
if ambiente == 'yalma':
    if len(sys.argv) != 3:
        print("!!! Something went wrong, try something like: $python3 main.py uc_45.json yalma")
        print("archivo:  ", sys.argv[1])
        print("ambiente: ", sys.argv[2])
        sys.exit()
    ambiente  = sys.argv[2]
    instancia = sys.argv[1]

localtime = time.asctime(time.localtime(time.time()))

## Append a list as new line to an old csv file using as log
new_row = [localtime,instancia,""]
util.append_list_as_row('log.csv', new_row)
print(localtime,        'solving --->', instancia)

## Lee instancia de archivo .json con formato de Knueven2020
G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,Pb,C,mpc,Cs,Tmin,names = reading.reading(ruta+instancia)

## Start of the calculation time count.
t_o = time.time() 

fix   = False        ## True si se fija la solución entera, False, si se desea resolver de manera exacta.
relax = False         ## True si se relaja la solución entera, False, si se desea resolver de manera entera.
model = uc_Co.uc(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,pc_0,mpc,Pb,C,Cs,Tmin,names,fix,relax)

sol = Solution(model    = model,
               nameins  = instancia,
               env      = ambiente,
               gap      = 0.1,
               time     = 300,
               tee      = False,
               tofile   = True)

z = sol.solve_problem() ## Prepara solver y resuelve modelo

print("z = ", z)