from csv import writer

#https://thispointer.com/python-how-to-append-a-new-row-to-an-existing-csv-file/#:~:text=Open%20our%20csv%20file%20in,in%20the%20associated%20csv%20file
def append_list_as_row(file_name, list_of_elem):
    # Open file in append mode
    with open(file_name, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        csv_writer = writer(write_obj)
        # Add contents of list as last row in the csv file
        csv_writer.writerow(list_of_elem)
    
def sendtofilesolution(U,name):
    N = len(U)
    T = len(U[0])
    file = open(name, "w")
    cadena = ""
    for g in range(N):
        for t in range(T):
            cadena = cadena + str(U[g][t])+","
        cadena = cadena + "\n"
        file.write(cadena)
        cadena = ""
    file.close()

def sendtofileTUTD(TU,TD,name):
    N = len(TU)
    file = open(name, "w")
    for g in range(N):         
        file.write(str(TU[g])+","+str(TD[g])+ "\n")
    file.close()
    
def imprime_sol(model,sol):
    Uu = dict(zip(model.T, sol.getUu()))
    V  = dict(zip(model.T, sol.getV()))
    W  = dict(zip(model.T, sol.getW()))
    P  = dict(zip(model.T, sol.getP()))
    R  = dict(zip(model.T, sol.getR()))
    # print("u",Uu)
    # print("v",V)
    # print("w",W)
    # print("p",P)
    # print("r",R)