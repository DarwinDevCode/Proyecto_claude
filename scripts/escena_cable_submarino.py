"""Paso 2 · Prueba 3D estilizada: corte del fondo marino con cable de fibra óptica.

Construye la escena completa (modelos Poly Haven CC0 + formas simples), el sombreado
toon de 3 bandas con sombras de color, contorno Freestyle y la cámara con 3 movimientos.

Uso:
  Construir en vivo (MCP):  exec(open(r"<ruta>").read(), {"ROOT": r"<raíz del proyecto>", "__name__": "mcp"})
  Render final (sin interfaz):
    "<blender.exe>" -b --factory-startup --python "scripts/escena_cable_submarino.py" -- --render
  Opciones tras "--": --render  --frames 1-450  --out "<carpeta>"  --samples 16
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

# ---------------------------------------------------------------- rutas
if "ROOT" in globals():
    ROOT = globals()["ROOT"]
else:
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROYECTO = os.path.join(ROOT, "proyectos", "2026-11-21_prueba-3d")
MODELOS = os.path.join(ROOT, "biblioteca", "modelos3d", "polyhaven")

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(nombre, defecto=None):
    if nombre in ARGS:
        i = ARGS.index(nombre)
        return ARGS[i + 1] if i + 1 < len(ARGS) and not ARGS[i + 1].startswith("--") else True
    return defecto


# ---------------------------------------------------------------- paleta
def hex_lin(h):
    """#RRGGBB (sRGB) -> RGBA lineal para nodos."""
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


P = {
    "fondo": "#F3F0EA",      # blanco roto
    "indigo": "#3D4FA0",     # color de todas las sombras
    "linea": "#2B3150",      # contorno
    "arena": "#EBD3A4",
    "arena_corte": "#DDBB86",
    "arcilla": "#CFA37C",
    "rayado": "#B98A5C",
    "agua_1": "#D3EEF4",
    "agua_2": "#B3E0EC",
    "agua_3": "#8FCBDF",
    "superficie": "#A6DDEA",
    "casco": "#E5644E",
    "cabina": "#F6F0E2",
    "roca": "#C9C4BC",
    "boya": "#F2B33D",
    "funda": "#34417A",
    "acero": "#AEB6C4",
    "cobre": "#DB8550",
    "gel": "#F3E7C6",
    "fibra": "#5ED3B5",
}

FPS = 30
FRAMES = 450
ANCHO, ALTO = 1080, 1920

# Geometría del diorama (metros, estilizado)
X0, X1 = -1.8, 1.8
Y0, Y1 = -3.0, 3.0          # Y0 = plano de corte frontal
Z_LECHO = 0.0
Z_ARCILLA = -0.38
Z_BASE = -1.05
Z_AGUA = 4.2
R_CABLE = 0.12


# ---------------------------------------------------------------- utilidades de nodos
def _mix_rgb(nt, fac=None, a=None, b=None, fac_valor=None):
    m = nt.nodes.new("ShaderNodeMix")
    m.data_type = "RGBA"
    ent_a = next(s for s in m.inputs if s.name == "A" and s.type == "RGBA")
    ent_b = next(s for s in m.inputs if s.name == "B" and s.type == "RGBA")
    sal = next(s for s in m.outputs if s.type == "RGBA")
    if fac is not None:
        nt.links.new(fac, m.inputs["Factor"])
    elif fac_valor is not None:
        m.inputs["Factor"].default_value = fac_valor
    for ent, v in ((ent_a, a), (ent_b, b)):
        if isinstance(v, tuple):
            ent.default_value = v
        elif v is not None:
            nt.links.new(v, ent)
    return sal


def material_toon(nombre, base, rayado=None, bandas_z=None):
    """Toon de 3 bandas (sombra índigo / media / luz) con Shader to RGB.

    base: hex de color base.  rayado: (hex_linea, escala) para caras de corte.
    bandas_z: lista [(z_desde, hex)] para un degradado escalonado por altura.
    """
    mat = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    # Color base (plano o por bandas de altura)
    if bandas_z:
        coord = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        mapa = nt.nodes.new("ShaderNodeMapRange")
        mapa.inputs["From Min"].default_value = Z_LECHO
        mapa.inputs["From Max"].default_value = Z_AGUA
        rampa_z = nt.nodes.new("ShaderNodeValToRGB")
        rampa_z.color_ramp.interpolation = "CONSTANT"
        els = rampa_z.color_ramp.elements
        while len(els) < len(bandas_z):
            els.new(0.5)
        for el, (z, h) in zip(els, bandas_z):
            el.position = (z - Z_LECHO) / (Z_AGUA - Z_LECHO)
            el.color = hex_lin(h)
        nt.links.new(coord.outputs["Generated"] if False else coord.outputs["Object"], sep.inputs[0])
        nt.links.new(sep.outputs["Z"], mapa.inputs["Value"])
        nt.links.new(mapa.outputs["Result"], rampa_z.inputs["Fac"])
        color_base = rampa_z.outputs["Color"]
    else:
        rgb = nt.nodes.new("ShaderNodeRGB")
        rgb.outputs[0].default_value = hex_lin(base)
        color_base = rgb.outputs[0]

    if rayado:
        h_linea, escala = rayado
        coord2 = nt.nodes.new("ShaderNodeTexCoord")
        onda = nt.nodes.new("ShaderNodeTexWave")
        onda.wave_type = "BANDS"
        onda.bands_direction = "DIAGONAL"
        onda.inputs["Scale"].default_value = escala
        onda.inputs["Distortion"].default_value = 0.0
        rampa_r = nt.nodes.new("ShaderNodeValToRGB")
        rampa_r.color_ramp.interpolation = "CONSTANT"
        rampa_r.color_ramp.elements[0].position = 0.0
        rampa_r.color_ramp.elements[0].color = (0, 0, 0, 1)
        rampa_r.color_ramp.elements[1].position = 0.82
        rampa_r.color_ramp.elements[1].color = (1, 1, 1, 1)
        nt.links.new(coord2.outputs["Object"], onda.inputs["Vector"])
        nt.links.new(onda.outputs["Fac"], rampa_r.inputs["Fac"])
        color_base = _mix_rgb(nt, fac=rampa_r.outputs["Color"], a=color_base, b=hex_lin(h_linea))

    # Luz -> bandas
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    dif.inputs["Color"].default_value = (1, 1, 1, 1)
    a_rgb = nt.nodes.new("ShaderNodeShaderToRGB")
    bandas = nt.nodes.new("ShaderNodeValToRGB")
    bandas.color_ramp.interpolation = "CONSTANT"
    e = bandas.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0, 0, 0, 1)
    e[1].position, e[1].color = 0.55, (1, 1, 1, 1)
    medio = e.new(0.18)
    medio.color = (0.5, 0.5, 0.5, 1)
    nt.links.new(dif.outputs["BSDF"], a_rgb.inputs["Shader"])
    nt.links.new(a_rgb.outputs["Color"], bandas.inputs["Fac"])

    sombra = _mix_rgb(nt, fac_valor=0.62, a=color_base, b=hex_lin(P["indigo"]))
    final = _mix_rgb(nt, fac=bandas.outputs["Color"], a=sombra, b=color_base)

    emi = nt.nodes.new("ShaderNodeEmission")
    salida = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(final, emi.inputs["Color"])
    nt.links.new(emi.outputs["Emission"], salida.inputs["Surface"])
    return mat


# ---------------------------------------------------------------- geometría
def objeto_desde_bmesh(nombre, bm, coleccion, material=None, suave=False):
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    if suave:
        for p in me.polygons:
            p.use_smooth = True
        try:
            me.set_sharpness_by_angle(angle=math.radians(40))
        except Exception:
            pass
    ob = bpy.data.objects.new(nombre, me)
    coleccion.objects.link(ob)
    if material:
        ob.data.materials.append(material)
    return ob


def caja(nombre, x0, x1, y0, y1, z0, z1, coleccion, materiales, indice_por_normal=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = x0 if v.co.x < 0 else x1
        v.co.y = y0 if v.co.y < 0 else y1
        v.co.z = z0 if v.co.z < 0 else z1
    if indice_por_normal:
        bm.normal_update()
        for f in bm.faces:
            f.material_index = indice_por_normal(f.normal)
    ob = objeto_desde_bmesh(nombre, bm, coleccion)
    for m in materiales:
        ob.data.materials.append(m)
    return ob


def cilindro_y(nombre, radio, largo, coleccion, material, segmentos=48, centro_xz=(0.0, 0.0)):
    """Cilindro a lo largo de +Y con la cara frontal en y=0 (origen del objeto)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segmentos,
                          radius1=radio, radius2=radio, depth=largo)
    bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.radians(-90), 4, "X"), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector((centro_xz[0], largo / 2, centro_xz[1])), verts=bm.verts)
    return objeto_desde_bmesh(nombre, bm, coleccion, material, suave=True)


def anillo_cilindros_y(nombre, n, radio_anillo, radio, largo, coleccion, material, segmentos=12):
    bm = bmesh.new()
    for i in range(n):
        a = 2 * math.pi * i / n
        tmp = bmesh.new()
        bmesh.ops.create_cone(tmp, cap_ends=True, segments=segmentos, radius1=radio, radius2=radio, depth=largo)
        bmesh.ops.transform(tmp, matrix=Matrix.Rotation(math.radians(-90), 4, "X"), verts=tmp.verts)
        bmesh.ops.translate(tmp, vec=Vector((radio_anillo * math.cos(a), largo / 2, radio_anillo * math.sin(a))),
                            verts=tmp.verts)
        me_tmp = bpy.data.meshes.new("tmp")
        tmp.to_mesh(me_tmp)
        tmp.free()
        bm.from_mesh(me_tmp)
        bpy.data.meshes.remove(me_tmp)
    return objeto_desde_bmesh(nombre, bm, coleccion, material, suave=True)


def barco(coleccion, mat_casco, mat_cabina):
    """Barco pequeño de formas simples: casco afilado en proa, cabina y mástil."""
    largo, ancho, alto = 1.5, 0.52, 0.34
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        x = v.co.x * largo
        y = v.co.y * ancho
        z = (v.co.z + 0.5) * alto
        if v.co.z < 0:          # fondo más estrecho
            y *= 0.45
            x *= 0.86
        if v.co.x > 0:          # proa en punta
            y *= 0.08
            x += 0.18 if v.co.z > 0 else 0.0
        v.co = Vector((x, y, z))
    casco = objeto_desde_bmesh("Barco_casco", bm, coleccion, mat_casco)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((0.46, 0.38, 0.26)), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector((-0.3, 0.0, alto + 0.13)), verts=bm.verts)
    cabina = objeto_desde_bmesh("Barco_cabina", bm, coleccion, mat_cabina)

    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.022, radius2=0.022, depth=0.55)
    bmesh.ops.translate(bm, vec=Vector((-0.3, 0.0, alto + 0.26 + 0.27)), verts=bm.verts)
    mastil = objeto_desde_bmesh("Barco_mastil", bm, coleccion, mat_cabina, suave=True)

    raiz = bpy.data.objects.new("Barco", None)
    coleccion.objects.link(raiz)
    for o in (casco, cabina, mastil):
        o.parent = raiz
    return raiz


def importar_polyhaven(id_modelo, coleccion, tamano, material, nombre):
    """Agrega los meshes del .blend de Poly Haven, los une y los escala al tamaño pedido."""
    ruta = os.path.join(MODELOS, id_modelo, f"{id_modelo}_1k.blend")
    with bpy.data.libraries.load(ruta, link=False) as (src, dst):
        dst.objects = list(src.objects)
    mallas = [o for o in dst.objects if o is not None and o.type == "MESH"]
    for o in dst.objects:
        if o is not None and o.type != "MESH":
            bpy.data.objects.remove(o)
    for o in mallas:
        coleccion.objects.link(o)
        o.parent = None
        o.data.materials.clear()
        o.data.materials.append(material)
    # Unir en un solo objeto
    bm = bmesh.new()
    for o in mallas:
        me = o.data.copy()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    for o in mallas:
        bpy.data.objects.remove(o)
    ob = objeto_desde_bmesh(nombre, bm, coleccion, material, suave=True)
    # Centrar en XY y apoyar la base en z=0
    xs = [v.co.x for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    zs = [v.co.z for v in ob.data.vertices]
    ob.data.transform(Matrix.Translation(Vector((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs)))))
    mayor = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    ob.scale = (tamano / mayor,) * 3
    return ob


# ---------------------------------------------------------------- escena
def preparar_escena():
    nombre = "Cable_Submarino"
    vieja = bpy.data.scenes.get(nombre)
    if vieja:
        for o in list(vieja.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.scenes.remove(vieja)
    esc = bpy.data.scenes.new(nombre)
    if bpy.context.window:
        bpy.context.window.scene = esc
    return esc


def construir():
    esc = preparar_escena()
    col = esc.collection

    # Render
    motores = {i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    esc.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in motores else "BLENDER_EEVEE_NEXT"
    esc.render.resolution_x, esc.render.resolution_y = ANCHO, ALTO
    esc.render.resolution_percentage = 100
    esc.render.fps = FPS
    esc.frame_start, esc.frame_end = 1, FRAMES
    esc.view_settings.view_transform = "Standard"
    esc.eevee.taa_render_samples = int(arg("--samples", 16))
    esc.render.image_settings.file_format = "PNG"
    esc.render.image_settings.color_mode = "RGB"
    esc.render.image_settings.compression = 40

    # Contorno Freestyle
    esc.render.use_freestyle = True
    esc.render.line_thickness_mode = "ABSOLUTE"
    esc.render.line_thickness = 1.6
    vl = esc.view_layers[0]
    vl.use_freestyle = True
    fs = vl.freestyle_settings
    fs.crease_angle = math.radians(140)
    ls = fs.linesets[0] if fs.linesets else fs.linesets.new("Contorno")
    ls.select_by_visibility = True
    ls.select_silhouette = True
    ls.select_border = True
    ls.select_crease = True
    ls.select_contour = False
    ls.linestyle.color = hex_lin(P["linea"])[:3]
    ls.linestyle.thickness = 1.6

    # Mundo: la cámara ve blanco roto; la luz ambiente es casi nula (para que las sombras sean índigo)
    mundo = bpy.data.worlds.new("Mundo_cable")
    mundo.use_nodes = True
    wn, wl = mundo.node_tree.nodes, mundo.node_tree.links
    wn.clear()
    visto = wn.new("ShaderNodeBackground")
    visto.inputs["Color"].default_value = hex_lin(P["fondo"])
    luz = wn.new("ShaderNodeBackground")
    luz.inputs["Color"].default_value = (0.03, 0.03, 0.05, 1)
    camino = wn.new("ShaderNodeLightPath")
    mezcla = wn.new("ShaderNodeMixShader")
    sal = wn.new("ShaderNodeOutputWorld")
    wl.new(camino.outputs["Is Camera Ray"], mezcla.inputs["Fac"])
    wl.new(luz.outputs["Background"], mezcla.inputs[1])
    wl.new(visto.outputs["Background"], mezcla.inputs[2])
    wl.new(mezcla.outputs["Shader"], sal.inputs["Surface"])
    esc.world = mundo

    # Materiales
    M = {
        "arena": material_toon("T_arena", P["arena"]),
        "arena_corte": material_toon("T_arena_corte", P["arena_corte"], rayado=(P["rayado"], 9.0)),
        "arcilla": material_toon("T_arcilla", P["arcilla"]),
        "arcilla_corte": material_toon("T_arcilla_corte", P["arcilla"], rayado=(P["rayado"], 9.0)),
        "agua_fondo": material_toon("T_agua_fondo", P["agua_2"],
                                    bandas_z=[(Z_LECHO, P["agua_3"]), (1.6, P["agua_2"]), (3.1, P["agua_1"])]),
        "superficie": material_toon("T_superficie", P["superficie"]),
        "casco": material_toon("T_casco", P["casco"]),
        "cabina": material_toon("T_cabina", P["cabina"]),
        "roca": material_toon("T_roca", P["roca"]),
        "boya": material_toon("T_boya", P["boya"]),
        "funda": material_toon("T_funda", P["funda"]),
        "acero": material_toon("T_acero", P["acero"]),
        "cobre": material_toon("T_cobre", P["cobre"]),
        "gel": material_toon("T_gel", P["gel"]),
        "fibra": material_toon("T_fibra", P["fibra"]),
    }

    # Lecho marino en dos capas; la cara frontal (corte) lleva rayado
    def idx_corte(n):
        return 1 if n.y < -0.9 else 0
    caja("Lecho_arena", X0, X1, Y0, Y1, Z_ARCILLA, Z_LECHO, col, [M["arena"], M["arena_corte"]], idx_corte)
    caja("Lecho_arcilla", X0, X1, Y0, Y1, Z_BASE, Z_ARCILLA, col, [M["arcilla"], M["arcilla_corte"]], idx_corte)

    # Agua: pared del fondo con bandas de profundidad + lámina de superficie
    caja("Agua_fondo", X0, X1, Y1, Y1 + 0.08, Z_LECHO, Z_AGUA, col, [M["agua_fondo"]])
    # Superficie: solo la cara superior (visible desde arriba, invisible desde abajo) y un
    # canto frontal fino que marca la línea del agua en el corte. No proyecta sombra.
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((X0, Y0, Z_AGUA), (X1, Y0, Z_AGUA), (X1, Y1, Z_AGUA), (X0, Y1, Z_AGUA))]
    bm.faces.new(vs)
    sin_contorno = bpy.data.collections.new("Sin_contorno")
    col.children.link(sin_contorno)
    sup = objeto_desde_bmesh("Agua_superficie", bm, sin_contorno, M["superficie"])
    M["superficie"].use_backface_culling = True
    sup.visible_shadow = False
    # Freestyle no respeta el backface culling: la superficie queda fuera del contorno
    ls.select_by_collection = True
    ls.collection = sin_contorno
    ls.collection_negation = "EXCLUSIVE"
    canto = caja("Agua_canto", X0, X1, Y0 - 0.01, Y0, Z_AGUA - 0.07, Z_AGUA, col, [M["superficie"]])
    canto.visible_shadow = False

    # Cable por capas (cara frontal en y=Y0; se despliega en escalera al final)
    largo = 6.7
    z_c = R_CABLE
    capas = [
        ("Cable_funda", lambda: cilindro_y("Cable_funda", R_CABLE, largo, col, M["funda"]), 0.00),
        ("Cable_armadura", lambda: anillo_cilindros_y("Cable_armadura", 18, 0.087, 0.0125, largo, col, M["acero"]), 0.12),
        ("Cable_cobre", lambda: cilindro_y("Cable_cobre", 0.074, largo, col, M["cobre"]), 0.22),
        ("Cable_gel", lambda: cilindro_y("Cable_gel", 0.056, largo, col, M["gel"]), 0.31),
        ("Cable_fibras", lambda: anillo_cilindros_y("Cable_fibras", 8, 0.028, 0.0095, largo, col, M["fibra"]), 0.41),
    ]
    cable = {}
    for i, (nombre, crear, salida_final) in enumerate(capas):
        ob = crear()
        ob.location = (0.0, Y0, z_c)
        # Antes del despliegue cada capa interior queda 3 mm más adentro (evita z-fighting)
        cable[nombre] = (ob, salida_final, 0.003 * i)

    # Rocas Poly Haven (CC0)
    r1 = importar_polyhaven("moon_rock_02", col, 0.62, M["roca"], "Roca_A")
    r1.location = (0.62, -0.9, -0.08)
    r1.rotation_euler = (0.1, 0.0, 0.7)
    r2 = importar_polyhaven("moon_rock_03", col, 0.38, M["roca"], "Roca_B")
    r2.location = (-0.55, 0.9, -0.04)
    r3 = importar_polyhaven("moon_rock_02", col, 0.34, M["roca"], "Roca_C")
    r3.location = (-0.85, -2.15, -0.05)
    r3.rotation_euler = (0.0, 0.2, 2.1)

    # Superficie: barco (formas simples) y boya Poly Haven (CC0)
    b = barco(col, M["casco"], M["cabina"])
    b.location = (0.25, 0.6, Z_AGUA - 0.12)
    b.rotation_euler = (0, 0, math.radians(-25))
    drv = b.driver_add("location", 2).driver
    drv.type = "SCRIPTED"
    drv.expression = f"{Z_AGUA - 0.12} + 0.025*sin(frame/11)"
    drv_r = b.driver_add("rotation_euler", 0).driver
    drv_r.type = "SCRIPTED"
    drv_r.expression = "0.03*sin(frame/13 + 1.2)"
    boya = importar_polyhaven("ocean_buoy", col, 0.62, M["boya"], "Boya")
    boya.location = (-1.15, -1.7, Z_AGUA - 0.16)

    # Luz: sol desde arriba-izquierda-frente; sombras nítidas
    sol_d = bpy.data.lights.new("Sol", "SUN")
    sol_d.energy = 3.5
    sol_d.angle = math.radians(1.0)
    sol = bpy.data.objects.new("Sol", sol_d)
    col.objects.link(sol)
    sol.rotation_euler = (math.radians(50), 0, math.radians(-38))

    # Cámara con objetivo (Track To)
    cam_d = bpy.data.cameras.new("Camara")
    cam_d.lens = 35
    cam_d.clip_start = 0.05
    cam = bpy.data.objects.new("Camara", cam_d)
    col.objects.link(cam)
    obj = bpy.data.objects.new("Camara_objetivo", None)
    col.objects.link(obj)
    t = cam.constraints.new("TRACK_TO")
    t.target = obj
    t.track_axis = "TRACK_NEGATIVE_Z"
    t.up_axis = "UP_Y"
    esc.camera = cam

    animar(cam, obj, cable)
    esc.frame_set(1)
    return esc


# ---------------------------------------------------------------- animación
# Planos (posición de cámara, objetivo, focal)
PLANOS = {
    "inicio":   ((0.9, -6.9, 6.3), (0.15, 0.2, 3.9), 35),
    "general":  ((2.6, -9.6, 2.9), (0.0, 0.2, 1.85), 35),
    "cable":    ((1.25, -4.6, 0.95), (0.0, -1.5, 0.12), 35),
    "corte":    ((0.62, -4.25, 0.46), (0.0, -3.22, 0.12), 40),
}
# Fotogramas (1 = primero). Movimientos de 1,5-1,8 s y pausas de 2,5 s
TIEMPOS = [
    (1, "inicio"), (24, "inicio"),       # 0,8 s de respiro
    (78, "general"),                     # mov. 1 (1,8 s)
    (153, "general"),                    # pausa 2,5 s
    (207, "cable"),                      # mov. 2 (1,8 s)
    (282, "cable"),                      # pausa 2,5 s
    (336, "corte"),                      # mov. 3 (1,8 s)
    (450, "corte"),                      # final (capas se despliegan 342-396)
]
DESPLIEGUE = (342, 396)


def _clave(ob, ruta, f, valor):
    setattr(ob, ruta, valor) if not isinstance(valor, tuple) else setattr(ob, ruta, valor)
    ob.keyframe_insert(data_path=ruta, frame=f)


def animar(cam, obj, cable):
    for f, plano in TIEMPOS:
        pos, objetivo, lente = PLANOS[plano]
        cam.location = pos
        cam.keyframe_insert("location", frame=f)
        obj.location = objetivo
        obj.keyframe_insert("location", frame=f)
        cam.data.lens = lente
        cam.data.keyframe_insert("lens", frame=f)

    for ob, salida, hundido in cable.values():
        ob.location.y = Y0 + hundido
        ob.keyframe_insert("location", index=1, frame=1)
        ob.keyframe_insert("location", index=1, frame=DESPLIEGUE[0])
        ob.location.y = Y0 - salida
        ob.keyframe_insert("location", index=1, frame=DESPLIEGUE[1])
        ob.location.y = Y0 - salida
        ob.keyframe_insert("location", index=1, frame=FRAMES)

    # Suavizado: entrada y salida lentas en todos los movimientos
    for idb in (cam, obj, cam.data, *[c[0] for c in cable.values()]):
        ad = idb.animation_data
        if not ad or not ad.action:
            continue
        curvas = []
        try:
            curvas = list(ad.action.fcurves)
        except AttributeError:
            for capa in ad.action.layers:
                for tira in capa.strips:
                    for bolsa in tira.channelbags:
                        curvas.extend(bolsa.fcurves)
        for fc in curvas:
            for k in fc.keyframe_points:
                k.interpolation = "BEZIER"
                k.easing = "AUTO"
                k.handle_left_type = k.handle_right_type = "AUTO_CLAMPED"
            fc.update()


# ---------------------------------------------------------------- render
def renderizar(esc):
    salida = arg("--out", os.path.join(PROYECTO, "04_blender", "frames"))
    os.makedirs(salida, exist_ok=True)
    rango = arg("--frames")
    if isinstance(rango, str) and "-" in rango:
        a, b = (int(x) for x in rango.split("-"))
        esc.frame_start, esc.frame_end = a, b
    esc.render.filepath = os.path.join(salida, "f_####")
    bpy.ops.render.render(animation=True, scene=esc.name)
    print(f"RENDER_OK {esc.frame_start}-{esc.frame_end} -> {salida}")


if __name__ == "__main__":
    if bpy.app.background:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    escena = construir()
    print("ESCENA_OK", escena.name, len(escena.objects), "objetos")
    if arg("--render"):
        renderizar(escena)
elif __name__ == "mcp":
    escena = construir()
    print("ESCENA_OK", escena.name, len(escena.objects), "objetos")
