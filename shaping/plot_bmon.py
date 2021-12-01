import matplotlib.pyplot as plt
import sys
def convertToMbits(txt):
    if ("Mb" in txt):
        txt = float(txt.replace("Mb",""))
        return txt

    if ("MiB" in txt):
        txt = float(txt.replace("MiB",""))*8
        return txt
    if ("KiB" in txt):
        txt = float(txt.replace("KiB",""))*8/1000
        return txt
    return 0


def linePlot(data, filename, interval = 0.2):
    x = generate_x(data,interval)
    plt.plot(x, data)
    plt.title(filename.replace(".txt","")+"/s")
    plt.xlabel("timestamp(s)")
    plt.ylabel("throughput (Mbits/s)")
    plt.savefig("/home/jiamoliu/Desktop/viasat_code/"+filename+".bmon.png")
    plt.show()


def generate_x(data,interval):
    res = []
    for i in range(len(data)):
        res.append(i*interval)
    return res


filename = sys.argv[1]
f = open(filename, "r")
text = f.read()
lines = text.split("\n")
numberoflines = len(lines)
downrate = []
uprate = []

data = [y for x,y in enumerate(lines) if x%2 != 0]

for row in data:
    tokens = row.split()
    downrate.append(convertToMbits(tokens[1]))
    uprate.append(convertToMbits(tokens[3]))

linePlot(downrate,filename.split(".")[0])
