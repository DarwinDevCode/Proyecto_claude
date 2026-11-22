# 03 · Plan visual

**Base:** escena v2 (`scripts/escena_cable_submarino_v2.py`) → nueva `scripts/escena_cable_submarino_v3.py` para este short.
**Estado:** borrador. Se cierra tras aprobar el guion (puerta 1); el storyboard es la puerta 2.

## Correcciones obligatorias sobre la v2

| Corrección | Cómo |
|---|---|
| Recuperar el color de la v1 (arena cálida, sombras índigo visibles) | El tinte del agua desaturaba todo. La capa de agua solo se compone en el plano general (E2) y en los planos de superficie (E5); en los planos cercanos (E1, E3, E4, E6) no se compone. Opacidad lateral de 0,30 a 0,15 y tono algo más claro. Volver al sol desde delante-izquierda de la v1 donde no haya mano (la v2 lo giró por la mano). |
| Nada de barco cortado visto desde abajo | Ninguna cámara bajo la superficie con el barco en cuadro. En E2 y E5 la cámara está por encima de la línea del agua o encuadra sin el casco. Regla en el script: si la cámara está bajo el agua, el barco se oculta. |
| Quitar las manchas negras del agua | En la v2 aparecen trazos oscuros sueltos en la zona superior (2-3,5 s). Hipótesis: fragmentos de Freestyle de la boya o del casco sumergidos, vistos a través del agua. Diagnosticar renderizando la capa de escena sola en ese tramo; solución prevista: excluir del contorno las partes sumergidas o subir el umbral de crease. |
| El corte de capas ocupa al menos la mitad del encuadre | Macro: cámara a ~0,9 m del extremo con objetivo de 50 mm. Comprobación automática en QA: medir el ancho del corte en píxeles (≥ 540 px de 1080). |
| La mano entra desde el borde del encuadre | La muñeca queda siempre fuera de cuadro (por abajo o por la izquierda). La animación parte de fuera del encuadre y nunca muestra el corte de la muñeca ni la mano flotando. |
| Orden real de las capas (investigación, punto 4) | De dentro hacia fuera: fibras → acero (elemento de tracción) → cobre → polietileno. Se elimina la capa de "gel" de la v2, que no tiene fuente. Armadura exterior solo si aparece un tramo de costa. |

## Planos (tiempos con la voz medida: 49,6 s + 1 s de cierre)

| Plano | Escena | Tiempo aprox. | Cámara | Contenido | Agua |
|---|---|---|---|---|---|
| P1 | E1 | 0,0–5,0 s | Macro fijo del corte (≥ 50 % del cuadro) | Capas visibles desde f0; la mano entra desde abajo y el pulgar se apoya junto al cable | No |
| P2 | E2 | 5,0–12,5 s | Movimiento rápido (0,8 s) hacia atrás y arriba hasta el plano general; pausa | Maqueta completa del océano; barco de carga en superficie; etiquetas +99 % y 607 | Sí |
| P3 | E3 | 12,5–22,5 s | Movimiento rápido (0,8 s) de vuelta al macro | Las capas se despliegan una por palabra; etiquetas con flecha a cada capa; "17–21 mm" con cota | No |
| P4 | E4a | 22,5–27,5 s | Plano medio del lecho, a la altura del cable | "¿Tiburones? Casi nunca": el tiburón pasa, mira el cable y sigue | Sí (suave) |
| P5 | E4b | 27,5–32,5 s | Mismo plano, con un leve paneo | El ancla y la red de arrastre se arrastran por el lecho, enganchan el cable y lo parten | Sí (suave) |
| P6 | E5 | 32,5–44,5 s | Plano general vertical (de la superficie al fondo) y después corte a cubierta | Barco cablero, gancho que baja y sube el cable, empalme, el cable vuelve a bajar; etiqueta 5–9 días | Sí |
| P7 | E6 | 44,5–50,6 s | Vuelta exacta al encuadre de P1 | El pulgar toca el cable y un pulso de luz recorre las fibras; 1 s de cierre | No |

## Modelos

### Reutilizados (ya en `biblioteca/` y en `LICENCIAS.csv`)
- Barco de carga "Container Ship" (CC BY 3.0), mano "Hand" (CC BY 3.0), rocas y boya de Poly Haven (CC0).

### Nuevos: candidatos encontrados (pendientes de inspección visual; se registran en LICENCIAS.csv al descargarlos)

| Necesidad | Candidato (Poly Pizza) | Licencia | Comentario |
|---|---|---|---|
| Ancla (E4) | "Anchor", Quaternius (`ejWQny9Gcz`) | CC0 1.0 | Preferido (CC0). Alternativa: "Anchor", Nikdane12 (`SxdMzDMKpS`, CC0). |
| Cadena del ancla (E4) | "Hook and chain", Zacharylll (`dBp9m8k9kTi`) | CC BY 3.0 | Revisar si sirve; si no, cadena simple procedural. |
| Tiburón (E4, gag) | "Shark", Quaternius (`AyHTK3zUSG`, animado) | CC0 1.0 | Ya trae animación de nado. |
| Barco de pesca (E4) | "Boat", Quaternius (`5UEl54KsuC`, 224 tris) | CC0 1.0 | Alternativa: "Boat", Poly by Google (`84-DYhLzxNq`, CC BY 3.0). |
| Red de pesca (E4) | "Fishing Net", J-Toastie (`Z11I3AUBO9`) | CC BY 3.0 | Ver si sirve como red de arrastre; si no, malla procedural. |
| **Barco cablero (E5)** | **DECIDIDO (D-006):** "TugBoat", Some "Random" Person (`0C28iix4FPm`), inspeccionado y exportado a `biblioteca/modelos3d/polypizza/barco_cablero_base/tugboat.glb` | CC BY 3.0 | Se adapta: roldana de proa, tambor de cable en la cubierta de popa y casco recoloreado con la paleta. Descartado "Small Ship" (Quaternius, CC0) por ser una barca de madera de estilo pirata. |
| **Gancho (grapnel) (E5)** | **DECIDIDO (D-006):** modelado con formas simples (eje, anilla y 4 uñas curvas) | propio | No hay alternativa con licencia (solo "Fish hook" y señuelos). |
| Cubierta / empalme (E5) | No buscado todavía | — | Opción: resolverlo en Remotion con una ilustración 2D en vez de un plano 3D. |

## Etiquetas en pantalla (Remotion)
- Cápsula oscura + texto Lilita One (estilo de la v2).
- Cada etiqueta con dato lleva su fuente en pequeño: "Fuente: ITU 2026", "TeleGeography 2026", "ICPC 2026", "KIS-ORCA".
- Las etiquetas de capas (E3) son cuatro flechas que aparecen sincronizadas con cada palabra.
