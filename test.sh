#!/bin/bash
mivariable="Inicia script kernel search para UC"
echo $mivariable

for i in 45 46 47 48 49 50 51 52 53 54 55 56
#1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 
#21 22 23 24 
#25 26 27 28 29 30 31 32 33 34 35 36 
#37 38 39 40 41 42 43 44

do

sleep 1s

#Aqui se ejecucuta el programa en python
python3 ksuc.py uc_$i.json yalma #| tee >> Log.log

sleep 2s

done

#mv: mueve o renombra archivos y directorios
#mkdir: crea un directorio.
#cp: copia archivos.
#   s  :  segundos (por defecto)  sleep 10s
#   m  :  minutos
#   h  :  horas
#   d  :  dias
