import pathlib
import csv
import json
import pickle
import statistics
import logging
from time import sleep
from datetime import datetime, timedelta

from gpiozero import DistanceSensor
from twilio.rest import Client

# Set up global logger
this_dir = pathlib.Path(__file__).parent.absolute()
logging_path = this_dir.joinpath('sensor.log')
logging.basicConfig(filename=logging_path,format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO)
logging.getLogger("twilio").setLevel(logging.WARNING)
logging.getLogger("gpiozero").setLevel(logging.WARNING)

# https://gpiozero.readthedocs.io/en/stable/api_input.html#distancesensor-hc-sr04
def get_distance():
    measurements = []
    # Trying to set max_distance to 2m, default is 1m
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
        log_message = 'Warning sent to: {0}, sid {1}, message: {2}'.format(
        	number, sent.sid, message)
        logging.info(log_message)

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
        'base_dir': base_dir,
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
    fill_str = '''Warning: Your {0} level is {1}cm, which is above your allowed level of {2}cm.'''
    drain_str = '''Warning: Your {0} level is {1}cm, which is below your allowed level of {2}cm.'''
    static_str = '''Warning: Your {0} level is {1}cm, which is out of your allowed range of {2} to {3}cm.'''

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

    # If no warning is warranted:
    return None

def run_sample(config, paths):
    state = get_state(paths['state_path'])
    now = datetime.now()
    distance = get_distance()

    # Note, if datum is above sensor, sensor_height will be negative
    # so the math works out. This will even work if datum is between
    # the sensor_height and distance. Everything is relative to datum.
    level = config['sensor_height'] - distance
    record_level(paths['results_path'], now, config['sensor_height'], distance, level)
    logging.info('Reading recorded: {0}cm'.format(round(level, 2)))

    # Don't warn if you've already warned within frequency period
    # Note, if sending the SMS fails, the state will never be set. So as long as 
    # the measurement continues to be high, the warning will be sent next measurement.
    timeout = (now - state['last_warning']) < timedelta(minutes=config['warning_frequency'])

    level=50
    
    warning = create_warning(config, level)
    if warning:
        if not timeout:
            send_texts(config, warning)
            state['last_warning'] = now
            set_state(paths['state_path'], state)
        else:
            log_message = 'Warning warranted ({0}cm), but on timeout for {1}min.' \
                .format(round(level, 2), config['warning_frequency'])
            logging.info(log_message)

def main():
    paths = register_paths()
    config = get_config(paths['config_path'])
    try:
        run_sample(config, paths)
    except:
        logging.exception("An exception was thrown:")
        raise


if __name__ == '__main__':
    main()
