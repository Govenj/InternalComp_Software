from microdot import Microdot
from microdot.websocket import with_websocket
from microdot.cors import CORS
from machine import Pin, PWM
import asyncio 
import network
import time

# Connect to Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('WIFI_NAME', 'PASSWORD')
time.sleep(5)

# Wait for connection
max_attempts = 10
attempt = 0

while not wlan.isconnected() and attempt < max_attempts:
    print(f"Trying to connect (Attempt {attempt + 1}/{max_attempts})...")
    time.sleep(10)
    attempt += 1

# Connection is successful when LED blinks on the Pi
if wlan.isconnected():
    print("Connected to IP:", wlan.ifconfig()[0])
    led = Pin("LED", Pin.OUT)
    for i in range(5):
        print(i)
        led.on()
        time.sleep(1)
        led.off()
        time.sleep(1)
else:
    print("Failed to connect to Wi-Fi. Please check your SSID and password.")
    
# Initialize PWM and direction pins 
motor2_PWM = PWM(Pin(11, Pin.OUT), freq=1000)
motor2_in1= Pin(5, Pin.OUT)
motor2_in2 = Pin(9, Pin.OUT)

motor4_PWM = PWM(Pin(19, Pin.OUT), freq=1000)
motor4_in1 = Pin(20, Pin.OUT)
motor4_in2 = Pin(21, Pin.OUT)

app = Microdot()
CORS(app, allowed_origins = '*', allow_credentials = True)


@app.route('/hello_world', methods=['GET'])
async def get_invoices(request):
    return 'Hello World!'

@app.get('/')
@with_websocket
async def index(request, ws):
    try: 
        while True:
            data = await ws.receive()
            if not data:
                break
            await ws.send('hello world')
            
    except OSError as msg:
        print(msg)

@app.get('/motion')
@with_websocket
async def index(request, ws):
    # Helper function to set motor direction
    def set_wheel_direction(wheel1_dir, wheel2_dir):
        motor2_in1.value(wheel1_dir[0]), motor2_in2.value(wheel1_dir[1])
        motor4_in1.value(wheel2_dir[0]), motor4_in2.value(wheel2_dir[1])

    # Function to control wheel speed using PWM
    def motion(wheel1, wheel2):
        print(f"Wheel1: {wheel1}, Wheel2: {wheel2}")
        motor2_PWM.duty_u16(int(wheel1 / 100 * 65535))
        motor4_PWM.duty_u16(int(wheel2 / 100 * 65535))

    # Main movement function
    def move(x, y):
        print("moving\n")
        abs_x, abs_y = abs(x), abs(y)

        if x >= 0 and y >= 0:  # Forward and turn right
            print("forward and turn right")
            set_wheel_direction((0, 1), (0, 1))  # Both wheels forward
            motion(abs_y, abs(abs_y - abs_x))

        elif x <= 0 and y <= 0:  # Backward and turn left
            print("backward and turn left")
            set_wheel_direction((1, 0), (1, 0))  # Both wheels backward
            motion(abs(abs_y - abs_x), abs_y)

        elif x >= 0 and y <= 0:  # Backward and turn right
            print("backward and turn right")
            set_wheel_direction((1, 0), (1, 0))  # Both wheels backward
            motion(abs_y, abs(abs_y - abs_x))

        elif x <= 0 and y >= 0:  # Forward and turn left
            print("forward and turn left")
            set_wheel_direction((0, 1), (0, 1))  # Both wheels forward
            motion(abs(abs_y - abs_x), abs_y)
            
    set_wheel_direction((0, 0), (0, 0))
    while True:
        data = await ws.receive()
        if not data:
            break
        direction = data.split(",")
        x = direction[0]
        y = direction[1]        
        move(int(float(x)), int(float(y)))
        
        await ws.send('good bye')
app.run(port=80)