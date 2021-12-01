sudo tc qdisc del dev enp0s3 handle ffff: ingress
sudo tc qdisc del dev ifb0 root
sudo modprobe -r ifb
