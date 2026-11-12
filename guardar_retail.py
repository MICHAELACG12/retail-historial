"""Corre solo en GitHub (varias veces al día): toma la foto del sentimiento retail de Myfxbook
y la guarda en historial_retail.csv. Una fila por par y por día (la última foto del día).

El correo y la contraseña de Myfxbook NO están aquí: GitHub los guarda como "secretos"
(MYFXBOOK_EMAIL y MYFXBOOK_PASSWORD) y nadie más puede verlos.
"""
import csv
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

from curl_cffi import requests

API = "https://www.myfxbook.com/api"
ARCHIVO = Path(__file__).with_name("historial_retail.csv")


def pedir(url):
    respuesta = requests.get(url, impersonate="chrome", timeout=60)
    datos = respuesta.json()
    if datos.get("error"):
        raise SystemExit(f"Myfxbook respondió con error: {datos.get('message')}")
    return datos


email, clave = os.environ["MYFXBOOK_EMAIL"].strip(), os.environ["MYFXBOOK_PASSWORD"]
sesion = pedir(f"{API}/login.json?email={quote(email, safe='')}&password={quote(clave, safe='')}")["session"]
simbolos = pedir(f"{API}/get-community-outlook.json?session={sesion}").get("symbols", [])
try:
    pedir(f"{API}/logout.json?session={sesion}")
except BaseException:
    pass
if not simbolos:
    raise SystemExit("Myfxbook no devolvió pares")

hoy = datetime.now(ZoneInfo("America/Bogota")).strftime("%Y-%m-%d")
filas = []
if ARCHIVO.exists():
    with ARCHIVO.open(encoding="utf-8") as f:
        filas = [r for r in csv.DictReader(f) if r["fecha"] != hoy]  # la foto de hoy se reemplaza
filas += [{"fecha": hoy, "simbolo": s["name"].upper(), "largo": float(s["longPercentage"]),
           "corto": float(s["shortPercentage"])} for s in simbolos]
with ARCHIVO.open("w", encoding="utf-8", newline="") as f:
    escritor = csv.DictWriter(f, fieldnames=["fecha", "simbolo", "largo", "corto"])
    escritor.writeheader()
    escritor.writerows(filas)
print(f"Guardados {len(simbolos)} pares del {hoy}. Días en el historial: {len({r['fecha'] for r in filas})}")
