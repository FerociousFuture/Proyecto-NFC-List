import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
from datetime import datetime
import os

# --- Configuración del Archivo de Registro ---
NOMBRE_ARCHIVO = "registro_uid.txt"

# Crea una instancia de la clase SimpleMFRC522
reader = SimpleMFRC522()

# --- Funciones ---

def registrar_lectura(id_tarjeta):
    """Guarda el UID de la tarjeta y la marca de tiempo en el archivo."""
    
    # 1. Obtiene la fecha y hora actual
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 2. Crea la línea de registro (Formato simple: ID, Fecha, Hora)
    linea_registro = f"{id_tarjeta}, {timestamp}\n"
    
    try:
        # Abre el archivo en modo "a" (append/añadir) para agregar al final
        with open(NOMBRE_ARCHIVO, 'a') as archivo:
            archivo.write(linea_registro)
        print(f"--> Registro guardado en '{NOMBRE_ARCHIVO}'")
        
    except IOError as e:
        print(f"*** ERROR al escribir en el archivo '{NOMBRE_ARCHIVO}': {e}")
        
# --- Programa Principal ---

print("--- Lector de ID Único (UID) MFRC522 ---")
print(f"Los registros se guardarán en: {os.path.abspath(NOMBRE_ARCHIVO)}")
print("Coloca tu tarjeta cerca del lector...")
print("Presiona Ctrl+C para salir.")

try:
    while True:
        # read_id() lee SOLO el ID ÚNICO de la tarjeta (UID) y bloquea la ejecución.
        # No intenta autenticarse ni leer memoria, evitando el AUTH ERROR.
        id_unico = reader.read_id()
        
        if id_unico:
            # Imprime la información detectada
            print("-" * 50)
            print(f"¡Tarjeta detectada a las {datetime.now().strftime('%H:%M:%S')}!")
            print(f"ID Único de la tarjeta (UID): {id_unico}")
            
            # *** Llama a la función para guardar el registro ***
            registrar_lectura(id_unico)
            
            print("-" * 50)
            
            # Espera un período largo para evitar registrar la misma tarjeta muchas veces
            time.sleep(3) 

except KeyboardInterrupt:
    print("\nPrograma detenido por el usuario.")

finally:
    # Limpia los pines GPIO al finalizar
    GPIO.cleanup()
    print("Limpieza de GPIO completada.")