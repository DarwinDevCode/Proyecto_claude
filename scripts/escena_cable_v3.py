"""Paso 3 · Short "cable submarino": escena v3 y fotogramas clave del storyboard.

Reutiliza las utilidades de la v2 (materiales toon, bloque de agua, importadores) cargando
scripts/escena_cable_submarino_v2.py como biblioteca, y aplica las correcciones de
proyectos/2026-11-22_cable-submarino/03_storyboard/plan.md:
  - cable con el orden real de capas (fibras -> acero -> cobre -> polietileno), sin "gel";
  - agua menos opaca y solo en los planos que la necesitan;
  - ninguna cámara bajo la superficie con un barco en cuadro;
  - corte del cable >= 50 % del ancho en los macros; la mano entra desde el borde.
Modelos nuevos (biblioteca/LICENCIAS.csv): barco cablero (TugBoat adaptado, D-006), ancla,
tiburón, pesquero; gancho y red de arrastre con formas simples (D-006).

Uso:
  MCP:   exec(open(r"<ruta>", encoding="utf-8").read(), {"ROOT": r"<raíz>", "__name__": "mcp"})
         luego aplicar_plano("P1a") en el mismo espacio de nombres.
  Stills del storyboard:
         "<blender.exe>" -b --factory-startup --python "scripts/escena_cable_v3.py" -- --storyboard [--planos P1a,P2]
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

if "ROOT" in globals():
    ROOT = globals()["ROOT"]
else:
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROYECTO = os.path.join(ROOT, "proyectos", "2026-11-22_cable-submarino")
MODELOS = os.path.join(ROOT, "biblioteca", "modelos3d")

# --- utilidades de la v2 como biblioteca --------------------------------------------------
V2 = {"ROOT": ROOT, "__name__": "lib"}
exec(open(os.path.join(ROOT, "scripts", "escena_cable_submarino_v2.py"), encoding="utf-8").read(), V2)
P = V2["P"]
P.update({"cablero": "#3A7CA5", "chispa": "#FFE066", "red": "#E8DCC0", "linea_cabo": "#5B5F73"})
hex_lin = V2["hex_lin"]
material_toon = V2["material_toon"]
X0, X1, Y0, Y1 = V2["X0"], V2["X1"], V2["Y0"], V2["Y1"]
Z_LECHO, Z_ARCILLA, Z_BASE, Z_AGUA = V2["Z_LECHO"], V2["Z_ARCILLA"], V2["Z_BASE"], V2["Z_AGUA"]
R_CABLE = V2["R_CABLE"]
objeto_desde_bmesh = V2["objeto_desde_bmesh"]

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(nombre, defecto=None):
    if nombre in ARGS:
        i = ARGS.index(nombre)
        return ARGS[i + 1] if i + 1 < len(ARGS) and not ARGS[i + 1].startswith("--") else True
    return defecto


FPS = 30
FRAMES = 1492            # voz (con E3 empalmada): última palabra a 48,70 s + 1 s

# ------------------------------------------------------------------------------ geometría
def cilindro_entre(nombre, a, b, radio, coleccion, material, segmentos=10):
    """Cilindro fino entre dos puntos (cabos, cadenas, líneas del gancho)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segmentos, radius1=radio, radius2=radio, depth=d.length)
    rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=bm.verts)
    return objeto_desde_bmesh(nombre, bm, coleccion, material, suave=True)


def cable_capas(coleccion, M, prefijo="Cable", y_trasero=Y1, largo=None):
    """Cable con el orden real: fibras (centro) -> acero -> cobre -> polietileno (exterior).
    Origen de cada capa en el extremo trasero; se despliega escalando Y."""
    largo = largo or (y_trasero - Y0)
    cyl = V2["cilindro_y_atras"]
    ring = V2["anillo_y_atras"]
    capas = [
        (f"{prefijo}_polietileno", lambda: cyl(f"{prefijo}_polietileno", R_CABLE, largo, coleccion, M["funda"]), 0.00),
        (f"{prefijo}_cobre", lambda: cyl(f"{prefijo}_cobre", 0.078, largo, coleccion, M["cobre"]), 0.12),
        (f"{prefijo}_acero", lambda: ring(f"{prefijo}_acero", 14, 0.052, 0.0135, largo, coleccion, M["acero"]), 0.22),
        (f"{prefijo}_fibras", lambda: ring(f"{prefijo}_fibras", 8, 0.022, 0.0085, largo, coleccion, M["fibra"]), 0.33),
    ]
    out = []
    for i, (nombre, crear, salida) in enumerate(capas):
        ob = crear()
        ob.location = (0.0, y_trasero, R_CABLE)
        out.append({"ob": ob, "largo": largo, "salida": salida, "hundido": 0.004 * i})
    # relleno interior del acero (para que no se vea hueco entre fibras y acero)
    nucleo = cyl(f"{prefijo}_nucleo", 0.040, largo, coleccion, M["gel_neutro"])
    nucleo.location = (0.0, y_trasero, R_CABLE)
    out.append({"ob": nucleo, "largo": largo, "salida": 0.27, "hundido": 0.010})
    return out


def desplegar(capas, t):
    """t=0: cara plana (capas interiores apenas hundidas); t=1: escalera completa."""
    for c in capas:
        sal = -c["hundido"] * (1 - t) + c["salida"] * t
        c["ob"].scale = (1, (c["largo"] + sal) / c["largo"], 1)


def gancho(coleccion, material):
    """Gancho de reparación (grapnel), formas simples (D-006): eje, anilla y 4 uñas curvas."""
    partes = []
    partes.append(cilindro_entre("Gancho_eje", (0, 0, 0), (0, 0, 0.55), 0.022, coleccion, material))
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=False, segments=16, radius=0.05)
    me = bpy.data.meshes.new("tmp_anilla")
    bm.to_mesh(me)
    bm.free()
    anilla = bpy.data.objects.new("Gancho_anilla", me)
    coleccion.objects.link(anilla)
    anilla.rotation_euler = (math.radians(90), 0, 0)
    anilla.location = (0, 0, 0.6)
    sk = anilla.modifiers.new("grosor", "SKIN")
    for v in me.skin_vertices[0].data:
        v.radius = (0.012, 0.012)
    anilla.data.materials.append(material)
    partes.append(anilla)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        dirx, diry = math.cos(a), math.sin(a)
        p0 = Vector((0, 0, 0.02))
        p1 = Vector((dirx * 0.16, diry * 0.16, 0.04))
        p2 = Vector((dirx * 0.2, diry * 0.2, 0.2))
        partes.append(cilindro_entre(f"Gancho_una{k}a", p0, p1, 0.017, coleccion, material))
        partes.append(cilindro_entre(f"Gancho_una{k}b", p1, p2, 0.015, coleccion, material))
    raiz = bpy.data.objects.new("Gancho", None)
    coleccion.objects.link(raiz)
    for p in partes:
        p.parent = raiz
    return raiz


def red_arrastre(coleccion, material):
    """Red de arrastre (formas simples, D-006): cono de malla con modificador Wireframe."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=14, radius1=0.42, radius2=0.08, depth=1.3)
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.1],
                              cuts=5, use_grid_fill=False)
    bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.radians(-90), 4, "X"), verts=bm.verts)
    ob = objeto_desde_bmesh("Red", bm, coleccion, material)
    w = ob.modifiers.new("malla", "WIREFRAME")
    w.thickness = 0.018
    w.use_even_offset = False
    return ob


def material_toon_textura(nombre, imagen):
    """Toon de 3 bandas cuyo color base es una textura (modelos con color en imagen)."""
    mat = material_toon(nombre, "#FFFFFF")
    nt = mat.node_tree
    rgb = next(n for n in nt.nodes if n.type == "RGB")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = imagen
    for l in list(rgb.outputs[0].links):
        nt.links.new(tex.outputs["Color"], l.to_socket)
    nt.nodes.remove(rgb)
    return mat


def importar_textura_toon(ruta, coleccion, tamano, nombre, prefijo_imagen):
    """Importa un .glb cuyo color está en una textura y le aplica toon con esa textura."""
    antes = set(bpy.data.images)
    ob = V2["importar_glb"](ruta, coleccion, tamano, nombre)
    img = next((i for i in bpy.data.images if i not in antes and i.name.startswith(prefijo_imagen)), None) \
        or next((i for i in bpy.data.images if i.name.startswith(prefijo_imagen)), None)
    if img:
        m = material_toon_textura(f"T3_tex_{nombre}", img)
        ob.data.materials.clear()
        ob.data.materials.append(m)
        for p in ob.data.polygons:
            p.material_index = 0
    return ob


def importar_rig(ruta, coleccion, tamano, nombre):
    """Importa un .glb con esqueleto SIN unir mallas: escala el objeto raíz y pasa los
    materiales a toon conservando su color."""
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=ruta)
    # Solo lo que el importador enlazó a la escena: su "Icosphere" de forma de hueso queda fuera
    nuevos = [o for o in bpy.data.objects if o not in antes and o.users_collection]
    formas_hueso = {pb.custom_shape for o in nuevos if o.type == "ARMATURE" for pb in o.pose.bones if pb.custom_shape}
    for f in formas_hueso:
        for c in list(f.users_collection):
            c.objects.unlink(f)
    nuevos = [o for o in nuevos if o not in formas_hueso]
    for o in nuevos:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coleccion.objects.link(o)
    raices = [o for o in nuevos if o.parent is None]
    raiz = bpy.data.objects.new(nombre, None)
    coleccion.objects.link(raiz)
    for r in raices:
        r.parent = raiz
    bpy.context.view_layer.update()
    mallas = [o for o in nuevos if o.type == "MESH"]
    pts = [o.matrix_world @ Vector(c) for o in mallas for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centro = (lo + hi) / 2
    for r in raices:
        r.location -= centro
    raiz.scale = (tamano / max(hi - lo),) * 3
    for o in mallas:
        for sl in o.material_slots:
            m = sl.material
            color = (0.8, 0.8, 0.8, 1)
            if m and m.use_nodes:
                b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                if b:
                    color = tuple(b.inputs["Base Color"].default_value)
            sl.material = material_toon(f"T3_rig_{V2['lin_hex'](color)[1:]}", V2["lin_hex"](color))
    return raiz


def recolorear_oscuros(ob, material_nuevo, umbral=0.06):
    """Sustituye los materiales casi negros de un modelo importado (casco del TugBoat)."""
    for i, slot in enumerate(ob.material_slots):
        m = slot.material
        if not m or not m.use_nodes:
            continue
        rgb = next((n for n in m.node_tree.nodes if n.type == "RGB"), None)
        if rgb and sum(rgb.outputs[0].default_value[:3]) / 3 < umbral:
            ob.material_slots[i].material = material_nuevo


# ------------------------------------------------------------------------------ escena
ESC = {}


def construir():
    nombre = "Cable_v3"
    vieja = bpy.data.scenes.get(nombre)
    if vieja:
        for o in list(vieja.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        for c in list(vieja.collection.children_recursive):
            bpy.data.collections.remove(c)
        bpy.data.scenes.remove(vieja)
    esc = bpy.data.scenes.new(nombre)
    if bpy.context.window:
        bpy.context.window.scene = esc
    try:
        esc.blendermcp_use_polypizza = True     # el ajuste del addon es por escena
    except AttributeError:
        pass
    raiz = esc.collection
    col = bpy.data.collections.new("Escena_obj")
    col_agua = bpy.data.collections.new("Agua_col")
    raiz.children.link(col)
    raiz.children.link(col_agua)

    motores = {i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    esc.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in motores else "BLENDER_EEVEE_NEXT"
    esc.render.resolution_x, esc.render.resolution_y = 1080, 1920
    esc.render.resolution_percentage = int(arg("--porcentaje", 100))
    esc.render.fps = FPS
    esc.frame_start, esc.frame_end = 1, FRAMES
    esc.view_settings.view_transform = "Standard"
    esc.eevee.taa_render_samples = int(arg("--samples", 16))
    esc.render.film_transparent = True
    esc.render.image_settings.file_format = "PNG"
    esc.render.image_settings.color_mode = "RGBA"

    vl_escena = esc.view_layers[0]
    vl_escena.name = "escena"
    vl_agua = esc.view_layers.new("agua")
    for vl in (vl_escena, vl_agua):
        vl.use_freestyle = True
    vl_escena.layer_collection.children[col_agua.name].exclude = True
    vl_agua.layer_collection.children[col.name].holdout = True
    esc.render.use_freestyle = True
    esc.render.line_thickness_mode = "ABSOLUTE"
    esc.render.line_thickness = 2.2
    for vl, inclusiva in ((vl_escena, False), (vl_agua, True)):
        fs = vl.freestyle_settings
        # 100° (antes 140°): mantiene las aristas de 90° de la maqueta y elimina los
        # "garabatos" de pliegue sobre las rocas fotogramétricas (manchas negras de la v2)
        fs.crease_angle = math.radians(100)
        ls = fs.linesets[0] if fs.linesets else fs.linesets.new("Contorno")
        V2["configurar_lineset"](ls, col_agua, inclusiva)

    mundo = bpy.data.worlds.new("Mundo_v3")
    mundo.use_nodes = True
    next(n for n in mundo.node_tree.nodes if n.type == "BACKGROUND").inputs["Color"].default_value = (0.03, 0.03, 0.05, 1)
    esc.world = mundo

    M = {k: material_toon(f"T3_{k}", P[k]) for k in
         ("arena", "arcilla", "casco", "cabina", "roca", "boya", "funda", "acero", "cobre", "fibra", "piel", "cablero")}
    M["arena_corte"] = material_toon("T3_arena_corte", P["arena_corte"], rayado=(P["rayado"], 9.0))
    M["arcilla_corte"] = material_toon("T3_arcilla_corte", P["arcilla"], rayado=(P["rayado"], 9.0))
    M["gel_neutro"] = material_toon("T3_nucleo", "#E9E2D0")
    M["metal"] = material_toon("T3_metal", "#8E96A6")
    M["cabo"] = material_toon("T3_cabo", P["linea_cabo"])
    M["red"] = material_toon("T3_red", P["red"])
    M["agua"] = V2["material_agua"]("T3_agua")
    # Agua menos opaca que en la v2 (lados 0,15) para no apagar el color
    mr = next(n for n in M["agua"].node_tree.nodes if n.type == "MAP_RANGE")
    mr.inputs["To Min"].default_value = 0.15
    mr.inputs["To Max"].default_value = 0.75

    def idx_corte(n):
        return 1 if n.y < -0.9 else 0
    V2["caja"]("Lecho_arena", X0, X1, Y0, Y1, Z_ARCILLA, Z_LECHO, col, [M["arena"], M["arena_corte"]], idx_corte)
    V2["caja"]("Lecho_arcilla", X0, X1, Y0, Y1, Z_BASE, Z_ARCILLA, col, [M["arcilla"], M["arcilla_corte"]], idx_corte)
    V2["bloque_agua"](col_agua, M["agua"])

    ESC["cable"] = cable_capas(col, M)
    # Cable roto (E4b) y cable izado (E5b): ocultos salvo en sus planos
    ESC["roto_a"] = cilindro_entre("Roto_A", (0, Y1, R_CABLE), (0, -0.7, R_CABLE), R_CABLE, col, M["funda"], 32)
    ESC["roto_b"] = cilindro_entre("Roto_B", (0, -1.45, R_CABLE), (0, Y0, R_CABLE), R_CABLE, col, M["funda"], 32)

    ph = os.path.join(MODELOS, "polyhaven")
    rocas = [
        ("moon_rock_02", 0.55, (0.75, -0.2, -0.08), (0.1, 0, 0.7)),
        ("moon_rock_03", 0.36, (-0.65, 0.7, -0.04), (0, 0, 0)),
        ("moon_rock_02", 0.32, (-0.95, -2.3, -0.05), (0, 0.2, 2.1)),
    ]
    for i, (rid, t, loc, rot) in enumerate(rocas):
        r = V2["importar_blend"](os.path.join(ph, rid, f"{rid}_1k.blend"), col, t, f"Roca_{i}", M["roca"])
        r.location, r.rotation_euler = loc, rot
        dec = r.modifiers.new("simplificar", "DECIMATE")   # menos facetas => contorno limpio
        dec.ratio = 0.04

    pp = os.path.join(MODELOS, "polypizza")
    ESC["carguero"] = V2["importar_glb"](os.path.join(pp, "barco", "barco.glb"), col, 1.6, "Carguero")
    ESC["mano"] = V2["importar_glb"](os.path.join(pp, "escala", "escala.glb"), col, 2.3, "Mano",
                                     base_en_cero=False, material_fijo=M["piel"], suave=True)
    ESC["cablero"] = V2["importar_glb"](os.path.join(pp, "barco_cablero_base", "tugboat.glb"), col, 1.7, "Cablero")
    recolorear_oscuros(ESC["cablero"], M["cablero"])
    ESC["pesquero"] = importar_textura_toon(os.path.join(pp, "pesquero", "pesquero.glb"), col, 1.3, "Pesquero",
                                            "Tugboat_BaseColor")
    ESC["ancla"] = V2["importar_glb"](os.path.join(pp, "ancla", "ancla.glb"), col, 0.7, "Ancla",
                                      base_en_cero=False, material_fijo=M["metal"])
    ESC["tiburon"] = importar_rig(os.path.join(pp, "tiburon", "tiburon.glb"), col, 1.7, "Tiburon")
    ESC["gancho"] = gancho(col, M["metal"])
    ESC["red"] = red_arrastre(col, M["red"])
    ESC["boya"] = V2["importar_blend"](os.path.join(ph, "ocean_buoy", "ocean_buoy_1k.blend"), col, 0.5, "Boya", M["boya"])
    ESC["boya"].location = (-1.2, -1.9, Z_AGUA - 0.14)

    # Roldana de proa y tambor del cablero (formas simples, D-006); se emparentan al barco
    rold = cilindro_entre("Cablero_roldana", (-0.09, 0, 0), (0.09, 0, 0), 0.13, col, M["metal"], 20)
    tamb = cilindro_entre("Cablero_tambor", (0, -0.22, 0), (0, 0.22, 0), 0.16, col, M["cablero"], 20)
    ESC["roldana"], ESC["tambor"] = rold, tamb
    ESC["cabos"] = []

    sol_d = bpy.data.lights.new("Sol", "SUN")
    sol_d.energy = 3.5
    sol_d.angle = math.radians(1.0)
    sol = bpy.data.objects.new("Sol", sol_d)
    col.objects.link(sol)
    sol.rotation_euler = (math.radians(50), 0, math.radians(38))

    cam_d = bpy.data.cameras.new("Camara")
    cam_d.clip_start = 0.02
    cam = bpy.data.objects.new("Camara", cam_d)
    col.objects.link(cam)
    obj = bpy.data.objects.new("Camara_objetivo", None)
    col.objects.link(obj)
    t = cam.constraints.new("TRACK_TO")
    t.target = obj
    t.track_axis = "TRACK_NEGATIVE_Z"
    t.up_axis = "UP_Y"
    esc.camera = cam
    ESC.update({"esc": esc, "col": col, "M": M, "cam": cam, "obj": obj})
    return esc


# ------------------------------------------------------------------------------ planos
OCULTABLES = ("carguero", "mano", "cablero", "pesquero", "ancla", "tiburon", "gancho", "red",
              "roto_a", "roto_b", "boya", "roldana", "tambor")


def _ver(clave, visible):
    ob = ESC[clave]
    for o in [ob] + list(ob.children_recursive):
        o.hide_render = not visible
        o.hide_viewport = not visible


def _cable_visible(visible):
    for c in ESC["cable"]:
        c["ob"].hide_render = not visible
        c["ob"].hide_viewport = not visible


def _limpiar_cabos():
    for o in ESC["cabos"]:
        bpy.data.objects.remove(o, do_unlink=True)
    ESC["cabos"] = []


def _cabo(nombre, a, b, radio=0.012, material=None):
    o = cilindro_entre(nombre, a, b, radio, ESC["col"], material or ESC["M"]["cabo"], 24 if radio > 0.05 else 10)
    ESC["cabos"].append(o)
    return o


def _camara(pos, objetivo, lente):
    ESC["cam"].location = pos
    ESC["obj"].location = objetivo
    ESC["cam"].data.lens = lente


def _cablero_en(pos, giro_z):
    b = ESC["cablero"]
    b.location = pos
    b.rotation_euler = (0, 0, giro_z)
    bpy.context.view_layer.update()
    mw = b.matrix_world
    # proa = extremo +Y local del modelo normalizado (TugBoat: eslora en Y tras importar)
    proa = mw @ Vector((0, 0.8 / b.scale[1] * 1.0, 0.0))
    return mw


def _mano_borde(pos, giro_z=math.radians(180), inclinacion=0.0):
    m = ESC["mano"]
    m.location = pos
    m.rotation_euler = (inclinacion, 0, giro_z)


# Cada plano: cámara, visibilidad, poses y capas que se componen.
def aplicar_plano(nombre):
    esc = ESC["esc"]
    _limpiar_cabos()
    for k in OCULTABLES:
        _ver(k, False)
    _cable_visible(True)
    desplegar(ESC["cable"], 0.0)
    capas = ["escena"]

    if nombre in ("P1a", "P1b", "P6"):
        # Macro del corte: el cable ocupa > 50 % del ancho
        _camara((0.34, -4.0, 0.36), (0.0, -3.05, 0.125), 56)   # corte >= 50 % del ancho
        desplegar(ESC["cable"], 0.18)     # capas visibles desde el fotograma 0
        if nombre in ("P1b", "P6"):
            _ver("mano", True)
            # dedos hacia +X (hacia el cable) y muñeca fuera de cuadro por la izquierda;
            # la yema del índice queda junto al extremo del cable
            _mano_borde(tuple(ESC.get("mano_pos", (-1.17, -3.2, 0.03))), math.radians(90),
                        ESC.get("mano_incl", 0.0))
    elif nombre == "P2":
        # Plano general a la altura de la superficie (ni barco visto desde abajo ni cortado)
        _camara((2.9, -8.6, 3.45), (0.0, -0.4, 1.55), 35)
        _ver("carguero", True)
        _ver("boya", True)
        ESC["carguero"].location = (0.3, -0.2, Z_AGUA - 0.14)
        ESC["carguero"].rotation_euler = (0, 0, math.radians(-28))
        capas = ["escena", "agua"]
    elif nombre in ("P3a", "P3b"):
        _camara((0.42, -4.05, 0.4), (0.0, -3.2, 0.125), 50)
        desplegar(ESC["cable"], 0.55 if nombre == "P3a" else 1.0)
    elif nombre == "P4a":
        _camara((1.7, -5.6, 1.05), (0.0, -1.3, 0.45), 35)
        _ver("tiburon", True)
        # el tiburón pasa por encima del cable, mirándolo de reojo (gag "¿Tiburones? Casi nunca")
        ESC["tiburon"].location = (0.15, -1.9, 0.75)
        ESC["tiburon"].rotation_euler = (0, math.radians(-12), math.radians(-30))
        capas = ["escena", "agua"]
    elif nombre == "P4b":
        _camara((1.7, -5.6, 1.05), (0.0, -1.2, 0.45), 35)
        _cable_visible(False)
        _ver("roto_a", True)
        _ver("roto_b", True)
        _ver("ancla", True)
        _ver("red", True)
        # ancla enganchada en el hueco del cable roto (y entre -0.7 y -1.45)
        ESC["ancla"].location = (-0.15, -1.08, 0.36)
        ESC["ancla"].rotation_euler = (math.radians(-20), math.radians(10), math.radians(80))
        _cabo("Cadena", (-0.15, -1.08, 0.7), (-0.9, 0.6, Z_AGUA), 0.02)
        # red de arrastre de perfil (eje a lo largo de X), arrastrada sobre el tramo de atrás
        ESC["red"].location = (0.75, -0.2, 0.42)
        ESC["red"].rotation_euler = (0, 0, math.radians(90))
        _cabo("Calon_1", (0.1, -0.05, 0.62), (-0.4, 1.6, Z_AGUA), 0.01)
        _cabo("Calon_2", (0.1, -0.35, 0.62), (-0.4, 1.3, Z_AGUA), 0.01)
        capas = ["escena", "agua"]
    elif nombre in ("P5a", "P5b"):
        _camara((2.9, -8.6, 3.45), (0.0, -0.6, 1.55), 35)
        _ver("cablero", True)
        _ver("roldana", True)
        _ver("tambor", True)
        _ver("gancho", True)
        b = ESC["cablero"]
        # de costado a la cámara: eslora en X, proa hacia -X (medido: cubierta a z≈Z_AGUA+0.25)
        b.location = (0.15, -0.9, Z_AGUA - 0.16)
        b.rotation_euler = (0, 0, 0)
        bpy.context.view_layer.update()
        proa = (-0.75, -0.9, Z_AGUA + 0.27)
        ESC["roldana"].location = proa
        ESC["roldana"].scale = (0.8, 0.8, 0.8)
        ESC["tambor"].location = (0.6, -0.9, Z_AGUA + 0.36)
        ESC["tambor"].scale = (0.75, 0.75, 0.75)
        if nombre == "P5a":
            ESC["gancho"].location = (-0.1, -1.05, 0.05)
            ESC["gancho"].rotation_euler = (0, 0, 0)
            _cabo("Linea_gancho", (-0.1, -1.05, 0.66), proa)
        else:
            _cable_visible(False)
            _ver("roto_a", True)
            _ver("roto_b", True)
            ESC["gancho"].location = (-0.75, -0.9, Z_AGUA - 0.75)
            _cabo("Linea_gancho", (-0.75, -0.9, Z_AGUA - 0.14), proa)
            # los dos extremos del cable suben en V hasta la roldana (color del cable)
            _cabo("Izado_1", (0, -0.7, R_CABLE), (proa[0] + 0.05, proa[1] + 0.08, proa[2] - 0.05), R_CABLE * 0.85, ESC["M"]["funda"])
            _cabo("Izado_2", (0, -1.45, R_CABLE), (proa[0] + 0.05, proa[1] - 0.08, proa[2] - 0.05), R_CABLE * 0.85, ESC["M"]["funda"])
        capas = ["escena", "agua"]
    else:
        raise ValueError(nombre)
    bpy.context.view_layer.update()
    return capas


PLANOS_STORYBOARD = ["P1a", "P1b", "P2", "P3a", "P3b", "P4a", "P4b", "P5a", "P5b", "P6"]


def storyboard():
    esc = ESC["esc"]
    salida = arg("--out", os.path.join(PROYECTO, "03_storyboard", "capas"))
    os.makedirs(salida, exist_ok=True)
    pedidos = arg("--planos")
    planos = pedidos.split(",") if isinstance(pedidos, str) else PLANOS_STORYBOARD
    esc.render.use_single_layer = True
    for p in planos:
        capas = aplicar_plano(p)
        for capa in capas:
            esc.render.filepath = os.path.join(salida, f"{p}_{capa}.png")
            bpy.ops.render.render(write_still=True, scene=esc.name, layer=capa)
            print(f"STILL_OK {p} {capa}")


if __name__ == "__main__":
    if bpy.app.background:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    construir()
    print("ESCENA_OK v3")
    if arg("--storyboard"):
        storyboard()
elif __name__ == "mcp":
    construir()
    print("ESCENA_OK v3", len(ESC["esc"].objects), "objetos")
