import os
import glob
from re import X
from typing import final
import matplotlib.pyplot as plt
import pandas as pd
import random
import matplotlib.colors as colors
import matplotlib
import seaborn as sns
import numpy as np
import pyshark
from statsmodels.tsa.api import ExponentialSmoothing, SimpleExpSmoothing, Holt
import math
import scipy
from scipy import spatial

from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
import statistics



markers = ['o',">",""]
markers = [""]
linestype = ["dashed","solid","dotted"]
colors_list = list(colors._colors_full_map)
ping_addr = "8.8.8.8"
folder_path = "logs_5times_unshaped"





class packet:
    def __init__(self):
        self.timestamp = 0
        self.bytes = 0
        self.protocol = ""
        self.source = ""
        self.dest = ""







def get_pcaps():
    path = os.getcwd()+"/"+folder_path
    extension = 'pcap'
    os.chdir(path)
    result = glob.glob('*.{}'.format(extension))
    return result

def read_capture(filename,filter):
    path = os.getcwd()
    cap = pyshark.FileCapture(path+"/"+filename,display_filter=filter)
    cap.set_debug()
    return cap

def parse_packets(filename,allcaps,pkts):
    i = 0
    icmps = 0
    init_time = 0
    final_time = 0
    started = False
    myip = ""
    try:
        for pkt in allcaps:
            if ("icmp" not in dir(pkt) and not started):
                print("skipped")
                continue

            if ("icmp" in dir(pkt)):
                print("icmps!")
                if (icmps == 0):          
                    init_time = pkt.sniff_timestamp
                    started=True
                    address = pkt.ip.__dict__["_all_fields"]["ip.src"]+pkt.ip.__dict__["_all_fields"]["ip.dst"]
                    myip = address.replace(ping_addr,"")
                    icmps = icmps+1
                if (icmps == 3):
                    final_time = pkt.sniff_timestamp
                    break

            pack = packet()
            pack.protocol = pkt.highest_layer
            pack.timestamp = pkt.sniff_timestamp
            pack.bytes = len(pkt)
            pack.source = pkt.ip.__dict__["_all_fields"]["ip.src"]
            pack.dest  = pkt.ip.__dict__["_all_fields"]["ip.dst"]
            pkts.append(pack)
    except:
        print("pyshark bug")

    if (final_time == 0):
        final_time = pkts[-1].timestamp
    return init_time, final_time, myip
    
def add_plot(x,y,label =None):
    plt.plot(x,y, linestyle = random.choice(linestype), marker=random.choice(markers),color=random.choice(colors_list),lw=1,label = label)
    #plt.hist(y, bins=len(x)) 
    #plt.axis(x) 

def calculate_bw(init_time,pkts):
    res = {}
    flow_bw={}
    flow_size = {}
    max_flow = ""
    max = 0
    for pkt in pkts:
        flow = pkt.source + "->" +pkt.dest
        #print(flow)
        #print(pkt.bytes)
        x = math.floor(1000*(float(pkt.timestamp) - float(init_time)))/1000
        #print(x)
        if (x in res):
            res[x] = res[x] + pkt.bytes
        else:
            res[x] = pkt.bytes

        if (flow in flow_bw):
            if (x in flow_bw[flow]):
                flow_bw[flow][x] = flow_bw[flow][x] + pkt.bytes
                flow_size[flow] = flow_size[flow] + pkt.bytes
            else:
                flow_bw[flow][x] = pkt.bytes
                flow_size[flow] = pkt.bytes

            #print(max)
            if (flow_size[flow] > max):
                max = flow_size[flow]
                max_flow = flow
        else:
            flow_bw[flow] = {}
            flow_bw[flow][x] = pkt.bytes
            flow_size[flow] = pkt.bytes

            if (flow_size[flow] > max):
                #print(flow_size[flow])
                max = flow_size[flow]
                max_flow = flow

    #print(max_flow)
    #print(flow_bw[max_flow])
    return res,flow_bw,max_flow

def plot_bw(bw_dict,label = None):
    xs = bw_dict.keys()
    #print(xs)
    ys = list(bw_dict.values())
    add_plot(xs,ys,label)
    return ys



def get_up_bw(flow_dict,myip):
    flows = flow_dict.keys()
    res = {}    
    for flow in flows:
        #print("|"+flow.split("->")[0] + "|" +myip + "|" )
        if (flow.split("->")[0] == myip):
            timestamps = flow_dict[flow].keys()
            for timestamp in timestamps:
                if (timestamp in res):
                    res[timestamp] = res[timestamp] + flow_dict[flow][timestamp]
                else:
                    res[timestamp] = flow_dict[flow][timestamp]
        else:
            continue
    #print(res)
    return res

def get_down_bw(flow_dict,myip):
    flows = flow_dict.keys()
    res = {}    
    for flow in flows:
        #print("|"+flow.split("->")[0] + "|" +myip + "|" )
        if (flow.split("->")[1] == myip):
            timestamps = flow_dict[flow].keys()
            for timestamp in timestamps:
                if (timestamp in res):
                    res[timestamp] = res[timestamp] + flow_dict[flow][timestamp]
                else:
                    res[timestamp] = flow_dict[flow][timestamp]
        else:
            continue
    #print(res)
    return res

    #print(df.head())
    #print(csv)
def get_shape_file(flow_dict,filename,myip, delay_in_ms = 5000,write_file = True):
    upflows = get_up_bw(flow_dict,myip)
    downflows = get_down_bw(flow_dict,myip)
    timestamp = upflows.keys()
    #print(timestamp)s
    down_res = {}
    res = ""
    current = 0
    while (True):
        ms = round(float(current)*1000 +1)+delay_in_ms
        if current in timestamp:
            res = res + math.ceil(upflows[current]/1500) * (str(ms)+"\n")
        #print(list(timestamp)[-1])
        current =round(current + 0.001,3)
        if (current > float(str(list(timestamp)[-1]))):
            break

    if (write_file):
        with open(filename + ".upload.shape", "w") as text_file:
            text_file.write(res)
    
    down_shape = res
    res = ""
    timestamp = downflows.keys()
    current = 0
    while (True):
        if current in timestamp:
            ms = round(float(current)*1000 +1)+delay_in_ms
            res = res + math.ceil(downflows[current]/1500) * (str(ms)+"\n")
        #print(current)
        current =round(current + 0.001,3)
        if (current > float(str(list(timestamp)[-1]))):
            break

    if (write_file):
        with open(filename + ".download.shape", "w") as text_file:
            text_file.write(res)

    ups_shape = res
    return down_shape,ups_shape,downflows,upflows

def plot_flow_bw(flow_dict,max_flow):  
    keys = flow_dict.keys()
    for key in keys:
        xs = flow_dict[key].keys()
        ys = list(flow_dict[key].values())
        if key == max_flow:
            #print(max_flow)
            add_plot(xs,ys)
    #plt.legend(keys)

def ewa_smoothing(input_y,input_x):
    data = pd.Series(input_y,input_x)
    #print(data)
    fit3 = SimpleExpSmoothing(data, initialization_method="estimated").fit(smoothing_level=0.2)
    return dict(fit3.fittedvalues)

def pad_zeroes(bw_dict):
    iter = int(1000*float(list(bw_dict.keys())[-1]))
    res = {}
    current = 0
    for i in range(iter):
        current = round(0.001 * i,3)
        if current in bw_dict:
            #print("hit")
            bw = round(bw_dict[current])
            res[current] = bw

        else:
            res[current] = 0
    #rint(list(bw_dict.keys())[0:200])
    return res

def pad_smoothed_bw(bw_dict):
    iter = int(1000*float(list(bw_dict.keys())[-1]))
    res = {}
    current = 0
    previous = 0
    for i in range(iter):
        current = round(0.001 * i,3)
        if current in bw_dict:
            #print("hit")
            bw = round(bw_dict[current])
            res[current] = bw

            if (bw > 5000 or previous == 0):
                previous = bw
        else:
            if (previous == 0):
                continue
            res[current] = previous
    #rint(list(bw_dict.keys())[0:200])
    return res




def get_shape_from_bw_profile(input_dict,filename,file_write =True,delay = 5000):
    timestamps = input_dict.keys()
    res = ""
    for timestamp in timestamps:
        ms = str(int(timestamp*1000)+delay)
        #print(input_dict[timestamp]/1500)
        res = res + math.ceil(input_dict[timestamp]/1500) * (str(ms)+"\n")
    
    if (file_write):
        with open(filename + ".shape", "w") as text_file:
            text_file.write(res)


def get_packet_size_plot(pkts,flowname):
    res = {}
    src = flowname.split("->")[0]
    dest = flowname.split("->")[1]
    for pkt in pkts:
        if (src == pkt.source and dest == pkt.dest):
            if float(pkt.timestamp) not in res:
                res[float(pkt.timestamp)] = pkt.bytes
    return res

def plot_cdf(df,label = None):
    #print(df.head())

    data = df.values
    sns.ecdfplot(data,linestyle = random.choice(linestype), marker=random.choice(markers),color=random.choice(colors_list),label = label)
    #sns.kdeplot(data = df.values, cumulative = True,linestyle = random.choice(linestype), marker=random.choice(markers),color=random.choice(colors_list),lw =1)


def plot_pcaps():
    files = get_pcaps()
    for filename in files:
        allcaps = None
        pkts = []
        allcaps = read_capture(filename,"tcp or tls or icmp or dns")
        init_time,final_time,myip = parse_packets(filename,allcaps,pkts)
        bw,flow_res,max_flow = calculate_bw(init_time,pkts)
        plot_bw(bw, filename)
    
    # down_shape, up_shape, down_flow,up_flow = get_shape_file(flow_res_2,files[1],myip_2,write_file=False)
    # #smoothed_bw = ewa_smoothing(down_flow.values(),list(down_flow.keys()))
    # #print(down_flow.values())

    # padded_smooth = pad_smoothed_bw(down_flow)
    # plot_bw(padded_smooth,"padded")
    # get_shape_from_bw_profile(padded_smooth,files[1] + ".smoothened.download")

    plt.xlabel("Timestamp(s)")
    plt.ylabel("Bandwidth(Bytes/ms)")
    plt.legend()
    plt.show()


def get_only_above(values,thresh):
    return [i for i in values if i >= thresh]

def amp_scaling(values):
    std = statistics.pstdev(values)
    mean = statistics.mean(values)
    return [(i - mean)/std for i in values]


def calculate_dtw_distance(padding = False):
    files = get_pcaps()
    vectors = []
    for filename in files:
        allcaps = None
        pkts = []
        allcaps = read_capture(filename,"tcp or tls or icmp or dns")
        init_time,final_time,myip = parse_packets(filename,allcaps,pkts)
        bw,flow_res,max_flow = calculate_bw(init_time,pkts)
        if (padding):
            bw = pad_zeroes(bw)
        bw = list(bw.values())
        #bw =get_only_above(bw,1000)
        #bw = pad_smoothed_bw(bw)
        vectors.append(bw)
        #df = pd.DataFrame(list(bw.values()), columns = ["values"])
    a = amp_scaling(vectors[0])
    b = amp_scaling(vectors[1])
    #print(a)
    distance, path = fastdtw(a, b, dist=euclidean,radius=10)
    print("dtw distance:" + str(distance))
    #print(path)


def plot_bw_pearson(padding=False,filtering = False,scaling=False,ispearson = False,isspearman= False):
    files = get_pcaps()
    vectors = []
    for filename in files:
        allcaps = None
        pkts = []
        allcaps = read_capture(filename,"tcp or tls or icmp or dns")
        init_time,final_time,myip = parse_packets(filename,allcaps,pkts)
        bw,flow_res,max_flow = calculate_bw(init_time,pkts)
        if (padding):
            bw = pad_zeroes(bw)
        bw = list(bw.values())
        if (filtering):
            bw =get_only_above(bw,1000)
        if (scaling):
            bw = amp_scaling(bw)
        #
        vectors.append(bw)
        #df = pd.DataFrame(list(bw.values()), columns = ["values"])
    length = min(len(vectors[0]), len(vectors[1]))
    if (ispearson): 
        r, p = scipy.stats.pearsonr(vectors[0][0:length], vectors[1][0:length])
        print("pearson:" + str(r))
        print("pearson p:"+str(p))
        plt.scatter(vectors[0][0:length], vectors[1][0:length],s= 0.1)
        plt.xlabel("Normalised bandwidth pcap 1")
        plt.ylabel("Normalised bandwidth pcap 2")
        plt.show()

    if (isspearman):
        print("spearman rho:" + str(scipy.stats.spearmanr(vectors[0][0:length], vectors[1][0:length])[0]))
    result = 1 - spatial.distance.cosine(vectors[0][0:length], vectors[1][0:length])
    print("cosine sim:"+ str(result))



def plot_bw_cdf():
    files = get_pcaps()
    for filename in files:
        allcaps = None
        pkts = []
        allcaps = read_capture(filename,"tcp or tls or icmp or dns")
        init_time,final_time,myip = parse_packets(filename,allcaps,pkts)
        bw,flow_res,max_flow = calculate_bw(init_time,pkts)
        df = pd.DataFrame(list(bw.values()), columns = ["values"])
        plot_cdf(df,filename)
    plt.xlabel("Bandwidth(Bytes)")
    plt.ylabel("Density")
    plt.show()

def plot_packet_sizes():
    allcaps = None
    pkts = []
    files = get_pcaps()
    filename = files[0]
    allcaps = read_capture(filename,"tcp or tls or icmp or dns")
    init_time,final_time,myip = parse_packets(filename,allcaps,pkts)
    bw,flow_res,max_flow = calculate_bw(init_time,pkts)
    packet_sizes = get_packet_size_plot(pkts,max_flow)
    df = pd.DataFrame(list(packet_sizes.values()), columns = ["values"])
    print(min(df.values))
    plot_cdf(df)
    plt.ylabel("Cumulative probability")
    plt.xlabel("Packet size(Bytes)")
    plt.legend()
    plt.show()


def main():
    allcaps = None
    pkts = []
    files = get_pcaps()
    filename = files[0]
    allcaps = read_capture(filename,"tcp or tls or icmp or dns")
    init_time,final_time,myip = parse_packets(filename,allcaps,pkts)
    bw,flow_res,max_flow = calculate_bw(init_time,pkts)
    ys = plot_bw(bw, files[0])


    down_shape, up_shape, down_flow,up_flow = get_shape_file(flow_res,filename,myip)
    #smoothed_bw = ewa_smoothing(down_flow.values(),list(down_flow.keys()))
    #print(down_flow.values())

    padded_smooth = pad_smoothed_bw(down_flow)
    plot_bw(padded_smooth,"padded")
    get_shape_from_bw_profile(padded_smooth,filename + ".smoothened.download")
    #plot_flow_bw(flow_res,max_flow)
    plt.xlabel("Timestamp(s)")
    plt.ylabel("Bandwidth(Bytes/ms)")
    plt.legend()
    plt.show()


if __name__ == "__main__":
    plot_bw_pearson(padding=True,filtering=False,scaling= False,ispearson=True, isspearman=True)
    #calculate_dtw_distance(padding=False)
    #plot_pcaps()
    #plot_bw_cdf()
#plot_packet_sizes()
#main()
#plot_pcaps()