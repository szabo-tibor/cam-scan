import requests
from shodan import Shodan
from time import sleep,time
import os
import threading
import webbrowser
import csv

class CamScan:
    
    def __init__(self, dirname='Images', search=None,
                 path=None, timeout=4, verbose=False):

        self.search = search
        self.path = path
        self.dirname = dirname
        self.timeout = timeout
        self.pages = {0: None}
        self.verbose = verbose
        self.api = None
        self.live_hosts = []
        self.store_offline = True
        self.success_count = 0
        self.failed_count = 0
        self.total = 0

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
            print('Select search from below:\n')
            y = 0
            for x in data:
                print(str(y) + ") " + x['friendlyName'])
                searches[x['searchQuery']] = x['imagePath']
                y += 1

            f.close()
            print("\nSearches marked with '(Free)' don't require a paid Shodan account to use")
            choice = int(input('Choose search: '))
            self.search = list(searches.keys())[choice]
            self.path = list(searches.values())[choice]

        else:

            raise FileNotFoundError


    def pagesCount(self):
        
        hosts = self.api.count(self.search)['total']

        return int(hosts / 100) + 1


    def setPages(self, pages_str):

        self.pages = {}

        if type(pages_str) == str:
            for num in pages_str.split(','):
                if '-' in num:
                    r = num.split('-')
                    for number in range(int(r[0]),int(r[1]) + 1):
                        self.pages[int(number)] = None

                else:
                    self.pages[int(num)] = None

        elif pages_str == None:
            self.pages = None

        else:
            raise Exception("Page value needs to be a string, or None")

        
    def requestAndDownload(self, shodan_result):
        
        host = str(shodan_result['ip_str'])
        port = str(shodan_result['port'])
        url = 'http://{}:{}'.format(host,port) + self.path

        try:

            r = requests.get(url, timeout=self.timeout)

            if r.status_code == 200:

                if self.verbose:
                    print('[Info] Connection to {}:{} successfull'.format(host,port))

                filename = '{}-{}'.format(host,port) + '.png'

                if self.store_offline == True:

                    with open(filename, 'wb') as img:
                        img.write(r.content)

                self.live_hosts.append([filename,shodan_result])
                self.success_count += 1

            else:
                self.failed_count += 1
                if self.verbose:
                    print('[HTTP {} Error] Connection to {}:{} failed'.format(r.status_code,host,port))

        except requests.exceptions.ReadTimeout:
            self.failed_count += 1
            if self.verbose:
                print('[Network Error] Connection to {}:{} timed out'.format(host,port))

        except Exception as e:
            self.failed_count += 1
            #print(e)
            if self.verbose:
                print('[Network Error] Connection to {}:{} failed'.format(host,port))


    def runOnPage(self, pagenumber):

        r = self.pages[pagenumber]

        if self.verbose:
            print("[Info] Contacting hosts on page",pagenumber)
            
        for result in r['matches']:
            self.total += 1

            x = threading.Thread(target=self.requestAndDownload, args=(result,))
            self.threads.append(x)
            x.start()

        #for thread in threads:
        #    thread.join()
                    

    def shodanSearch(self):

        if self.api == None:
            raise Exception('Shodan API key not set')
        
        else:
            for pageNum in self.pages:

                if self.verbose:
                    print("[Info] Searching shodan on page",pageNum)
                
                tries = 0
                while self.pages[pageNum] == None:
                    try:
                        self.pages[pageNum] = self.api.search(self.search, page=pageNum)
                    except Exception as e:
                        tries += 1

                        if "upgrade your API plan" in e.args[0]:
                            print("[Fatal error] Paid Shodan account required for pages and search filters.")
                            self.end = True
                            #raise Exception(e.args[0]) from e
                            break
                            
                        if tries == 35:
                            print("[Fatal Error] Shodan not responding correctly, giving up")
                            self.end = True
                            #raise Exception(e.args[0]) from e
                            break

                        print("[API Error]", e, "- Retrying...")

                    sleep(1.5)


    def run(self):

        self.end = False
	self.threads = []

        if self.pages == None:
            self.pages = {}
            for page in range(1,self.pagesCount() + 1):
                self.pages[page] = None

        os.mkdir(self.dirname)
        os.chdir(self.dirname)

        print('Saving images to', os.getcwd(), '\n')
        threading.Thread(target=self.shodanSearch).start()

        print("[Info] Starting...")
        start_time = time()

        for page in self.pages:

            while self.pages[page] == None and not self.end:
                sleep(1.5)

            if not self.end:
                self.runOnPage(page)

        for thread in self.threads:
            thread.join()

        if self.verbose:
            print("[Info] Completed")
            
        self.time_elapsed = time() - start_time


    def generatePage(self,open_on_completion=True):

        html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Saved Images</title>
        <script>
            function changeColumns() {
                let columns = parseInt(document.getElementById('cols').value);
                let gallery = document.getElementsByClassName("gallery")[0];
		let images = document.getElementsByTagName("img");
		let s = "";
		let h;
			
		for (let i = 0; i < columns; i++ ) {
		    s += "auto ";
		}
		gallery.style.gridTemplateColumns = s;
			
		switch (columns) {
                    case 2:
                        h = 700;
			break;
		    case 3:
			h = 480;
			break;
		    case 4:
			h = 300;
			break;
		}

		for (let i = 0; i < images.length; i++) {
                    images[i].height = h;
		}
	    }
        </script>
    <style>
	button {
		border: none;
		border-radius: 5px;
		outline: none;
		color: white;
		padding: 5px 40px;
		text-align: center;
		text-decoration: none;
		display: inline-block;
		font-size: 16px;
		margin: 5px 2px;
		cursor: pointer;
		transition-duration: 0.2s;
		background-color: #386fc2;
	}
	
	button.shodan_button {
		background-color: #be473c
	}
	
        button:hover {
            background-color: #305896;
        }

        .shodan_button:hover {
            background-color: #a63c32;
        }
	
    .gallery {
        display: grid;
        grid-template-columns: auto auto auto auto;
	grid-template-rows: auto;
        grid-gap: 10px;
    }
    .gallery img {
        width: 100%;
    }
	.gallery .item {
		position: relative;
		overflow: hidden;
	}
	.gallery .item img {
		vertical-align: middle;
	}
	
	.gallery .caption {
		margin: 0;
		padding: .5em;
		position: absolute;
		z-index: 1;
		bottom: 0;
		left: 0;
		width: 100%;
		max-height: 100%;
		overflow: auto;
		box-sizing: border-box;
		transition: transform 0.2s;
		transform: translateY(100%);
		background: rgba(0, 0, 0, 0.4);
		color:white;
		font-family: Arial;
	}
	
	.gallery .item:hover .caption {
		transform: translateY(0%);
	}

    h1 {
        text-align: center;
        color:#919191;
        font-family: Arial;
    }
    label {
        color:#919191;
		font-family: Arial;
    }
    </style>
</head>
<body style="background-color:black" onload="changeColumns()">
    <h1>Saved Images:</h1>
	<label for="cols">Columns:</label>
	<select id="cols" onchange="changeColumns()">
	  <option value="2">2</option>
	  <option value="3">3</option>
	  <option value="4" selected="selected">4</option>
	</select>
	<hr style="width:70%;">

    <div class=gallery>
'''

        with open('images.html', 'w') as page:

            page.write(html)
            no_dupes = []
            for h in self.live_hosts:
                if h not in no_dupes:
                    no_dupes.append(h)
            
            for host in no_dupes:

                link = 'http://' + host[1]['ip_str'] + ':' + str(host[1]['port'])
                
                if self.store_offline == True:
                    img_src = host[0]
                    if os.path.getsize(host[0]) <= 1:
                        continue
                else:
                    img_src = link + self.path
                    
                data = (img_src,
                        host[1]['ip_str'],
                        host[1]['location']['city'],
                        host[1]['location']['country_name'],
                        host[1]['org'],
                        link,
                        host[1]['ip_str'])

                element = f'''
                <div class="item">
			<img src="%s" onerror="this.parentElement.remove()">
			
			<span class="caption">
				
				<table style="margin: auto;font-weight: bold;color:white;">
				  <tr>
					<td>IP Address:</td>
					<td>%s</td>
				  </tr>
				  <tr>
					<td>City:</td>
					<td>%s</td>
				  </tr>
				  <tr>
					<td>Country:</td>
					<td>%s</td>
				  </tr>
				  <tr>
					<td>Organization:</td>
					<td>%s</td>
				  </tr>
				</table>
				
				<div style="text-align: center;">
				<a href="%s" target="_blank" style="text-decoration: none">
					<button type="submit" class="stream_button">Open stream in new tab</button>
				</a>
                                <a href="https://www.shodan.io/host/%s" target="_blank" style="text-decoration: none">
                                    <button class="shodan_button">Shodan Page</button>
                                </a>
				</div>
				
			</span>
		</div>
''' % data

                try:
                    page.write(element)

                except UnicodeEncodeError:
                    if self.verbose:
                        print("[Unicode Error] That was wierd. UnicodeEncodeError for host", host[1]['ip_str'])
                    pass
                        
            page.write('\n\t</div>\n</body>\n</html>')

        if open_on_completion:
            webbrowser.open('images.html')
            
        
    def info(self):

        print('search:', self.search)
        print('path:', self.path)
        print('dirname', self.dirname)
        print('timeout:', self.timeout)
        try:
            print('pages:', len(self.pages))
        except TypeError:
            print('pages:', None)

    def stats(self):
        percent_success = int((self.success_count / self.total) * 100)
        percent_failure = int((self.failed_count / self.total) * 100)
        s = "{} out of {} hosts are viewable, {}% success rate".format(self.success_count,self.total,percent_success)

        return [s,percent_success,percent_failure]
