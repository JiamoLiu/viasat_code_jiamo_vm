# need SSIM, # of changes, rebuffer time, minimize startup delay
from selenium import webdriver
from selenium import common
import sys
import time, json
import os
from subprocess import call, check_output
import numpy as np, re, csv, pickle
import pyshark
import threading
import traceback
from subprocess import Popen, PIPE
import  signal

from pyvirtualdisplay import Display

#display = Display(visible=0, size=(1024, 768))
#display.start()



def ping_local():
	os.system("ping -c 1 8.8.8.8")


def touch(fname):
    print(fname)
    open(fname, 'a').close()

def capture_live_packets(yvl,link, network_interface, stop):
	filename = yvl.get_filename(link)
	output = filename+".pcap"

	process = Popen(['tshark', '-i',network_interface, '-w', output,"-s","100"])
	#stdout,stderr = process.communicate()

	while (stop() == False):
		pass
	process.send_signal(signal.SIGINT)

        #print(stop())
		# if (stop()):
		# 	print("breaking the loop")
		# 	capture.close()
		# 	break

# Usage: python youtube_video.py --link [video link]
#
# Make sure to provide the video link within quotes "" via the command
# line because the link often contains shell characters in it


class Youtube_Video_Loader:
	def __init__(self, _id):
		self.t_initialize = time.time()
		self.pull_frequency = .5 # how often to look at stats for nerds box (seconds)
		self.early_stop = 10 # how long before the end of the video to stop (seconds)
		# how many consecutive iterations of the same video progress before we declare an error
		# TODO - remove
		self.max_pb_ctr_allowance = 4

		self.max_time = 10000000000000

		chrome_options = webdriver.ChromeOptions();
		#chrome_options.add_argument("--headless")
		chrome_options.add_extension("Chrome extension.crx") #doesn't work in headless chrome
		#chrome_options.binary_location = "CHROME_BINARY_LOCATION"
		chrome_options.add_argument("--window-size=2000,3555") # Needs to be big enough to get all the resolutions
		chrome_options.add_argument("--disable-quic")
		caps = webdriver.common.desired_capabilities.DesiredCapabilities.CHROME
		caps['goog:loggingPrefs'] = {'performance': 'ALL','brwoser': 'ALL'}
		self.driver = webdriver.Chrome(chrome_options=chrome_options, desired_capabilities=caps,executable_path="/usr/bin/chromedriver_linux64/chromedriver")

		self.video_statistics = {}
		self._id = _id
		self.logfile_dir = "./logs"
		self.error_report_dir = "./"
		self.has_ads = False
		self.ads_duration = 0
		if not os.path.exists(self.logfile_dir):
			call("mkdir {}".format(self.logfile_dir), shell=True)
		self.log_prefix = "youtube_stats_log_{}-".format(self._id)

	def done_watching(self, video_progress):
		# check to see if max time has been hit, or if we are close enough to the video end
		if time.time() - self.t_initialize > self.max_time:
			print("Max time reached - exiting.")
			return True
		elif time.time() > video_progress - self.early_stop:
			print("Close enough to video end - exiting.")
			return True
		return False

	def save_screenshot(self, img_name):
		self.driver.save_screenshot(os.path.join(self.error_report_dir, "youtube_" + img_name))

	def get_rid_of_ads(self):
		# Check to see if there are ads
		print("Checking for ads.")
		try:
			self.driver.find_element_by_css_selector(".video-ads")
		except:
			# no ads
			return
		done = False
		self.has_ads = True
		while not done:
			try:
				self.driver.find_element_by_css_selector(".ytp-ad-skip-button").click()
				#print("Pressed skip")
				# we skipped an ad, wait a sec to see if there are more
				time.sleep(1)
			except:
				# check to see if ad case is still covering
				#print("Display: {}".format(self.driver.find_element_by_css_selector(".video-ads").value_of_css_property("display")))
				if self.driver.find_element_by_css_selector(".video-ads").value_of_css_property("display") != "none":
					# there are more ads, potentially not skippable, just sleep
					time.sleep(1)
				else:
					done = True
					return

	def get_filename(self,link):
		return  os.path.join(self.logfile_dir, self.log_prefix + re.search("youtube\.com\/watch\?v=(.+)",link).group(1))

	def shutdown(self):
		# write all data to file
		for link in self.video_statistics:
			if self.video_statistics[link]["stats"] == []:
				continue
			video_hash = re.search("youtube\.com\/watch\?v=(.+)",link).group(1)
			fn = os.path.join(self.logfile_dir, self.log_prefix + video_hash)
			with open(fn + "-stats.csv", 'w') as f:
				csvw = csv.DictWriter(f, list(self.video_statistics[link]["stats"][0].keys()))
				csvw.writeheader()
				[csvw.writerow(row) for row in self.video_statistics[link]["stats"]]
			pickle.dump(self.video_statistics[link]["metadata"], open(fn + "-metadata.pkl", 'wb'))

		# kill the browser instance
		self.driver.quit()

	def get_bitrate_data(self, link):
		try:
			"""Youtube doesn't neatly expose things like available bitrates, etc..., so we use other tools to get this."""
			available_formats = check_output("youtube-dl {} --list-formats".format(link), shell=True).decode('utf-8')
			available_formats = available_formats.split("\n")[4:]
			d = []
			resolution_to_format = {}
			for row in available_formats:
				fields = row.split('       ')
				if fields == ['']:
					continue
				code = int(fields[0])
				extension = fields[1].strip()
				if extension != "mp4":
					continue
				resolution = fields[2].split(",")[0].strip()
				resolution = resolution.split(" ")
				try:
					re.search("(.+)x(.+)", resolution[0])
					resolution = resolution[0]
					try:
						resolution_to_format[resolution]
						# prefer webm over mp4
						if extension not in ["mp4", "webm"]:
							raise ValueError("Unprepared to handle extension: {}".format(extension))
						#resolution_to_format[resolution] = ("webm", code)					
						resolution_to_format[resolution] = ("mp4", code)
					except KeyError:
						# this is the only format with this resolution so far
						resolution_to_format[resolution] = (extension, code)
				except:
					# audio
					continue

			bitrates_by_resolution = {}
			for resolution in resolution_to_format:
				fmt,code = resolution_to_format[resolution]
				print("Resolution: {}, Format: {}".format(resolution, fmt))
				if os.path.exists("tmp.{}".format(fmt)):
					call("rm tmp.{}".format(fmt), shell=True)
				# download the video
				call("youtube-dl -o tmp.{} -f {} {}".format(fmt, code, link), shell=True) 
				# get the bitrates for this video
				raw_output = check_output("ffmpeg_bitrate_stats -s video -of json tmp.{}".format(fmt), shell=True)
				bitrate_obj = json.loads(raw_output.decode('utf-8'))
				bitrates_by_resolution[resolution] = bitrate_obj["bitrate_per_chunk"]

				call("rm tmp.{}".format(fmt), shell=True)
			# save this to the links metadata file
			video_hash = re.search("youtube\.com\/watch\?v=(.+)",link).group(1)
			fn = os.path.join(self.logfile_dir, self.log_prefix + video_hash)
			if not os.path.exists(fn + "-metadata.pkl"):
				# just create an empty object
				pickle.dump({}, open(fn + "-metadata.pkl",'wb'))
			this_link_metadata = pickle.load(open(fn + "-metadata.pkl",'rb'))
			this_link_metadata["bitrates_by_resolution"] = bitrates_by_resolution
			pickle.dump(this_link_metadata, open(fn + "-metadata.pkl",'wb'))

		except Exception as e:
			print(sys.exc_info())
		finally:
			self.driver.quit()

	def run(self, link):
		""" Loads a video, pulls statistics about the run-time useful for QoE estimation, saves them to file."""
		self.video_statistics[link] = {"stats":[], "metadata": {}}
		init_time = 0
		init_time = time.time()
		try: # lots of things can go wrong in this loop TODO - report errors 
			self.driver.get(link)

			#time.sleep(5)
			#self.driver.switch_to.window(self.driver.window_handles[0])
			#time.sleep(3) # a common error is that the page takes a little long to load, and it cant find the player 
			max_n_tries,i = 500,0
			while True:
				try:
					player = self.driver.find_element_by_css_selector("#player-container-inner")
					#print(player)
					break
				except:
					self.driver.get(link)
					print("waiting ? seconds")
					#time.sleep(5)
					i += 1
				if i == max_n_tries:
					print("Max number of tries hit trying to get the player-container-inner. Exiting.")
					self.save_screenshot("player_container_unable_{}.png".format(self._id))
					return


			#start_time = time.time()
			# Remove ads
			self.get_rid_of_ads()
			#self.ads_duration = time.time() - start_time
			# right click to open option for stats for nerds
			actions = webdriver.common.action_chains.ActionChains(self.driver)
			actions.context_click(player) 
			actions.perform()
			# click on stats for nerds
			self.driver.find_element_by_css_selector('div:nth-child(7) > div.ytp-menuitem-label').click()
			# Find the statistics
			stats_for_nerds_i = None
			for i in range(50):
				try:
					if self.driver.find_element_by_xpath('//*[@id="movie_player"]/div[{}]/div/div[1]/div'.format(i)).text == "Video ID / sCPN":
						stats_for_nerds_i = i
						break
				except common.exceptions.NoSuchElementException:
					continue
			if not stats_for_nerds_i:
				self.save_screenshot("no_stats_for_nerds_{}.png".format(self._id))
				raise ValueError("Couldn't find stats for nerds box.")

			# get video length
			i=0
			while True:
				print("Finding video length.")
				video_length = self.driver.find_element_by_css_selector('.ytp-time-duration').text.split(":")
				try:
					video_length = 60 * int(video_length[0]) + int(video_length[1])
					break
				except:
					actions = webdriver.common.action_chains.ActionChains(self.driver)
					actions.move_to_element(player)  # bring up the video length box again
					actions.perform()
					if i == max_n_tries:
						raise ValueError("Couldn't find video length: {}".format(video_length))
					i+=1

			tick=time.time()
			self.video_statistics[link]["metadata"]["start_wait"] = tick - self.t_initialize
			print("Starting Player")
			player.click(); 
			print("Going through stats for nerds")
			# pull data from stats for nerds with whatever frequency you want
			stop = False
			last_playback_progress, no_pb_progress_ctr = None, 0
			find_str = '//*[@id="movie_player"]/div[{}]'.format(stats_for_nerds_i)
			vsl = self.driver.find_element_by_xpath(find_str)
			while not stop:
				# get video progress
				# Note - this reading process can take a while, so sleeping is not necessarily advised
				t_calls = time.time()
				video_stats_text = vsl.get_attribute("textContent")
				video_stats_re = re.search("\[x\]Video ID (.+)Viewport \/ Frames(.+) Optimal Res(.+)Volume(.+)Codecs(.+)Connection Speed(.+) KbpsNetwork Activity(.+) KBBuffer Health(.+) sLive LatencyLive ModePlayback CategoriesMystery Texts:(.+) t\:(.+) b",video_stats_text)
				if video_stats_re:
					viewport_frames = video_stats_re.group(2)
					current_optimal_res = video_stats_re.group(3)
					network_bw_estimate_kbps = video_stats_re.group(6)
					network_activity = video_stats_re.group(7)
					buffer_health = float(video_stats_re.group(8))
					mystery_text = video_stats_re.group(9)
				else:
					time.sleep(.5)
					print("Didn't match regex: {}".format(video_stats_text))
					continue
				try:
					state = int(mystery_text) # 4 -> paused, 5 -> paused&out of buffer, 8 -> playing, 9 -> rebuffering
				except ValueError:
					state = mystery_text # c44->?
				video_progress = float(video_stats_re.group(10))

				self.video_statistics[link]["stats"].append({
					"viewport_frames": viewport_frames,
					"current_optimal_res": current_optimal_res,
					"buffer_health": buffer_health,
					"state": state,
					"playback_progress": video_progress,
					"timestamp": time.time(),
					"has_ads":bool(self.has_ads),
					"ads_duration":self.ads_duration,
					"init_time" : init_time,
					"network_estimate_kbps":network_bw_estimate_kbps,
					'network_activity': network_activity
				})
				if np.random.random() > .8:
					print("Res : {} Buf health: {} plbck progress: {}".format(
						current_optimal_res, buffer_health, video_progress))
				if last_playback_progress is not None and buffer_health > .5:
					if video_progress == last_playback_progress:
						no_pb_progress_ctr += 1
					else:
						no_pb_progress_ctr = 0
					if no_pb_progress_ctr > self.max_pb_ctr_allowance:
						self.save_screenshot("not_progressing_{}_youtube.png".format(self._id))
						player.click()
						no_pb_progress_ctr = 0
				last_playback_progress = video_progress


				# Check to see if video is almost done
				if self.done_watching(tick + video_length):
					stop = True
					ping_local()
					player.click() # stop the video
				time.sleep(np.maximum(self.pull_frequency - (time.time() - t_calls),.001))
			

		except Exception as e:
			#print("screenshot")
			traceback.print_exc()
			self.save_screenshot("went_wrong_{}.png".format(self._id))
			print(sys.exc_info())
		finally:

			browser_log = self.driver.get_log('browser') 
			#print(browser_log)
			self.shutdown()

def main():
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('--link', action='store')
	parser.add_argument('--id', action='store')
	parser.add_argument('--mode', action='store')
	parser.add_argument("--times",action="store")
	parser.add_argument("--iface", action="store")
	args = parser.parse_args()


	stopthreads =False


	
	
	for i in range(int(args.times)):
		yvl = Youtube_Video_Loader(int(args.id)+i)
		th = threading.Thread(target=capture_live_packets, args=(yvl,args.link,args.iface,lambda: stopthreads,))
		th.start()
		thread_start_tick = time.time()
		time.sleep(1)
		ping_local()
		if args.mode == "run":
			youtube_tick = time.time()
			yvl.run(args.link)
			print("youtube ran for:" + str(time.time() - youtube_tick))
			time.sleep(3)
			stopthreads=True
			th.join()
			print("thread ran for:" + str(time.time() - thread_start_tick))
			stopthreads=False
			time.sleep(2)
		elif args.mode == "get_bitrate":
			yvl.get_bitrate_data(args.link)
		else:
			raise ValueError("Mode {} not recognized.".format(args.mode))




if __name__ == "__main__":
	main()
