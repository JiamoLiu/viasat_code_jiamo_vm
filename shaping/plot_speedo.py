import matplotlib.pyplot as plt
import sys
import math
upper = 48
lower = 2
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
    plt.savefig("/home/jiamoliu/Desktop/viasat_code/"+filename+".speedo.png")
    plt.show()

def get_target(data):
    if abs(upper - data) < abs(lower -data):
        return upper
    else:
        return lower
def RMSE(data):
    sqr =0
    for i in data:
        print(i)
        target = get_target(i)
        #print(target)
        sqr += (target-i)*(target-i)
    return math.sqrt(sqr/len(data))



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
downrate = [0]
uprate = []

data = lines

for row in data:
    tokens = row.split()
    print(tokens)
    if tokens == []:
        break
    if (float(tokens[0]) <0.5):
        continue
    if (float(tokens[0]) >100):
    	downrate.append(float(tokens[0])/1000)
    	continue
    downrate.append(float(tokens[0]))
print(RMSE(downrate))
downrate.append(0)
linePlot(downrate,filename.split(".")[0])
