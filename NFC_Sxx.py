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

def registrar_lectura(matricula_leida):
    """Guarda la matrícula leída y la marca de tiempo en el archivo."""
    
    # 1. Obtiene la fecha y hora actual
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 2. Crea la línea de registro (Formato: Matrícula, Fecha, Hora)
    # Usamos strip() para limpiar cualquier espacio extra que la tarjeta pueda tener.
    linea_registro = f"{matricula_leida.strip()}, {timestamp}\n"
    
    try:
        # Abre el archivo en modo "a" (append/añadir)
        with open(NOMBRE_ARCHIVO, 'a') as archivo:
            archivo.write(linea_registro)
        print(f"--> Registro de MATRÍCULA guardado en '{NOMBRE_ARCHIVO}'")
        
    except IOError as e:
        print(f"*** ERROR al escribir en el archivo '{NOMBRE_ARCHIVO}': {e}")
        
# --- Programa Principal ---

print("--- Lector de Matrículas NFC (Texto Plano) ---")
print(f"Los registros se guardarán en: {os.path.abspath(NOMBRE_ARCHIVO)}")
print("Formato de salida: SNNNNNNNN, AAAA-MM-DD HH:MM:SS")
print("Coloca tu tarjeta cerca del lector...")
print("Presiona Ctrl+C para salir.")

try:
    # Usaremos un set para almacenar las matrículas vistas y evitar spam en el registro
    matriculas_vistas = set()
    
    while True:
        # read() lee el ID Único (UID) y el TEXTO de la memoria.
        # Aquí, el texto_leido es "S22002198"
        id_unico, texto_leido = reader.read()
        
        # Limpiamos el texto
        matricula_leida = texto_leido.strip()
        
        if matricula_leida:
            # Se usa el UID y el texto como una clave combinada para evitar doble registro
            registro_clave = f"{id_unico}:{matricula_leida}"
            
            if registro_clave not in matriculas_vistas:
                # 1. Imprime la información detectada
                print("-" * 50)
                print(f"¡Tarjeta detectada a las {datetime.now().strftime('%H:%M:%S')}!")
                print(f"MATRÍCULA LEÍDA: {matricula_leida}")
                
                # 2. Llama a la función para guardar el registro
                registrar_lectura(matricula_leida)
                
                print("-" * 50)
                
                # Agregamos a la lista de vistas y luego esperamos un momento
                matriculas_vistas.add(registro_clave)

        # Si el texto es nulo, significa que la tarjeta no está en el lector.
        # Esto permite que la matrícula_vistas se limpie lentamente al retirar la tarjeta.
        else:
            # Pequeña pausa para evitar sobrecargar la CPU
            time.sleep(0.1)

except KeyboardInterrupt:
    print("\nPrograma detenido por el usuario.")

finally:
    # Limpia los pines GPIO al finalizar
    GPIO.cleanup()
    print("Limpieza de GPIO completada.")