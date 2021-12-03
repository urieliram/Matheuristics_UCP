def sendtofilesolution(U,name):
    N=len(U)
    T=len(U[0])
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
    N=len(TU)
    file = open(name, "w")
    for g in range(N):         
        file.write(str(TU[g])+","+str(TD[g])+ "\n")
    file.close()