import requests
from shodan import Shodan
from time import sleep,time,localtime
import os
import threading
import webbrowser
import csv

class CamScan:
    
    def __init__(self, dirname='Images', search=None,
                 path=None, timeout=7, verbose=False):

        self.search = search
        self.path = path
        self.dirname = dirname
        self.timeout = timeout
        self.pages = {0: None}
        self.verbose = verbose
        self.api = None
        self.live_hosts = []
        self.checkPTZ = False
        self.checkPTZPath = None
        self.store_offline = True

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

            searches = []
            print('Select search from below:\n')
            y = 0
            for x in data:
                item = []
                item.append(x['searchQuery'])
                item.append(x['imagePath'])
                item.append(x['ptzCheckPath'])
                item.append(x['friendlyName'])
                print(str(y) + ") " + x['friendlyName'])
                searches.append(item)
                y += 1

            f.close()

            print("\nSearches marked with (Free) don't require a paid Shodan account to use")
            print("Searches marked with [PTZ] support checking for locked PTZ controls")
            
            try:
                choice = int(input('Choose search: '))
                self.search = searches[choice][0]
                self.path = searches[choice][1]
                self.checkPTZPath = searches[choice][2]
                self.friendly_name = searches[choice][3]
            except ValueError:
                print("That's not a number...")
            except IndexError:
                print("That's not one of the choices...")
            except Exception:
                print("You're an idiot...")


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
        self.total += 1

        try:

            r = requests.get(url, timeout=self.timeout)

            if r.status_code == 200:

                filename = '{}-{}'.format(host,port) + '.png'

                if self.store_offline == True:

                    with open(filename, 'wb') as img:
                        img.write(r.content)

                if self.checkPTZ and self.checkPTZPath:

                    ptz_url = 'http://{}:{}'.format(host,port) + self.checkPTZPath
                    ptz_request = requests.get(ptz_url, timeout=self.timeout)
                    bad_codes = [x for x in range(400,512)]
                    
                    if ptz_request.status_code not in bad_codes:
                        if self.verbose:
                            print('[Info] Connection to {}:{} successfull, camera possibly controllable'.format(host,port))

                        self.ptz_count += 1
                        self.live_hosts.append([filename,shodan_result,True])

                    else:
                        if self.verbose:
                            print('[Info] Connection to {}:{} successfull, camera controls locked'.format(host,port))

                        self.live_hosts.append([filename,shodan_result,False])

                else:
                    if self.verbose:
                        print('[Info] Connection to {}:{} successfull'.format(host,port))

                    self.live_hosts.append([filename,shodan_result,False])
                
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


    def _runOnPage(self, pagenumber):

        r = self.pages[pagenumber]

        if self.verbose:
            print("[Info] Contacting hosts on page",pagenumber)
            
        for result in r['matches']:

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
                            break
                            
                        if tries == 35:
                            print("[Fatal Error] Shodan not responding correctly, giving up")
                            self.end = True
                            break

                        print("[API Error]", e, "- Retrying...")

                    sleep(1.5)


    def run(self):

        self.success_count = 0
        self.failed_count = 0
        self.ptz_count = 0
        self.total = 0
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
        t = localtime()
        self.start_time_str = "{}/{}/{} {}:{}:{}".format(t[1],t[2],t[0],t[3],t[4],t[5])

        for page in self.pages:

            while self.pages[page] == None and not self.end:
                sleep(.1)

            if not self.end:
                self._runOnPage(page)

        for thread in self.threads:
            thread.join()

        if self.verbose:
            print("[Info] Completed")
            
        self.time_elapsed = time() - start_time


    def generatePage(self,open_on_completion=True):

        if self.checkPTZ and self.checkPTZPath:
            ptz_box = '''
            <div class="thing">
                <label for="ptz_box">Hide hosts with closed PTZ controls:</label>
                <input id="ptz_box" type="checkbox" onchange="ptzCheckBox()">
            </div>'''

        else:
            ptz_box = ""

        html = '''<!DOCTYPE html>
<html>
<head>
    <title>'''+self.friendly_name+'''</title>
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
        let nonptz_list = [];
        let all_items = [];
        let not_ran = true;

        function ptzCheckBox() {
            const gal = document.getElementsByClassName("gallery")[0];
            let all = gal.getElementsByClassName("item");
            let box = document.getElementById("ptz_box");
            let nonptz_items = gal.getElementsByClassName("nonptz");

            if (not_ran) {
                for (let i = 0; i < gal.childElementCount; i++) {
                    all_items.push(all[i]);
                }
                not_ran = false;
            }

            for (let i = 0; i < nonptz_items.length; i++) {
                nonptz_list.push(nonptz_items[i]);
            }   

            if (box.checked) {
                for (let i = 0; i < nonptz_list.length; i++) {
                    nonptz_list[i].remove()
                }
            } else {
                for (let i = 0; i < all_items.length; i++) {
                    all_items[i].remove();
                }
                for (let i = 0; i < all_items.length; i++) {
                    gal.appendChild(all_items[i]);
                }
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
        font-family: Arial;
        color: white;
    }
    label {
        font-family: Courier New;
        color: white;
    }
        div.container{
        display: flex;
        background: linear-gradient(#8f8f8f, #757575);
        padding: 10px;
        border-radius: 17px;
        margin-bottom: 8px;
        margin: 20px;
    }
    div.section {
        flex: auto;
        width: 33%;
    }
    div.thing {
        margin: 5px;
    }

    .stats_table {
        float: right;
        font-family: Courier New;
        color: white;
    }
    </style>
</head>
<body style="background-color:black" onload="changeColumns()">
    <div class="container">
        <div class="section">
            <div class="thing">
                <label for="cols">Columns:</label>
                <select id="cols" onchange="changeColumns()">
                    <option value="2">2</option>
                    <option value="3">3</option>
                    <option value="4" selected="selected">4</option>
                </select>
            </div>'''+ptz_box+'''
        </div>

        <div class="section" style="text-align: center;">
            <h1>'''+self.friendly_name+'''</h1>
        </div>

        <div class="section">
            <table class="stats_table">
                <tr>
                    <td>Query:</td>
                    <td>'''+self.search+'''</td>
                </tr>
                <tr>
                    <td>Count:</td>
                    <td>'''+str(self.success_count)+''' open, '''+str(self.failed_count)+''' closed</td>
                </tr>
                <tr>
                    <td>Ran at:</td>
                    <td>'''+self.start_time_str+'''</td>
                </tr>
            </table>
        </div>

    </div>

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


                if host[2]:
                    classname = "item ptz"
                else:
                    classname = "item nonptz"

                if self.checkPTZ and self.checkPTZPath:
                    if host[2]:
                        ptz_controls_tr = '''
                  <tr>
                    <td>PTZ Controls:</td>
                    <td style="font-weight: bold;">Authorized</td>
                  </tr>'''
                    else:
                        ptz_controls_tr = '''
                  <tr>
                    <td>PTZ Controls:</td>
                    <td style="font-weight: bold;">Unauthorized</td>
                  </tr>'''
                else:
                    ptz_controls_tr = ""
                    
                data = (classname,
                        img_src,
                        host[1]['ip_str'],
                        host[1]['location']['city'],
                        host[1]['location']['country_name'],
                        host[1]['org'],
                        ptz_controls_tr,
                        link,
                        host[1]['ip_str'])

                element = f'''
                <div class="%s">
			<img src="%s" onerror="this.parentElement.remove()">
			
			<span class="caption">
				
				<table style="margin: auto;color:white;">
				  <tr>
					<td>IP Address:</td>
					<td style="font-weight: bold;">%s</td>
				  </tr>
				  <tr>
					<td>City:</td>
					<td style="font-weight: bold;">%s</td>
				  </tr>
				  <tr>
					<td>Country:</td>
					<td style="font-weight: bold;">%s</td>
				  </tr>
				  <tr>
					<td>Organization:</td>
					<td style="font-weight: bold;">%s</td>
				  </tr>%s
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

        print("checkPTZ:", self.checkPTZ)
        print("checkPTZPath:", self.checkPTZPath)


    def stats(self):

        if self.total != 0:
            percent_success = int((self.success_count / self.total) * 100)
            percent_failure = int((self.failed_count / self.total) * 100)
        else:
            percent_success = 0
            percent_failure = 0

        s = "{} out of {} hosts are viewable, {}% success rate".format(self.success_count,self.total,percent_success)
        t = "Time elapsed: " + str(int(self.time_elapsed)) + " seconds"
        u = "{} hosts found with potentially open PTZ controls".format(self.ptz_count)

        return [s,t,u,percent_success,percent_failure]
