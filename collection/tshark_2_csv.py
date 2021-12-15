import os
folder = "/production/traces"
from glob import glob
from subprocess import Popen, PIPE

files = glob(os.getcwd() + folder + "/*/*.pcap")
for i in range(len(files)):
    cmd = r""" tshark -r {} -t ad -q -z io,stat,1,,"BYTES()ip.src != 184.21.61.204 && ip.dst != 184.21.61.204" | grep -P "\d+\.?\d*\d-\d+-\d+|Date and time +\|"  | tr "|" "," | sed -E 's/(^,|,$|,$)//g;'>{}.csv

 """.format(files[i],files[i].replace(".pcap",""))
    print(cmd)
    process =  Popen(cmd,stdin=PIPE, stdout=PIPE,shell=True)
    #process.stdin.write(cmd.encode())
    #process.stdin.close()
    #process.communicate(cmd.encode())
    #result = process.stdout.read() 
    #print(result)
    process.communicate()
    process.terminate()


#print(glob(os.getcwd() + folder + "/*/*.pcap"))