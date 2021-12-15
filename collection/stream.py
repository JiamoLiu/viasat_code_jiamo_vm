from datetime import date, datetime

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
import os
from pyvirtualdisplay import Display
from selenium.webdriver import ActionChains
from subprocess import Popen, PIPE
import  signal
import argparse



def get_interface_name():
    ints = os.listdir('/sys/class/net/')
    for face in ints:
        if "link-" in face:
            return face

def touch(fname):
    print(fname)
    open(fname, 'a').close()



today= date.today()
t = time.localtime()
current_time = time.strftime("%H:%M:%S", t)


def get_filename(link):
    return "./production/traces/"+link.split("v=")[1] + "."+str(time.time())


def capture_live_packets(link, network_interface, stop):
	filename = get_filename(link)
	output = filename+".pcap"

	process = Popen(['tshark', '-i',network_interface, '-w', output,"-s","100"])
	#stdout,stderr = process.communicate()

	while (stop() == False):
		pass
	process.send_signal(signal.SIGINT)




print(os.getcwd())



display = Display(visible=0, size=(2000, 3555))
display.start()

parser = argparse.ArgumentParser()
parser.add_argument('--link', action='store')
parser.add_argument('--iface', action='store')
parser.add_argument("--useQuic", action="store")
args = parser.parse_args()
url = args.link
intface = args.iface

options = webdriver.ChromeOptions()
#options = webdriver.ChromeOptions()
#options.add_argument("--headless")
#print(os.path.exists())
#options.add_argument("--disable-extensions")
options.add_extension('{}/Chrome extension.crx'.format(os.getcwd()))
options.add_argument("--window-size=2000,3555") # Needs to be big enough to get all the resolutions
print(args.useQuic)
if (args.useQuic == "False"):
    options.add_argument("--disable-quic")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")

stopthreads =False
th = threading.Thread(target=capture_live_packets, args=(url,intface,lambda: stopthreads,))


driver = webdriver.Chrome(chrome_options=options,executable_path="/usr/bin/chromedriver_linux64/chromedriver")
driver.get(url)
#print(driver.page_source)



th.start()
try:  
    WebDriverWait(driver, 15).until(EC.element_to_be_clickable(
        (By.XPATH, "//button[@aria-label='Play']"))).click()
except:
    print("cant find play button")
    pass



count =0
while True:
    player_status = driver.execute_script("return document.getElementById('movie_player').getPlayerState()")
    time.sleep(1)
    count = count +1
    print(count)
    if (player_status == 0):
        print("breaking main inf loop")
        break

time.sleep(5)
driver.close()
stopthreads= True
th.join()
display.stop()
# url of the video 

  
# creating pafy object of the video 
#video = pafy.new(url) 
#print(video.length)

# getting best stream 
#best = video.getbest() 
  
# creating vlc media player object 
#media = vlc.MediaPlayer(best.url) 
  
# start playing video 
#media.play() 
