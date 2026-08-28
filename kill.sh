ps -eaf | grep main.py
ps -eaf | grep test.sh
ps -eaf | grep cplex

pkill -9 -f main.py
pkill -9 -f test.sh
pkill -9 -f cplex

