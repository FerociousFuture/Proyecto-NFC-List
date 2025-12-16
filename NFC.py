
"""
Sistema de Registro NFC con MFRC522 para Raspberry Pi 4
Requiere: pip3 install mfrc522 spidev
"""

import json
from datetime import datetime
import os
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

class RegistroNFC:
    def __init__(self, archivo='registros.json'):
        self.archivo = archivo
        self.registros = self.cargar_registros()
        self.reader = SimpleMFRC522()
        print("✓ Lector MFRC522 inicializado")
    
    def cargar_registros(self):
        """Carga registros existentes del archivo"""
        if os.path.exists(self.archivo):
            with open(self.archivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def guardar_registros(self):
        """Guarda registros en el archivo"""
        with open(self.archivo, 'w', encoding='utf-8') as f:
            json.dump(self.registros, f, indent=2, ensure_ascii=False)
    
    def escribir_tarjeta(self, id_persona, nombre, tipo='E'):
        """
        Escribe datos en la tarjeta NFC
        id_persona: ID único (ej: "12345678")
        nombre: Nombre completo
        tipo: E=Empleado, V=Visitante, etc.
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
                return False
            
            print(f"\nAcerca la tarjeta para escribir...")
            print(f"Datos: {datos} ({tamaño} bytes)")
            
            self.reader.write(datos)
            print("✓ Tarjeta escrita exitosamente")
            return True
            
        except Exception as e:
            print(f"✗ Error al escribir tarjeta: {e}")
            return False
    
    def leer_tarjeta(self):
        """Lee datos de la tarjeta NFC"""
        try:
            print("Esperando tarjeta NFC...")
            id_tarjeta, texto = self.reader.read()
            
            if texto:
                texto = texto.strip()
                print(f"✓ Tarjeta detectada (ID: {id_tarjeta})")
                return texto
            return None
            
        except Exception as e:
            print(f"✗ Error al leer tarjeta: {e}")
            return None
    
    def registrar_acceso(self, datos_nfc, accion='entrada'):
        """
        Registra entrada o salida de una persona
        datos_nfc: string JSON del NFC
        accion: 'entrada' o 'salida'
        """
        try:
            # Parsear datos del NFC
            persona = json.loads(datos_nfc)
            
            # Crear registro
            registro = {
                'id': persona['i'],
                'nombre': persona['n'],
                'tipo': persona['t'],
                'accion': accion,
                'timestamp': datetime.now().isoformat(),
                'fecha': datetime.now().strftime('%Y-%m-%d'),
                'hora': datetime.now().strftime('%H:%M:%S')
            }
            
            self.registros.append(registro)
            self.guardar_registros()
            
            print(f"\n{'='*50}")
            print(f"✓ {accion.upper()}: {persona['n']}")
            print(f"  ID: {persona['i']} | Tipo: {persona['t']}")
            print(f"  Fecha: {registro['fecha']} | Hora: {registro['hora']}")
            print(f"{'='*50}\n")
            return True
            
        except json.JSONDecodeError:
            print("✗ Error: Datos NFC inválidos")
            return False
        except KeyError as e:
            print(f"✗ Error: Falta el campo {e}")
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
        # Buscar último registro de esta persona
        registros_persona = [r for r in self.registros if r['id'] == id_persona]
        
        if not registros_persona:
            return 'entrada'  # Primera vez
        
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
        print(f"RESUMEN DEL DÍA - {stats['fecha']}")
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
        GPIO.cleanup()


def menu_principal():
    """Muestra el menú principal"""
    print("\n" + "="*60)
    print("SISTEMA DE REGISTRO NFC - MFRC522")
    print("="*60)
    print("1. Modo Registro (lectura automática)")
    print("2. Escribir nueva tarjeta")
    print("3. Ver resumen del día")
    print("4. Buscar por ID")
    print("5. Salir")
    print("="*60)


def modo_registro(sistema):
    """Modo de registro continuo"""
    print("\n🔄 MODO REGISTRO ACTIVADO")
    print("Acerca tarjetas NFC para registrar entrada/salida")
    print("Presiona Ctrl+C para volver al menú\n")
    
    try:
        while True:
            datos = sistema.leer_tarjeta()
            if datos:
                try:
                    persona = json.loads(datos)
                    # Determinar automáticamente si es entrada o salida
                    accion = sistema.determinar_accion(persona['i'])
                    sistema.registrar_acceso(datos, accion)
                except:
                    print("✗ Tarjeta con formato incorrecto\n")
            
    except KeyboardInterrupt:
        print("\n\n✓ Volviendo al menú...")


def modo_escritura(sistema):
    """Modo para escribir nuevas tarjetas"""
    print("\n✍️  ESCRIBIR NUEVA TARJETA")
    print("-" * 60)
    
    id_persona = input("ID (8 dígitos): ").strip()
    nombre = input("Nombre completo: ").strip()
    
    print("\nTipo de persona:")
    print("  E - Empleado")
    print("  V - Visitante")
    print("  A - Administrador")
    tipo = input("Tipo (E/V/A): ").strip().upper() or 'E'
    
    sistema.escribir_tarjeta(id_persona, nombre, tipo)


if __name__ == "__main__":
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
            
            elif opcion == '4':
                id_buscar = input("\nID a buscar: ").strip()
                registros = sistema.buscar_por_id(id_buscar)
                if registros:
                    print(f"\n📋 Registros encontrados: {len(registros)}")
                    print("-" * 60)
                    for r in registros[-10:]:  # Últimos 10
                        print(f"{r['fecha']} {r['hora']} - {r['accion'].upper()}: {r['nombre']}")
                else:
                    print("✗ No se encontraron registros")
                input("\nPresiona Enter para continuar...")
            
            elif opcion == '5':
                print("\n👋 Cerrando sistema...")
                break
            
            else:
                print("✗ Opción no válida")
    
    except KeyboardInterrupt:
        print("\n\n👋 Sistema interrumpido")
    
    finally:
        sistema.limpiar()
        print("✓ Recursos liberados. Adiós!")