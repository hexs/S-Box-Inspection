import os
import logging
import time
from hexss import json_load, json_update, is_port_available, close_port, check_packages
from hexss.network import get_all_ipv4, get_hostname
from hexss.path import get_script_directory, move_up

check_packages(
    'numpy', 'opencv-python', 'Flask', 'requests', 'pygame', 'pygame-gui', 'tensorflow', 'matplotlib', 'pyzbar',
)

from flask import Flask, render_template, request, jsonify, Response
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        button_name = request.form.get('button')
        if button_name:
            data = app.config['data']
            data['events'].append(button_name)
            logger.info(f"Button clicked: {button_name}")
    return render_template('index.html')


@app.route('/status_robot', methods=['GET'])
def status_robot():
    data = app.config['data']
    return data['robot capture']


@app.route('/data', methods=['GET'])
def data():
    data = app.config['data']

    # return jsonify(data), 200

    def generate():
        result = ''
        while True:
            old_result = result
            result = f"data: {str(data)}\n\n"
            if result != old_result:
                yield result
            time.sleep(0.1)

    return Response(generate(), mimetype='text/event-stream')


def run_server(data):
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    app.config['data'] = data
    ipv4 = "0.0.0.0"
    port = data['config']['port']
    if ipv4 == '0.0.0.0':
        for ipv4_ in {'127.0.0.1', *get_all_ipv4(), get_hostname()}:
            logging.info(f"Running on http://{ipv4_}:{port}")
    else:
        logging.info(f"Running on http://{ipv4}:{port}")
    app.run(host=ipv4, port=port, debug=False, use_reloader=False)


def send_request(robot_url, endpoint, method='post', **kwargs):
    try:
        response = getattr(requests, method)(f"{robot_url}/api/{endpoint}", **kwargs)
        response.raise_for_status()
        logger.info(f"{endpoint.capitalize()} request sent successfully")
        return response.json() if method == 'get' else None
    except requests.RequestException as e:
        logger.error(f"Error sending {endpoint} request: {e}")
        return None


if __name__ == '__main__':
    import auto_inspection
    from hexss.constants.cml import *
    from hexss.control_robot import app as robot_app
    from hexss.control_robot.robot import Robot
    from hexss.serial import get_comport
    from hexss.threading import Multithread
    import robot_capture

    config = json_load('config.json', {
        'ipv4': '0.0.0.0',
        'port': 3000,
        'device_note': 'PC, RP',
        'device': 'RP',
        'resolution_note': ['1920x1080', '800x480'],
        'resolution': '800x480',
        'model_names': [],
        'model_name_note': ['-', 'QC7-7990-000'],
        'model_name': 'QC7-7990-000',
        'fullscreen': False,
        'xfunction_note': ['robot'],
        'xfunction': 'robot',

        'image_url': 'http://box01:2002/image?source=video_capture&id=0',
        'robot_url': 'http://box01:2005',
    }, True)

    close_port(config['ipv4'], config['port'])

    script_directory = get_script_directory()
    projects_directory = move_up(script_directory)

    m = Multithread()
    data = {
        'config': config,
        'script_directory': script_directory,
        'projects_directory': projects_directory,
        'model_name': config['model_name'],
        'model_names': config['model_names'],
        'events': [],
        'play': True,
        'robot capture': '',  # *'', 'capture', 'capture ok', 'error'
        'images': None,
    }

    try:
        comport = get_comport('ATEN USB to Serial', 'USB-Serial Controller')
        robot = Robot(comport, baudrate=38400)
        print(f"{GREEN}Robot initialized successfully{ENDC}")
    except Exception as e:
        print(f"Failed to initialize robot: {e}")
        exit()

    m.add_func(auto_inspection.main, args=(data, robot))
    m.add_func(run_server, args=(data,), join=False)
    if config.get('xfunction') == 'robot':
        m.add_func(robot_capture.main, args=(data, robot))
        m.add_func(robot_app.run, args=({'config': {
            "ipv4": '0.0.0.0',
            "port": 2005
        }}, robot))

    m.start()
    m.join()
