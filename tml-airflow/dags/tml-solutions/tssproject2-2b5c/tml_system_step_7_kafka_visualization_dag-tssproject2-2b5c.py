from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
from airflow.decorators import dag, task
import sys
import subprocess
import tsslogging
import os
import time
import random

sys.dont_write_bytecode = True
######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'topic' : 'iot-preprocess,iot-preprocess2',    # <<< *** Separate multiple topics by a comma - Viperviz will stream data from these topics to your browser
  'dashboardhtml': 'dashboard.html', # <<< *** name of your dashboard html file  try: iot-failure-seneca.html
  'secure': '1',   # <<< *** 1=connection is encrypted, 0=no encryption
  'offset' : '-1',    # <<< *** -1 indicates to read from the last offset always
  'append' : '0',   # << ** Do not append new data in the browser
  'rollbackoffset' : '400', # *************** Rollback the data stream by rollbackoffset.  For example, if 500, then Viperviz wll grab all of the data from the last offset - 500
}

######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml_system_step_7_kafka_visualization_dag_tssproject2-2b5c", default_args=default_args, tags=["tml_system_step_7_kafka_visualization_dag_tssproject2-2b5c"], schedule=None,catchup=False)
def startstreaming():    
  def empty():
      pass
dag = startstreaming()

def windowname(wtype,vipervizport,sname,dagname):
    randomNumber = random.randrange(10, 9999)
    wn = "viperviz-{}-{}-{}={}".format(wtype,randomNumber,sname,dagname)
    with open("/tmux/vipervizwindows_{}.txt".format(sname), 'a', encoding='utf-8') as file: 
      file.writelines("{},{}\n".format(wn,vipervizport))
    
    return wn

def startstreamingengine(**context):
        repo=tsslogging.getrepo()  
        tsslogging.locallogs("INFO", "STEP 7: Visualization started")
        try:
          tsslogging.tsslogit("Visualization DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
          tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")    
        except Exception as e:
            #git push -f origin main
            os.chdir("/{}".format(repo))
            subprocess.call("git push -f origin main", shell=True)
    
        sd = context['dag'].dag_id
        sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))
        chip = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_chip".format(sname)) 
        vipervizport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERVIZPORT".format(sname)) 
        solutionvipervizport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_SOLUTIONVIPERVIZPORT".format(sname)) 
        tss = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_TSS".format(sname)) 
    
        topic = default_args['topic']
        secure = default_args['secure']
        offset = default_args['offset']
        append = default_args['append']
        rollbackoffset = default_args['rollbackoffset']
        dashboardhtml = default_args['dashboardhtml']
                
        ti = context['task_instance']
        ti.xcom_push(key="{}_topic".format(sname),value=topic)
        ti.xcom_push(key="{}_dashboardhtml".format(sname),value=dashboardhtml)        
        ti.xcom_push(key="{}_secure".format(sname),value="_{}".format(secure))
        ti.xcom_push(key="{}_offset".format(sname),value="_{}".format(offset))
        ti.xcom_push(key="{}_append".format(sname),value="_{}".format(append))
        ti.xcom_push(key="{}_chip".format(sname),value=chip)
        ti.xcom_push(key="{}_rollbackoffset".format(sname),value="_{}".format(rollbackoffset))
    
        # start the viperviz on Vipervizport
        # STEP 5: START Visualization Viperviz 
        vizgood=0
        for i in range(5):
          wn = windowname('visual',vipervizport,sname,sd)
          subprocess.run(["tmux", "new", "-d", "-s", "{}".format(wn)])
          subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "cd /Viperviz", "ENTER"])
          mainport=0 
          if tss[1:] == "1":
            subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "/Viperviz/viperviz-linux-{} 0.0.0.0 {}".format(chip,vipervizport[1:]), "ENTER"])            
            mainport=int(vipervizport[1:])
          else:    
            subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "/Viperviz/viperviz-linux-{} 0.0.0.0 {}".format(chip,solutionvipervizport[1:]), "ENTER"])
            mainport=int(solutionvipervizport[1:])

          time.sleep(5)   
          if tsslogging.testvizconnection(mainport)==1:
            tsslogging.locallogs("INFO", "STEP 7: /Viperviz/viperviz-linux-{} 0.0.0.0 {}".format(chip,mainport))            
            vizgood=1
            break
          else:
             if i < 4:
               subprocess.call(["tmux", "kill-window", "-t", "{}".format(wn)])        
               subprocess.call(["kill", "-9", "$(lsof -i:{} -t)".format(mainport)])
             tsslogging.locallogs("WARN", "STEP 7: Cannot make a connection to Viperviz on port {}.  Going to try again...".format(mainport))
            
                    
        if vizgood==0:  
          tsslogging.locallogs("ERROR", "STEP 7: Network issue.  Cannot make a connection to Viperviz on port {}".format(mainport))
