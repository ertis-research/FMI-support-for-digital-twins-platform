from flask import Flask, request, Response
import json
from kafka import KafkaProducer
import multiprocessing as mp
from pyfmi import load_fmu
from time import sleep
import os
import requests
import logging
import kafka.errors as Errors
import time

logging.basicConfig(level=logging.INFO)

##################################################
#----------  Carga de JSON de entrada  ----------#
##################################################
KAFKA_DEFAULT_TOPIC = 'kafkaTopicDefault' if os.environ.get('KAFKA_TOPIC') is None else os.environ.get('KAFKA_TOPIC')
BOOTSTRAP_SERVERS= [] if os.environ.get('KAFKA_SERVER') is None else os.environ.get('KAFKA_SERVER')
id = os.environ.get('IDejecucion')
print(os.environ.get('REST_SERVER'))

resp = requests.get(os.environ.get('REST_SERVER')+'/get-FMI/{}'.format(id))
logging.info(resp)

file = open("FMU.fmu","wb")
file.write(resp.content)
file.close()

variables = None if os.environ.get('VARIABLES') == 'None' else json.loads(os.environ.get('VARIABLES'))
opciones = None if os.environ.get('OPCIONES') == 'None' else json.loads(os.environ.get('OPCIONES'))



##################################################
#---------- Lectura de datos de tiempo ----------#
##################################################

try:
    bySteps     = os.environ.get('BYSTEPS')
    if bySteps == 'True':
        bySteps = True
        time_jump   = os.environ.get('TIME_JUMP')
        time_jump   = float(time_jump)
    else:
        bySteps = False

    start_time  = os.environ.get('START_TIME')
    end_time    = os.environ.get('END_TIME')
    
    start_time  = float(start_time)
    end_time    = float(end_time)

except:
    Exception("Parámetros incorrectos")


model = load_fmu("FMU.fmu")
logging.info("La he cargado")
if variables != None:
    for i in variables.items():
        model.set(i[0], i[1])




if not bySteps:
##################################################
#------ En caso de ejecución con opciones -------#
##################################################
    options = model.simulate_options()
    if opciones != None:
        for i in opciones.keys():
            if i in options.keys():
                options[i] = opciones[i]
            else: print("Clave "+i+" no encontrada")
    
    print(options)


    res = model.simulate(start_time = start_time, final_time = end_time, options = options)


    ##################################################
    #---------------  KAFKA Producer  ---------------#
    ##################################################
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)

    tiempo = res['time']
    keys = res.keys()
    try:
        keys.remove('time')
    except ValueError:
        print("No esta tiempo entre las variables")
    long = len(tiempo)

    for i in range(long):
        sub = {}
        for key in keys:
            sub[key] = res[key][i]
        envio = {
            'id' : id,
            'tiempo':tiempo[i],
            'values':sub,
            'kafkaInsertTime':time.time()
            }

        producer.send(KAFKA_DEFAULT_TOPIC, json.dumps(envio).encode('utf-8'))
        producer.flush()
    producer.close()
else:
##################################################
#-------- En caso de ejecución por pasos --------#
##################################################
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
    model.initialize(start_time, end_time)

    curr_time = start_time

    while curr_time < end_time:
        
        model.do_step(current_t = curr_time, step_size = time_jump, new_step = True)

        paso = {}
        for i in model.get_model_variables().keys():
            paso[i]=model.get(i)[0]

        
        resultado = {
            'id': id,
            'tiempo': curr_time,
            'values':paso,
            'kafkaInsertTime':time.time()
        }

        producer.send(KAFKA_DEFAULT_TOPIC, json.dumps(resultado).encode('utf-8'))
        producer.flush()
        curr_time+=time_jump

    
    producer.close()
##################################################

logging.info("Executions finished, all data have been sent")
requests.get(os.environ.get('REST_SERVER')+'/delete-FMI/'+KAFKA_DEFAULT_TOPIC)
logging.info("Deleting FMU on server")