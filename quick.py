from CamScan import CamScan

scan = CamScan()
scan.timeout = 7

if scan.api == None:
    key = input("Please paste your shodan API key here: ")
    scan.initShodan(key)

scan.search = 'product:"webcamXP httpd"'
scan.path = '/cam_1.jpg'
scan.run()
scan.generatePage()
scan.showImages()
