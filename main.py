import time
import board
import pwmio
import busio
import socketpool
import wifi
from adafruit_motor import servo
from main import IdeaBoard
import mfrc522

# Wi-Fi Configuration
SSID = "LoboUlloa"
PASSWORD = "Patatitas"

print("Connecting to Wi-Fi...")
wifi.radio.connect(SSID, PASSWORD)
print(f"Connected to {SSID}!")
print("IP Address:", wifi.radio.ipv4_address)

# Setup for socket server
pool = socketpool.SocketPool(wifi.radio)
server = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
server.bind(('0.0.0.0', 80))
server.listen(1)
server.settimeout(0.1)  # Set a short timeout for non-blocking behavior

# Configuración del IdeaBoard y el servomotor
ib = IdeaBoard()
pwm = pwmio.PWMOut(board.IO25, duty_cycle=2 ** 15, frequency=50)
servo_motor = servo.Servo(pwm)

# Configuración del lector RFID
reader = mfrc522.MFRC522(board.SCK, board.MOSI, board.MISO, board.IO4, board.IO5)

# Tags RFID autorizados
tag1 = "63819b13"
tag2 = "c33c7630"

# Parámetros de control
timeout = 5
last_detection_time = time.time()

# Posiciones del servomotor
initial_position = 180
open_position = 0

def rotateServo(angle):
    servo_motor.angle = angle

def leer_tag(rdr):
    print("Starting RFID reader...")
    rdr.set_antenna_gain(0x07 << 4)
    print("Antenna gain set to maximum.")
    
    (stat, tag_type) = rdr.request(rdr.REQIDL)
    if stat == rdr.OK:
        print(f"RFID request successful, tag type: {tag_type:#x}")
        (stat, raw_uid) = rdr.anticoll()
        if stat == rdr.OK:
            print("Anti-collision successful.")
            uid = ''.join(f'{x:x}' for x in raw_uid[0:4])
            print(f"Tag UID detected: {uid}")
            return uid
        else:
            print("Anti-collision failed.")
    else:
        print("RFID request failed.")

    return None

# Configuración del servidor HTTP
def handle_request(request):
    if "GET /open" in request:
        rotateServo(open_position)
        ib.pixel = (0, 255, 0)  # Verde
        return "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nDoor opened\n"
    elif "GET /close" in request:
        rotateServo(initial_position)
        ib.pixel = (255, 0, 0)  # Rojo
        return "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nDoor closed\n"
    else:
        return "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nNot found\n"

while True:
    ib.pixel = (0, 0, 0)  # Apagar LED
    current_time = time.time()

    # Handle incoming HTTP requests first, if any
    try:
        client, addr = server.accept()
        request = bytearray(1024)

        try:
            size = client.recv_into(request)
            request = str(request[:size], 'utf-8')
            print("Request:", request)

            response = handle_request(request)
            client.send(response.encode('utf-8'))
        except OSError as e:
            if e.errno == 11:  # EAGAIN
                print("No data available yet, retrying...")
                continue
        finally:
            client.close()

    except OSError as e:
        # This handles both timeout and other potential errors gracefully
        if e.errno != 110 and e.errno != 116:  # Ignore timeout exceptions ETIMEDOUT and ETIMEOUT
            raise

    # Check the RFID reader
    uid = leer_tag(reader)
    if uid:
        last_detection_time = current_time
        if uid == tag1:
            ib.pixel = (0, 255, 0)  # Verde
            rotateServo(open_position)  # Abre cerradura
            print("Tag 1 detectado: Servo movido a 180 grados y LED verde")
            time.sleep(10)
            rotateServo(initial_position)  # Cierra cerradura
        elif uid == tag2:
            ib.pixel = (255, 0, 0)  # Rojo
            print("Error: Tag 2 detectado")
            time.sleep(3)
        else:
            ib.pixel = (0, 0, 0)  # Apagar LED

    # If no RFID tag is detected and a timeout occurs, reset the servo
    if current_time - last_detection_time > timeout:
        if servo_motor.angle != initial_position:
            rotateServo(initial_position)
            print(f"Tiempo de espera alcanzado: Servo regresado a {servo_motor.angle} grados")
        last_detection_time = current_time
