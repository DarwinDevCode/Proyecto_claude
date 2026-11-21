# Proyectos

Cada video vive en su propia carpeta: `proyectos/AAAA-MM-DD_slug/` (por ejemplo `proyectos/2026-12-01_fotosintesis/`). Todas las carpetas siguen la misma plantilla:

| Elemento | Contenido |
|---|---|
| `00_concepto.md` | Idea, público, objetivo de aprendizaje, duración objetivo. |
| `01_investigacion.md` | Datos con **fuente primaria enlazada y fechada** (D-003). |
| `02_guion.json` | Guion estructurado por escenas: texto de voz, duración, notas visuales. **Puerta humana 1** (D-004). |
| `03_storyboard/` | Fotogramas clave o bocetos por escena. **Puerta humana 2** (D-004). |
| `04_blender/` | Archivos `.blend` y scripts de escena (sombreado toon, D-002). Solo modelos registrados en `biblioteca/LICENCIAS.csv`. |
| `05_audio/` | Voz (borrador con edge-tts, final con voz propia, Kokoro o servicio con licencia, D-005), música y efectos usados. |
| `06_render/` | Renders intermedios y final. **No se sube a git.** |
| `07_qa/` | Resultados de la revisión automática y capturas de control. |
| `08_publicacion/` | Título, descripción, créditos, miniatura. **Puerta humana 3**: video final (D-004). |
| `ESTADO.md` | Fase actual, puertas aprobadas (quién/cuándo) y bloqueos. |

Las herramientas que crean esta plantilla se definirán en un paso posterior.
