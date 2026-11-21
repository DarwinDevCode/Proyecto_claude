# Estudio de producción de videos educativos con IA

Pipeline en el que Claude Code produce videos verticales 1080x1920 en 3D estilizado (toon, sombras de color, fondos limpios): escenas en Blender, montaje en Remotion, voz, subtítulos palabra por palabra, música, efectos y revisión automática. Estado: **Paso 1, base del proyecto**.

**Antes de cada tarea, lee `docs/`** (DECISIONES, PENDIENTES, BIBLIA_VISUAL y AUDITORIA_SISTEMA_VIDEO como lecciones aprendidas P1-P12; no copiar su arquitectura).

## Estructura
- `src/`: código Remotion (composición de prueba `Prueba`).
- `scripts/`: `doctor.mjs` (`npm run doctor`), `config.json` (**única** fuente de la ruta de Blender), scripts de Blender.
- `docs/`: decisiones, pendientes, biblia visual, auditoría.
- `biblioteca/`: `modelos3d/`, `sfx/`, `musica/`, `fuentes/` + `LICENCIAS.csv` (todo recurso se registra ahí).
- `proyectos/`: un video por carpeta, plantilla en `proyectos/README.md`.
- `referencias/estilo/`: solo para analizar; nunca se usa en nuestros videos ni se sube a git.
- `.agents/skills/` + `skills-lock.json`: skills oficiales de Remotion (junctions en `.claude/skills/`).
- `.mcp.json`: servidor MCP `blender` (mcp-for-blender, puerto 9876).
- `out/`: salidas de prueba (ignorado por git).

## Decisiones vigentes (detalle en docs/DECISIONES.md)
- **D-001** Remotion es el compositor: texto, subtítulos, sincronía, montaje y render final.
- **D-002** Blender con sombreado toon; nada de objetos hechos con primitivas: modelos CC0/CC-BY registrados en `biblioteca/LICENCIAS.csv`.
- **D-003** Ningún dato se publica sin fuente primaria enlazada y fechada.
- **D-004** Tres puertas humanas: guion, storyboard y video final.
- **D-005** edge-tts solo para borradores; voz final propia, Kokoro o servicio con licencia comercial.

## Reglas de trabajo
- **Plan primero**: inspecciona, muestra el plan y espera aprobación antes de crear o instalar.
- **Permiso para instalar**: pide permiso antes de cada instalación (winget, npm, pip, uv/uvx), diciendo qué y por qué.
- **Commits por GitHub Desktop**: nunca `git commit` ni `git push`. En cada punto de commit, entrega Summary (una línea) + Description y espera "listo". Git solo para status, log, diff.
- **Rutas siempre entre comillas** en comandos y scripts.
- Si algo falla, máximo 2 intentos; después, detenerse y explicar error y opciones.
- No borrar archivos sin permiso. No declarar un paso terminado: lo revisa el usuario.
- Registrar decisiones nuevas en `docs/DECISIONES.md` y lo no resuelto en `docs/PENDIENTES.md`.

## Comandos
- `npm run doctor`: diagnóstico del entorno (OK/FALLA/AVISO).
- `npm run dev`: Remotion Studio.
- `npm run render_prueba`: render de la composición `Prueba` a `out/prueba.mp4`.
- Blender sin interfaz: lee `blender.exe` de `scripts/config.json` y ejecuta
  `"<blender.exe>" -b --factory-startup --python "scripts/blender_prueba_render.py" -- "out/prueba_blender.png"`.
