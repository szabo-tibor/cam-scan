import CamScan
from argparse import ArgumentParser

def main():

    parser = ArgumentParser(description='Find interesting internet-exposed cameras through the Shodan API.')
    pageInfo = parser.add_mutually_exclusive_group()


    parser.add_argument('--init',
                        help='Initialize Shodan API with your API key (only has to be done on first run)')

    pageInfo.add_argument('-p','--page',
                          help='Specify page or comma-separated page values of Shodan results to run against. Ex. 1-5,8,9')

    pageInfo.add_argument('--all',
                          help='Run every page of search results on Shodan',
                          action='store_true')

    parser.add_argument('-d','--dirname',
                        help='Specify name of directory or absolute path of location to store images',
                        type=str)

    parser.add_argument('-t','--timeout',
                        help='Time in seconds to wait for each host until giving up',
                        type=int)

    parser.add_argument('-v','--verbose',
                        help='Print each url to terminal as each connection is made, along with its status',
                        action='store_true')

    parser.add_argument("-ext",
                        help='Generate an HTML page which loads external images from each host, rather than downloading images to your local machine',
                        action='store_true')

    cli_input = parser.parse_args()

    scan = CamScan.CamScan()

    if cli_input.init:
        scan.initShodan(cli_input.init)

    if cli_input.page:
        scan.setPages(cli_input.page)

    if cli_input.all:
        scan.setPages(None)

    if cli_input.dirname:
        scan.dirname = cli_input.dirname

    if cli_input.timeout:
        scan.timeout = int(cli_input.timeout)

    if cli_input.verbose:
        scan.verbose = True

    if cli_input.ext:
        scan.store_offline = False

    scan.chooseFromCSV('queries.csv')
    total_available_pages = scan.pagesCount()

    if type(scan.pages) == dict:
        for pageNumber in scan.pages:
            if int(pageNumber) > total_available_pages + 1:
                print("Page number {} goes past end of {} total available pages of results for this search. Exiting...".format(pageNumber,total_available_pages+1))
                exit(1)

        print("Running a total of {} pages, from an available {}.".format(len(scan.pages),total_available_pages + 1))

    if scan.pages == None:
        print("Running all {} pages.".format(total_available_pages))
        

    choice = input("Continue? [y/n]:")

    if choice != 'y':
        exit(0)

    try:
        scan.run()

    finally:
        if len(scan.live_hosts) != 0:
            scan.generatePage()

if __name__ == '__main__':
    main()
