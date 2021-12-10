import json

instancia = 'anjos.json'
ruta      = 'instances/'
Pmin  = []     # power min

with open(ruta+instancia) as json_file:
    md = json.load(json_file)
 
    # Print the type of data variable
    print(md)
    
    
    for i, gen in md.elements("generator", generator_type="thermal", in_service=True):   
 
        print("\ntime_periods:", md["time_periods"])
        Pmin.append(gen["p_min"])
    
    print(Pmin)
    
    ## egret/parser/pglib_uc_parser.py
    # gen["startup_cost"] = list( (s["lag"], s["cost"]) for s in gen["startup"] )
    # ["p_cost"] = { "data_type":"cost_curve", "cost_curve_type":"piecewise", 
                                # "values": list( (c["mw"], c["cost"]) for c in gen["piecewise_production"]) }