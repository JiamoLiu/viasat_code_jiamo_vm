from numpy.lib.function_base import _append_dispatcher
import pandas as pd
import os
import random
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from pandas.core.frame import DataFrame
import scipy.stats
from scipy import spatial

from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
import seaborn as sns
from matplotlib.pyplot import figure, text
from datetime import datetime, timedelta
from pandas.plotting import scatter_matrix
from dateutil import parser

markers = ['o',">",""]
markers = [""]
#linestype = ["solid","dotted"]
linestype = ["solid"]
colors_list = list(colors._colors_full_map)[-20:-1]

def dtw(x,y):
    distance, path = fastdtw(x, y, dist=euclidean)
    return distance

def cosine_sim(x,y):
    return  1 - spatial.distance.cosine(x, y)

resolution_mapping ={
    "highres":7,
    "hd1080":6,
    "hd720":5,
    "large":4,
    "medium":3,
    "small":2,
    "tiny": 1
}

resolution_counts ={
    "highres":0,
    "hd1080":0,
    "hd720":0,
    "large":0,
    "medium":0,
    "small":0,
    "tiny": 0
}

def get_total_buffer_before(row, seconds):
    res = 0
    buffers = str(row["bufferdurationwithtime"]).split(":")
    for buffer_time in buffers:
        if (buffer_time == "nan" or buffer_time == ""):
            continue
        instant = int(buffer_time.split("?")[0])
        if (instant<= seconds):
            res = res  + int(buffer_time.split("?")[1])

    return res



def plot_when_buffer_resolution_switch_happens(df):
    buffering_ys = np.zeros(int(df.videoduration[0])+10)
    reso_ys = np.zeros(int(df.videoduration[0])+10)
    reso_ups = np.zeros(int(df.videoduration[0])+10)
    reso_downs = np.zeros(int(df.videoduration[0])+10)


    for index, row in df.iterrows():
        buffers = str(row["bufferdurationwithtime"]).split(":")
        init_buffer_time = int(row["initialbufferingtime"]/1000)


        for buffer_time in buffers:
            if (buffer_time == "nan" or buffer_time == ""):
                continue


            instant = int(buffer_time.split("?")[0])
            corrected_time = instant - get_total_buffer_before(row, instant)
            buffering_ys[corrected_time] = buffering_ys[corrected_time] + 1





        resolution_changes = str(row["requestedresolutionswithtime"]).split(":")
        for i in range(len(resolution_changes)):
            if (resolution_changes[i] == "nan" or resolution_changes[i] == ""):
                continue

            instant = int(resolution_changes[i].split("?")[0])
            corrected_time = instant - get_total_buffer_before(row,instant) 
            if (corrected_time != 0 ):
                reso_ys[corrected_time] = reso_ys[corrected_time]+1

            if (i!=0):
                previous_reso = resolution_changes[i-1].split("?")[1]
                current_reso  =resolution_changes[i].split("?")[1]
                if (resolution_mapping[previous_reso] > resolution_mapping[current_reso]):
                    reso_downs[corrected_time] = reso_downs[corrected_time] + 1
                else:
                    reso_ups[corrected_time] = reso_ups[corrected_time] + 1
        

    #plot_line(np.arange(len(buffering_ys)), buffering_ys)
    figure5,ax = plt.subplots(4)
    ax[0].plot(np.arange(len(buffering_ys)), buffering_ys)
    ax[1].plot(np.arange(len(buffering_ys)), reso_ys)
    ax[2].plot(np.arange(len(buffering_ys)), reso_ups)
    ax[3].plot(np.arange(len(buffering_ys)), reso_downs)
    ax[0].set_ylabel("No. of rebufferings",fontsize=10)
    ax[1].set_ylabel("No. of Resolution changes",fontsize=10)
    ax[2].set_ylabel("No. of switch ups",fontsize=10)
    ax[3].set_ylabel("No. of switch downs",fontsize=10)
    plt.xlabel("Video playback in seconds",fontsize=10)

    print("perason correlation for switch up and rebuffering times: {}".format(scipy.stats.pearsonr(buffering_ys,reso_ups)))
    print("cos similarity for switch up and rebuffering times:{}".format(cosine_sim(buffering_ys,reso_ups)))
    figure5.show()


    temp = pd.DataFrame()
    temp["rebufferings"] = buffering_ys
    temp["reso_changes"] = reso_ys
    temp["reso_ups"] = reso_ups
    temp["reso_downs"] =reso_downs
    scatter_matrix(temp,  figsize = (6, 6), diagonal = 'kde')
    #figure5.savefig("when_things_happen.png",dpi=1200)
        #print(buffers)


def plot_reso_infos(df):
    figure2 = plt.figure()
    ups_with_lvl= 0
    ups = 0
    downs = 0
    downs_with_lvl = 0
    items = 0
    for index, row in df.iterrows():
        reso = row["requestedresolutions"].split(":")
        previous = reso[0]
        for i in range(1, len(reso)):
            if reso[i] == "":
                continue
            previous_score = resolution_mapping[previous]
            current_score = resolution_mapping[reso[i]]

            if (current_score > previous_score):
                ups_with_lvl = ups_with_lvl+ (current_score - previous_score)
                ups = ups + 1
            if (current_score<previous_score):
                downs_with_lvl = downs_with_lvl+ (previous_score - current_score)
                downs = downs +1 
            previous = reso[i]

    figure = plt.figure()
    plt.bar(["ups","downs"],[ups,downs],color="r")
    plt.ylabel("Number of switching up or down")
    figure.show()
    figure.savefig("ups_downs.png",dpi=1200)

    figure2 = plt.figure()
    plt.bar(["ups with levels","downs with levels"],[ups_with_lvl,downs_with_lvl],color="r")
    plt.ylabel("Number of switching up or down with levels")
    figure2.show()
    figure2.savefig("ups_downs_with_levels.png",dpi=1200)
    #plt.bar(["ups","downs","ups_with_lvl","downs_with_lvl"],[ups,downs,ups_with_lvl,downs_with_lvl])
    
    #plt.ylabel("Number of switching up or down")


def plot_cdf(data,bw = 0.01,override_color = None):
    #print(df.head())
    if (override_color == None):
        sns.kdeplot(data = data, cumulative = True,linestyle = random.choice(linestype), marker=random.choice(markers),color=random.choice(colors_list),lw =1,bw_method = bw)
    else:
        sns.kdeplot(data = data, cumulative = True,linestyle = random.choice(linestype), marker=random.choice(markers),color = override_color,lw =1,bw_method = bw)
    #plt.hist(data,cumulative=True)
def plot_line(x,y,override_color = None):
    if(override_color == None):
        plt.plot(x,y, linestyle = random.choice(linestype), marker=random.choice(markers),color=random.choice(colors_list),lw=1)
    else:
        plt.plot(x,y, linestyle = random.choice(linestype), marker=random.choice(markers),color=override_color,lw=1)

def plot_buffers_switches(df):
    #figure1 = plt.figure()
    temp = DataFrame()
    res_switches = df["resolutionchanges"]
    buffer_times = df["numofrebufferings"]
    buffer_durations = df["bufferduration"]
    startup_delay = df["initialbufferingtime"]
    print("perason correlation for buffer times and resolutions switch times: {}".format(scipy.stats.pearsonr(buffer_times,res_switches)))
    print("perason correlation for buffer durations and buffer times: {}".format(scipy.stats.pearsonr(buffer_durations,buffer_times)))
    print("perason correlation for buffer durations and resolutions switch times: {}".format(scipy.stats.pearsonr(buffer_durations,res_switches)))


    print("perason correlation for startup delay and resolutions switch times: {}".format(scipy.stats.pearsonr(startup_delay,res_switches)))
    print("perason correlation for startup delay and buffer times: {}".format(scipy.stats.pearsonr(startup_delay,buffer_times)))
    print("perason correlation for startup delay and buffer durations: {}".format(scipy.stats.pearsonr(startup_delay,buffer_durations)))
    xs = np.arange(0,len(res_switches),step = 1)

    temp["reso_changes"] = res_switches
    temp["rebufferings_no"] = buffer_times
    temp["rebuffering_duration"] = buffer_durations
    temp["start_up_delay"] = startup_delay
    temp["start_up_delay"] = temp["start_up_delay"].apply(lambda x: x/1000)
    scatter_matrix(temp,  figsize = (6, 6), diagonal = 'kde')
    #return
    
    start = parser.parse(df.localtime[0]) -  timedelta(hours=10)
    end = parser.parse(df.localtime[140]) - timedelta(hours=10)
    print(start)
    #return
    

    figure_c = plt.figure()
    plot_line(xs, res_switches,"r")
    plt.vlines(x=0, ymin=0, ymax=20, color = 'b')
    text(1, 15, start, rotation=90, verticalalignment='center')
    plt.vlines(x=140, ymin=0, ymax=20, color = 'b')
    text(141, 15, end, rotation=90, verticalalignment='center')
    plt.xlabel("Session_ids",fontsize= 16)
    plt.ylabel("Number of resolution switches",fontsize= 16)
    #figure_c.show()
    figure_c.savefig("switch_times_grpah.png", dpi=1200)
    #return

    figure_d = plt.figure()
    plot_line(xs, buffer_times,"r")
    plt.vlines(x=0, ymin=0, ymax=10, color = 'b')
    text(1, 8, start, rotation=90, verticalalignment='center')
    plt.vlines(x=140, ymin=0, ymax=10, color = 'b')
    text(141, 8, end, rotation=90, verticalalignment='center')
    plt.xlabel("Session_ids",fontsize= 16)
    plt.ylabel("Number of rebufferings",fontsize= 16)
    figure_d.show()
    figure_d.savefig("rebuffering_times_grpah.png", dpi=1200)
    #return
    
    figure_e = plt.figure()
    plot_line(xs, buffer_durations,"r")
    plt.vlines(x=0, ymin=0, ymax=40, color = 'b')
    text(1, 30, start, rotation=90, verticalalignment='center')
    plt.vlines(x=140, ymin=0, ymax=40, color = 'b')
    text(141, 30, end, rotation=90, verticalalignment='center')
    plt.xlabel("Session_ids",fontsize= 16)
    plt.ylabel("Total rebuffering duration in seconds",fontsize= 16)
    figure_e.show()
    figure_e.savefig("total_rebuffering_duration_grpah.png", dpi=1200)
    #return
    #figure1.legend(["resolution switches","number of bufferings","buffer duration (seconds)"])
    #figure1.show()

    figure_a = plt.figure()
    plot_line(xs, startup_delay,"r")
    plt.vlines(x=0, ymin=0, ymax=40000, color = 'b')
    text(1, 30000, start, rotation=90, verticalalignment='center')
    plt.vlines(x=140, ymin=0, ymax=40000, color = 'b')
    text(141, 30000, end, rotation=90, verticalalignment='center')
    plt.xlabel("Session_ids",fontsize= 16)
    plt.ylabel("Start up delay (ms)",fontsize= 16)
    figure_a.savefig("start_up_delay.png", dpi=1200)
    figure_a.show()
    #return
    figure_b = plt.figure()
    plot_cdf(startup_delay,override_color="r")
    plt.xlabel("Start up delay in ms",fontsize= 16)
    plt.ylabel("Density",fontsize= 16)
    figure_b.savefig("start_up_delay_cdf.png", dpi=1200)
    figure_b.show()


    figure2 = plt.figure()
    plot_cdf(res_switches,override_color= "r")
    plt.xlabel("Number of resolution switches",fontsize= 16)
    plt.ylabel("Density",fontsize= 16)
    figure2.savefig("resolution_switches_cdf.png", dpi=1200)
    
    figure3 = plt.figure()
    plot_cdf(buffer_times,override_color= "r")
    plt.xlabel("Number of rebufferings",fontsize= 16)
    plt.ylabel("Density",fontsize= 16)
    figure3.savefig("rebuffering_times_cdf.png", dpi=1200)
    
    
    figure4 = plt.figure()
    plot_cdf(buffer_durations,override_color= "r")
    plt.xlabel("Total rebuffering duration in seconds",fontsize= 16)
    plt.ylabel("Density",fontsize= 16)
    figure4.savefig("rebuffering_duration_cdf.png", dpi=1200)
    
    
    
    figure2.show()
    figure3.show()
    figure4.show()

def is_reso_up(switches,index):
    current_reso = switches[index].split("?")[1]
    previous_reso = switches[index-1].split("?")[1]
    if(resolution_mapping[current_reso] > resolution_mapping[previous_reso]):
        return True
    else:
        return False

def plot_buffer_health(played_series, loaded_fraction,switches,video_duration,buffers):
    figure = plt.figure()
    print(switches)
    played_series = played_series.split(" ")
    loaded_fraction = loaded_fraction.split(" ")
    buffer_health = []
    print(len(played_series))
    for i in range(len(played_series)):
        #print(loaded_fraction[i])
        if (loaded_fraction[i] == "NaN"):
            loaded_fraction[i] = loaded_fraction[i-1]

        buffer_health.append(float(loaded_fraction[i])*float(video_duration) - float(played_series[i]))
        #print(float(loaded_fraction[i])*float(video_duration))
    xs = np.arange(0, len(played_series)*10, 10)
    plot_line(xs, buffer_health,'r')
    
    changes = switches.split(":")
    ups = []
    downs = []
    for i in range(1,len(changes)):
        if (changes[i] != ""):
            if is_reso_up(changes, i):
                ups.append(int(changes[i].split("?")[0])*100)
            else:
                downs.append(int(changes[i].split("?")[0])*100)
    plt.vlines(downs,ymin=0,ymax= 20,color ="blue")
    plt.vlines(ups,ymin=0,ymax= 20,color ="purple")
    plt.xlabel("elapsed time (ms)",fontsize = 16)
    plt.ylabel("buffer health (seconds)",fontsize = 16)
    
    temp = []
    buffers = str(buffers)
    if buffers !="nan":
        buffers = buffers.split(":")
        for buffer in buffers:
            if buffer == "":
                continue
            x = int(buffer.split("?")[0])
            plt.plot(x*100, 20,'ro')
    plt.savefig("buffer_health.png",dpi=1200)
    #print(temp)


    
    figure.show()

df = pd.read_csv(os.getcwd()+"/video_records.csv")
df['resolutionchanges'] = df['resolutionchanges'].apply(lambda x: x - 1)
#df = df.query("initialbufferingtime < 7000")
#df = df.reset_index(drop=True)
#plot_reso_infos(df)
#plot_buffers_switches(df)
#plot_when_buffer_resolution_switch_happens(df)

df = df.query("resolutionchanges == 2")
df = df.reset_index(drop=True)
selected = df.iloc[0]
print(selected.localtime)
plot_buffer_health(selected.playback_fractions.strip(), selected.loaded_fractions.strip(), selected.requestedresolutionswithtime,selected.videoduration,selected.bufferdurationwithtime)

plt.show()
