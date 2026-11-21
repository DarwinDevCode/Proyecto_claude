# Registro de decisiones

Cada decisión de arquitectura o de proceso se registra aquí. No se borra: si cambia, se añade una nueva que la reemplace y se indica en el motivo.

| ID | Fecha | Decisión | Motivo | Alternativa descartada |
|---|---|---|---|---|
| D-001 | 2026-11-21 | Remotion es el compositor: texto, subtítulos, sincronía, montaje y render final. | Composición declarativa en React/TypeScript, reproducible desde código y controlable por Claude Code; sincronía exacta por fotograma. | Montar en Blender (VSE) o editar a mano en un NLE: menos reproducible y difícil de automatizar. |
| D-002 | 2026-11-21 | Las escenas se hacen en Blender con sombreado toon. Nada de construir objetos con primitivas: se usan modelos con licencia CC0/CC-BY registrados en `biblioteca/LICENCIAS.csv`. | Calidad visual consistente con el estilo objetivo y trazabilidad legal de cada recurso. | Modelar con primitivas por código: resultado pobre y poco reconocible. |
| D-003 | 2026-11-21 | Ningún dato se publica sin fuente primaria enlazada y fechada. | Credibilidad del contenido educativo y verificabilidad. | Fuentes secundarias o datos sin fecha. |
| D-004 | 2026-11-21 | Tres puertas humanas: guion, storyboard y video final. | Un humano aprueba en los puntos donde un error es más caro de corregir después. | Pipeline totalmente automático sin revisión. |
| D-005 | 2026-11-21 | edge-tts solo para borradores; la voz final será propia, Kokoro o un servicio con licencia comercial. | edge-tts no ofrece garantías de licencia para uso comercial. | Publicar con edge-tts. |
