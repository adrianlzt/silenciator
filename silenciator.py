#!/usr/bin/env python
## This is an example of a simple sound capture script.
##
## The script opens an ALSA pcm for sound capture. Set
## various attributes of the capture, and reads in a loop,
## Then prints the volume.
##
## To test it out, run it and shout at your microphone:

import alsaaudio, time, audioop
import datetime
from threading import Timer
from subprocess import Popen, STDOUT
from random import randint
import yaml
import sys
import os


# Open the device in nonblocking capture mode. The last argument could
# just as well have been zero for blocking mode. Then we could have
# left out the sleep call in the bottom of the loop
inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NONBLOCK)

# Set attributes: Mono, 8000 Hz, 16 bit little endian samples
inp.setchannels(1)
inp.setrate(8000)
inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)

# The period size controls the internal number of frames per period.
# The significance of this parameter is documented in the ALSA api.
# For our purposes, it is suficcient to know that reads from the device
# will return this many frames. Each frame being 2 bytes long.
# This means that the reads below will return either 320 bytes of data
# or 0 bytes of data. The latter is possible because we are in nonblocking
# mode.
#inp.setperiodsize(160)
inp.setperiodsize(3600)

with open("config.yml") as f:
    config = yaml.load(f)

aviso_t = datetime.datetime.now()
avisos_n = 0

def clean_avisos():
    global avisos_n
    print("avisos_n = 0")
    avisos_n = 0
    global hilo
    hilo = Timer(config['clean_time'], clean_avisos)
    hilo.start()

def play(audio):
    ran = randint(0,len(audio)-1) 
    FNULL = open(os.devnull, 'w')
    Popen([config['play'], os.path.join("sonidos",audio[ran])], stdout=FNULL, stderr=STDOUT)

def avisa_nivel():
    print("callarse! [%s]" % avisos_n)
    if avisos_n <= 2:
        play(config['n1_wav'])
    elif avisos_n <= 4:
        play(config['n2_wav'])
    else:
        play(config['n3_wav'])

def avisador():
    """
    Se van contando avisos durante un periodo 'clean_time'
    Se avisa como rapido cada 'wait_warns'
    Segun se reciban mas avisos en un 'clean_time' se va subiendo el nivel de callarse
    """
    global aviso_t
    if (datetime.datetime.now() - aviso_t).seconds > config['wait_warns']:
        aviso_t = datetime.datetime.now()
        global avisos_n
        avisos_n += 1
        avisa_nivel()

if __name__ == '__main__':
    global hilo
    hilo = Timer(config['clean_time'], clean_avisos)
    hilo.start()

    try:
        while True:
            # Read data from device
            l,data = inp.read()
            if l:
                # Return the maximum of the absolute value of all samples in a fragment.
                max_v = audioop.max(data, 2)
                #print max_v
                if max_v > config['threshold']:
                    avisador()
            time.sleep(.001)
    except (KeyboardInterrupt, SystemExit):
        hilo.cancel()
        sys.exit(0)
