from   math import ceil
from   csv import writer
import numpy as np
import pandas as pd

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

def trunc(values, decs=1):
    return np.trunc(values*10**decs)/(10**decs)

def getLetter(index):    
    total    = 26
    cociente = int(index / total)-1
    modulo   = int(index % total)    
    if index < total:
        return   '_'+chr(index+97)
    else:
        return   '_'+chr(cociente+97)+chr(modulo+97)

def saveSolution(t_lp,z_lp,t_,z_,SB_Uu,No_SB_Uu,lower_Pmin_Uu,Vv,Ww,delta,option,instance):
    result_ = []
    result_.append((t_lp,z_lp))
    result_.append((t_,z_))
    result_.append((len(SB_Uu)        , len(No_SB_Uu)))
    result_.append((len(lower_Pmin_Uu), len(Vv)))
    result_.append((len(Ww)           , len(delta)))
    result_ = result_ + SB_Uu + No_SB_Uu + lower_Pmin_Uu
    result_ = np.array(result_)    
    np.savetxt('sol'+option+'_a_'+instance+'.csv', result_, delimiter=',')
    result_ = Vv + Ww + delta 
    result_ = np.array(result_)    
    np.savetxt('sol'+option+'_b_'+instance+'.csv', result_, delimiter=',')
    return None

def loadSolution(option,instance):
    array_a = np.loadtxt('sol'+option+'_a_'+instance+'.csv', delimiter=',')
    array_b = np.loadtxt('sol'+option+'_b_'+instance+'.csv', delimiter=',')
    t_lp           = array_a[0][0]
    z_lp           = array_a[0][1]
    t_             = array_a[1][0]
    z_             = array_a[1][1]
    nSB_Uu         = array_a[2][0].astype(int)
    nNo_SB_Uu      = array_a[2][1].astype(int)
    nlower_Pmin_Uu = array_a[3][0].astype(int)
    nVv            = array_a[3][1].astype(int)
    nWw            = array_a[4][0].astype(int)
    ndelta         = array_a[4][1].astype(int)
    array_a        = array_a[5:]
    a = nSB_Uu + nNo_SB_Uu
    SB_Uu         = array_a[:nSB_Uu].astype(int)
    No_SB_Uu      = array_a[nSB_Uu:a].astype(int)
    lower_Pmin_Uu = array_a[a:].astype(int)
    b = nVv + nWw
    Vv            = array_b[:nVv].astype(int)
    Ww            = array_b[nVv:b].astype(int)
    delta         = array_b[b:].astype(int)
    
    #t_,z_,SB_Uu,No_SB_Uu,lower_Pmin_Uu,Vv,Ww,delta,option,instance
    # print(t_,z_,len(SB_Uu),len(No_SB_Uu),len(lower_Pmin_Uu),len(Vv),len(Ww),len(delta))
    return t_lp,z_lp,t_,z_,SB_Uu,No_SB_Uu,lower_Pmin_Uu,Vv,Ww,delta

def igap(LB,UB):
    ## Calcula el integrality gap    
    return abs( LB - UB ) / ( 1e-10 + abs(UB) )    

def compare(array1,array2):
    npArray1 = np.array(array1)
    npArray2 = np.array(array2)
    print(npArray1) 
    print(npArray2) 
    # comparison = npArray1 == npArray2
    # # equal_arrays = comparison.all() 
    # print('comparison  =',comparison)        
    # out_num = np.subtract(npArray1, npArray2) 
    # print ('Uu Difference of two input number : ',type(out_num), out_num) 
    result = np.array_equal(array1, array2)
    
    print('result  =',result)     

def delete_tabu(rightbranches):
    # x_=[[0,1,2],[3,4,5],[7,8,9]]
    # rightbranches = []
    # rightbranches.append([x_[0],x_[1],x_[2],0])
    # rightbranches.append([x_[0],x_[1],x_[2],1])
    # rightbranches.append([x_[0],x_[1],x_[2],2])
    # rightbranches.append([x_[0],x_[1],x_[2],0])
    # rightbranches.append([x_[0],x_[1],x_[2],3])
    # rightbranches.append([x_[0],x_[1],x_[2],0])
    # rightbranches.append([x_[0],x_[1],x_[2],4])
    try:
        i=0
        for cut in rightbranches:
            if cut[3] == 0:
                #print(cut)
                #print(i)
                rightbranches.pop(i)
            i=i+1
    except:
        print('>>> Fail deleting tabu coinstraints')
        
    return(rightbranches)


def config_env(filec='config.con'):
    #ambiente='localPC',ruta='instances/',executable='/home/uriel/cplex1210/cplex/bin/x86-64_linux/cplex3'
    # Set column as Index
    try:
        df = pd.read_csv(filec, index_col='index')
        ambiente           = df.loc['ambiente'                ].values[0]
        ruta               = df.loc['ruta'                    ].values[0]
        executable         = df.loc['executable'              ].values[0]
        timelp             = float(df.loc['timelp'            ].values[0])
        timeconst          = float(df.loc['timeconst'         ].values[0])
        timefull           = float(df.loc['timefull'          ].values[0])
        
        emphasizeMILP      = int(df.loc['emphasysmilp'        ].values[0])
        symmetryMILP       = int(df.loc['symmetrymilp'        ].values[0])
        lbheurMILP         = str(df.loc['lbheurmilp'          ].values[0])
        strategyMILP       = int(df.loc['strategymilp'        ].values[0])
        
        diveMILP           = int(df.loc['divemilp'            ].values[0])
        heuristicfreqMILP  = int(df.loc['heuristicfreqmilp'   ].values[0])
        numericalMILP      = str(df.loc['numericalmilp'       ].values[0])
        tolfeasibilityMILP = float(df.loc['tolfeasibilitymilp'].values[0])
        toloptimalityMILP  = float(df.loc['toloptimalitymilp' ].values[0])
        
        emphasizeHEUR      = int(df.loc['emphasysheur'        ].values[0])
        symmetryHEUR       = int(df.loc['symmetryheur'        ].values[0])
        lbheurHEUR         = str(df.loc['lbheurheur'          ].values[0])
        strategyHEUR       = int(df.loc['strategyheur'        ].values[0])
        
        gap                = float(df.loc['gap'               ].values[0])
        k                  = int(df.loc['k'                   ].values[0])
        iterstop           = int(df.loc['iterstop'            ].values[0])
        
        Hard3              = df.loc['Hard3'                   ].values[0] == 'True'
        Harjk              = df.loc['Harjk'                   ].values[0] == 'True'
        MILP2              = df.loc['MILP2'                   ].values[0] == 'True'
        lbc1               = df.loc['lbc1'                    ].values[0] == 'True'
        lbc2               = df.loc['lbc2'                    ].values[0] == 'True'
        lbc3               = df.loc['lbc3'                    ].values[0] == 'True'
        lbc4               = df.loc['lbc4'                    ].values[0] == 'True'
        KS                 = df.loc['KS'                      ].values[0] == 'True'
        MILP               = df.loc['MILP'                    ].values[0] == 'True'
    except:
        print('!!! Problema al cargar la configuración. Verifique el ')
        print('formato y rutas del archivo <config.con>, algo como esto en columnas:')
        print('ambiente,ruta,executable,timelp,timeconst,timefull, emphasysmilp,symmetrymilp,lbheurmilp,strategymilp, divemilp,heuristicfreqmilp,numericalmilp,tolfeasibilitymilp,toloptimalitymilp, emphasysheur,symmetryheur,lbheurheur,strategyheur, gap,k,iterstop, MILP,MILP2,Hard3,Harjk,FP,lbc1,lbc2,lbc3,KS')
        print('yalma,instances/,/home/uriel/cplex1210/cplex/bin/x86-64_linux/cplex,1200,7200,1,1,yes,3, 1,0,no,3, 0.0001,20,30')
        print('localPC,instances/,/home/uriel/cplex1210/cplex/bin/x86-64_linux/cplex,400,1000,1,1,yes,3, 1,0,no,3, 0.0001,20,30')
    return  ambiente,ruta,executable,timelp,timeconst,timefull,                                    \
            emphasizeMILP,symmetryMILP,lbheurMILP,strategyMILP,                             \
            diveMILP,heuristicfreqMILP,numericalMILP,tolfeasibilityMILP,toloptimalityMILP,  \
            emphasizeHEUR,symmetryHEUR,lbheurHEUR,strategyHEUR,                             \
            gap,k,iterstop,Hard3,Harjk,MILP2,lbc1,lbc2,lbc3,lbc4,KS,MILP
# index,value
# ambiente,yalma
# ruta,instances/
# executable,/opt/ibm/ILOG/CPLEX_Studio221/cplex/bin/x86-64_linux/cplex
# timelp,2300
# timeconst,900
# timefull,3800
# emphasysmilp,1
# symmetrymilp,1
# lbheurmilp,yes
# strategymilp,3
# divemilp,2
# heuristicfreqmilp,50
# numericalmilp,yes
# tolfeasibilitymilp,1.00E-09
# toloptimalitymilp,1.00E-09
# emphasysheur,1
# symmetryheur,0
# lbheurheur,no
# strategyheur,3
# gap,0.0
# k,20
# iterstop,999
# Hard3,True
# Harjk,True
# MILP2,True
# lbc1,True
# lbc2,True
# lbc3,True
# lbc4,True
# KS,True
# MILP,True

