#!/usr/bin/env python
# -*- coding: utf-8 -*-
# lsusb to check device name
#dmesg | grep "tty" to find port name

import serial,time


if __name__ == '__main__':
    
    print('Running. Press CTRL-C to exit.')
    with serial.Serial("/dev/ttyAMA0", 115200, timeout=1) as arduino:
        time.sleep(2) #wait for serial to open
        if arduino.isOpen():
            print("{} connected!".format(arduino.port))
            #arduino.write("g91\n".encode('utf-8'))
            arduino.write("x50y100\n".encode('utf-8'))
            arduino.write("x0y0\n".encode('utf-8'))
            arduino.write("x-20y-800\n".encode('utf-8'))
