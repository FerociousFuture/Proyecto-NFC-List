import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import csv
from datetime import datetime
import os
import sys

# --- Configuraciones de Archivos (TODOS CSV) ---
ARCHIVO_USUARIOS = "usuarios.csv"
ARCHIVO_ESTADOS = "estados.csv"       # Almacena el estado y la hora de la última ENTRADA
ARCHIVO_ACCESOS = "registro_accesos.csv" # Log de todos los eventos (ENTRADA/SALIDA)
ARCHIVO_TIEMPOS = "registro_tiempos.csv" # Log de permanencia (Entrada -> Salida)

# --- Estructuras Globales ---
USUARIOS = {}          # UID: {'nombre': '', 'matricula': ''}
ESTADOS_ACCESO = {}    # UID: {'estado': 'ENTRADA'/'SALIDA', 'ultima_entrada': 'YYYY-MM-DD HH:MM:SS'}

# Crea una instancia del lector
reader = SimpleMFRC522()

# ==============================================================================
# 1. GESTIÓN DE ARCHIVOS Y DATOS
# ==============================================================================

def inicializar_archivos():
    """Asegura que los archivos CSV existan y tengan encabezados."""
    
    # Definición de encabezados para los archivos CSV
    archivos_config = {
        ARCHIVO_USUARIOS: ['UID', 'Nombre', 'Matricula'],
        ARCHIVO_ESTADOS: ['UID', 'Estado', 'Ultima_Entrada_Timestamp'],
        ARCHIVO_ACCESOS: ['Timestamp', 'Matricula', 'Nombre', 'Evento'],
        # ¡ENCABEZADO MODIFICADO! Ahora incluye Horas, Minutos, Segundos separados
        ARCHIVO_TIEMPOS: ['Timestamp_Salida', 'Matricula', 'Nombre', 'Horas', 'Minutos', 'Segundos']
    }
    
    for nombre_archivo, encabezados in archivos_config.items():
        if not os.path.exists(nombre_archivo):
            with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(encabezados)

def cargar_datos():
    """Carga los usuarios y sus estados actuales de los CSV."""
    global USUARIOS, ESTADOS_ACCESO
    USUARIOS.clear()
    ESTADOS_ACCESO.clear()
    
    try:
        # Cargar USUARIOS.CSV
        with open(ARCHIVO_USUARIOS, mode='r', newline='', encoding='utf-8') as f:
            lector_csv = csv.reader(f)
            next(lector_csv) 
            for uid, nombre, matricula in lector_csv:
                try:
                    USUARIOS[int(uid)] = {'nombre': nombre.strip(), 'matricula': matricula.strip()}
                except ValueError:
                    continue

        # Cargar ESTADOS.CSV
        with open(ARCHIVO_ESTADOS, mode='r', newline='', encoding='utf-8') as f:
            lector_csv = csv.reader(f)
            next(lector_csv) 
            # El estado ahora tiene 3 columnas: UID, Estado, Ultima_Entrada_Timestamp
            for fila in lector_csv:
                if len(fila) >= 3:
                    uid, estado, timestamp = fila
                    try:
                        ESTADOS_ACCESO[int(uid)] = {'estado': estado.strip(), 'ultima_entrada': timestamp.strip()}
                    except ValueError:
                        continue
                    
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
            writer.writerow(['UID', 'Estado', 'Ultima_Entrada_Timestamp'])
            for uid, data in ESTADOS_ACCESO.items():
                writer.writerow([uid, data['estado'], data['ultima_entrada']])
    except Exception as e:
        print(f"*** ERROR al guardar estados: {e}")
        
def registrar_evento_acceso(datos_usuario, evento):
    """Guarda el evento (ENTRADA/SALIDA) en el log de accesos (CSV)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(ARCHIVO_ACCESOS, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, datos_usuario['matricula'], datos_usuario['nombre'], evento])
        print(f"   -> Evento {evento} REGISTRADO en '{ARCHIVO_ACCESOS}'")
    except IOError as e:
        print(f"*** ERROR al escribir en el archivo de accesos: {e}")

def registrar_tiempo_permanencia(datos_usuario, horas, minutos, segundos):
    """Guarda los componentes de tiempo en el log de tiempos (CSV)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(ARCHIVO_TIEMPOS, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Escribir la fila con los componentes de tiempo separados
            writer.writerow([timestamp, datos_usuario['matricula'], datos_usuario['nombre'], 
                             horas, minutos, segundos])
        print(f"   -> Tiempo de permanencia GUARDADO en '{ARCHIVO_TIEMPOS}'")
    except IOError as e:
        print(f"*** ERROR al escribir en el archivo de tiempos: {e}")

# ==============================================================================
# 2. FUNCIÓN DE REGISTRO (ALTA DE USUARIOS) - Se mantiene igual
# ==============================================================================

def registrar_usuario():
    """Interfaz para dar de alta un nuevo usuario."""
    print("\n" + "="*50)
    print("      MODO DE REGISTRO DE NUEVO USUARIO")
    print("="*50)
    print("PASO 1: Por favor, coloque la tarjeta cerca del lector para leer el ID.")

    try:
        uid_nuevo = reader.read_id()
        
        if uid_nuevo in USUARIOS:
            print(f"\n*** ERROR: La tarjeta ya está registrada.")
            print(f"   - UID: {uid_nuevo}")
            print(f"   - Usuario: {USUARIOS[uid_nuevo]['nombre']}")
            time.sleep(2)
            return

        print(f"\nTarjeta detectada. UID de Hardware: {uid_nuevo}")
        
        nombre = input("PASO 2: Ingrese el Nombre Completo del usuario: ").strip()
        matricula = input("PASO 3: Ingrese la Matrícula (ej: S22002198): ").strip()

        if not nombre or not matricula:
            print("*** Cancelado: Nombre o Matrícula no ingresados.")
            time.sleep(2)
            return
            
        with open(ARCHIVO_USUARIOS, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([uid_nuevo, nombre, matricula])
        
        USUARIOS[uid_nuevo] = {'nombre': nombre, 'matricula': matricula}
        # Inicializar el estado de este nuevo usuario
        ESTADOS_ACCESO[uid_nuevo] = {'estado': 'SALIDA', 'ultima_entrada': ''}
        guardar_estados()
        
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
# 3. FUNCIÓN DE CONTROL DE ACCESO (ENTRADA/SALIDA Y CÁLCULO)
# ==============================================================================

def calcular_permanencia(timestamp_entrada):
    """
    Calcula la diferencia entre la hora actual y la hora de entrada y 
    devuelve horas, minutos y segundos por separado.
    """
    try:
        # Convertir la cadena de entrada a objeto datetime
        dt_entrada = datetime.strptime(timestamp_entrada, "%Y-%m-%d %H:%M:%S")
        dt_salida = datetime.now()
        
        # Calcular la diferencia (timedelta object)
        diferencia = dt_salida - dt_entrada
        
        # Convertir a horas, minutos y segundos
        segundos_totales = int(diferencia.total_seconds())
        horas = segundos_totales // 3600
        minutos = (segundos_totales % 3600) // 60
        segundos = segundos_totales % 60
        
        return horas, minutos, segundos
        
    except Exception:
        return 0, 0, 0 # Devolver cero en caso de error

def iniciar_lector_control():
    """Función principal de lectura con lógica de Entrada/Salida y cálculo."""
    print("\n" + "="*50)
    print("     MODO CONTROL DE ACCESO (ENTRADA/SALIDA)")
    print(f"   {len(USUARIOS)} usuarios registrados. (Ctrl+C para Menú)")
    print("="*50)

    try:
        while True:
            print("\nEsperando tarjeta...")
            id_unico = reader.read_id()
            
            if id_unico:
                print("-" * 50)
                
                if id_unico in USUARIOS:
                    datos_usuario = USUARIOS[id_unico]
                    estado_data = ESTADOS_ACCESO.get(id_unico, {'estado': 'SALIDA', 'ultima_entrada': ''})
                    estado_anterior = estado_data['estado']
                    
                    datos_para_registro = {
                        "uid": id_unico,
                        "nombre": datos_usuario['nombre'],
                        "matricula": datos_usuario['matricula']
                    }

                    if estado_anterior == 'SALIDA':
                        # --- ENTRADA (Check-in) ---
                        nuevo_estado = 'ENTRADA'
                        tiempo_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        print(f"[{nuevo_estado}] Bienvenid@: {datos_usuario['nombre']}")
                        
                        # Actualizar estado y registrar hora de entrada
                        ESTADOS_ACCESO[id_unico] = {'estado': nuevo_estado, 'ultima_entrada': tiempo_actual}
                        registrar_evento_acceso(datos_para_registro, nuevo_estado)
                        
                    else:
                        # --- SALIDA (Check-out) ---
                        nuevo_estado = 'SALIDA'
                        timestamp_entrada = estado_data['ultima_entrada']
                        
                        print(f"[{nuevo_estado}] Hasta pronto: {datos_usuario['nombre']}")
                        
                        # Calcular y registrar el tiempo de permanencia
                        horas, minutos, segundos = calcular_permanencia(timestamp_entrada)
                        
                        if (horas + minutos + segundos) > 0:
                            print(f"   -> Permanencia: {horas} horas, {minutos} minutos, {segundos} segundos")
                            # Registrar los tres componentes de tiempo por separado
                            registrar_tiempo_permanencia(datos_para_registro, horas, minutos, segundos)
                        else:
                            print("   -> Permanencia registrada, pero la duración es mínima o inválida.")
                        
                        # Actualizar estado y borrar hora de entrada
                        ESTADOS_ACCESO[id_unico] = {'estado': nuevo_estado, 'ultima_entrada': ''}
                        registrar_evento_acceso(datos_para_registro, nuevo_estado)
                        
                    guardar_estados() # Guardar el estado actualizado

                else:
                    # TARJETA NO REGISTRADA
                    print(f"ACCESO DENEGADO. UID: {id_unico}")
                    print("-> Tarjeta NO registrada. Use la opción '1' para registrar.")
                
                print("-" * 50)
                time.sleep(3) 

    except KeyboardInterrupt:
        print("\nRegresando al menú principal...")
    except Exception as e:
        print(f"*** ERROR crítico en el lector: {e}")
    finally:
        pass

# ==============================================================================
# 4. FUNCIÓN MENÚ PRINCIPAL
# ==============================================================================

def menu_principal():
    """Muestra el menú de opciones."""
    while True:
        os.system('clear')
        print("\n" + "*"*50)
        print("      SISTEMA UNIFICADO DE ACCESO NFC/RFID")
        print("*"*50)
        print(f"Usuarios cargados: {len(USUARIOS)}")
        print(f"Registro de Tiempos en: {ARCHIVO_TIEMPOS}")
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