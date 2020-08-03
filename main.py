import CamScan
from argparse import ArgumentParser

parser = ArgumentParser(description='Find interesting internet-exposed cameras through the Shodan API')

pageInfo = parser.add_mutually_exclusive_group()
query = parser.add_mutually_exclusive_group(required=True)


query.add_argument('-s','--search',
                   help='Shodan search query. use single quotation marks inside shodan query, wrap entire search around double quotation marks')

query.add_argument('--csv',
                   help='Choose search/path from CSV file. use "searchQuery,imagePath" as a title row.')

parser.add_argument('-pa','--path',
                    help='Path in URL for image scraping e.g, "/index/shot.jpeg"')

parser.add_argument('--init',
                    help='Initialize Shodan API with your API key (only has to be done on first run)')

pageInfo.add_argument('-p','--page',
                      help='Specify page or pages to search')

pageInfo.add_argument('--all',
                      help='Run every page of search results on Shodan',
                      action='store_true')

parser.add_argument('-d','--dirname',
                    help='specify name of new directory to save images',
                    type=str)

parser.add_argument('-t','--timeout',
                    help='Time in seconds to wait for each host until giving up',
                    type=int)

parser.add_argument('-v','--verbose',
                    help='Print each url to terminal as each connection is made, along with its status',
                    action='store_true')

cli_input = parser.parse_args()


def main():

    scan = CamScan.CamScan()

    if cli_input.init:
        scan.initShodan(cli_input.init)

    if cli_input.search:
        scan.search = cli_input.search
        if cli_input.path:
            scan.path = cli_input.path
        else:
            raise Exception('Custom search requires path')

    if cli_input.path and not cli_input.search:
        raise Exception('requires both search and path values')

    
    if cli_input.page:
        scan.setPages(eval(cli_input.page))

    if cli_input.all:
        scan.setPages(None)

    if cli_input.dirname:
        scan.dirname = cli_input.dirname

    if cli_input.timeout:
        scan.timeout = int(cli_input.timeout)

    if cli_input.verbose:
        scan.verbose = True

    if cli_input.csv:
        scan.chooseFromCSV(cli_input.csv)
        

    scan.run()
    scan.generatePage()
    scan.showImages()


if __name__ == '__main__':
    main()
