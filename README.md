# cam-scan
Find interesting internet-exposed cameras through the Shodan API. This script will gather images from live hosts found on Shodan and present them in an HTML document. Great for showcasing the poor state of IoT security today.

Install dependancies using the command:
> pip install -r requirements.txt

usage: main.py [-h] [--init INIT] [-p PAGE | --all] [-d DIRNAME] [-t TIMEOUT] [-v] [-c]

Alternatively, users who do not understand or care about these options can simply run quick.py

Some of the Shodan queries used here require a paid Shodan account to use
