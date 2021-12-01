import pyshark
import os
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import random
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



def get_youtube_video_ip(filename,match = "edgedl"):
    caps = read_capture(filename,"dns")
    ip = None
    for pkt in caps:
        try:
            resp = (pkt.dns.__dict__["_all_fields"]["dns.resp.name"])
            if match in resp:
                ip = pkt.dns.__dict__["_all_fields"]["dns.a"]
                break
        except:
            pass
    caps.close()
    if ip == None:
        raise("Cant find youtube video ip from dns")
    return ip


def plot_cdf(data,bw = 0.01,override_color = None):
    #print(df.head())
    if (override_color == None):
        sns.kdeplot(data = data, cumulative = True,linestyle = random.choice(linestype), marker=random.choice(markers),color=random.choice(colors_list),lw =1,bw_method = bw)
    else:
        sns.kdeplot(data = data, cumulative = True,linestyle = random.choice(linestype), marker=random.choice(markers),color = override_color,lw =1,bw_method = bw)
    #plt.hist(data,cumulative=True)





def get_video_flow(youtube_ip,filename):
    res = []
    caps = read_capture(filename, "ip.addr=={}".format(youtube_ip))
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
    


def main():
    filename = "1reso.32VFLs1COxo.1636854279.4675097.pcap"
    #filename = "5reso.32VFLs1COxo.1636833966.1925867.pcap"
    #filename = "10reso.32VFLs1COxo.1636922170.4861689.pcap"
    youtube_ip = get_youtube_video_ip(filename)
    #youtube_ip = "34.104.35.123"
    video_packets = get_video_flow(youtube_ip,filename)
    plot_inter_packet_delay(video_packets)

    plt.show()






main()