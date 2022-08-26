import json
import util
import shutil
import os
import pandas as pd
import numpy as np

def reading(file):
    with open(file) as json_file:
        md = json.load(json_file)
        
    G       = []   ## generators number
    T       = []   ## periodos de tiempo
    S       = {}   ## eslabones de costo variable de arranque
    L       = {}   ## eslabones de costo en piecewise
    C       = {}   ## cost of segment of piecewise
    Pb      = {}   ## maximum power available for piecewise segment L for generator g (MW).
    Cb      = {}   ## cost of generator g producing Pb MW of power ($/h).
    De      = {}   ## load
    R       = {}   ## reserve_requirement
    Pmin    = {}   ## power min
    Pmax    = {}   ## power max
    RU      = {}   ## ramp_up_limit", "ramp_up_60min"
    RD      = {}   ## ramp_down_limit", "ramp_down_60min"
    SU      = {}   ## ramp_startup_limit", "startup_capacity"
    SD      = {}   ## ramp_shutdown_limit", "shutdown_capacity"
    TU      = {}   ## time_upminimum
    TD      = {}   ## time_down_minimum
    D       = {}   ## number of hours generator g is required to be off at t=1 (h).
    U       = {}   ## number of hours generator g is required to be on at t=1 (h).
    TD_0    = {}   ## Number of hours that the unit has been offline before the scheduling horizon.
    p_0     = {}   ## power_output_t0
    mpc     = {}   ## cost of generator g running and operating at minimum production Pmin ($/h).
    C       = {}   ## 
    Cs      = {}   ## Costo de cada escalón del conjunto S de la función de costo variable de arranque.
    Tunder  = {}   ## lag de cada escalón del conjunto S de la función de costo variable de arranque.
    Startup = {}   ## start-up cost
        
    time_periods = int(md['time_periods'])
    demand       = md['demand']  
    reserves     = md['reserves']  

    for t in range(1, time_periods+1):
        T.append(t)    
    De   = dict(zip(T, demand))
    R    = dict(zip(T, reserves))
    
    names_list = []
    i = 1
    ## Se obtiene nombre de los generadores y número
    for gen in md['thermal_generators']:  
        names_list.append(gen)
        G.append(i)
        i+=1
        
    must_run             = []
    power_output_minimum = []
    power_output_maximum = []
    ramp_up_limit        = []
    ramp_down_limit      = []
    ramp_startup_limit   = []
    ramp_shutdown_limit  = []
    time_up_minimum      = []
    time_down_minimum    = []
    power_output_t0      = []
    unit_on_t0           = []
    time_up_t0           = []
    time_down_t0         = []   
    startup              = []
    piecewise_production = []
    Piecewise            = []
    Startup              = []
    Ulist                = []
    Dlist                = []
    TD0list              = []
    p_0_list             = []
    u_0_list             = []
    fixed_cost           = []
    abajo_min =0
    
    ## To get the data from the generators
    i=1 ## Cuenta los generadores
    for gen in names_list:  
        must_run.append(md['thermal_generators'][gen]["must_run"]) #0,
        power_output_minimum.append(md['thermal_generators'][gen]["power_output_minimum"])#80
        power_output_maximum.append(md['thermal_generators'][gen]["power_output_maximum"])#300.0
        ramp_up_limit.append(md['thermal_generators'][gen]["ramp_up_limit"])#50
        ramp_down_limit.append(md['thermal_generators'][gen]["ramp_down_limit"])#30
        ramp_startup_limit.append(md['thermal_generators'][gen]["ramp_startup_limit"])#100
        ramp_shutdown_limit.append(md['thermal_generators'][gen]["ramp_shutdown_limit"])#80
        time_up_minimum.append(md['thermal_generators'][gen]["time_up_minimum"])#3
        time_down_minimum.append(md['thermal_generators'][gen]["time_down_minimum"])#2
        power_output_t0.append(md['thermal_generators'][gen]["power_output_t0"])#120
        unit_on_t0.append(md['thermal_generators'][gen]["unit_on_t0"])#1
        time_up_t0.append(md['thermal_generators'][gen]["time_up_t0"])#1
        time_down_t0.append(md['thermal_generators'][gen]["time_down_t0"])#0        
        try:
            fixed_cost.append(md['thermal_generators'][gen]["fixed_cost"] )        
            #print(md['thermal_generators'][gen]["fixed_cost"] )       
        except:
            fixed_cost.append(0)   
            
        startup = (md['thermal_generators'][gen]["startup"]) # variable start-up cost
        piecewise_production = md['thermal_generators'][gen]["piecewise_production"] #piecewise cost
        
        ## Para obtener los piecewise del costo de los generadores
        lista_aux = []
        j = 0
        for piece in piecewise_production:
            lista_aux.append((piece['mw'],piece['cost']))
            j+=1            
        Piecewise.append(lista_aux)
        
        lista = []
        jj=1
        for ii in range(j-1):
            lista.append(jj)
            jj= jj+1
        L[i] = lista
                
        ## Obtiene segmentos del costo variable de arranque
        lista_aux2 = []
        lista2 = []
        j = 1        
        for segment in startup:
            if segment['lag']>=time_down_minimum[i-1]:
                lista_aux2.append((segment['lag'],segment['cost']))
                lista2.append(j)
                j+=1         
            
        Startup.append(lista_aux2)
        S[i] = lista2
        
        ## Caso apagado
        if unit_on_t0[i-1] == 0: 
            u_0_list.append(0)   
            aux=max(0,time_down_minimum[i-1] - time_down_t0[i-1])
            Ulist.append(0)
            Dlist.append(aux)
            TD0list.append(time_down_t0[i-1])    
        else:  
        ## Caso prendido
            u_0_list.append(1)
            aux=max(0,time_up_minimum[i-1] - time_up_t0[i-1])
            Ulist.append(aux)
            Dlist.append(0)
            TD0list.append(0)

                
        ## Validaciones de prendido y apagado
        if power_output_t0[i-1] !=0 and unit_on_t0[i-1] == 0:
            print('Error: The generator ',str(i),' cannot be off and its output greater than zero')
            quit()
        if time_down_t0[i-1] !=0 and unit_on_t0[i-1] != 0:
            print('Error: The generator  ',str(i),' cannot be off and on at the same time')
            quit()
        
        ########################################################################
        ## Este código considera las potencias de arranque de los generadores
        #           10             -          100             =   -90  prendido
        #           0              -          100             =   -100 apagado       
        if power_output_t0[i-1]<power_output_minimum[i-1] and power_output_t0[i-1]!=0: ## potencia abajo del mínimo
            abajo_min=abajo_min+1
            print('estado=',gen,unit_on_t0[i-1])
        p_0_list.append(power_output_t0[i-1])
        ########################################################################
                                 
        i+=1  ## Se incrementa un generador  
                            
       
       
    ## Se extraen los diccionarios Pb y C de la lista de listas Piecewise    
    k=0; n=0
    for i in Piecewise:
        k=k+1
        n=0
        for j in i:
            n=n+1
            C[k,n] = j[1]
            # ## Se calcula el costo mínimo de operación mpc
            # if n==1:
            #     mpc[k] = j[0]*j[1] 
        del C[(k,n)]      
         
        
    k=0; n=0
    for i in Piecewise:
        k=k+1
        n=0
        for j in i:
            if n!=0:
                #print(k,",",n,",",j[0],",",j[1])
                Pb[k,n] = j[0]
                Cb[k,n] = j[1]   
            n=n+1
                
    ## Se extraen los diccionarios Tunder y Cs de la lista de listas Startup    
    k=0; n=0
    for i in Startup:
        k=k+1
        n=0
        for j in i:
            n=n+1
            # print(k,",",n,",",j[0],",",j[1])
            Tunder[k,n] = j[0]
            Cs[k,n]     = j[1] 
    
    ## Aqui se pasan de arreglos a diccionarios como los usa Pyomo
    Pmax = dict(zip(G, power_output_maximum))
    Pmin = dict(zip(G, power_output_minimum))
    TU   = dict(zip(G, time_up_minimum))     
    TD   = dict(zip(G, time_down_minimum))  
    u_0  = dict(zip(G, u_0_list))          
    U    = dict(zip(G, Ulist))              
    D    = dict(zip(G, Dlist))             
    TD_0 = dict(zip(G, TD0list))                
    SU   = dict(zip(G, ramp_startup_limit))
    SD   = dict(zip(G, ramp_shutdown_limit))
    RU   = dict(zip(G, ramp_up_limit))
    RD   = dict(zip(G, ramp_down_limit))
    p_0  = dict(zip(G, p_0_list))  
    names= dict(zip(G, names_list))  
    mpc  = dict(zip(G, fixed_cost))  
    
    ## -----------------  Caso de ejemplo de anjos.json  --------------------------
    #G        = [1, 2, 3]
    #T        = [1, 2, 3, 4, 5, 6]
    #L        = {1: [1, 2, 3], 2: [1, 2, 3], 3: [1, 2, 3, 4]}
    #S        = {1: [1, 2, 3], 2: [1, 2, 3], 3: [1, 2, 3, 4]}
    #Pmax     = {1: 300.0, 2: 200.0, 3: 100.0}
    #Pmin     = {1: 80, 2: 50, 3: 30}
    #TU       = {1: 3, 2: 2, 3: 1}
    #TD       = {1: 2, 2: 2, 3: 2}
    #De       = {1: 240, 2: 250, 3: 200, 4: 170, 5: 230, 6: 190}
    #R        = {1: 10, 2: 10, 3: 10, 4: 10, 5: 10, 6: 10}
    #u_0      = {1: 1, 2: 0, 3: 0}
    #D        = {1: 0, 2: 0, 3: 0}
    #U        = {1: 2, 2: 0, 3: 0}
    #SU       = {1: 100, 2: 70, 3: 40}
    #SD       = {1: 80, 2: 50, 3: 30}
    #RU       = {1: 50, 2: 60, 3: 70}
    #RD       = {1: 30, 2: 40, 3: 50}
    #p_0     = {1: 40, 2: 0, 3: 0}
    #mpc      = {1: 400.0, 2: 750.0, 3: 900.0}
    #Pb       = {(1, 1): 80, (1, 2): 150, (1, 3): 300, (2, 1): 50, (2, 2): 100, (2, 3): 200, (3, 1): 30, (3, 2): 50, (3, 3): 70, (3, 4): 100}   
    #C        = {(1, 1): 5.0, (1, 2): 5.0, (1, 3): 5.0, (2, 1): 15.0, (2, 2): 15.0, (2, 3): 15.0, (3, 1): 30.0, (3, 2): 30.0, (3, 3): 30.0, (3, 4): 30.0}
    #Cs       = {(1, 1): 800.0, (1, 2): 800.0, (1, 3): 800.0, (2, 1): 500.0, (2, 2): 500.0, (2, 3): 500.0, (3, 1): 25.0, (3, 2): 250.0, (3, 3): 
    #500.0, (3, 4): 1000.0}
    #Tunder     = {(1, 1): 2, (1, 2): 3, (1, 3): 4, (2, 1): 2, (2, 2): 3, (2, 3): 4, (3, 1): 2, (3, 2): 3, (3, 3): 4, (3, 4): 5}
    #fixShedu = False
    #relax    = False
    #ambiente = 'localPC'
    ## ----------------------------------  o  -------------------------------------
    
    #to_dirdat(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,p_0,Pb,C,mpc,Cs,Tunder,names)
    
    # validation(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,Pb,Cb,C,mpc,Cs,Tunder,names,abajo_min)
       
    return G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,Pb,Cb,C,mpc,Cs,Tunder,names
          
          
# (EN PROCESO ...)
def validation(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,Pb,Cb,C,mpc,Cs,Tunder,names,abajo_min): 
        
    print('>>> generadores abajo del límite mínimo:',abajo_min)  
       
    print('*** Capacidades totales de los generadores en el tiempo cero ***')
    gen0=0
    for i in p_0:
        gen0 = p_0[i] + gen0 
    print('potencia p_0            =',gen0)
    maxi=0
    for i in Pmax:
        if u_0[i]==1:
          maxi = Pmax[i] + maxi
    maxi = maxi - gen0
    print('capacidad subir gen_0   =',maxi)    
    mini=0
    for i in Pmin:
        if u_0[i]==1:
          mini = Pmin[i] + mini
    mini = gen0 - mini
    print('capacidad bajar gen_0   =',mini)
    
    rampUp=0
    for i in RU:
        if u_0[i]==1:
          rampUp = util.trunc(RU[i] + rampUp,1)
    print('rampUp_0                =',rampUp)    
    rampDown=0
    for i in RD:
        if u_0[i]==1:
          rampDown = util.trunc(RD[i] + rampDown,1)
    print('rampDown_0              =',rampDown)
    startUp=0
    for i in SU:
        if u_0[i]==0:
          startUp = SU[i] + startUp
    print('startUp_0               =',startUp)
    shutDown=0
    for i in SD:
        if u_0[i]==1:
          shutDown = SD[i] + shutDown
    print('shutDown_0              =',shutDown)    
        
    print('Delta demanda  De_0     =',De[1]-gen0)
    print('Reserve  R_0            =',R[1])    
    
    lista1 = []
    for i in range(2,len(De)):
        lista1.append(De[i-1]-De[i])
    print('máx demanda subida      =',abs(util.trunc(min(lista1),1)) )
    print('máx demanda bajada      =',abs(util.trunc(max(lista1),1) ))
        
    lista2 = []
    for i in range(2,len(R)):
        lista2.append(R[i-1]-R[i])
    print('máx reserva subida      =',util.trunc(max(lista2),1) )
    print('máx reserva bajada      =',util.trunc(min(lista2),1) )
    
    #print(gen0,maxi,mini,startUp,shutDown,rampUp,rampDown,De[1],R[1],
          #util.trunc(max(lista1)),util.trunc(min(lista1)),util.trunc(max(lista2)),util.trunc(min(lista2)))
        
    return 0

# (EN PROCESO ...)
def to_dirdat(G,T,L,S,Pmax,Pmin,TU,TD,De,R,u_0,U,D,SU,SD,RU,RD,p_0,Pb,C,mpc,Cs,Tunder,names):    
    print('Exporting instance data to dirdat csv files...')
    
## Deleting an non-empty folder dirdat
    shutil.rmtree('dirdat', ignore_errors=True)
    os.mkdir('dirdat')    
##  Escribiendo HORIZOMDA.csv
    data = {'periodos': [len(T)],'duracion': [60],'bandera': [0],'dias': [1]}
    df = pd.DataFrame(data)
    df.to_csv('dirdat/HORIZOMDA.csv',header=False, index=False)
    
##  Escribiendo PRODEM.csv
    index = list(range(len(De)))
    my_list = list(De.values())
    df = pd.DataFrame(columns = index)  
    df_length = len(df)
    df.loc[df_length] = my_list
    df.to_csv('dirdat/PRODEM.csv',header=False, index=False)
    
##  Escribiendo RRESUS.csv
    index = list(range(len(R)))
    my_list = list(R.values())
    df = pd.DataFrame(columns = index)  
    df_length = len(df)
    df.loc[df_length] = my_list
    df.to_csv('dirdat/RRESUS.csv',header=False, index=False)

##  Escribiendo UNITRC.csv
##  Escribiendo ASIGNRC.csv
##  Escribiendo LIUNITRC.csv
##  Escribiendo LSUNITRC.csv
##  Escribiendo RAMPASRC.csv
##  Escribiendo ARRARC.csv
##  Escribiendo OPPARORC.csv
##  Escribiendo UNITRCCI.csv
##  Escribiendo CGMRC.csv
##  Escribiendo COVAARRC.csv
##  Escribiendo POTVERC.csv
##  Escribiendo PREVERC.csv
##  Escribiendo UNIHMDA.csv