from flask import Flask, request, Response
from flask import send_file, send_from_directory, abort
from flask_cors import CORS, cross_origin
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
cors = CORS(app)

@app.route('/FMI', methods=['POST'])
def getData():
    #CODIGO PARA CREAR EL CONTENEDOR DE KUBERNETES
    logging.info("Petición de ejecución recibida")

    # INTENTO DE CREACION DE DIRECTORIO PARA GUARDAR FMU
    try:
        os.mkdir("FMUs")
    except FileExistsError:
        logging.info("La carpeta FMUs ya existe")

    # LECTURA DE DATOS DE REQUEST
    data = request.form
    logging.info("Formulario con los datos recibido")

    #LECTURA DE PARAMETROS
    if 'start_time' not in data: return Response("No se ha recibido el timpo de inicio", status=400) 
    else: start_time = data['start_time']

    if 'final_time' not in data: return Response("No se ha recibido el timpo de finalización", status=400)
    else: final_time = data['final_time']

    if 'by_steps' not in data: by_steps = 'None'
    else: by_steps = data['by_steps']

    if 'time_jump' not in data and by_steps == 'True': return Response("No se ha recibido el salto de tiempo", status=400)
    elif 'time_jump' not in data: time_jump = 'None'
    else: time_jump = data['time_jump']

    if 'kafkaTopic' not in data: kafkaTopic = 'None'
    else: kafkaTopic = data['kafkaTopic'].lower()

    if 'id' not in data: Response("No se ha recibido id", status=400)
    else: id = data['id']

    if 'variables' not in data: variables = 'None'
    else: variables = data['variables']

    if 'opciones' not in data: opciones = 'None'
    else:
        print("Llegan opciones")
        opciones = data['opciones']
    print(data)
    
    # LECTURA DE FMU
    if 'file' not in request.files:
        return Response("No se ha recibido el archivo", status=400)
    else:
        uploaded_file = request.files['file']
        uploaded_file.save("FMUs/"+str(id)+".fmu")
        logging.info("Fichero recibido")

    logging.info('Leido datos y creando nueva ejecución')
    
    
    if 'kafkaClusterIP' in data.keys():
        BOOTSTRAP_SERVERS = data['kafkaClusterIP']
    else:
        BOOTSTRAP_SERVERS = []


    job_manifest = {
        'apiVersion': 'batch/v1',
        'kind': 'Job',
        'metadata': {
            'name': 'fmu-executer'+kafkaTopic+id
        },
        'spec': {
            'ttlSecondsAfterFinished' : 10,
            'template' : {
                'spec': {
                    'containers': [{
                        'image': "10.10.32.232:30501/fmurunner", 
                        'name': 'fmurunner-'+kafkaTopic+id,
                        'env': [{'name': 'KAFKA_TOPIC', 'value': kafkaTopic},
                                {'name': 'KAFKA_SERVER', 'value': BOOTSTRAP_SERVERS},
                                {'name': 'REST_SERVER', 'value': 'http://fmi-rest-deploy:7999'},
                                {'name': 'START_TIME', 'value': start_time},
                                {'name': 'END_TIME', 'value': final_time},
                                {'name': 'TIME_JUMP', 'value': time_jump},
                                {'name': 'BYSTEPS', 'value': by_steps},
                                {'name': 'IDejecucion', 'value': id},
                                {'name': 'VARIABLES', 'value': variables},
                                {'name': 'OPCIONES', 'value': opciones}]
                    }],
                    'imagePullPolicy': 'Always', # TODO: Remove this when the image is in DockerHub
                    'restartPolicy': 'OnFailure'
                }
            }
        }
    }
    logging.info('Creando job')
    resp = api_instance.create_namespaced_job(body=job_manifest, namespace='digitaltwins')
    logging.info('Job creado')

    return Response(status=200)


@app.route("/get-FMI/<fmu_name>")
def sendFMU(fmu_name):
    logging.info("Sending FMU file")
    try:
        return send_from_directory("FMUs", fmu_name+".fmu", as_attachment=True)
    except FileNotFoundError:
        abort(400)

@app.route("/delete-FMI/<fmu_name>")
def delFMU(fmu_name):
    logging.info("Eliminando archivo")
    logging.info(os.listdir('FMUs/'))
    try:
        location = '/usr/src/app/FMUs'
        file = fmu_name+'.fmu'
        path = os.path.join(location, file)
        os.system('rm -f ' + path)
    except Exception as err:
        logging.info(err)
        logging.info("Archivo no encontrado")
    return Response(status=200)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)


    """ KUBERNETES code goes here"""
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