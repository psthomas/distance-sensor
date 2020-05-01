# depth-sensor

# Distance Sensor

This code is for a general purpose depth sensor, which can be used for monitoring things like water levels. I use it to monitor my sump pump to make sure it doesn't overflow. It's configured to send a warning message by SMS via [Twilio](https://www.twilio.com/) when the water level gets too high:

![image in local repo]()

Below are a list of materials and setup instructions you can use to monitor levels of anything you want.

# Materials

Wireless capable raspberry pi with GPIO header, wiring, sensor, power cord, and sd card.

Also need an internet connection to send text messages through Twilio. 

# Hardware Setup

![image header diagram]()

Say which pins to attach

Place above what you need to measure. Uses soundwaves to measure distances, so it need to be level and perpendicular to the surface. 

# Installation

choose directory

git clone this repo

set up venv

activate venv

pip3 install requirements.txt

set up the configuration as outlined below. This will require you to create a Twilio account.

edit raspberry pi crontab to run the script run.sh as a cron job. You can choose any frequency you want, but anything less than a minute probably isn't a good idea.

# Configuration

There's an `example_config.json` file in the top directory that shows a complete configuration. You need to add a `config.json` file in this same directory, which is the actual file that will be read by `sensor.py`. Note that this file will contain sensitive information like your authorization token, so it **should never be included in version control** (it's already in the `.gitignore` file). 

To complete the configuration file, you need to first [create](https://www.twilio.com/docs/usage/tutorials/how-to-use-your-free-trial-account) a Twilio account and get a phone number. You then need to find your Account SID and Auth Token on the Twilio dashboard and place them in the appropriate fields in `config.json`.  

```
{
  "name": "Sump Pump",
  "sensor_height": 60.96,
  "warning_level": 45.72,
  "type": "fill",
  "warning_frequency": 15,
  "twilio_number": "+15017122661",
  "phone_numbers": ["+15017122661","+15017122661"],
  "twilio_account_sid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "twilio_auth_token": "your_auth_token"
}
```
The configuration options are explaned below:

- **name**: This string is the title of your sensor, and it will be referenced in any SMS notifications you get so you can distinguish between this sensor and others you may have installed.

- **type**: This string represents the sensor type. There are three options: `fill`, `drain` and `static`.  

- **sensor_height**: In centimeters, this integer or float is the distance of your sensor from a common reference point called a datum. For example, if you wanted to measure the depth of water in a tank, you would set your datum to be the bottom of the tank and measure the sensor height upwards from there.

- **warning_level**: In centimeters, this integer or float is the distance from the datum that triggers a warning message. If the datum was the bottom of your tank, and it was filling upwards to the brim, this would be the height from the bottom that triggers a warning.





