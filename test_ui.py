import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time

reader = SimpleMFRC522()

try:
    print("Intentando leer solo el ID Único (UID)...")
    while True:
        # El método read_id_non_block no necesita autenticación de sector, solo lee el UID
        id = reader.read_id_non_block()
        if id:
            print(f"ID Único detectado: {id}")
            # Si esto funciona, el SPI está bien, y el problema es la autenticación (AUTH ERROR).
            time.sleep(2)
        else:
            time.sleep(0.1)

except KeyboardInterrupt:
    GPIO.cleanup()

except Exception as e:
    # Si la tarjeta ni siquiera puede leer el ID aquí, el cableado o SPI sigue siendo la causa.
    print(f"Error general: {e}") 
    GPIO.cleanup()
