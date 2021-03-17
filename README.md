# cam-scan
Find interesting internet-exposed cameras through the Shodan API. This script will gather images from live hosts found on Shodan and present them in an HTML document. Great for showcasing the poor state of IoT security today.

Install dependancies using the command:
> pip install -r requirements.txt

usage: main.py [-h] [--init INIT] [-p PAGE | --all] [-d DIRNAME] [-t TIMEOUT] [-v] [-ext]

Arguments:
- -h, --help - Prints the help page
- --init - Initializes Shodan with your API key (needs to be used only on first run)
- -p, --page - Set page or range of Shodan results to run against
- --all - Run every available page on Shodan
- -d, --dirname - Set the name of the directory to store images in
- -t, --timeout - Time in seconds to wait for a response from each host before giving up
- -v, --verbose - Print each url to terminal as each connection is made, along with its status
- -ext - Generate an HTML page which loads external images from each host, rather than downloading images to your local machine


A few examples:

> main.py -h

> main.py --init api_key_here -p 1-3 -d myImages

> main.py --all -t 5 -v

> main.py --page 1-5,7,9 -ext --dirname savedImages

Alternatively, users who do not understand or care about these options can simply run quick.py

Some of the Shodan queries used here and the --page argument require a paid Shodan account to use
