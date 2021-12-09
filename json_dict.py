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