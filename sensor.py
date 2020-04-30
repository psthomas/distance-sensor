import os
import pathlib
import csv
import json
import pickle
import statistics
from time import sleep
from datetime import datetime, timedelta

#from gpiozero.pins.native import NativeFactory
from gpiozero import DistanceSensor
from twilio.rest import Client

# https://gpiozero.readthedocs.io/en/stable/api_input.html#distancesensor-hc-sr04
def get_distance():
    measurements = []
    # Trying to set max_distance to 2m, default is 1m
    #factory = NativeFactory() pin_factory=factory)
    sensor = DistanceSensor(echo=17, trigger=27)
    for i in range(5):
        dist = sensor.distance  # Initial value in m
        measurements.append(dist)
        sleep(0.25)
    result = statistics.mean(measurements)*100 # Convert to cm
    return result # Returns result in cm

def send_texts(config, message):
    # https://www.twilio.com/docs/sms/quickstart/python
    # https://www.twilio.com/docs/usage/secure-credentials
    account_sid = config['twilio_account_sid']
    auth_token = config['twilio_auth_token']
    client = Client(account_sid, auth_token)
    
    for number in config['phone_numbers']:
        sent = client.messages.create(
            body=message,
            from_=config['twilio_number'],
            to=number
        )
        print('Warning sent to: {0}, sid {1}, message: {2}'.format(number, sent.sid, message))

def record_level(results_path, now, sensor_height, distance, level):
    # Append to CSV file
    # Note that this file will always exist, as handled in register_paths()
    with results_path.open('a', newline='') as csvfile:
        #https://docs.python.org/2/library/csv.html#csv.DictWriter
        fieldnames = ['time', 'sensor_height', 'distance', 'level']
        writer = csv.DictWriter(csvfile, fieldnames)
        writer.writerow({
            'time': now.isoformat(),
            'sensor_height': sensor_height,
            'distance': distance, 
            'level': level
        })

def get_state(state_path):
    # Load most recent warning time from .pickle
    state = pickle.load(state_path.open('rb'))
    return state

def set_state(state_path, state):
    # If warning was sent, update state to most recent
    pickle.dump(state, state_path.open('wb'))

def register_paths():    
    # Filepaths need to be built with reference to this 
    # file because crontab's current working directory 
    # might not be the file's working directory.
    # https://stackoverflow.com/questions/3430372
    base_dir = pathlib.Path(__file__).parent.absolute()
    state_path = base_dir.joinpath('state.pkl')
    results_path = base_dir.joinpath('results.csv')
    config_path = base_dir.joinpath('config.json')

    if not state_path.exists():
        # Initialize and write out arbitrary earlier date
        state = {'last_warning': datetime(year=2005, month=1, day=1)}
        pickle.dump(state, state_path.open('wb'))
        
    if not results_path.exists():
        # Write out CSV file with header
        with results_path.open('w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            header = ['time', 'sensor_height', 'distance', 'level']
            writer.writerow(header)

    return {
        'state_path': state_path,
        'results_path': results_path,
        'config_path': config_path
    }

def validate_config(config):
    pass

def get_config(config_path):
    with config_path.open('r') as f:
        data = f.read()
    config = json.loads(data)
    return config

def create_warning(config, level):

    fill_str = '''Warning: your {0} level is {1}cm, which is above your allowed level of {2}cm.'''
    drain_str = '''Warning: your {0} level is {1}cm, which is below your allowed level of {2}cm.'''
    static_str = '''Warning: your {0} level is {1}cm, which is out of your allowed range of {2} to {3}cm.'''

    # Note: Absolute values need to be used to handle situation where sensor 
    # height/warning_level are negative relative to datum.
    # E.g. when it's draining, level = -7 relative to datum, and warning_level = -6
    # Actually it's not needed, this will work as is?
    # And for this to work with the static numbers, the upper bound must always be the
    # larger of the two numbers, even if they're negative (e.g. -5 > -10)

    name = config['name']

    if (config['type'] == 'fill') and (level > config['warning_level']):
        return fill_str.format(name, round(level, 2), config['warning_level'])
    elif (config['type'] == 'drain') and (level < config['warning_level']):
        return drain_str.format(name, round(level, 2), config['warning_level'])
    # Note: for this to work, the upper bound must always be the larger
    # of the two numbers, even if they're negative (e.g. -5cm > -10cm)
    elif (config['type'] == 'static'):
        upper_bound = config['warning_level']['upper']
        lower_bound = config['warning_level']['lower']
        if (level > upper_bound) or (level < lower_bound):
            return static_str.format(name, round(level, 2), lower_bound, upper_bound)

    # If no warning is warranted
    return False

def update_web():
    # Use this function to create the matplotlib visualization,
    # and pass it and the data into the template. Maybe put this
    # in app.py along with the server, then import and use it below
    # after the measurement has been taken?
    pass

def run_sample(config, paths):
    state = get_state(paths['state_path'])
    now = datetime.now()
    distance = get_distance()

    # Note, if datum is above sensor, sensor_height will be negative
    # so the math works out. This will even work if datum is between
    # the sensor_height and distance. Everything is relative to datum.
    level = config['sensor_height'] - distance
    record_level(paths['results_path'], now, config['sensor_height'], distance, level)
    print('Actual level: ', level)

    level = 50
    print('Fake level: ', level)

    # Don't warn if you've already warned within frequency period
    # Note, if sending the SMS fails, the state will never be set. So as long as 
    # the measurement continues to be higher, the warning will be sent next measurement.
    if (now - state['last_warning']) >= timedelta(minutes=config['warning_frequency']):
        warning = create_warning(config, level)
        if warning:
            print(warning)
            send_texts(config, warning)
            state['last_warning'] = now
            set_state(paths['state_path'], state)
    else:
        print('Too soon, {0}'.format(state['last_warning']))


def main():
    paths = register_paths()
    config = get_config(paths['config_path'])
    
    while True:
        run_sample(config, paths)
        sleep(config['test_frequency']*60) # Wait in seconds


if __name__ == '__main__':
    # TODO: if sys.argv[0] == "--test":
    # load test_config.json and pass to main
    # otherwise load config.json and pass it to main
    # That way all the user has to do is change config.json
    main()


# types: upper, lower, static
# types: fill, drain, static
# if static, confic must have +- error bound
# so if static, needs "bound": {"upper": cm, "lower": cm}
# Note that the "upper" will always be closest to sensor
# maybe have datum? Or just have heights all measured relative to same point?

# TODO: mention limitations of sensor, e.g. near and far distance
# TODO: Tab delimit, or comma delimit and just format the webpage? Just comma delimit
# TODO: except for config, wrap below in another function? 
# TODO: To build matplotlib vis, take tail off CSV with largest number of points it can handle. 
# This will prevent the plotting from slowing down once many points have been gathered.
# TODO: Logging

# DONE: install requirements, figure out venv, .env variables
# TODO: Implement text messaging

# so what requirements do I have?
# matplotlib, twilio, gpiozero.
# Server can be handled with python, templating too. 

# "datum": 0, # Height all other measurements are relative
# "sensor_height": 60.96, # Height above datum in centimeters
# so warning_distance below should be 60.96-45.72 = 15.24 cm
# Just say that all heights need to be measured relative to the same height
# in the directions. Could be relative to sensor? Should all measurements just
# be relative to the sensor?
# just have warning distance?
# Example bound dict: {'lower': 5, 'upper': 10}, note, upper has to be furthest from datum
# so if the datum is above the level (e.g. top of tank), the upper bound is actually the more
# negative of the two numbers. NO THIS IS NOT TRUE. THE UPPER BOUND SHOULD ALWAYS BE THE
# LARGER OF THE TWO NUMBERS. SO IF IT'S NEGATIVE, IT SHOULD ALWAYS BE LESS NEGATIVE THAN
# THE LOWER BOUND.
