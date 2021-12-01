import os
import glob
import matplotlib.pyplot as plt
import pandas as pd
import random
import matplotlib.colors as colors
import matplotlib
import seaborn as sns
import numpy as np
markers = ['o',">",""]
markers = [""]
linestype = ["dashed","solid","dotted"]

colors_list = list(colors._colors_full_map)
#print(matplotlib.__version__)
#print(colors_list)
#print(random.choice(colors_list))
def get_csvs():
    path = os.getcwd()+"/logs"
    extension = 'csv'
    os.chdir(path)
    result = glob.glob('*.{}'.format(extension))
    return result
def plot_pdf(df):
    sns.kdeplot(data = df.buffer_health, cumulative = False,linestyle = random.choice(linestype), marker=random.choice(markers),color=random.choice(colors_list),lw =1)

def plot_cdf(df):
    #print(df.head())
    sns.kdeplot(data = df.buffer_health, cumulative = True,linestyle = random.choice(linestype), marker=random.choice(markers),color=random.choice(colors_list),lw =1)


def read_file_as_df(filename):
    df = pd.read_csv(filename)
    return df

def get_buffer_health_from_file(df):
    return df["buffer_health"].tolist()

def get_elasped_time(df):
    timestamps = df["timestamp"].tolist()
    timestamps = [x - timestamps[0] for x in timestamps]
    return timestamps

def add_plot(x,y):
    plt.plot(x,y, linestyle = random.choice(linestype), marker=random.choice(markers),color=random.choice(colors_list),lw=1)



def main():
    files = get_csvs()
    legends = []
    dfs = []
    for file in files:
        df = read_file_as_df(file)
        dfs.append(df)
        legends.append(file.split("_")[3].split("-")[0])
        buffer_health = get_buffer_health_from_file(df)
        add_plot(get_elasped_time(df), buffer_health)
    plt.legend(legends)
    dfs = pd.concat(dfs, axis=0)
    #plt.show(block=False)
    
    plt2 = plt.figure()
    for file in files:
        df = read_file_as_df(file)
        id = file.split("_")[3].split("-")[0]
        legends.append(id)
        #sns.kdeplot(data = df.buffer_health, cumulative = False,linestyle = random.choice(linestype), marker=random.choice(markers),color='r')
        plot_cdf(df)
    #plt.legend(legends)
    #plt.show(block=False)
    plt2.legend(legends)
    plt2.show()

    plt3 = plt.figure()
    for file in files:
        df = read_file_as_df(file)
        id = file.split("_")[3].split("-")[0]
        legends.append(id)
        #sns.kdeplot(data = df.buffer_health, cumulative = False,linestyle = random.choice(linestype), marker=random.choice(markers),color='r')
        plot_pdf(df)
    #plt.legend(legends)
    #plt.show(block=False)
    plt3.legend(legends)
    plt3.show()

    plt4 = plt.figure()
    plot_pdf(dfs)
    plt4.show()

    plt5 = plt.figure()
    plot_cdf(dfs)
    plt5.show()

    plt.show()

main()