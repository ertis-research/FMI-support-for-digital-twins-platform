from flask import Flask, request, Response
from flask import send_file, send_from_directory, abort
from kubernetes import client, config
import logging
import os

from urllib3 import HTTPResponse


def kubernetes_config( token=None, external_host=None ):
    """ Get Kubernetes configuration.
        You can provide a token and the external host IP 
        to access a external Kubernetes cluster. If one
        of them is not provided the configuration returned
        will be for your local machine.
        Parameters:
            str: token 
            str: external_host (e.g. "https://192.168.65.3:6443")
        Return:
            Kubernetes API client
    """
    aConfiguration = client.Configuration()
    if token != None and \
        external_host != None:

        aConfiguration.host = external_host 
        aConfiguration.verify_ssl = False
        aConfiguration.api_key = { "authorization": "Bearer " + token }
    api_client = client.ApiClient( aConfiguration) 
    return api_client



app = Flask(__name__)

@app.route('/FMI', methods=['POST'])
def getData():
    #CODIGO PARA CREAR EL CONTENEDOR DE KUBERNETES
    logging.info("Creating new job")
    try:
        os.mkdir("FMUs")
    except FileExistsError:
        logging.info("FMUs already exists")

    data = request.form
    uploaded_file = request.files['file']
    uploaded_file.save("FMUs/"+data['kafkaTopic']+".fmu")

    #Kafka cluster IP
    BOOTSTRAP_SERVERS= None


    job_manifest = {
        'apiVersion': 'batch/v1',
        'kind': 'Job',
        'metadata': {
            'name': 'fmu-executer'+data['kafkaTopic']
        },
        'spec': {
            'ttlSecondsAfterFinished' : 10,
            'template' : {
                'spec': {
                    'containers': [{
                        'image': "localhost:5000/fmurunner", 
                        'name': 'fmurunner-'+data['kafkaTopic'],
                        'env': [{'name': 'KAFKA_TOPIC', 'value': data['kafkaTopic']},
                                {'name': 'KAFKA_SERVER', 'value': BOOTSTRAP_SERVERS},
                                {'name': 'REST_SERVER', 'value': 'http://fmi-rest-deploy:7999'},
                                {'name': 'START_TIME', 'value': data['start_time']},
                                {'name': 'END_TIME', 'value': data['final_time']},
                                {'name': 'TIME_JUMP', 'value': data['time_jump']},
                                {'name': 'BYSTEPS', 'value': data['by_steps']},
                                {'name': 'DATOS', 'value': data['data']}]
                    }],
                    'imagePullPolicy': 'IfNotPresent', # TODO: Remove this when the image is in DockerHub
                    'restartPolicy': 'OnFailure'
                }
            }
        }
    }

    resp = api_instance.create_namespaced_job(body=job_manifest, namespace='default')

    return Response(status=200)


@app.route("/get-FMI/<fmu_name>")
def sendFMU(fmu_name):
    try:
        return send_from_directory("FMUs", fmu_name+".fmu", as_attachment=True)
    except FileNotFoundError:
        abort(400)

@app.route("/delete-FMI/<fmu_name>")
def delFMU(fmu_name):
    os.remove('FMUs/'+fmu_name+'.fmu')
    return Response(status=200)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    """We need to run this code in order to get Kubernetes config"""
    config.load_incluster_config() # To run inside the container
    #config.load_kube_config() # To run externally
    logging.info("Connection to Kubernetes %s %s", os.environ.get('KUBE_TOKEN'), os.environ.get('KUBE_HOST'))
    api_client = kubernetes_config(token=os.environ.get('KUBE_TOKEN'), external_host=os.environ.get('KUBE_HOST'))
    api_instance = client.BatchV1Api(api_client)
    #api_instance = client.BatchV1Api()


    from waitress import serve
    logging.info("Todo inicializado")
    serve(app, host="0.0.0.0", port=8001)
    #app.run(debug=True, host="0.0.0.0", port = 8001)