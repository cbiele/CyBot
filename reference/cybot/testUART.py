#!/usr/bin/env python

import time
import serial

ser = serial.Serial('/dev/ttyS0', 115200, timeout=0.050)
count = 0

while 1:
    ser.write('Sent %d time(s)')
    time.sleep(1)
    count += 1                        
          
   
