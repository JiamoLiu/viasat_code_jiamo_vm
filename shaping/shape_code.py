import subprocess
import os
import time
import random

interval_in_sec = 1
lower = 2
upper = 6

bashCmd2 = "bash ingress_shape_bfifo.sh -l 6"

bashCmd = "bash ingress_shape.sh -l 6"
process = subprocess.Popen(bashCmd2.split(), stdout=subprocess.PIPE)
output, error = process.communicate()
time.sleep(interval_in_sec)

lower_mode = True
while True:
    if lower_mode:
        bashCmd = "bash ingress_shape.sh -l {}".format(lower)
        bashCmd2 = "bash ingress_shape_bfifo.sh -l {}".format(upper)
        lower_mode = False
        print(lower)
    else:
        bashCmd = "bash ingress_shape.sh -l {}".format(upper)
        bashCmd2 = "bash ingress_shape_bfifo.sh -l {}".format(upper)
        lower_mode = True
        print(upper)
    process = subprocess.Popen(bashCmd2.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    print(output)
    time.sleep(interval_in_sec)


