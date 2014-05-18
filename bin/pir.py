#!/usr/bin/env python
#
# stream pi camera 
#

import os
import signal
import time
import logging
import RPi.GPIO as GPIO
from datetime import datetime

GPIO_PIR = 23
GPIO_LED = 27
DELAY_OFF_TIME = 60

print 'GPIO Version:', GPIO.VERSION

# init GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIR, GPIO.IN)
GPIO.setup(GPIO_LED, GPIO.OUT, initial=GPIO.LOW)

is_trigger_pir_off = False
time_stamp = time.time()
sensor_status = GPIO.LOW

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def signal_term_handler(signal, frame):
    logging.info('got SIGTERM, GPIO cleanup')
    GPIO.cleanup()
    logging.info('PIR sensor stopped')
    exit(0)


# install signal handler
signal.signal(signal.SIGTERM, signal_term_handler)
signal.signal(signal.SIGINT, signal_term_handler)

def pir_signal_callback(channel):
    global time_stamp
    global sensor_status
    global is_trigger_pir_off

    time_stamp = time.time()
    sensor_status = GPIO.input(channel)
    GPIO.output(GPIO_LED, sensor_status)

    if sensor_status:  # and check again the input
        is_trigger_pir_off = False

        # trigger PIR event
        send_event('pir-on')
    else:
        is_trigger_pir_off = True

        # trigger PIR event
        send_event('pir-off')


def send_event(name):
    cmd = 'initctl emit --no-wait %s' % name
    logging.info('%s: %s' % (os.getpid(), cmd))
    os.system(cmd)


# init sensor and LED status
sensor_status = GPIO.input(GPIO_PIR)
GPIO.output(GPIO_LED, sensor_status)
print 'LED status:', GPIO.input(GPIO_LED)

logging.info('PIR sensor start (%s)' % os.getpid())

GPIO.add_event_detect(GPIO_PIR, GPIO.BOTH, callback=pir_signal_callback, bouncetime=50)

while True:
    time.sleep(1)

    if is_trigger_pir_off:
        time_now = time.time()

        # delay off event
        if time_now - time_stamp >= DELAY_OFF_TIME:
            is_trigger_pir_off = False  # clear event trigger, do not send event one more times

            send_event('pir-delay-off')

            # reassign event handler, GPIO bug?
            GPIO.remove_event_detect(GPIO_PIR)
            GPIO.add_event_detect(GPIO_PIR, GPIO.BOTH, callback=pir_signal_callback, bouncetime=50)

