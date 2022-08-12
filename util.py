from math import ceil
import numpy as np
from csv import writer
import pandas as pd
import matplotlib.pyplot as plt

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
            cadena = cadena + str(ceil(U[g][t]))+","
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
    
def resultados_lp_milp(instance,ambiente,gap,timelimit):
    
    z_milp = 0; z_hard = 0; t_milp = 0; t_hard = 0; precargado = False
    df = pd.read_csv('resultados_previos.csv')
    df = df.loc[(df['instancia'] == instance) & (df['ambiente'] == ambiente) & (df['gap'] == gap) & (df['timelimit'] == timelimit)]
    
    if len(df.index) != 0:
        z_milp = df['z_milp'].values[0]
        z_hard = df['z_hard'].values[0]
        t_milp = df['t_milp'].values[0]
        t_hard = df['t_hard'].values[0]
        precargado = True
        print('Resultados de <milp> y <hard-fixing> pre-cargados y asignados.')
        
    return precargado, z_milp, z_hard, t_milp, t_hard

def config_env():
    #ambiente='localPC',ruta='instances/',executable='/home/uriel/cplex1210/cplex/bin/x86-64_linux/cplex3'
    df = pd.read_csv('config')    
    if len(df.index) == 1:
        ambiente     = df['ambiente'  ].values[0]
        ruta         = df['ruta'      ].values[0]
        executable   = df['executable'].values[0]
        timeheu      = df['timeheu'   ].values[0]
        timemilp     = df['timemilp'  ].values[0]
        gap          = df['gap'       ].values[0]
        k            = df['k'         ].values[0]
        iterpar      = df['iter'      ].values[0]
    else:
        print('!!! Problema al cargar la configuración. Verifique el ')
        print('formato y rutas del archivo <config>, algo como esto:')
        print('ambiente,ruta,executable,timeheu,timemilp,gap')
        print('localPC,instances/,/home/uriel/cplex1210/cplex/bin/x86-64_linux/cplex,4000,40000,0.001')
                
    return ambiente, ruta, executable, timeheu, timemilp, gap, k, iterpar


def trunc(values, decs=1):
    return np.trunc(values*10**decs)/(10**decs)