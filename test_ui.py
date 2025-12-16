import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time

# Crea una instancia de la clase SimpleMFRC522
reader = SimpleMFRC522()

print("--- Diagnóstico: Lectura de ID Único (UID) ---")
print("Coloca CUALQUIER tarjeta cerca del lector para ver su ID...")

try:
    while True:
        # read_id() lee solo el UID y bloquea el programa hasta que lo encuentra.
        # Es la forma más simple de verificar la comunicación SPI/Hardware.
        id_unico = reader.read_id()
        
        if id_unico:
            print("-" * 40)
            print(f"¡Hardware OK! ID Único detectado: {id_unico}")
            print("-" * 40)
            time.sleep(2) # Espera 2 segundos antes de volver a buscar
        
        # Nota: read_id() ya bloquea el programa, por lo que el sleep(0.1) anterior no es necesario.

except KeyboardInterrupt:
    print("\nPrograma detenido.")

finally:
    GPIO.cleanup()
    print("Limpieza de GPIO completada.")