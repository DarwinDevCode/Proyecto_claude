# Pendientes

Formato: `- [ ] (fecha) descripción — contexto`. Al resolver uno, márcalo `[x]` y anota cómo se resolvió.

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
