import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
from datetime import datetime
import os

# --- Configuración del Archivo de Registro ---
NOMBRE_ARCHIVO = "registro_matriculas.txt"

# Crea una instancia de la clase SimpleMFRC522
reader = SimpleMFRC522()

# --- Funciones ---

def registrar_lectura(id_tarjeta):
    """
    Guarda el ID de la tarjeta formateado como matrícula y la marca de tiempo en el archivo.
    
    NOTA IMPORTANTE: El ID original es un número largo (UID). Aquí se formatea 
    simplemente añadiéndole el prefijo 'S'. Si necesitas una conversión más compleja 
    (ej. mapear el UID a un número de 8 dígitos), se requiere una base de datos.
    """
    
    # 1. Aplicar el formato de Matrícula: Prefijamos con 'S'
    matricula_formato = f"S{id_tarjeta}"
    
    # 2. Obtiene la fecha y hora actual
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 3. Crea la línea de registro (Formato: Matrícula, Fecha, Hora)
    linea_registro = f"{matricula_formato}, {timestamp}\n"
    
    try:
        # Abre el archivo en modo "a" (append/añadir)
        with open(NOMBRE_ARCHIVO, 'a') as archivo:
            archivo.write(linea_registro)
        print(f"--> Registro de MATRÍCULA guardado en '{NOMBRE_ARCHIVO}'")
        
    except IOError as e:
        print(f"*** ERROR al escribir en el archivo '{NOMBRE_ARCHIVO}': {e}")
        
# --- Programa Principal ---

print("--- Lector de Matrículas NFC/RFID ---")
print(f"Los registros se guardarán en: {os.path.abspath(NOMBRE_ARCHIVO)}")
print("Formato de salida: S[UID de tarjeta], AAAA-MM-DD HH:MM:SS")
print("Coloca tu tarjeta cerca del lector...")
print("Presiona Ctrl+C para salir.")

try:
    while True:
        # read_id() obtiene el ID Único (UID) en formato numérico (entero grande)
        id_unico = reader.read_id()
        
        if id_unico:
            # Imprime la información detectada
            print("-" * 50)
            print(f"¡Tarjeta detectada a las {datetime.now().strftime('%H:%M:%S')}!")
            
            # 4. Formatear e imprimir antes de registrar
            matricula_a_mostrar = f"S{id_unico}"
            print(f"Matrícula (Formato S+UID): {matricula_a_mostrar}")
            
            # *** Llama a la función para guardar el registro ***
            registrar_lectura(id_unico)
            
            print("-" * 50)
            
            # Espera 3 segundos para evitar registrar la misma tarjeta repetidamente
            time.sleep(3) 

except KeyboardInterrupt:
    print("\nPrograma detenido por el usuario.")

finally:
    # Limpia los pines GPIO al finalizar
    GPIO.cleanup()
    print("Limpieza de GPIO completada.")
