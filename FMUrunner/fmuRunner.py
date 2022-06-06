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

logging.basicConfig(level=logging.INFO)


# Creating a request to get FMU file
KAFKA_DEFAULT_TOPIC = 'kafkaTopicDefault' if os.environ.get('KAFKA_TOPIC') is None else os.environ.get('KAFKA_TOPIC')
BOOTSTRAP_SERVERS= '127.0.0.1:9094' if os.environ.get('KAFKA_SERVER') is None else os.environ.get('KAFKA_SERVER')


resp = requests.get(os.environ.get('REST_SERVER')+'/get-FMI/'+KAFKA_DEFAULT_TOPIC)

logging.info(resp)


# We dont need a specific name, because we will only have just one FMU in every pod.
file = open("FMU.fmu","wb")
file.write(resp.content)
file.close()

try:
    datos = json.loads(os.environ.get('DATOS'))
except:
    json.decoder.JSONDecodeError("JSON couldn't load data, executing with default parameters")


# Time parameters
try:
    bySteps     = os.environ.get('BYSTEPS')
    if bySteps == 'True':
        bySteps = True
    else:
        bySteps = False

    start_time  = os.environ.get('START_TIME')
    end_time    = os.environ.get('END_TIME')
    time_jump   = os.environ.get('TIME_JUMP')

    start_time  = float(start_time)
    end_time    = float(end_time)
    time_jump   = float(time_jump)

except:
    Exception("Wrong parameters")


model = load_fmu("FMU.fmu")
logging.info("La he cargado")
if datos['variables'] != None:
    for i in datos['variables'].items():
        model.set(i[0], i[1])




if not bySteps:
    resultado = {}
    options = datos['options']
    if options is None:
        options = model.simulate_options()

    res = model.simulate(final_time = end_time, options = options)

    for i in model.get_model_variables().keys():
        resultado[i] = list(res[i])

    ##################################################
    #---------------  KAFKA Producer  ---------------#
    ##################################################
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
    producer.send(KAFKA_DEFAULT_TOPIC, json.dumps(resultado).encode('utf-8'))
    producer.flush()
    producer.close()
else:
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
    model.initialize(start_time, end_time)

    curr_time = start_time

    while curr_time < end_time:
        resultado = {}
        model.do_step(current_t = curr_time, step_size = time_jump, new_step = True)

        paso = {}
        for i in model.get_model_variables().keys():
            paso[i]=model.get(i)[0]

        resultado[curr_time] = paso

        producer.send(KAFKA_DEFAULT_TOPIC, json.dumps(resultado).encode('utf-8'))
        producer.flush()
        curr_time+=time_jump

    
    producer.close()
##################################################


logging.info("Executions finished, all data have been sent")



