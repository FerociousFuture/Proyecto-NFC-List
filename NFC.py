import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time

# Crea una instancia de la clase SimpleMFRC522
reader = SimpleMFRC522()

print("Coloca tu tarjeta o etiqueta RFID cerca del lector...")
print("Presiona Ctrl+C para salir.")

try:
    while True:
        # El método read() bloquea la ejecución hasta que se detecta una etiqueta.
        # Devuelve el ID de la tarjeta y el texto que contiene (si lo hay).
        id, text = reader.read()
        
        # Imprime la información detectada
        print("-" * 30)
        print("Tarjeta detectada")
        print(f"ID de la tarjeta: {id}")
        
        # Verifica si hay texto almacenado y lo imprime
        if text and text.strip():
            print(f"Texto almacenado: '{text.strip()}'")
        else:
            print("No hay texto almacenado en esta sección.")
            
        print("-" * 30)
        
        # Espera un breve período para evitar lecturas continuas rápidas
        time.sleep(1) 

except KeyboardInterrupt:
    # Se ejecuta cuando se presiona Ctrl+C
    print("\nPrograma detenido por el usuario.")

finally:
    # Limpia los pines GPIO al finalizar
    GPIO.cleanup()
    print("Limpieza de GPIO completada.")
