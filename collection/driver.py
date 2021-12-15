from subprocess import Popen, PIPE
import  signal

process = Popen("sudo iptables -P FORWARD ACCEPT".split(" "))
stdout,stderr = process.communicate()
process.terminate()

#this run is quic wtih proper shaping
for i in range (100):
    process = Popen("mm-delay 1 mm-link 48mbits.shape 12mbits.shape --uplink-log=48mbits.shape.log --downlink-log=youtube_stats_log_1-32VFLs1COxo.pcap.download.log".split(" "), stdin=PIPE, stdout=PIPE)
    process.stdin.write('python3 stream.py  --iface ingress --link https://www.youtube.com/watch?v=32VFLs1COxo'.encode())
    process.stdin.close()
    result = process.stdout.read() 
    print(result)
    process.terminate()
#process.send_signal(signal.SIGINT)
