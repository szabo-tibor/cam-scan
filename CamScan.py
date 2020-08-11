import requests
from shodan import Shodan
import os
import threading
from urllib.parse import urlparse
import webbrowser
import csv

class CamScan:
    
    def __init__(self, dirname='Images', search=None,
                 path=None, timeout=4, pages=0, verbose=False):

        self.search = search
        self.path = path
        self.dirname = dirname
        self.timeout = timeout
        self.pages = pages
        self.verbose = verbose
        self.api = None
        

        try:
            
            keyfile = open('shodan_api_key','r')
            key = keyfile.readline()
            keyfile.close()
            self.api = Shodan(key)
            
        except FileNotFoundError:
            
            print('Key file not found')
        

        DIR_NUMBER = 2
        while os.path.exists(self.dirname):
            self.dirname = self.dirname.strip('0987654321') + str(DIR_NUMBER)
            DIR_NUMBER += 1
        

    def initShodan(self, key):

        with open('shodan_api_key','w') as file:
            file.write(key)

        self.api = Shodan(key)

    def chooseFromCSV(self, file):

        if os.path.exists(file):
            
            f = open(file, newline='')
            data = csv.DictReader(f)

            searches = {}

            for x in data:
                searches[x['searchQuery']] = x['imagePath']

            f.close()
            
            print('CSV file input. Select search from below:\n')

            y = 0
            for search in searches:
                print(str(y) + ') ' + search)
                y += 1

            choice = int(input('\nChoose search: '))
            self.search = list(searches.keys())[choice]
            self.path = list(searches.values())[choice]

        else:

            raise FileNotFoundError


    def pagesCount(self):
        
        hosts = self.api.count(self.search)['total']

        return int(hosts / 100) + 1


    def setPages(self, pages):

        if type(pages) in [int, range, type(None)]:
            self.pages = pages

        else:
            raise Exception('Wrong type. pages value can be set to int, range, or None')
        

    def requestAndDownload(self, url):

        try:

            r = requests.get(url, timeout=self.timeout)

            if r.status_code == 200:

                if self.verbose:
                    print(url, ' - Success')
                    
                filename = urlparse(url).netloc.replace(':','-') + '.png'

                with open(filename, 'wb') as img:
                    img.write(r.content)

            else:
                if self.verbose:
                    print(url, r.status_code, 'Error')

        except requests.exceptions.ReadTimeout:
            if self.verbose:
                print(url, '- Timed out')

        except Exception as e:
            #print(e)
            if self.verbose:
                print(url, '- Connection Error')

    def runOnPage(self, pagenumber):

        results = None
        tries = 0

        while results is None and tries <= 10:

            try:
                results = self.api.search(self.search, page=pagenumber)

            except:
                tries += 1
                print('Shodan error')
                if tries == 10:
                    print('Giving up')

        threads = []

        for result in results['matches']:

            url = 'http://' + str(result['ip_str']) + ':' + str(result['port']) + self.path
            x = threading.Thread(target=self.requestAndDownload, args=(url,))
            threads.append(x)
            x.start()

        for thread in threads:
            thread.join()
                    

    def run(self):

        if self.api == None:
            raise Exception('No Shodan key')
        
        os.mkdir(self.dirname)
        os.chdir(self.dirname)

        print('Saving images to', os.getcwd(), '\n')

        if self.pages is None:

            print('Running every page')

            for page in range(self.pagesCount()):
                print('Starting page:', page)
                self.runOnPage(page)

        elif type(self.pages) is int:

            print('Running page', self.pages)

            self.runOnPage(self.pages)
            
        elif type(self.pages) is range:

            for page in self.pages:
                print('Starting page:', page)
                self.runOnPage(page)


    def generatePage(self):

        html = '''
<!DOCTYPE html>
<html>
<head>
    <title>{name}</title>
</head>
<body style="background-color:black">
    <p>Click on an image to open stream</p>
'''.format(name=self.dirname)

        with open('images.html', 'w') as page:

            page.write(html)

            for name_of_file in os.listdir():

                if '.png' in name_of_file:
                    
                    link = 'http://' + name_of_file.replace('-', ':').strip('.png')

                    page.write('\n\t<a href="{}" target="_blank">'.format(link))
                    page.write('\n\t\t<img src="{}" height="480" width="720">'.format(name_of_file))
                    page.write('\n\t</a>')
                    
            page.write('\n</body>\n</html>')
            
        
    def showImages(self):
        webbrowser.open('images.html')
        

    def info(self):

        print('search:', self.search)
        print('path:', self.path)
        print('dirname', self.dirname)
        print('timeout:', self.timeout)
        print('pages:', self.pages)
