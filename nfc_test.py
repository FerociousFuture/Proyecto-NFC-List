#!/usr/bin/env python3
from pirc522 import RFID
import time

rdr = RFID()

print("Esperando tarjeta...")
try:
    while True:
        rdr.wait_for_tag()
        (error, tag_type) = rdr.request()
        if not error:
            print(f"✓ Tarjeta detectada! Tipo: {tag_type}")
            (error, uid) = rdr.anticoll()
            if not error:
                print(f"✓ UID: {uid}")
        time.sleep(1)
except KeyboardInterrupt:
    print("\nCerrando...")
    rdr.cleanup()
