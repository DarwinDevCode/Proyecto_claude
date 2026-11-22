# Pendientes

Formato: `- [ ] (fecha) descripción — contexto`. Al resolver uno, márcalo `[x]` y anota cómo se resolvió.

## Paso 2: prueba 3D estilizada (proyectos/2026-11-21_prueba-3d)

- [ ] (2026-11-21) D-003: el dato "más del 99 % del tráfico entre continentes viaja por cables submarinos" no tiene fuente primaria enlazada y fechada. Es solo una prueba; no publicar sin fuente.
- [ ] (2026-11-21) D-003: el diámetro de 17-21 mm del cable submarino de aguas profundas (usado para escalar la mano en la v2) no tiene fuente primaria enlazada y fechada.
- [ ] (2026-11-21) Créditos CC-BY obligatorios si se publica: "Container Ship" (Alex Safayan) y "Hand" (Poly by Google), ambos CC BY 3.0 vía Poly Pizza. Definir dónde van los créditos (descripción del video).
- [ ] (2026-11-21) Poly Pizza vía MCP: la búsqueda con el término "hand" devuelve error 500 de forma sistemática (se encontró la mano buscando "glove"); el ajuste "usar Poly Pizza" del addon es por escena.
- [ ] (2026-11-21) D-002: el barco y el cable se modelaron con formas simples (no hay barco moderno en Poly Haven y el cable en corte es un diagrama). Excepción autorizada para esta prueba; decidir si se registra como decisión o se buscan modelos CC0/CC-BY.
- [ ] (2026-11-21) Tipografía de subtítulos: usa fuentes del sistema (Segoe UI Black / Arial Black). Elegir una fuente con licencia libre, guardarla en `biblioteca/fuentes/` y registrarla en LICENCIAS.csv.
- [ ] (2026-11-21) `Audio` de `remotion` funciona, pero la skill oficial recomienda `@remotion/media`; decidir si se instala (requiere permiso).
- [ ] (2026-11-21) El agua en corte es solo la pared del fondo y la superficie; falta un volumen de agua frontal (transparencia o color) para que el corte se lea como mar.

## Paso 1: base del proyecto

- [x] (2026-11-21) `docs/AUDITORIA_SISTEMA_VIDEO.md` estaba vacío (0 bytes). Resuelto: el usuario copió la versión completa (67 895 bytes, 652 líneas); el doctor da OK.
- [x] (2026-11-21) Probar el MCP de Blender en vivo. Resuelto: addon instalado por el usuario con "Install from Disk" desde `scripts/blender_mcp_addon.py`; protocolo 16/16, escena `Prueba_MCP` creada por MCP y captura del visor en `docs/prueba_blender.png`.
- [ ] (2026-11-21) **Regla permanente:** la app de Claude (paquete MSIX) desvía sus escrituras en `AppData\Roaming` a una carpeta privada (`AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\...`); desde dentro de la app la ruta parece existir, pero los demás programas no la ven. Cualquier instalación en carpetas de usuario de Blender u otros programas la hace el usuario con "Install from Disk" o manualmente; Claude solo deja el archivo en una ruta visible del proyecto (p. ej. `scripts/`). Mantener este punto abierto como recordatorio.
- [ ] (2026-11-21) Decidir si activar `BLENDER_MCP_SAFE_MODE=1` en `.mcp.json` (valida scripts antes de ejecutarlos en Blender; bloquea escritura directa de archivos).
- [ ] (2026-11-21) Llenar `docs/BIBLIA_VISUAL.md` analizando `referencias/estilo/REF01_toon3d_tutorial.mp4` (paso posterior).
- [ ] (2026-11-21) Node 22 es LTS en mantenimiento (fin de soporte: abril de 2027). Decidir cuándo migrar a Node 24/26.
- [ ] (2026-11-21) `npm install` reportó 9 vulnerabilidades moderadas en dependencias de la plantilla de Remotion. Revisar con `npm audit` sin `--force`.
- [ ] (2026-11-21) Tras clonar el repo: `npm install`, `npx remotion browser ensure` y `npx remotion skills add` (recrea las junctions de `.claude/skills/`, ignoradas por git). Las carpetas ignoradas `biblioteca/modelos3d|sfx|musica` no existen en un clon nuevo.
- [ ] (2026-11-21) `README.md` de la raíz es el genérico de la plantilla de Remotion; reemplazarlo por uno del proyecto.
- [x] (2026-11-21) La skill oficial remotion-docs incluye la clave pública de búsqueda de Algolia de la documentación de Remotion; revisada y aceptada (no es nuestra ni da acceso de escritura).
- [x] (2026-11-21) Remotion no podía descargar Chrome Headless Shell (`remotion.media` no resolvía por DNS). Resuelto por el usuario cambiando el DNS del equipo a 1.1.1.1 / 8.8.8.8.
