# Prueba 3D estilizada: estado

- **Fase:** prueba técnica de estilo (no es un video para publicar).
- **Puertas humanas (D-004):** guion — no aplica (texto dado); storyboard — no aplica; video final — **pendiente de revisión**.
- **Salida:** `out/prueba_3d.mp4` (1080x1920, 30 fps, 450 fotogramas, 15,0 s, h264 + aac).
- **QA:** `07_qa/hoja_contactos_2fps.png` (30 cuadros, 2 fps).

## Cómo reproducir
1. Blender: `"<blender.exe>" -b --factory-startup --python "scripts/escena_cable_submarino.py" -- --render`
   → `04_blender/frames/f_0001.png … f_0450.png` (ignorado por git).
2. Voz de borrador (D-005, solo borrador):
   `uv run --no-project --with edge-tts==7.3.1 python "scripts/tts_borrador.py" --texto "<texto>" --voz es-MX-JorgeNeural --salida "proyectos/2026-11-21_prueba-3d/05_audio/voz_borrador"`
3. Montaje: `npm run render_prueba3d` (usa `--public-dir` = esta carpeta).

## Tiempos (2026-11-21, RTX 5050 Laptop)
| Etapa | Tiempo |
|---|---|
| Blender, 450 fotogramas Eevee + Freestyle | 699,4 s (11 min 39 s; ~1,55 s/fotograma incl. ~22 s de compilación de shaders) |
| Remotion, render final | 46,9 s (primer render: 50,2 s) |

## Recursos
- Poly Haven CC0: `moon_rock_02` (2 usos), `moon_rock_03`, `ocean_buoy` (registrados en `biblioteca/LICENCIAS.csv`).
- Formas simples propias: barco, cable por capas, lecho, agua (excepción a D-002 autorizada para esta prueba).
- Voz: edge-tts `es-MX-JorgeNeural` (borrador; no publicable, D-005).

## Bloqueos para publicar
- Dato del 99 % sin fuente primaria (D-003).
- Voz de borrador (D-005).
