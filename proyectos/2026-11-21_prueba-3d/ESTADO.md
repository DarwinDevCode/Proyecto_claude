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

## Versión 2 (paso 2B)
- **Salida:** `out/prueba_3d_v2.mp4` (1080x1920, 30 fps, 266 fotogramas, 8,9 s; audio AAC 48 kHz).
  Intermedio sin masterizar: `out/prueba_3d_v2_sinmaster.mp4`.
- **QA:** `07_qa/hoja_contactos_v2_2fps.png` (18 cuadros).
- **Audio:** −14,0 LUFS integrados, pico verdadero −2,0 dBTP, medidos con ebur128 sobre el MP4 ya codificado.
- **Cómo reproducir:**
  1. Voz: `uv run --no-project --with edge-tts==7.3.1 python "scripts/tts_borrador.py" --texto "<texto>" --voz es-MX-JorgeNeural --salida "proyectos/2026-11-21_prueba-3d/05_audio/voz_borrador_v2"` (velocidad normal).
  2. Blender, dos capas: `"<blender.exe>" -b --factory-startup --python "scripts/escena_cable_submarino_v2.py" -- --render --capa escena` y lo mismo con `--capa agua`.
  3. Montaje + máster: `npm run render_prueba3d_v2`.

| Etapa v2 | Tiempo |
|---|---|
| Blender capa escena (266 f, Eevee + Freestyle + desenfoque de movimiento) | 557,2 s |
| Blender capa agua (266 f) | 313,9 s |
| **Blender total** | **871,1 s (14 min 31 s)** |
| Remotion (Prueba3Dv2) | 42,3 s |
| Masterizado de audio | 1,2 s |

- **Recursos v2:** Poly Pizza "Container Ship" (Alex Safayan, CC BY 3.0) y "Hand" (Poly by Google, CC BY 3.0); Poly Haven CC0 (rocas, boya); fuente Lilita One (OFL 1.1). Todo en `biblioteca/LICENCIAS.csv`.

## Bloqueos para publicar
- Dato del 99 % sin fuente primaria (D-003).
- Voz de borrador (D-005).
- Diámetro real del cable (17-21 mm) sin fuente (D-003).
- Créditos CC BY obligatorios de los modelos de Poly Pizza.
