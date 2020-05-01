# Distance Sensor

This code is for a general purpose distance sensor, which can be used for monitoring things like water levels. For example, I use it to monitor my sump pump to make sure it doesn't overflow. It's configured to send  warning text messages to me via [Twilio](https://www.twilio.com/) when the water level gets too high:

![phone screen]!(phone.png)

Below are a list of materials and setup instructions you can use this code to monitor anything you want.

# Materials

- Wireless capable [Raspberry Pi](https://www.adafruit.com/category/176) with GPIO headers, power cord, and SD card
- Female to Female [Jumper Wires](https://www.adafruit.com/product/1919)
- An ultrasonic sensor, either [US-100](https://www.adafruit.com/product/4019) or [RCWL-1601](https://www.adafruit.com/product/4007).
- An internet connection to send text messages through Twilio's API 

All told, the above materials should cost around $40.  

# Hardware Setup

The first step is to get the Raspberry Pi up and running and connect the distance sensor. I won't go in-depth into this as there are [better resources](https://learn.adafruit.com/ultrasonic-sonar-distance-sensors) out there but the crucial thing to know is that I assume that the echo of your sensor is attached to GPIO 17, and the trigger to GPIO 27. The power can be attached to any 3V pin, and the ground to any ground pin. 

![headers]!(gpio.png)

The next step is to put the sensor in position.Point the sensor at what you want to measure, keeping it perpendicular to the surface (these sensors use soundwaves to measure distances, so oblique angles won't work). The sensors will work at about 2cm to 450cm away, but 10cm-250cm will give you the best results.  

# Code Installation

All of the code for this project is available in [this](https://github.com/psthomas/distance-sensor) GitHub repository. Either ssh into your Raspberry Pi, or connect it to a keyboard or screen. Choose a directory to install this code, then clone and enter this repo:

```
$ git clone https://github.com/psthomas/distance-sensor.git
$ cd distance-sensor
```
Next, you need to install the dependencies, which I used a virtual environment for to keep consistent. The [recommended](https://docs.python.org/3/tutorial/venv.html) way to create virtual environments is now the built in `venv`, so that's what I'll use: 

```
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip3 install requirements.txt
```
Next, you need to set up the configuration file as outlined below. Once that's finished, come back here for the final commands to get it up and running.

The final thing to do is tell your computer to routinely run this script to take a distance measurement. There's a small script in the root directory called `run.sh` that's used for this purpose. All you need to do is open it and change the path `/home/pi/Projects/depth-sensor` to whatever path your project is installed at.

```
#!/bin/bash

cd /home/pi/Projects/distance-sensor
source .venv/bin/activate # Activate Python environment
python3 sensor.py # Run the sensor code
```

Then use [crontab](https://www.raspberrypi.org/documentation/linux/usage/cron.md) to add this script as a routinely repeating Cron job using this command:

```
$ crontab -e
```

This will open up a file for editing which you can then add a job to. You can choose any interval that suits you, but I chose to run it every minute using the line below (any frequency less than a minute probably isn't a good idea). Note that you should change the path `/home/pi/Projects/distance-sensor/run.sh` to point wherever the script is located on your device:

```
*/1 * * * * /bin/bash /home/pi/Projects/distance-sensor/run.sh
``` 
After you save and close the Cron file, the script will be up and running at the interval you specified. A `results.csv` file will then be created in the top directory to record the distance measurements, and any logging outputs from `sensor.py` will be recorded in `sensor.log` in the same directory. 

# Configuration

There's an `example_config.json` file in the top directory that shows a complete configuration. You need to add a `config.json` file in this same directory, which is the actual file that will be read in by `sensor.py`. Note that this file will contain sensitive information like your Twilio authorization token, so it **should never be included in version control** (it's already in the `.gitignore` file for this reason).

To complete the configuration file, you need to first [create](https://www.twilio.com/docs/usage/tutorials/how-to-use-your-free-trial-account) a Twilio account and get a phone number. You then need to find your Account SID and Auth Token on the Twilio dashboard and place them in the appropriate fields in `config.json`.  

```
{
  "name": "sump pump",
  "type": "near",
  "warning_distance": 15.5,
  "warning_frequency": 15,
  "twilio_number": "+15017122661",
  "phone_numbers": ["+15017122661","+15017122661"],
  "twilio_account_sid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "twilio_auth_token": "your_auth_token"
}
```
The configuration options are explaned below:

- **name**: This string is the title of your sensor, and it will be referenced in any SMS notifications you get so you can distinguish between this sensor and others you may have installed.

- **type**: This string represents the sensor type. There are three options: `near`, `far` or `static`. A `near` type sensor will send a warning whenever a measurement is closer than the warning distance to the sensor. A `far` type sensor will warn you if a measurement is further away than the warning distance. And a `static` sensor defines an upper and lower bound that the measurement must be between.     

- **warning_distance**: In centimeters, this setting represents the distance from the sensor that triggers a warning message. This will always be a positive distance because it is measured relative to the sensor. For the `near` and `far` sensors, this value will be an integer or float. For `static` sensors, this value will be represented by an object like `{"lower": 25, "upper": 50}` that sets the bounds for the measurement.

- **warning_frequency**: How often, in minutes, the warning should be sent if a measurement warrants a warning. This is to prevent your phone from getting blown up by warnings after you've already received one.

- **twilio_number**: A string representing the number you've purchased from Twilio.

- **phone_numbers**: A list of one or more phone numbers that will recieve the warning message. These phone numbers should be strings.

- **twilio_account_sid**: A string of the account_sid from your Twilio dashboard.

- **twilio_auth_token**: A string of the authorization token from your Twilio dashboard.

Here are a few more configuration examples. The first is for monitoring the water in a christmas tree stand. The water level will be getting further away from the sensor as it drains, so it has a `far` type sensor. 

```
{
  "name": "christmas tree",
  "type": "far",
  "warning_distance": 10,
  "warning_frequency": 15,
  "twilio_number": "+15017122661",
  "phone_numbers": ["+15017122661"],
  "twilio_account_sid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "twilio_auth_token": "your_auth_token"
}
```

The final configuration is for monitoring if a garage door is open. It uses a `static` type sensor:

```
{
  "name": "garage door",
  "type": "static",
  "warning_distance": {"lower": 30, "upper": 100},
  "warning_frequency": 15,
  "twilio_number": "+15017122661",
  "phone_numbers": ["+15017122661"],
  "twilio_account_sid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "twilio_auth_token": "your_auth_token"
}
```





