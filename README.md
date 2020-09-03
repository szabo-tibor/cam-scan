# cam-scan
Find interesting internet-exposed cameras through the Shodan API. This script will gather images from live hosts found on Shodan and present them in an HTML document.

Install dependancies using the command:
> pip install -r requirements.txt

usage: main.py [-h] (-s SEARCH | --csv CSV) [-pa PATH] [--init INIT]
               [-p PAGE | --all] [-d DIRNAME] [-t TIMEOUT] [-v]
