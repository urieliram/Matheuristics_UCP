import json
import util
# import shutil
import os
import pandas as pd

def reading(file):
    """Lee una instancia UC en formato JSON [Knueven2020] y devuelve la lista `instance`.

    ATENCION: el valor de retorno es una lista POSICIONAL de 47 elementos que uc_Co.uc()
    consume como instance[0], instance[1], ... Cualquier reordenamiento rompe el modelo en
    silencio. El mapa de indices es:

      [ 0] G        list[int] - generator indices 1..|G|, one per key of md['thermal_generators'] in
               JSON order (reading.py:72-75). Consumed by uc_Co.py:32; main.py:637 reads
               len(instance[0]) as the generator count.
      [ 1] T        list[int] - period indices 1..time_periods (reading.py:63-64). main.py:637 reads
               len(instance[1]) as the horizon; tests/test_util.py:130 asserts on it.
      [ 2] L        dict g -> list[int] of piecewise production segment indices 1..(#piecewise points -
               1) (reading.py:138-143). Note the count is points-1, matching the deletion of the
               last C entry at reading.py:207.
      [ 3] S        dict g -> list[int] of start-up cost segment indices, containing ONLY the JSON
               startup segments whose 'lag' >= time_down_minimum[g] (reading.py:149-156). Segments
               with a shorter lag are dropped, so S[g] can be shorter than the JSON list.
      [ 4] Pmax     dict g -> float, thermal_generators[gen]['power_output_maximum'] (reading.py:107,
               341).
      [ 5] Pmin     dict g -> float, thermal_generators[gen]['power_output_minimum'] (reading.py:106,
               342).
      [ 6] UT       dict g -> int, minimum up time, thermal_generators[gen]['time_up_minimum']
               (reading.py:112, 343).
      [ 7] DT       dict g -> int, minimum down time, thermal_generators[gen]['time_down_minimum']
               (reading.py:113, 344).
      [ 8] De       dict t -> float, system demand at period t = md['demand'][t-1] * factor_demand,
               truncated to time_periods (reading.py:60, 66). tests/test_util.py:141 indexes it as
               inst[8].
      [ 9] R        dict t -> float, reserve requirement at period t = md['reserves'][t-1] *
               factor_demand (reading.py:61, 67).
      [10] u_0      dict g -> int in {0,1}, commitment state immediately before the horizon, derived
               from unit_on_t0 (reading.py:159-167, 345).
      [11] U        dict g -> int, number of initial periods the unit is FORCED ON = max(0,
               time_up_minimum - time_up_t0) when on at t0, else 0 (reading.py:162/169, 346).
      [12] D        dict g -> int, number of initial periods the unit is FORCED OFF = max(0,
               time_down_minimum - time_down_t0) when off at t0, else 0 (reading.py:161/163/170,
               347).
      [13] TD_0     dict g -> int, hours the unit has been offline before the horizon (time_down_t0 when
               off at t0, else 0) (reading.py:164/171, 348). EFFECTIVELY UNUSED: uc_Co.py:45
               unpacks it, but its only reader is enforce2() at uc_Co.py:728-736, which is never
               called; no model.TD_0 Param is ever declared.
      [14] SU       dict g -> float, start-up ramp limit, thermal_generators[gen]['ramp_startup_limit']
               (reading.py:110, 349).
      [15] SD       dict g -> float, shut-down ramp limit,
               thermal_generators[gen]['ramp_shutdown_limit'] (reading.py:111, 350).
      [16] RU       dict g -> float, ramp-up limit, thermal_generators[gen]['ramp_up_limit']
               (reading.py:108, 351).
      [17] RD       dict g -> float, ramp-down limit, thermal_generators[gen]['ramp_down_limit']
               (reading.py:109, 352).
      [18] p_0      dict g -> float, power output immediately before the horizon,
               thermal_generators[gen]['power_output_t0'] (reading.py:114/189, 353).
      [19] Pb       dict (g,l) -> float, MW breakpoint of piecewise production segment l. Built by
               skipping the FIRST piecewise point (which is Pmin) and numbering the rest from 1, so
               keys run (g,1)..(g,len(L[g])) (reading.py:210-219).
      [20] Cb       dict (g,l) -> float, cost at the Pb[g,l] breakpoint; identical key set to Pb
               (reading.py:218). DEAD in practice: model.Cb is declared at uc_Co.py:223 but
               referenced only at uc_Co.py:512 and 514, both inside `if mode == 'Compact' and
               False:`.
      [21] C        dict (g,n) -> float, cost coefficient of piecewise point n, numbered from 1 over ALL
               points with the LAST one deleted per generator (reading.py:197-207, note the `del
               C[(k,n)]`). This is the marginal cost used by Piecewise_offer44 (uc_Co.py) and by
               Piecewise_mpc via C[g,1].
      [22] CR       dict g -> float, thermal_generators[gen]['fixed_cost'], defaulting to 0 when the key
               is absent (reading.py:118-122, 355). uc_Co.py:54 labels it 'Minimum production
               cost'; it multiplies u[g,t] in total_cMP_rule.
      [23] Cs       dict (g,s) -> float, cost of start-up segment s, numbered from 1 over the FILTERED
               startup segments of index 3 (reading.py:222-230).
      [24] Tunder   dict (g,s) -> int, 'lag' (hours offline) of start-up segment s, same key set as Cs
               (reading.py:229). Used by Start_up_cost54 as the offline-window bounds.
      [25] names    dict g -> str, the original generator key from md['thermal_generators']
               (reading.py:354). Sole consumer in uc_Co.py is the diagnostic print inside the bare
               `except:` of Piecewise_mpc.
      [26] LOAD     list[int] - elastic-load indices 1..|md['loads']| (reading.py:244-247). Empty list
               when the JSON has no 'loads' key (the whole block is wrapped in try/except at
               reading.py:241/281). Read only under scope=='POZ+EL' (uc_Co.py:60).
      [27] Ld       dict d -> list[int] of purchase-bid segment indices 1..#points for elastic load d
               (reading.py:259-264). Unlike L (index 2) this keeps ALL points, no minus-one. Read
               only under scope=='POZ+EL'.
      [28] Pd       dict (d,i) -> float, MW of purchase-bid segment i of elastic load d, numbered from 1
               over all points (reading.py:267-277). Read only under scope=='POZ+EL'.
      [29] Cd       dict (d,i) -> float, bid price of purchase-bid segment i, same key set as Pd
               (reading.py:276). Read only under scope=='POZ+EL'.
      [30] GRO      list[int] - generator indices that have prohibited operating zones, from
               md['operative_zones']['GRO'] (reading.py:296-297). Empty when the key is absent
               (try/except at reading.py:294/316). Read only under scope=='POZ+EL'.
      [31] RO       dict g -> list[int] of operating-zone indices for generator g (reading.py:306-307,
               357). CAVEAT: every generator is given the SAME `noz` list object by reference, so
               all POZ generators necessarily share one zone count. Read only under
               scope=='POZ+EL'.
      [32] ROmin    dict (g,z) -> float, lower MW bound of prohibited zone z for generator g, computed
               as power_output_maximum[g-1] * minoz[z-1] * 0.01, i.e. the JSON stores percentages
               (reading.py:311-313, 358). Read only under scope=='POZ+EL'.
      [33] ROmax    dict (g,z) -> float, upper MW bound of prohibited zone z = power_output_maximum[g-1]
               * maxoz[z-1] * 0.01 (reading.py:314, 359). Read only under scope=='POZ+EL'.
      [34] Crr      dict g -> float, offer price for regulation reserve. NOT from the JSON:
               reading.py:445 hardcodes 1.0 for every generator ('Artificialmente creamos ofertas
               de venta de reservas', reading.py:398). Read only under scope=='POZ+EL'.
      [35] Cs10     dict g -> float, offer price for 10-minute spinning reserve. Synthetic constant 1.0
               for every generator (reading.py:446, 457). Read only under scope=='POZ+EL'.
      [36] Cs30     dict g -> float, offer price for 30-minute spinning reserve. Synthetic constant 1.0
               (reading.py:447, 458). Read only under scope=='POZ+EL'.
      [37] Cns10    dict g -> float, offer price for 10-minute non-spinning reserve. Synthetic constant
               1.0 (reading.py:448, 459). Read only under scope=='POZ+EL'.
      [38] Cns30    dict g -> float, offer price for 30-minute non-spinning reserve. Synthetic constant
               1.0 (reading.py:449, 460). Read only under scope=='POZ+EL'.
      [39] RRe      dict g -> float, MW cap on regulation reserve per generator. Synthetic constant 2.0
               (reading.py:450, 461); enforced by limit_rre_rule. Read only under scope=='POZ+EL'.
      [40] RR10     dict g -> float, MW cap on 10-minute spinning reserve. Synthetic constant 2.0
               (reading.py:451, 462). Read only under scope=='POZ+EL'.
      [41] RR30     dict g -> float, MW cap on 30-minute spinning reserve. Synthetic constant 2.0
               (reading.py:452, 463). Read only under scope=='POZ+EL'.
      [42] RN10     dict g -> float, MW cap on 10-minute non-spinning reserve. Synthetic constant 2.0
               (reading.py:453, 464). Read only under scope=='POZ+EL'.
      [43] RN30     dict g -> float, MW cap on 30-minute non-spinning reserve. Synthetic constant 2.0
               (reading.py:454, 465). Read only under scope=='POZ+EL'.
      [44] ORDC     list[int] 1..12 - segment indices of the Operating Reserve Demand Curve, generated
               from len(RCO) (reading.py:410, 441-442). Read only under scope=='POZ+EL'.
      [45] Cordc    dict b -> float, system purchase price for ORDC segment b. Hardcoded ladder 15.0,
               14.0, ... 4.0 (reading.py:427-438, 466). Read only under scope=='POZ+EL'.
      [46] RCO      dict b -> float, MW cap of ORDC segment b. Hardcoded ladder 24.0, 22.0, ... 2.0
               (reading.py:414-425, 467); enforced by limit_rco_rule. Read only under
               scope=='POZ+EL'.

    Los indices 34 a 46 (Crr..RCO) NO provienen del JSON: reading() los genera con constantes
    sintetizadas en el propio codigo. Solo se usan si el modelo se corre con reservas y ORDC.
    """
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
    UT      = {}   ## time_upminimum
    DT      = {}   ## time_down_minimum
    D       = {}   ## number of hours generator g is required to be off at t=1 (h).
    U       = {}   ## number of hours generator g is required to be on at t=1 (h).
    TD_0    = {}   ## Number of hours that the unit has been offline before the scheduling horizon.
    p_0     = {}   ## power_output_t0
    CR      = {}   ## cost of generator g running and operating at minimum production Pmin ($/h).
    C       = {}   ## 
    Cs      = {}   ## Costo de cada escalón del conjunto S de la función de costo variable de arranque.
    Tunder  = {}   ## lag de cada escalón del conjunto S de la función de costo variable de arranque.
    Startup = {}   ## start-up cost 
           
    factor_demand = 1.0
    demand        = []
    reserves      = []
    
    # time_periods = int(md['time_periods'])
    # demand       =     md['demand']  
    # reserves     =     md['reserves']  
        
    time_periods  = int(md['time_periods'])
    demand1       =     md['demand']  
    reserves1     =     md['reserves']  
    
    ## Antes, cuando faltaba 'factor_demand', demand/reserves quedaban aliasados a las listas
    ## del dict parseado y el bucle les hacia append mientras las recorria: duplicaba la serie
    ## y mutaba md. Sobrevivia solo porque el zip(T, ...) de mas abajo truncaba el sobrante.
    ## Ademas se recorria len(demand1); uc_059 trae 121 demandas para 120 periodos y reventaba
    ## con IndexError sobre reserves1. Se recorre time_periods, que es el largo que zip conserva.
    factor_demand = float(md.get('factor_demand', 1.0))

    if factor_demand != 1:
        print('factor_demand=', factor_demand)

    demand   = [  demand1[t] * factor_demand for t in range(time_periods)]
    reserves = [reserves1[t] * factor_demand for t in range(time_periods)]

    for t in range(1, time_periods+1):
        T.append(t)
          
    De   = dict(zip(T, demand))
    R    = dict(zip(T, reserves))
    
    names_gens = []
    i = 1
    ## Se obtiene nombre de los generadores y número
    for gen in md['thermal_generators']:  
        names_gens.append(gen)
        G.append(i)
        i += 1
        
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
    abajo_min            = 0
    
    ## To get the data from the generators
    i = 1 ## Cuenta los generadores
    for gen in names_gens:  
        must_run.append(md[            'thermal_generators'][gen]["must_run"]) #0,
        power_output_minimum.append(md['thermal_generators'][gen]["power_output_minimum"])#80
        power_output_maximum.append(md['thermal_generators'][gen]["power_output_maximum"])#300.0
        ramp_up_limit.append(md[       'thermal_generators'][gen]["ramp_up_limit"])#50
        ramp_down_limit.append(md[     'thermal_generators'][gen]["ramp_down_limit"])#30
        ramp_startup_limit.append(md[  'thermal_generators'][gen]["ramp_startup_limit"])#100
        ramp_shutdown_limit.append(md[ 'thermal_generators'][gen]["ramp_shutdown_limit"])#80
        time_up_minimum.append(md[     'thermal_generators'][gen]["time_up_minimum"])#3
        time_down_minimum.append(md[   'thermal_generators'][gen]["time_down_minimum"])#2
        power_output_t0.append(md[     'thermal_generators'][gen]["power_output_t0"])#120
        unit_on_t0.append(md[          'thermal_generators'][gen]["unit_on_t0"])#1
        time_up_t0.append(md[          'thermal_generators'][gen]["time_up_t0"])#1
        time_down_t0.append(md[        'thermal_generators'][gen]["time_down_t0"])#0        
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
            j += 1            
        Piecewise.append(lista_aux)
        

        
        lista = []
        jj = 1
        for ii in range(j-1):
            lista.append(jj)
            jj= jj+1
        L[i] = lista
                
        ## Obtiene segmentos del costo variable de arranque
        lista_aux2 = []
        lista2     = []
        j = 1        
        for segment in startup:
            if segment['lag']>=time_down_minimum[i-1]:
                lista_aux2.append((segment['lag'],segment['cost']))
                lista2.append(j)
                j += 1         
            
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
                                 
        i += 1;  ## Se incrementa un generador  
                            
       
       
    ## Se extraen los diccionarios Pb y C de la lista de listas Piecewise    
    k=0; n=0
    for i in Piecewise:
        k=k+1
        n=0
        for j in i:
            n=n+1
            C[k,n] = j[1]
            # ## Se calcula el costo mínimo de operación CR
            # if n==1:
            #     CR[k] = j[0]*j[1] 
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
    
    ## Leemos cargas elásticas
    
    LOAD                      = []  
    Ld                        = {}   ## eslabones de oferta de compra en piecewise
    names_loads               = []  
    piecewise_production_load = []
    Piecewise_load            = []    
    Pd                        = {}   ## maximum load for piecewise segment LD for a load "load"(MW).
    Cd                        = {}   ## bid of a load "load" consuming Pd MW of power ($/h).
    try:
        i = 1
        ## Se obtiene nombre de las cargas elásticas y el número total
        for load in md['loads']:  
            names_loads.append(load)
            LOAD.append(i)
            i+=1   
        
        i=1 ## Cuenta las cargas
        for load in names_loads:
            piecewise_production_load = md['loads'][load]["piecewise_production"] # bids offer      
            ## Para obtener los piecewise del costo de los generadores
            lista_aux = []
            j = 0
            for piece in piecewise_production_load:
                lista_aux.append((piece['mw'],piece['cost']))
                j += 1            
            Piecewise_load.append(lista_aux)
            lista = []
            jj = 1
            for ii in range(j):
                lista.append(jj)
                jj = jj + 1
            Ld[i] = lista
            i += 1
                    
        k = 0; n = 0
        for i in Piecewise_load:
            # print(i)
            k = k+1
            n = 1
            for j in i:                
                # print(j)
                # print(k,",",n,",",j[0],",",j[1])
                Pd[k,n] = j[0]
                Cd[k,n] = j[1]               
                n = n+1
        # print('Cd',Cd)
        # print('Pd',Pd)

    except:
        x=0
        #print('reading.py sin información de cargas elásticas')
    
    ## Prohibid operating zones
    GRO   = []    
    oz    = []
    noz   = [] 
    toz   = []
    minoz = [] ## operating zones
    maxoz = [] ## operating zones
    romin = [] ## operating zones
    romax = [] ## operating zones
    try: 
        ## Read generators with prohibid operative zones
        for item in md['operative_zones']['GRO']:  
            GRO.append(item)
        
        ## Read operative zones
        i=0
        for item in md['operative_zones']['oz']:
            minoz.append(item['min'])
            maxoz.append(item['max'])
            i=i+1
            noz.append(i)
        for item in GRO:
            oz.append(noz)
        for i in GRO:
            for j in noz:
                toz.append((i,j))        
        for item in toz:
            #print(power_output_maximum[item[0]-1],minoz[item[1]-1],maxoz[item[1]-1])
            romin.append( power_output_maximum[item[0]-1]*minoz[item[1]-1]*0.01 )
            romax.append( power_output_maximum[item[0]-1]*maxoz[item[1]-1]*0.01  )                
        
    except: 
        x=0       
        #print('reading.py sin información de zonas prohibidas')


    
    # print('oz',oz)
    # print('noz',noz) 
    # print('toz',toz)  
    # print('minoz',minoz)  
    # print('maxoz',maxoz)  
    # print('romin',romin)  
    # print('romax',romax)  

    
    # GRO    = [1, 3]
    # RO     = {1: [1, 2, 3], 3: [1, 2, 3]}
    # ROmin  = {(1, 1):  0, (1, 2): 100, (1, 3): 230,    (3, 1):  0, (3, 2): 60, (3, 3): 95}   
    # ROmax  = {(1, 1): 50, (1, 2): 150, (1, 3): 305,    (3, 1): 41, (3, 2): 91, (3, 3): 100}   
    # print('GRO',GRO)
    # print('RO',RO)  
    # print('ROmin',ROmin)
    # print('ROmax',ROmax)   
    
    ## Aqui se pasan de arreglos a diccionarios como los usa Pyomo
    Pmax   = dict(zip(G, power_output_maximum))
    Pmin   = dict(zip(G, power_output_minimum))
    UT     = dict(zip(G, time_up_minimum))     
    DT     = dict(zip(G, time_down_minimum))  
    u_0    = dict(zip(G, u_0_list))          
    U      = dict(zip(G, Ulist))              
    D      = dict(zip(G, Dlist))             
    TD_0   = dict(zip(G, TD0list))                
    SU     = dict(zip(G, ramp_startup_limit))
    SD     = dict(zip(G, ramp_shutdown_limit))
    RU     = dict(zip(G, ramp_up_limit))
    RD     = dict(zip(G, ramp_down_limit))
    p_0    = dict(zip(G, p_0_list))  
    names  = dict(zip(G, names_gens))  
    CR     = dict(zip(G, fixed_cost))
    
    RO     = dict(zip(GRO, oz))   
    ROmin  = dict(zip(toz, romin))   
    ROmax  = dict(zip(toz, romax))   
    
    

    ## -----------------  Caso de ejemplo de anjos.json  --------------------------
    #G        = [1, 2, 3]
    #T        = [1, 2, 3, 4, 5, 6]
    #L        = {1: [1, 2, 3], 2: [1, 2, 3], 3: [1, 2, 3, 4]}
    #S        = {1: [1, 2, 3], 2: [1, 2, 3], 3: [1, 2, 3, 4]}
    #Pmax     = {1: 300.0, 2: 200.0, 3: 100.0}
    #Pmin     = {1: 80, 2: 50, 3: 30}
    #UT       = {1: 3, 2: 2, 3: 1}
    #DT       = {1: 2, 2: 2, 3: 2}
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
    #CR      = {1: 400.0, 2: 750.0, 3: 900.0}
    #Pb       = {(1, 1): 80, (1, 2): 150, (1, 3): 300, (2, 1): 50, (2, 2): 100, (2, 3): 200, (3, 1): 30, (3, 2): 50, (3, 3): 70, (3, 4): 100}   
    #C        = {(1, 1): 5.0, (1, 2): 5.0, (1, 3): 5.0, (2, 1): 15.0, (2, 2): 15.0, (2, 3): 15.0, (3, 1): 30.0, (3, 2): 30.0, (3, 3): 30.0, (3, 4): 30.0}
    #Cs       = {(1, 1): 800.0, (1, 2): 800.0, (1, 3): 800.0, (2, 1): 500.0, (2, 2): 500.0, (2, 3): 500.0, (3, 1): 25.0, (3, 2): 250.0, (3, 3): 
    #500.0, (3, 4): 1000.0}
    #Tunder     = {(1, 1): 2, (1, 2): 3, (1, 3): 4, (2, 1): 2, (2, 2): 3, (2, 3): 4, (3, 1): 2, (3, 2): 3, (3, 3): 4, (3, 4): 5}
    #fixShedu = False
    #relax    = False
    #ambiente = 'localPC'
    ## ----------------------------------  o  -------------------------------------

    ## Para obtener los Psu y los Psd 
    for i in Pmin:
        if SU[i]<Pmin[i]:
            print('Pmin',Pmin[i],SU[i])
            
    ## Artificialmente creamos ofertas de venta de reservas    
    Crr   = []  
    Cs10  = []   
    Cs30  = []   
    Cns10 = []   
    Cns30 = []  
    Cordc = []      
    RRe   = []  
    RR10  = []   
    RR30  = []   
    RN10  = []   
    RN30  = []  
    ORDC  = [] ## Segments of ORDC
    RCO   = [] ## Limits of MW for each ORDC segment
    
        
    RCO.append(24.0)   # 5 MW    
    RCO.append(22.0)   # 5 MW       
    RCO.append(20.0)   # 5 MW       
    RCO.append(18.0)   # 5 MW       
    RCO.append(16.0)   # 5 MW       
    RCO.append(14.0)   # 5 MW       
    RCO.append(12.0)   # 5 MW       
    RCO.append(10.0)   # 5 MW       
    RCO.append(8.0)    # 5 MW       
    RCO.append(6.0)    # 5 MW       
    RCO.append(4.0)    # 5 MW       
    RCO.append(2.0)    # 5 MW       
    
    Cordc.append(15.0)   # 5 MW    
    Cordc.append(14.0)   # 5 MW       
    Cordc.append(13.0)   # 5 MW       
    Cordc.append(12.0)   # 5 MW       
    Cordc.append(11.0)   # 5 MW       
    Cordc.append(10.0)   # 5 MW       
    Cordc.append(9.0)    # 5 MW       
    Cordc.append(8.0)    # 5 MW       
    Cordc.append(7.0)    # 5 MW       
    Cordc.append(6.0)    # 5 MW       
    Cordc.append(5.0)    # 5 MW       
    Cordc.append(4.0)    # 5 MW       
     
    ## Crea segmentos ORDC
    for i in range(1,len(RCO)+1):
        ORDC.append(i) 
        
    for i in G:
        Crr.append(  1.0) # $ 1
        Cs10.append( 1.0) # $ 1
        Cs30.append( 1.0) # $ 1
        Cns10.append(1.0) # $ 1
        Cns30.append(1.0) # $ 1
        RRe.append(2.0)   # $ 1
        RR10.append(2.0)  # $ 1
        RR30.append(2.0)  # $ 1
        RN10.append(2.0)  # $ 1
        RN30.append(2.0)  # $ 1
           
    Crr      = dict(zip(G    , Crr   ))
    Cs10     = dict(zip(G    , Cs10  ))
    Cs30     = dict(zip(G    , Cs30  ))
    Cns10    = dict(zip(G    , Cns10 ))
    Cns30    = dict(zip(G    , Cns30 ))    
    RRe      = dict(zip(G    , RRe   ))
    RR10     = dict(zip(G    , RR10  ))
    RR30     = dict(zip(G    , RR30  ))
    RN10     = dict(zip(G    , RN10  ))
    RN30     = dict(zip(G    , RN30  ))
    Cordc    = dict(zip(ORDC , Cordc ))
    RCO      = dict(zip(ORDC , RCO   ))
        
    instance = [G,T,L,S,Pmax,Pmin,UT,DT,De,R,u_0,U,D,TD_0,SU,SD,RU,RD,p_0,Pb,Cb,C,CR,Cs,Tunder,names,
                LOAD,Ld,Pd,Cd, 
                GRO,RO,ROmin,ROmax, 
                Crr,Cs10,Cs30,Cns10,Cns30,RRe,RR10,RR30,RN10,RN30,ORDC,Cordc,RCO]
            
    return instance