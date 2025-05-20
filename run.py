import os
import logging
import time
from datetime import datetime

from hexss import json_load, json_update, is_port_available, close_port, check_packages, get_hostname
from hexss.network import get_all_ipv4
from hexss.path import get_script_dir, ascend_path

check_packages(
    'numpy', 'opencv-python', 'Flask', 'requests', 'pygame', 'pygame-gui', 'tensorflow', 'matplotlib', 'pyzbar',
    'flatbuffers==23.5.26',
    auto_install=True
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
    return data['robot step']


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


def gpio(data, robot):
    check_packages(
        'lgpio',
        auto_install=True
    )

    import lgpio
    import threading

    def read(pin):
        return lgpio.gpio_read(h, pin)

    def write(pin, status):
        lgpio.gpio_write(h, pin, status)

    def led_off():
        global led_blinking
        global ledstatus
        led_blinking = False
        write(BUTTON_LED, 0)
        ledstatus = 'off'

    def led_on():
        global led_blinking
        global ledstatus
        led_blinking = False
        write(BUTTON_LED, 1)
        ledstatus = 'on'

    def blink_led():
        global led_blinking, led_blinking_time
        while led_blinking:
            write(BUTTON_LED, 1)
            time.sleep(led_blinking_time)
            write(BUTTON_LED, 0)
            time.sleep(led_blinking_time)

    def led_blink(blink_time=None):
        global led_blinking, led_blinking_time
        global ledstatus
        if blink_time:
            led_blinking_time = blink_time
        if not led_blinking:
            led_blinking = True
            threading.Thread(target=blink_led, daemon=True).start()

        ledstatus = 'blink'


    def reset_em():
        write(RESET_EM, 1)
        time.sleep(0.2)
        write(RESET_EM, 0)
        time.sleep(0.2)
        robot.home(slaves=[1, 2, 3, 4], alarm_reset=True, on_servo=True)
        robot.wait_for_target(slaves=[1, 2, 3, 4])
        robot.move_to(slaves=[1, 2, 3, 4], row=0)

    # GPIO Pin Definitions
    OUT1, OUT2, OUT3, OUT4 = 4, 17, 18, 27
    BUTTON_LED, OUT6, RESET_EM, OUT8 = 22, 23, 24, 25
    AREA1, AREA2, L_BUTTON, R_BUTTON = 21, 20, 19, 16
    IN4, IN3, IN2, ALARM = 13, 12, 6, 5

    # Global variables
    h = lgpio.gpiochip_open(0)
    led_blinking = False
    led_blinking_time = 0.3
    ledstatus = '-'
    l_button_press = None
    r_button_press = None

    input_pins = [AREA1, AREA2, L_BUTTON, R_BUTTON, IN4, IN3, IN2, ALARM]
    output_pins = [OUT1, OUT2, OUT3, OUT4, BUTTON_LED, OUT6, RESET_EM, OUT8]

    for pin in input_pins:
        lgpio.gpio_claim_input(h, pin)

    for pin in output_pins:
        lgpio.gpio_claim_output(h, pin)

    reset_em()
    led_on()
    step = 1
    while True:
        try:
            l_button = read(L_BUTTON)
            r_button = read(R_BUTTON)
            alarm = read(ALARM)
            area1 = read(AREA1)
            area2 = read(AREA2)
            print(step, area1, area2, l_button, r_button, data['robot step'], ledstatus)

            if alarm == 1:
                led_off()
                step = 1

                if l_button == 1:
                    l_button_press = None
                if r_button == 1:
                    r_button_press = None

                if l_button == 0 and l_button_press is None:
                    l_button_press = datetime.now()
                if r_button == 0 and r_button_press is None:
                    r_button_press = datetime.now()

                if l_button_press is not None and r_button_press is not None:
                    time_difference = abs((l_button_press - r_button_press).total_seconds())
                    if time_difference < 0.5:
                        reset_em()

                continue

            if step == 1:
                led_on()

                if l_button == 1:
                    l_button_press = None
                if r_button == 1:
                    r_button_press = None

                if l_button == 0 and l_button_press is None:
                    l_button_press = datetime.now()
                if r_button == 0 and r_button_press is None:
                    r_button_press = datetime.now()

                if l_button_press is not None and r_button_press is not None:
                    time_difference = abs((l_button_press - r_button_press).total_seconds())
                    if time_difference < 0.5:
                        data['events'].append('Capture&Predict')
                        led_blink(0.4)
                        step = 2

            if data['robot step'] == 'capture':
                step = 2



            elif step == 2:
                if data['robot step'] == 'wait capture':
                    step = 1
                    time.sleep(0.5)
                    led_on()
            #     if area1 == 1 or area2 == 1:
            #         # pause(True)
            #         step == 4
            #
            # elif step == 4:
            #     if l_button == 0 and r_button == 0:
            #         # pause(False)
            #         step = 3

            time.sleep(0.1)

        except:
            ...


if __name__ == '__main__':
    import auto_inspection
    from hexss.constants.terminal_color import *
    from hexss.control_robot import app as robot_app
    from hexss.control_robot.robot import Robot
    from hexss.serial import get_comport
    from hexss.threading import Multithread
    import robot_capture
    import platform

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

    script_directory = get_script_dir()
    projects_directory = ascend_path(script_directory)

    m = Multithread()
    data = {
        'config': config,
        'script_directory': script_directory,
        'projects_directory': projects_directory,
        'model_name': config['model_name'],
        'model_names': config['model_names'],
        'events': [],  # Capture, Adj, Predict, Capture&Predict
        'play': True,
        'robot step': 'wait capture',
        #                 |  (send)              | (receive)
        # 'wait capture'  | auto_inspection.main | auto_inspection.main
        # 'capture'       | auto_inspection.main | robot capture
        # 'capture ok'    | robot capture        | auto_inspection.main
        # 'capture error' | robot capture        |

        'images': None,
    }

    try:
        comport = get_comport('ATEN USB to Serial', 'USB-Serial Controller')
        robot = Robot(comport, baudrate=38400)
        print(f"{GREEN}Robot initialized successfully{END}")
    except Exception as e:
        print(f"Failed to initialize robot: {e}")
        # exit()
        robot=None

    m.add_func(auto_inspection.main, args=(data, robot))
    m.add_func(run_server, args=(data,), join=False)
    if config.get('xfunction') == 'robot':
        m.add_func(robot_capture.main, args=(data, robot))
        m.add_func(robot_app.run, args=({'config': {
            "ipv4": '0.0.0.0',
            "port": 2005
        }}, robot))
        if platform.system() == 'Linux':
            m.add_func(gpio, args=(data, robot))

    m.start()
    m.join()
