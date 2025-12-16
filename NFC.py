#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de Registro NFC con MFRC522 para Raspberry Pi 4
Requiere: pip3 install mfrc522 spidev
"""

import json
from datetime import datetime
import os
import signal
import sys
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import time

class RegistroNFC:
    def __init__(self, archivo='registros.json'):
        self.archivo = archivo
        self.registros = self.cargar_registros()
        self.ultima_lectura = None
        self.tiempo_ultima_lectura = 0
        self.tiempo_cooldown = 3  # segundos entre lecturas de la misma tarjeta
        
        # Inicializar lector con configuración mejorada
        try:
            GPIO.setwarnings(False)
            self.reader = SimpleMFRC522()
            print("✓ Lector MFRC522 inicializado correctamente")
        except Exception as e:
            print(f"✗ Error al inicializar lector: {e}")
            print("Verifica las conexiones SPI")
            sys.exit(1)
    
    def cargar_registros(self):
        """Carga registros existentes del archivo"""
        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def guardar_registros(self):
        """Guarda registros en el archivo"""
        try:
            with open(self.archivo, 'w', encoding='utf-8') as f:
                json.dump(self.registros, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"✗ Error al guardar: {e}")
    
    def escribir_tarjeta(self, id_persona, nombre, tipo='E'):
        """
        Escribe datos en la tarjeta NFC
        """
        try:
            datos = json.dumps({
                'i': id_persona,
                'n': nombre,
                't': tipo
            }, ensure_ascii=False)
            
            # Verificar tamaño
            tamaño = len(datos.encode('utf-8'))
            if tamaño > 130:
                print(f"✗ Error: Datos muy grandes ({tamaño} bytes). Máximo 130 bytes")
                print("Intenta con un nombre más corto")
                return False
            
            print(f"\n📝 Datos a escribir: {datos} ({tamaño} bytes)")
            print("🔄 Acerca la tarjeta al lector...")
            print("(Mantenla cerca hasta que termine)")
            
            # Intentar escribir con reintentos
            max_intentos = 3
            for intento in range(max_intentos):
                try:
                    self.reader.write(datos)
                    print("\n✓ ¡Tarjeta escrita exitosamente!")
                    time.sleep(1)
                    
                    # Verificar escritura
                    print("🔍 Verificando escritura...")
                    time.sleep(0.5)
                    _, texto_leido = self.reader.read_no_block()
                    if texto_leido and texto_leido.strip() == datos:
                        print("✓ Verificación exitosa")
                        return True
                    else:
                        print("⚠️  Advertencia: No se pudo verificar, pero probablemente esté escrita")
                        return True
                        
                except Exception as e:
                    if intento < max_intentos - 1:
                        print(f"⚠️  Intento {intento + 1} falló, reintentando...")
                        time.sleep(1)
                    else:
                        print(f"✗ Error al escribir después de {max_intentos} intentos")
                        return False
            
            return False
            
        except Exception as e:
            print(f"✗ Error al escribir tarjeta: {e}")
            return False
    
    def leer_tarjeta_segura(self):
        """Lee datos de la tarjeta NFC con manejo de errores mejorado"""
        try:
            # Usar read_no_block para evitar bloqueos
            id_tarjeta, texto = self.reader.read_no_block()
            
            if id_tarjeta and texto:
                texto = texto.strip()
                
                # Evitar lecturas duplicadas rápidas
                tiempo_actual = time.time()
                if (self.ultima_lectura == id_tarjeta and 
                    tiempo_actual - self.tiempo_ultima_lectura < self.tiempo_cooldown):
                    return None, None
                
                self.ultima_lectura = id_tarjeta
                self.tiempo_ultima_lectura = tiempo_actual
                
                return id_tarjeta, texto
            
            return None, None
            
        except Exception as e:
            # Ignorar errores de lectura comunes
            if "AUTH ERROR" not in str(e):
                print(f"⚠️  Error de lectura: {e}")
            return None, None
    
    def registrar_acceso(self, datos_nfc, accion='entrada'):
        """Registra entrada o salida de una persona"""
        try:
            # Parsear datos del NFC
            persona = json.loads(datos_nfc)
            
            # Validar campos requeridos
            if 'i' not in persona or 'n' not in persona:
                print("✗ Error: Tarjeta sin formato válido")
                return False
            
            # Crear registro
            registro = {
                'id': persona['i'],
                'nombre': persona['n'],
                'tipo': persona.get('t', 'E'),
                'accion': accion,
                'timestamp': datetime.now().isoformat(),
                'fecha': datetime.now().strftime('%Y-%m-%d'),
                'hora': datetime.now().strftime('%H:%M:%S')
            }
            
            self.registros.append(registro)
            self.guardar_registros()
            
            # Mostrar confirmación visual
            simbolo = "📥" if accion == 'entrada' else "📤"
            print(f"\n{'='*60}")
            print(f"{simbolo} {accion.upper()}: {persona['n']}")
            print(f"   ID: {persona['i']} | Tipo: {persona.get('t', 'E')}")
            print(f"   Fecha: {registro['fecha']} | Hora: {registro['hora']}")
            print(f"{'='*60}\n")
            return True
            
        except json.JSONDecodeError:
            print("✗ Error: Datos NFC con formato JSON inválido")
            return False
        except Exception as e:
            print(f"✗ Error al registrar: {e}")
            return False
    
    def obtener_estado_actual(self):
        """Obtiene quién está actualmente dentro"""
        personas_dentro = {}
        
        for registro in self.registros:
            id_persona = registro['id']
            if registro['accion'] == 'entrada':
                personas_dentro[id_persona] = registro
            elif registro['accion'] == 'salida' and id_persona in personas_dentro:
                del personas_dentro[id_persona]
        
        return list(personas_dentro.values())
    
    def determinar_accion(self, id_persona):
        """Determina si la próxima acción debe ser entrada o salida"""
        registros_persona = [r for r in self.registros if r['id'] == id_persona]
        
        if not registros_persona:
            return 'entrada'
        
        ultimo = registros_persona[-1]
        return 'salida' if ultimo['accion'] == 'entrada' else 'entrada'
    
    def contar_entradas_salidas(self, fecha=None):
        """Cuenta entradas y salidas por fecha"""
        if fecha is None:
            fecha = datetime.now().strftime('%Y-%m-%d')
        
        registros_dia = [r for r in self.registros if r['fecha'] == fecha]
        
        entradas = sum(1 for r in registros_dia if r['accion'] == 'entrada')
        salidas = sum(1 for r in registros_dia if r['accion'] == 'salida')
        
        return {'fecha': fecha, 'entradas': entradas, 'salidas': salidas}
    
    def mostrar_resumen(self):
        """Muestra resumen del día actual"""
        stats = self.contar_entradas_salidas()
        dentro = self.obtener_estado_actual()
        
        print("\n" + "="*60)
        print(f"📊 RESUMEN DEL DÍA - {stats['fecha']}")
        print("="*60)
        print(f"📥 Entradas totales: {stats['entradas']}")
        print(f"📤 Salidas totales: {stats['salidas']}")
        print(f"👥 Personas dentro actualmente: {len(dentro)}")
        
        if dentro:
            print("\n🏢 Personas dentro:")
            for p in dentro:
                print(f"  • {p['nombre']} (ID: {p['id']}) - Entrada: {p['hora']}")
        print("="*60 + "\n")
    
    def buscar_por_id(self, id_persona):
        """Busca todos los registros de una persona por ID"""
        return [r for r in self.registros if r['id'] == id_persona]
    
    def limpiar(self):
        """Limpia recursos GPIO"""
        try:
            GPIO.cleanup()
        except:
            pass


def menu_principal():
    """Muestra el menú principal"""
    print("\n" + "="*60)
    print("🔐 SISTEMA DE REGISTRO NFC - MFRC522")
    print("="*60)
    print("1. 🔄 Modo Registro (lectura automática)")
    print("2. ✍️  Escribir nueva tarjeta")
    print("3. 📊 Ver resumen del día")
    print("4. 🔍 Buscar por ID")
    print("5. 🧪 Test del lector")
    print("6. 🚪 Salir")
    print("="*60)


def modo_registro(sistema):
    """Modo de registro continuo"""
    print("\n" + "="*60)
    print("🔄 MODO REGISTRO ACTIVADO")
    print("="*60)
    print("✓ Acerca tarjetas NFC para registrar entrada/salida")
    print("✓ Presiona Ctrl+C para volver al menú")
    print("✓ Espera 3 segundos entre lecturas de la misma tarjeta")
    print("="*60 + "\n")
    
    intentos_sin_tarjeta = 0
    
    try:
        while True:
            id_tarjeta, datos = sistema.leer_tarjeta_segura()
            
            if id_tarjeta and datos:
                intentos_sin_tarjeta = 0
                print(f"📱 Tarjeta detectada (ID: {id_tarjeta})")
                
                try:
                    persona = json.loads(datos)
                    accion = sistema.determinar_accion(persona['i'])
                    sistema.registrar_acceso(datos, accion)
                except json.JSONDecodeError:
                    print("✗ Tarjeta con formato incorrecto")
                    print(f"   Contenido: {datos[:50]}...")
                except Exception as e:
                    print(f"✗ Error: {e}")
            else:
                intentos_sin_tarjeta += 1
                if intentos_sin_tarjeta % 20 == 0:  # Cada ~2 segundos
                    print("⏳ Esperando tarjeta...", end='\r')
            
            time.sleep(0.1)  # Pequeña pausa para no saturar
            
    except KeyboardInterrupt:
        print("\n\n✓ Volviendo al menú...")


def modo_escritura(sistema):
    """Modo para escribir nuevas tarjetas"""
    print("\n" + "="*60)
    print("✍️  ESCRIBIR NUEVA TARJETA")
    print("="*60)
    
    id_persona = input("ID (8 dígitos): ").strip()
    if len(id_persona) != 8 or not id_persona.isdigit():
        print("✗ El ID debe tener exactamente 8 dígitos")
        return
    
    nombre = input("Nombre completo: ").strip()
    if len(nombre) < 3:
        print("✗ El nombre es muy corto")
        return
    
    print("\nTipo de persona:")
    print("  E - Empleado")
    print("  V - Visitante")
    print("  A - Administrador")
    tipo = input("Tipo (E/V/A): ").strip().upper() or 'E'
    
    if tipo not in ['E', 'V', 'A']:
        print("✗ Tipo no válido, usando 'E' por defecto")
        tipo = 'E'
    
    print()
    sistema.escribir_tarjeta(id_persona, nombre, tipo)


def test_lector(sistema):
    """Prueba básica del lector"""
    print("\n" + "="*60)
    print("🧪 TEST DEL LECTOR MFRC522")
    print("="*60)
    print("Acerca una tarjeta NFC...")
    print("Presiona Ctrl+C para cancelar\n")
    
    try:
        while True:
            id_tarjeta, texto = sistema.leer_tarjeta_segura()
            if id_tarjeta:
                print(f"\n✓ ¡Tarjeta detectada!")
                print(f"   ID: {id_tarjeta}")
                print(f"   Contenido: {texto if texto else '(vacío)'}")
                print(f"   Longitud: {len(texto) if texto else 0} caracteres\n")
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n✓ Test cancelado")


def signal_handler(sig, frame):
    """Maneja la señal de interrupción"""
    print("\n\n👋 Cerrando sistema...")
    GPIO.cleanup()
    sys.exit(0)


if __name__ == "__main__":
    # Configurar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\n🚀 Iniciando sistema...")
    sistema = RegistroNFC()
    
    try:
        while True:
            menu_principal()
            opcion = input("\nSelecciona una opción: ").strip()
            
            if opcion == '1':
                modo_registro(sistema)
            
            elif opcion == '2':
                modo_escritura(sistema)
            
            elif opcion == '3':
                sistema.mostrar_resumen()
                input("\nPresiona Enter para continuar...")
            
            elif opcion == '4':
                id_buscar = input("\nID a buscar: ").strip()
                registros = sistema.buscar_por_id(id_buscar)
                if registros:
                    print(f"\n📋 Registros encontrados: {len(registros)}")
                    print("-" * 60)
                    for r in registros[-10:]:
                        print(f"{r['fecha']} {r['hora']} - {r['accion'].upper()}: {r['nombre']}")
                else:
                    print("✗ No se encontraron registros")
                input("\nPresiona Enter para continuar...")
            
            elif opcion == '5':
                test_lector(sistema)
                input("\nPresiona Enter para continuar...")
            
            elif opcion == '6':
                print("\n👋 Cerrando sistema...")
                break
            
            else:
                print("✗ Opción no válida")
    
    except KeyboardInterrupt:
        print("\n\n👋 Sistema interrumpido")
    
    finally:
        sistema.limpiar()
        print("✓ Recursos liberados. ¡Adiós!")