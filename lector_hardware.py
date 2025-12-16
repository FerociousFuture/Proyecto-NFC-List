import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import csv
import os

# --- Configuración ---
ARCHIVO_USUARIOS = "usuarios.csv"
USUARIOS = {} # Diccionario para almacenar los usuarios (UID será la clave)

# Crea una instancia de la clase SimpleMFRC522
reader = SimpleMFRC522()

# --- Funciones ---

def cargar_usuarios():
    """Carga los datos del CSV en el diccionario USUARIOS."""
    print(f"Cargando usuarios desde: {ARCHIVO_USUARIOS}...")
    
    if not os.path.exists(ARCHIVO_USUARIOS):
        print(f"*** ERROR: El archivo '{ARCHIVO_USUARIOS}' no existe.")
        print("Asegúrate de crearlo con los datos de UID y Nombre.")
        return False
        
    try:
        with open(ARCHIVO_USUARIOS, mode='r', newline='', encoding='utf-8') as archivo:
            lector_csv = csv.reader(archivo)
            next(lector_csv) # Saltar la fila de encabezados (UID,Nombre,Matricula)
            
            for fila in lector_csv:
                # La fila es: [UID, Nombre, Matricula]
                if len(fila) >= 2:
                    # El UID debe ser la clave y lo convertimos a INT para la comparación
                    try:
                        uid_key = int(fila[0].strip())
                        USUARIOS[uid_key] = {
                            "nombre": fila[1].strip(),
                            "matricula": fila[2].strip() if len(fila) > 2 else "N/A"
                        }
                    except ValueError:
                        print(f"*** ADVERTENCIA: UID no válido en la fila: {fila[0]}. Ignorando.")
                        
        print(f"Carga completa. {len(USUARIOS)} usuarios registrados.")
        return True
        
    except Exception as e:
        print(f"*** ERROR al leer el CSV: {e}")
        return False

# --- Programa Principal ---

# Intentar cargar los usuarios al inicio del programa
if not cargar_usuarios():
    print("El programa se cerrará. Resuelve el error de archivo CSV.")
    GPIO.cleanup()
    exit()

print("\n--- Lector de Identificación NFC/RFID ---")
print("Coloca tu tarjeta cerca del lector...")
print("Presiona Ctrl+C para salir.")

try:
    while True:
        # read_id() lee SOLO el ID Único (UID) en formato de número entero.
        id_unico = reader.read_id()
        
        if id_unico:
            print("-" * 50)
            print(f"Tarjeta detectada. UID: {id_unico}")
            
            # 1. Buscar el UID en el diccionario de usuarios
            if id_unico in USUARIOS:
                # 2. Si se encuentra, imprimir los datos del usuario
                datos_usuario = USUARIOS[id_unico]
                
                print("ACCESO CONCEDIDO")
                print(f"-> Nombre: {datos_usuario['nombre']}")
                print(f"-> Matrícula: {datos_usuario['matricula']}")
                
            else:
                # 3. Si no se encuentra, denegar el acceso
                print("ACCESO DENEGADO")
                print(f"-> Tarjeta NO registrada en el sistema.")
            
            print("-" * 50)
            
            # Esperar 3 segundos para evitar la re-lectura instantánea
            time.sleep(3) 

except KeyboardInterrupt:
    print("\nPrograma detenido por el usuario.")

finally:
    # Limpia los pines GPIO al finalizar
    GPIO.cleanup()
    print("Limpieza de GPIO completada.")
