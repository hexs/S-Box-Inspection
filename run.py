import time
import hexss

hexss.check_packages(
    'numpy', 'opencv-python', 'Flask', 'requests', 'pygame', 'pygame-gui', 'tensorflow', 'matplotlib', 'pyzbar',
    'flatbuffers==23.5.26',
    auto_install=True
)

from hexss import json_load, close_port, get_hostname
from hexss.config import load_config
from hexss.network import get_all_ipv4
from hexss.server import camera_server
from hexss.path import get_script_dir, ascend_path
from hexss.modbus.serial import app as robot_app
from hexss.modbus.serial.robot import Robot
from hexss.constants.terminal_color import *
from hexss.serial import get_comport

from flask import Flask, render_template, request, jsonify, Response
import requests

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        button_name = request.form.get('button')
        if button_name:
            data = app.config['data']
            data['events'].append(button_name)
            print(f"Button clicked: {button_name}")
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
    app.config['data'] = data
    ipv4 = "0.0.0.0"
    port = data['config']['port']
    for ipv4_ in {'127.0.0.1', *get_all_ipv4(), get_hostname()} if ipv4 == '0.0.0.0' else {ipv4}:
        print(f"Running on http://{ipv4_}:{port}")
    app.run(host=ipv4, port=port, debug=False, use_reloader=False)


def send_request(robot_url, endpoint, method='post', **kwargs):
    try:
        response = getattr(requests, method)(f"{robot_url}/api/{endpoint}", **kwargs)
        response.raise_for_status()
        print(f"{endpoint.capitalize()} request sent successfully")
        return response.json() if method == 'get' else None
    except requests.RequestException as e:
        print(f"Error sending {endpoint} request: {e}")
        return None


def gpio(data, robot: Robot):
    from hexss.raspberrypi.gpio import SimultaneousEvents
    from gpiozero import DigitalOutputDevice, DigitalInputDevice

    def area_ok():
        return not (area1.value or area2.value)

    def alarm_reset():
        reset_alarm.on()  # on relay | toggle switch
        time.sleep(0.05)  # on relay | toggle switch
        reset_alarm.off()  # on relay | toggle switch
        robot.home(alarm_reset=True, servo_on=True, unpause=True)
        robot.move_to(0)

    def simultaneous_button_events():
        nonlocal robot, error_step
        print(f'{CYAN}--- Press both buttons simultaneously. ---{END}')
        if robot.is_any_moving():
            return
        if robot.is_any_servo_off():
            robot.alarm_reset()
            robot.servo(True)
        if robot.is_any_paused():
            robot.pause(False)

        if alarm.value == 1:  # หากเกิด alarm อยู่ให้ reset alarm
            print(f'{CYAN}--- alarm reset ---{END}')
            button_led.blink(0.2, 0.4)
            alarm_reset()

        print('get_distance', robot.get_distance(0))
        if robot.get_distance(0) > 4.0:
            robot.move_to(0)
            print('move_to(0)')
            button_led.blink(0.2, 0.4)
            error_step.append('move to 0')

        elif data['robot step'] == 'wait capture':  # move robot ไป capture
            if area_ok():
                data['events'].append('Capture&Predict')
                button_led.blink(0.2, 0.4)

    def alarm_event():
        nonlocal robot
        print(f'{CYAN}--- alarm_event ---{END}')
        button_led.off()

    def area_activated_events():
        nonlocal robot, error_step
        print(f'{CYAN}--- area_activated_events ---{END}')

        if robot.is_any_moving():
            error_step.append('error')
            print('area_activated_events append error')
            robot.pause(True)
            button_led.off()


    # 0 setup
    # 1 wait capture (wait simultaneous_button_events)
    # 2 capture

    O1, O2, O3, O4, BUTTON_LED, O6, RESET_ALARM, O8 = 4, 17, 18, 27, 22, 23, 24, 25
    I1, I2, ALARM, I4, R_BUTTON, L_BUTTON, AREA2, AREA1 = 5, 6, 12, 13, 16, 19, 20, 21

    # output
    reset_alarm = DigitalOutputDevice(RESET_ALARM)
    button_led = DigitalOutputDevice(BUTTON_LED)

    # input
    alarm = DigitalInputDevice(ALARM, bounce_time=0.1)
    r_button = DigitalInputDevice(R_BUTTON, bounce_time=0.1)
    l_button = DigitalInputDevice(L_BUTTON, bounce_time=0.1)
    area2 = DigitalInputDevice(AREA2, bounce_time=0.1)
    area1 = DigitalInputDevice(AREA1, bounce_time=0.1)
    simultaneous_events = SimultaneousEvents((r_button, l_button), max_interval=0.2)

    alarm.when_activated = alarm_event
    simultaneous_events.when_activated = simultaneous_button_events
    area1.when_activated = area_activated_events
    area2.when_activated = area_activated_events

    old_robot_step = ['-', '-']
    error_step = ['-', '-']

    alarm_reset()  # go home
    while True:
        time.sleep(0.1)

        old_robot_step.append(data['robot step'])
        old_robot_step.pop(0)

        if data['robot step'] == 'capture':  # มีอะไรเข้ามาใน area ตอน capture
            if (area1.value or area2.value):
                data['robot step'] = 'stop'
                robot.servo(on=False)

        # print(list(slave.is_moving() for slave in robot.slaves), end=' ')
        # if error_step[-1] == 'error':
        #     print('is_any_moving = ', robot.is_any_moving())
        # else:
        #     print(error_step)

        if error_step[-1] == 'move to 0' and not robot.is_any_moving():
            error_step = ['-', '-']
            button_led.on()

        if old_robot_step[0] != 'capture' and old_robot_step[1] == 'capture':
            button_led.blink(0.2, 0.4)
        if old_robot_step[0] != 'wait capture' and old_robot_step[1] == 'wait capture':
            button_led.on()


if __name__ == '__main__':
    import auto_inspection
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

        # 'stop'          | gpio                 | auto_inspection.main and robot capture

        'images': None,
    }

    try:
        comport = get_comport('ATEN USB to Serial', 'USB-Serial Controller')
        robot = Robot(comport, baudrate=38400, num_slaves=4)
        print(f"{GREEN}Robot initialized successfully{END}")
    except Exception as e:
        print(f"Failed to initialize robot: {e}")
        robot = None

    m.add_func(camera_server.run)
    m.add_func(auto_inspection.main, args=(data, robot))
    m.add_func(run_server, args=(data,), join=False)
    if config.get('xfunction') == 'robot':
        m.add_func(robot_capture.main, args=(data, robot))
        m.add_func(robot_app.run, args=({'config': {
            "ipv4": '0.0.0.0',
            "port": 2005
        }}, robot))
        if hexss.system == 'Linux':
            m.add_func(gpio, args=(data, robot))

    m.start()
    try:
        while data['play']:
            # print(m.get_status())
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        data['play'] = False
        config = load_config('camera_server')
        close_port(config['ipv4'], config['port'], verbose=False)
        m.join()
