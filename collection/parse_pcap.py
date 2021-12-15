import pyshark
import os
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import random
import pandas as pd
from glob import glob
markers = ['o',">",""]
markers = [""]
#linestype = ["solid","dotted"]
linestype = ["solid"]
colors_list = list(colors._colors_full_map)[-20:-1]




class packet:
    def __init__(self):
        self.timestamp = 0
        self.bytes = 0
        self.protocol = ""
        self.source = ""
        self.dest = ""

def read_capture(filename,filter):
    path = os.getcwd()
    cap = pyshark.FileCapture(path+"/"+filename,display_filter=filter)
    cap.set_debug()
    return cap


def parse_packets(allcaps,pkts):
    try:
        for pkt in allcaps:
            pack = packet()
            pack.protocol = pkt.highest_layer
            pack.timestamp = pkt.sniff_timestamp
            pack.bytes = len(pkt)
            pack.source = pkt.ip.__dict__["_all_fields"]["ip.src"]
            pack.dest  = pkt.ip.__dict__["_all_fields"]["ip.dst"]
            pkts.append(pack)
    except:
        print("pyshark bug")



def get_youtube_video_ip(filename,matches = ["edgedl"]):
    caps = read_capture(filename,"dns")
    ip = []
    for pkt in caps:
        try:
            resp = (pkt.dns.__dict__["_all_fields"]["dns.resp.name"])
            if any(match in resp for match in matches):
                ip.append(pkt.dns.__dict__["_all_fields"]["dns.a"])
                break
        except:
            pass
    caps.close()
    if len(ip) == 0:
        raise("Cant find youtube video ip from dns")
    return ip


def plot_cdf(data,bw = 0.01,override_color = None):
    #print(df.head())
    if (override_color == None):
        sns.kdeplot(data = data, cumulative = True,linestyle = random.choice(linestype), marker=random.choice(markers),color=random.choice(colors_list),lw =1,bw_method = bw)
    else:
        sns.kdeplot(data = data, cumulative = True,linestyle = random.choice(linestype), marker=random.choice(markers),color = override_color,lw =1,bw_method = bw)
    #plt.hist(data,cumulative=True)


def get_filter_from_ips(ips):
    res = ""
    print(ips)
    for i in range(len(ips)):
        res = res + "ip.addr==".format(ips[i])
        if (i != len(ips) -1):
            res = res + "||"
    return res


def get_video_flow(youtube_ips,filename):
    res = []
    caps = read_capture(filename, get_filter_from_ips(youtube_ips))
    parse_packets(caps,res)
    return res

def find_time_diff(pkt1,pkt2):
    return float(pkt2.timestamp) - float(pkt1.timestamp)

def plot_inter_packet_delay(video_packets):
    ys = []
    for i in range(1,len(video_packets)):
        ys.append(find_time_diff(video_packets[i-1],video_packets[i]))
    plt.xlim(0,0.2)
    plot_cdf(ys)
    
def read_all_csvs(csvs):
    li = []

    for filename in csvs:
        df = pd.read_csv(filename, index_col=None, header=0)
        li.append(df)

    frame = pd.concat(li, axis=0, ignore_index=True)
    frame = frame.rename(columns=lambda x: x.strip())
    return frame


def main():
    parent_folder = os.getcwd() +"/production/traces"
    folders = glob(parent_folder + "/*/")
    for folder in folders:
        csvs = glob(folder+"/*.csv")        
        df = read_all_csvs(csvs)
        df.BYTES.hist(cumulative= True,bins=1000,density=1)
        break

    plt.show()






main()