#!/usr/bin/python
import time
import math
pi=3.14159

fn="/dev/servoblaster"
num=2
min_val=70
max_val=240
delay=0.02

omega=1

mean_val=(min_val+max_val)/2.0
amp=(max_val-min_val)/2.0

t=0
while 1:
    val=mean_val + amp*math.cos(2*pi*time.time()*omega)
    with open(fn,'wt') as fp:
        fp.write("%d=%d\n"%(num,int(val)))
    time.sleep(delay)

