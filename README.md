# cam-scan
Find interesting internet-exposed cameras through the Shodan API


usage: main.py [-h] (-s SEARCH | --csv CSV) [-pa PATH] [--init INIT]
               [-p PAGE | --all] [-d DIRNAME] [-t TIMEOUT] [-v]

Find interesting internet-exposed cameras through the Shodan API

optional arguments:
  -h, --help            show this help message and exit
  -s SEARCH, --search SEARCH
                        Shodan search query. use single quotation marks inside
                        shodan query, wrap entire search around double
                        quotation marks
  --csv CSV             Choose search/path from CSV file. use
                        "searchQuery,imagePath" as a title row.
  -pa PATH, --path PATH
                        Path in URL for image scraping e.g, "/index/shot.jpeg"
  --init INIT           Initialize Shodan API with your API key (only has to
                        be done on first run)
  -p PAGE, --page PAGE  Specify page or pages to search
  --all                 Run every page of search results on Shodan
  -d DIRNAME, --dirname DIRNAME
                        specify name of new directory to save images
  -t TIMEOUT, --timeout TIMEOUT
                        Time in seconds to wait for each host until giving up
  -v, --verbose         Print each url to terminal as each connection is made,
                        along with its status
