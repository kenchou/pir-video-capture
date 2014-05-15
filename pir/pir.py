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

delay_event_trigger = False
last_event_time = datetime.now()
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

def my_callback(channel):
    global last_event_time
    global sensor_status
    global delay_event_trigger

    logging.info('event trigger')

    now = datetime.now()
    sensor_status = GPIO.input(channel)

    if sensor_status:  # and check again the input
        delay_event_trigger = False

        logging.info('PIR ON')

        # trigger PIR event
        os.system('initctl emit --no-wait pir-on')
    else:
        delay_event_trigger = True

        logging.info('PIR OFF')

        # trigger PIR event
        ret = os.system('initctl emit --no-wait pir-off')

        logging.info('-------')

    GPIO.output(GPIO_LED, sensor_status)
    last_event_time = now


# init sensor and LED status
sensor_status = GPIO.input(GPIO_PIR)
GPIO.output(GPIO_LED, sensor_status)
print 'LED status:', GPIO.input(GPIO_LED)

logging.info('PIR sensor start')

GPIO.add_event_detect(GPIO_PIR, GPIO.BOTH, callback=my_callback, bouncetime=200)

# you can continue doing other stuff here
while True:
    if delay_event_trigger:
        time_delta = datetime.now() - last_event_time

        # delay off event
        if time_delta.total_seconds() >= DELAY_OFF_TIME:
            delay_event_trigger = False  # clear event trigger, do not send event one more times
            logging.info('PIR delay OFF')
            ret = os.system('initctl emit --no-wait pir-delay-off')
            logging.info('-------------')
    time.sleep(1)

