"""Voz de BORRADOR con edge-tts (D-005: nunca para publicar) + tiempos por palabra.

Uso:
  uv run --no-project --with edge-tts==7.3.1 python "scripts/tts_borrador.py" ^
      --texto "..." --voz es-MX-JorgeNeural --salida "proyectos/<p>/05_audio/voz_borrador"

Genera <salida>.mp3 y <salida>.palabras.json: [{"texto", "inicio_ms", "fin_ms"}, ...]
"""

import argparse
import asyncio
import json
import os

import edge_tts


async def generar(texto, voz, salida, velocidad):
    com = edge_tts.Communicate(texto, voz, rate=velocidad, boundary="WordBoundary")
    palabras = []
    os.makedirs(os.path.dirname(salida) or ".", exist_ok=True)
    with open(salida + ".mp3", "wb") as audio:
        async for trozo in com.stream():
            if trozo["type"] == "audio":
                audio.write(trozo["data"])
            elif trozo["type"] == "WordBoundary":
                inicio = trozo["offset"] / 10_000          # unidades de 100 ns -> ms
                palabras.append({
                    "texto": trozo["text"],
                    "inicio_ms": round(inicio),
                    "fin_ms": round(inicio + trozo["duration"] / 10_000),
                })
    with open(salida + ".palabras.json", "w", encoding="utf-8") as f:
        json.dump({"voz": voz, "texto": texto, "palabras": palabras}, f, ensure_ascii=False, indent=2)
    return palabras


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--texto", required=True)
    p.add_argument("--voz", default="es-MX-JorgeNeural")
    p.add_argument("--velocidad", default="+0%")
    p.add_argument("--salida", required=True)
    a = p.parse_args()
    palabras = asyncio.run(generar(a.texto, a.voz, a.salida, a.velocidad))
    for w in palabras:
        print(f'{w["inicio_ms"]:>6} {w["fin_ms"]:>6}  {w["texto"]}')
    print(f"TTS_OK {len(palabras)} palabras -> {a.salida}.mp3")


if __name__ == "__main__":
    main()
