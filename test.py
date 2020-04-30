import sensor
from time import sleep
from gpiozero import DistanceSensor

def test_sensor():
    sensor = DistanceSensor(echo=17, trigger=27)
    while True:
        print(sensor.distance)
        sleep(1)

def test_get_distance():
    while True:
        distance_cm = sensor.get_distance() #distance cm
        print('Distance: {0}cm'.format(distance_cm))
        sleep(3)

def test_create_warning():
    level1 = 50
    config1 = {
        'sensor_height': 60.96,
        'warning_level': 45.72,
        'type': 'fill', 
        'test_frequency': 1,
        'warning_frequency': 15,
        'phone_numbers': []
    }

    level2 = 25
    config2 = config1.copy()
    config2['type'] = 'drain'

    level3 = 50
    config3 = config1.copy()
    config3['warning_level'] = {'upper': 25, 'lower': 10}
    config3['type'] = 'static'

    level4 = -10
    config4 = config3.copy()
    config4['warning_level'] = {'upper': -3, 'lower': -5}
    
    tests = [(level1, config1), (level2, config2), (level3, config3),
        (level4, config4)]
    for test in tests:
        warning = sensor.create_warning(test[1], test[0])
        print(warning)

if __name__ == '__main__':
    #Uncomment as needed
    #test_sensor()
    #test_get_distance()
    #test_create_warning()
