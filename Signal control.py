import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt

# GPIO setup
GPIO.setmode(GPIO.BCM)
RED_LIGHT = 17
YELLOW_LIGHT = 27
GREEN_LIGHT = 22
TRIGGER_PIN = 23  # Ultrasonic sensor trigger
ECHO_PIN = 24     # Ultrasonic sensor echo

GPIO.setup(RED_LIGHT, GPIO.OUT)
GPIO.setup(YELLOW_LIGHT, GPIO.OUT)
GPIO.setup(GREEN_LIGHT, GPIO.OUT)
GPIO.setup(TRIGGER_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# MQTT Setup (IoT)
broker = "mqtt-broker-address"
client = mqtt.Client("traffic-light-controller")

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("traffic/sensor")

def on_message(client, userdata, msg):
    vehicle_count = int(msg.payload)
    adapt_traffic_lights(vehicle_count)

client.on_connect = on_connect
client.on_message = on_message

# Function to measure distance using the ultrasonic sensor
def measure_distance():
    GPIO.output(TRIGGER_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIGGER_PIN, False)

    start_time = time.time()
    stop_time = time.time()

    while GPIO.input(ECHO_PIN) == 0:
        start_time = time.time()

    while GPIO.input(ECHO_PIN) == 1:
        stop_time = time.time()

    elapsed_time = stop_time - start_time
    distance = (elapsed_time * 34300) / 2  # Speed of sound is 34300 cm/s
    return distance

# Adaptive traffic light timing based on vehicle count
def adapt_traffic_lights(vehicle_count):
    if vehicle_count < 5:
        light_cycle(5, 2, 10)  # Shorter green light
    elif 5 <= vehicle_count < 15:
        light_cycle(10, 2, 15)  # Moderate green light
    else:
        light_cycle(15, 3, 20)  # Longer green light

# Traffic light sequence (green -> yellow -> red)
def light_cycle(green_time, yellow_time, red_time):
    # Green light
    GPIO.output(RED_LIGHT, False)
    GPIO.output(GREEN_LIGHT, True)
    time.sleep(green_time)

    # Yellow light
    GPIO.output(GREEN_LIGHT, False)
    GPIO.output(YELLOW_LIGHT, True)
    time.sleep(yellow_time)

    # Red light
    GPIO.output(YELLOW_LIGHT, False)
    GPIO.output(RED_LIGHT, True)
    time.sleep(red_time)

# Main loop
try:
    client.connect(broker)
    client.loop_start()
    while True:
        distance = measure_distance()
        if distance < 50:  # Vehicle detected within 50 cm
            vehicle_count = 1  # This can be sent over MQTT for cloud-based processing
        else:
            vehicle_count = 0

        client.publish("traffic/sensor", vehicle_count)
        time.sleep(1)

except KeyboardInterrupt:
    print("Terminated by User")
    GPIO.cleanup()

finally:
    GPIO.cleanup()
