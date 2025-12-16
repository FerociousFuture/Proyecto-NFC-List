import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import csv
from datetime import datetime
import os
import sys

# --- Configuraciones de Archivos ---
ARCHIVO_USUARIOS = "usuarios.csv"
ARCHIVO_ESTADOS = "estados.csv"
ARCHIVO_REGISTRO = "registro_accesos.txt"

# --- Estructuras Globales ---
USUARIOS = {} # UID: {'nombre': '', 'matricula': ''}
ESTADOS_ACCESO = {} # UID: 'ENTRADA' o 'SALIDA'

# Crea una instancia del lector
reader = SimpleMFRC522()

# ==============================================================================
# 1. GESTIÓN DE ARCHIVOS
# ==============================================================================

def inicializar_archivos():
    """Asegura que los archivos existan y tengan encabezados."""
    
    # Inicializar USUARIOS.CSV
    if not os.path.exists(ARCHIVO_USUARIOS):
        with open(ARCHIVO_USUARIOS, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['UID', 'Nombre', 'Matricula'])
    
    # Inicializar ESTADOS.CSV
    if not os.path.exists(ARCHIVO_ESTADOS):
        with open(ARCHIVO_ESTADOS, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['UID', 'Estado'])
            
    # Inicializar REGISTRO_ACCESOS.TXT
    if not os.path.exists(ARCHIVO_REGISTRO):
        with open(ARCHIVO_REGISTRO, 'w') as f:
            f.write("Timestamp,Matricula,Nombre,Evento\n")
            
def cargar_datos():
    """Carga los usuarios y sus estados actuales de los CSV."""
    global USUARIOS, ESTADOS_ACCESO
    USUARIOS.clear()
    ESTADOS_ACCESO.clear()
    
    try:
        # Cargar USUARIOS.CSV
        with open(ARCHIVO_USUARIOS, mode='r', newline='', encoding='utf-8') as f:
            lector_csv = csv.reader(f)
            next(lector_csv) # Saltar encabezados
            for uid, nombre, matricula in lector_csv:
                try:
                    USUARIOS[int(uid)] = {'nombre': nombre.strip(), 'matricula': matricula.strip()}
                except ValueError:
                    print(f"UID inválido en usuarios.csv: {uid}. Saltando.")

        # Cargar ESTADOS.CSV
        with open(ARCHIVO_ESTADOS, mode='r', newline='', encoding='utf-8') as f:
            lector_csv = csv.reader(f)
            next(lector_csv) # Saltar encabezados
            for uid, estado in lector_csv:
                try:
                    ESTADOS_ACCESO[int(uid)] = estado.strip()
                except ValueError:
                    print(f"UID inválido en estados.csv: {uid}. Saltando.")
                    
        print(f"Sistema inicializado: {len(USUARIOS)} usuarios cargados.")
        return True
    
    except Exception as e:
        print(f"*** ERROR al cargar datos: {e}")
        return False

def guardar_estados():
    """Guarda el diccionario ESTADOS_ACCESO al archivo ESTADOS.CSV."""
    try:
        with open(ARCHIVO_ESTADOS, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['UID', 'Estado'])
            for uid, estado in ESTADOS_ACCESO.items():
                writer.writerow([uid, estado])
    except Exception as e:
        print(f"*** ERROR al guardar estados: {e}")
        
def registrar_evento(datos_usuario, evento):
    """Guarda el evento (ENTRADA/SALIDA) en el log de accesos."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    linea_registro = f"{timestamp},{datos_usuario['matricula']},{datos_usuario['nombre']},{evento}\n"
    
    try:
        with open(ARCHIVO_REGISTRO, 'a') as f:
            f.write(linea_registro)
        print(f"   -> Evento {evento} REGISTRADO en '{ARCHIVO_REGISTRO}'")
    except IOError as e:
        print(f"*** ERROR al escribir en el archivo de registro: {e}")

# ==============================================================================
# 2. FUNCIÓN DE REGISTRO (ALTA DE USUARIOS)
# ==============================================================================

def registrar_usuario():
    """
    Función de Interfaz para dar de alta un nuevo usuario.
    Lee el UID de la tarjeta y pide los datos.
    """
    print("\n" + "="*50)
    print("      MODO DE REGISTRO DE NUEVO USUARIO")
    print("="*50)
    print("PASO 1: Por favor, coloque la tarjeta cerca del lector para leer el ID.")

    try:
        # read_id() bloquea hasta que detecta una tarjeta
        uid_nuevo = reader.read_id()
        
        if uid_nuevo in USUARIOS:
            print(f"\n*** ERROR: La tarjeta ya está registrada.")
            print(f"   - UID: {uid_nuevo}")
            print(f"   - Usuario: {USUARIOS[uid_nuevo]['nombre']}")
            time.sleep(2)
            return

        print(f"\nTarjeta detectada. UID de Hardware: {uid_nuevo}")
        
        # PASO 2: Pedir datos al usuario
        nombre = input("PASO 2: Ingrese el Nombre Completo del usuario: ").strip()
        matricula = input("PASO 3: Ingrese la Matrícula (ej: S22002198): ").strip()

        if not nombre or not matricula:
            print("*** Cancelado: Nombre o Matrícula no ingresados.")
            time.sleep(2)
            return
            
        # PASO 3: Guardar en USUARIOS.CSV y actualizar el diccionario en memoria
        with open(ARCHIVO_USUARIOS, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([uid_nuevo, nombre, matricula])
        
        # Actualizar la estructura global
        USUARIOS[uid_nuevo] = {'nombre': nombre, 'matricula': matricula}
        
        print("\n" + "#"*50)
        print(f"¡USUARIO '{nombre}' REGISTRADO CON ÉXITO!")
        print(f"Matrícula: {matricula}")
        print("#"*50)
        time.sleep(3)

    except KeyboardInterrupt:
        print("\nRegistro cancelado.")
    except Exception as e:
        print(f"\nError en el registro: {e}")

# ==============================================================================
# 3. FUNCIÓN DE CONTROL DE ACCESO (ENTRADA/SALIDA)
# ==============================================================================

def iniciar_lector_control():
    """
    Función principal de lectura de tarjetas con lógica de Entrada/Salida.
    """
    print("\n" + "="*50)
    print("     MODO CONTROL DE ACCESO (ENTRADA/SALIDA)")
    print(f"   {len(USUARIOS)} usuarios registrados. (Ctrl+C para Menú)")
    print("="*50)

    try:
        while True:
            print("\nEsperando tarjeta...")
            # read_id() bloquea hasta que detecta una tarjeta
            id_unico = reader.read_id()
            
            if id_unico:
                print("-" * 50)
                
                # 1. COMPROBAR SI EL USUARIO EXISTE
                if id_unico in USUARIOS:
                    datos_usuario = USUARIOS[id_unico]
                    estado_anterior = ESTADOS_ACCESO.get(id_unico, 'SALIDA') # Estado por defecto si es nuevo
                    
                    # 2. DETERMINAR EL NUEVO ESTADO (Lógica ENTRADA/SALIDA)
                    if estado_anterior == 'SALIDA':
                        nuevo_estado = 'ENTRADA'
                        print(f"[{nuevo_estado}] Bienvenid@: {datos_usuario['nombre']}")
                    else:
                        nuevo_estado = 'SALIDA'
                        print(f"[{nuevo_estado}] Hasta pronto: {datos_usuario['nombre']}")
                        
                    # 3. REGISTRAR Y ACTUALIZAR DATOS
                    
                    # Log al archivo de registro (txt)
                    registrar_evento(datos_usuario, nuevo_estado)
                    
                    # Actualizar estado en memoria y en el archivo de estados (csv)
                    ESTADOS_ACCESO[id_unico] = nuevo_estado
                    guardar_estados()
                    
                else:
                    # ACCESO DENEGADO (Tarjeta no registrada)
                    print(f"ACCESO DENEGADO. UID: {id_unico}")
                    print("-> Tarjeta NO registrada. Use la opción '1' para registrar.")
                
                print("-" * 50)
                
                # Esperar 3 segundos para evitar doble lectura
                time.sleep(3) 

    except KeyboardInterrupt:
        print("\nRegresando al menú principal...")
    except Exception as e:
        print(f"*** ERROR crítico en el lector: {e}")
    finally:
        pass # La limpieza de GPIO se hace al salir del programa completo.

# ==============================================================================
# 4. FUNCIÓN MENÚ PRINCIPAL
# ==============================================================================

def menu_principal():
    """Muestra el menú de opciones."""
    while True:
        os.system('clear') # Limpia la consola (funciona en Linux/Raspbian)
        print("\n" + "*"*50)
        print("      SISTEMA UNIFICADO DE ACCESO NFC/RFID")
        print("*"*50)
        print(f"Usuarios cargados: {len(USUARIOS)}")
        print(f"Archivo de logs: {ARCHIVO_REGISTRO}")
        print("\nOpciones:")
        print(" [1] -> REGISTRAR NUEVO USUARIO (Alta de Tarjeta)")
        print(" [2] -> INICIAR LECTOR DE ACCESO (Entrada/Salida)")
        print(" [3] -> Salir del Programa")
        print("-" * 50)
        
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == '1':
            registrar_usuario()
        elif opcion == '2':
            iniciar_lector_control()
        elif opcion == '3':
            print("Saliendo del programa. ¡Hasta pronto!")
            break
        else:
            print("*** Opción no válida. Intente de nuevo.")
            time.sleep(1)

# ==============================================================================
# INICIO DEL PROGRAMA
# ==============================================================================

if __name__ == '__main__':
    try:
        inicializar_archivos()
        cargar_datos()
        menu_principal()
        
    except Exception as e:
        print(f"\n[ERROR CRÍTICO] El programa ha fallado: {e}")
        
    finally:
        GPIO.cleanup()
        print("Limpieza de pines GPIO y salida final.")