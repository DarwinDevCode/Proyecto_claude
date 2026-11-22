"""Paso 2B · Prueba 3D v2: corte tipo maqueta del océano con cable de fibra óptica.

Cambios respecto a v1: bloque de agua semitransparente de una pieza con superficie ondulada,
barco apoyado en el agua, objeto de escala junto al cable, cámara rápida (0,6-1 s) con
desenfoque de movimiento y render en DOS capas (Freestyle no respeta la transparencia):
  - capa "escena": todo menos el agua, con contorno, fondo transparente.
  - capa "agua": solo el bloque de agua (el resto en holdout), con su contorno.
Remotion compone: fondo + escena + agua.

Uso:
  MCP:    exec(open(r"<ruta>", encoding="utf-8").read(), {"ROOT": r"<raíz>", "__name__": "mcp"})
  Render: "<blender.exe>" -b --factory-startup --python "scripts/escena_cable_submarino_v2.py" -- --render --capa escena
          (y otra vez con --capa agua). Opciones: --frames 1-304  --out "<carpeta>"  --samples 16
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
PROYECTO = os.path.join(ROOT, "proyectos", "2026-11-21_prueba-3d")
MODELOS = os.path.join(ROOT, "biblioteca", "modelos3d")

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(nombre, defecto=None):
    if nombre in ARGS:
        i = ARGS.index(nombre)
        return ARGS[i + 1] if i + 1 < len(ARGS) and not ARGS[i + 1].startswith("--") else True
    return defecto


def hex_lin(h):
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def lin_hex(rgba):
    out = []
    for c in rgba[:3]:
        c = max(0.0, min(1.0, c))
        s = c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
        out.append(round(s * 255))
    return "#%02X%02X%02X" % tuple(out)


P = {
    "fondo": "#F3F0EA",
    "indigo": "#3D4FA0",
    "linea": "#2B3150",
    "arena": "#EBD3A4",
    "arena_corte": "#DDBB86",
    "arcilla": "#CFA37C",
    "rayado": "#B98A5C",
    "agua": "#7FC8DE",
    "agua_sup": "#A9E0EC",
    "casco": "#E5644E",
    "cabina": "#F6F0E2",
    "roca": "#C9C4BC",
    "boya": "#F2B33D",
    "funda": "#34417A",
    "acero": "#AEB6C4",
    "cobre": "#DB8550",
    "gel": "#F3E7C6",
    "fibra": "#5ED3B5",
    "piel": "#F1C7A3",
}

FPS = 30
FRAMES = 266            # última palabra termina a 7,85 s; el video dura 1 s más (8,85 s)
ANCHO, ALTO = 1080, 1920

X0, X1 = -1.8, 1.8
Y0, Y1 = -3.0, 1.8      # Y0 = cara de corte frontal
Z_LECHO = 0.0
Z_ARCILLA = -0.38
Z_BASE = -1.05
Z_AGUA = 3.3
R_CABLE = 0.12


# ---------------------------------------------------------------- nodos
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


def _toon_color(nt, color_base):
    """Devuelve el socket de color toon (3 bandas, sombra índigo) para un color base."""
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
    return _mix_rgb(nt, fac=bandas.outputs["Color"], a=sombra, b=color_base)


def material_toon(nombre, base, rayado=None):
    mat = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    rgb = nt.nodes.new("ShaderNodeRGB")
    rgb.outputs[0].default_value = hex_lin(base)
    color_base = rgb.outputs[0]
    if rayado:
        h_linea, escala = rayado
        coord = nt.nodes.new("ShaderNodeTexCoord")
        onda = nt.nodes.new("ShaderNodeTexWave")
        onda.wave_type = "BANDS"
        onda.bands_direction = "DIAGONAL"
        onda.inputs["Scale"].default_value = escala
        onda.inputs["Distortion"].default_value = 0.0
        rampa = nt.nodes.new("ShaderNodeValToRGB")
        rampa.color_ramp.interpolation = "CONSTANT"
        rampa.color_ramp.elements[0].color = (0, 0, 0, 1)
        rampa.color_ramp.elements[1].position = 0.82
        rampa.color_ramp.elements[1].color = (1, 1, 1, 1)
        nt.links.new(coord.outputs["Object"], onda.inputs["Vector"])
        nt.links.new(onda.outputs["Fac"], rampa.inputs["Fac"])
        color_base = _mix_rgb(nt, fac=rampa.outputs["Color"], a=color_base, b=hex_lin(h_linea))
    final = _toon_color(nt, color_base)
    emi = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(final, emi.inputs["Color"])
    nt.links.new(emi.outputs["Emission"], out.inputs["Surface"])
    return mat


def material_agua(nombre):
    """Toon semitransparente: caras laterales más transparentes, superficie más opaca."""
    mat = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    es_tapa = nt.nodes.new("ShaderNodeMath")
    es_tapa.operation = "GREATER_THAN"
    es_tapa.inputs[1].default_value = 0.6
    nt.links.new(sep.outputs["Z"], es_tapa.inputs[0])
    color = _mix_rgb(nt, fac=es_tapa.outputs[0], a=hex_lin(P["agua"]), b=hex_lin(P["agua_sup"]))
    final = _toon_color(nt, color)
    emi = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(final, emi.inputs["Color"])
    transp = nt.nodes.new("ShaderNodeBsdfTransparent")
    # opacidad: lados 0,3, superficie 0,9
    opac = nt.nodes.new("ShaderNodeMapRange")
    opac.inputs["To Min"].default_value = 0.3
    opac.inputs["To Max"].default_value = 0.9
    nt.links.new(es_tapa.outputs[0], opac.inputs["Value"])
    mezcla = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(opac.outputs["Result"], mezcla.inputs["Fac"])
    nt.links.new(transp.outputs["BSDF"], mezcla.inputs[1])
    nt.links.new(emi.outputs["Emission"], mezcla.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mezcla.outputs["Shader"], out.inputs["Surface"])
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        try:
            setattr(mat, attr, val)
        except (AttributeError, TypeError):
            pass
    try:
        mat.use_transparency_overlap = False
    except AttributeError:
        pass
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


def bloque_agua(coleccion, material):
    """Bloque de agua de una pieza: superficie ondulada (rejilla) + paredes hasta el lecho."""
    nx, ny = 48, 64
    bm = bmesh.new()
    filas = []
    for j in range(ny + 1):
        y = Y0 + (Y1 - Y0) * j / ny
        fila = []
        for i in range(nx + 1):
            x = X0 + (X1 - X0) * i / nx
            z = Z_AGUA + 0.045 * math.sin(x * 2.3 + y * 0.6) + 0.03 * math.sin(y * 3.1 - x * 0.8)
            fila.append(bm.verts.new((x, y, z)))
        filas.append(fila)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((filas[j][i], filas[j][i + 1], filas[j + 1][i + 1], filas[j + 1][i]))
    sup = list(bm.faces)
    ext = bmesh.ops.extrude_face_region(bm, geom=sup)
    abajo = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
    for v in abajo:
        v.co.z = Z_LECHO + 0.002
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = objeto_desde_bmesh("Agua", bm, coleccion, material)
    # Grupo de vértices de la superficie para el oleaje animado
    vg = ob.vertex_groups.new(name="superficie")
    vg.add([v.index for v in ob.data.vertices if v.co.z > Z_AGUA - 0.2], 1.0, "REPLACE")
    ola = ob.modifiers.new("Oleaje", "WAVE")
    ola.vertex_group = "superficie"
    ola.use_normal = False
    ola.height = 0.035
    ola.width = 0.9
    ola.narrowness = 1.2
    ola.speed = 0.012
    ola.start_position_x = -4.0
    ola.start_position_y = -6.0
    return ob


def cilindro_y_atras(nombre, radio, largo, coleccion, material, segmentos=48, centro_xz=(0.0, 0.0)):
    """Cilindro a lo largo de -Y con el origen en su extremo trasero (y=0) y frente en y=-largo."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segmentos, radius1=radio, radius2=radio, depth=largo)
    bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.radians(-90), 4, "X"), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector((centro_xz[0], -largo / 2, centro_xz[1])), verts=bm.verts)
    return objeto_desde_bmesh(nombre, bm, coleccion, material, suave=True)


def anillo_y_atras(nombre, n, radio_anillo, radio, largo, coleccion, material, segmentos=12):
    bm = bmesh.new()
    for i in range(n):
        a = 2 * math.pi * i / n
        tmp = bmesh.new()
        bmesh.ops.create_cone(tmp, cap_ends=True, segments=segmentos, radius1=radio, radius2=radio, depth=largo)
        bmesh.ops.transform(tmp, matrix=Matrix.Rotation(math.radians(-90), 4, "X"), verts=tmp.verts)
        bmesh.ops.translate(tmp, vec=Vector((radio_anillo * math.cos(a), -largo / 2, radio_anillo * math.sin(a))),
                            verts=tmp.verts)
        me_tmp = bpy.data.meshes.new("tmp")
        tmp.to_mesh(me_tmp)
        tmp.free()
        bm.from_mesh(me_tmp)
        bpy.data.meshes.remove(me_tmp)
    return objeto_desde_bmesh(nombre, bm, coleccion, material, suave=True)


def _unir_y_normalizar(mallas, nombre, coleccion, tamano, material_fijo=None, base_en_cero=True, suave=False):
    """Une mallas importadas en un objeto; convierte sus materiales a toon conservando su color."""
    toon_por_mat = {}
    bm = bmesh.new()
    mats_finales = []
    for o in mallas:
        me = o.data.copy()
        me.transform(o.matrix_world)
        # remapear índices de material al listado final
        mapa = []
        for slot in o.material_slots:
            m = slot.material
            if material_fijo:
                tm = material_fijo
            else:
                color = (0.8, 0.8, 0.8, 1)
                if m and m.use_nodes:
                    bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                    if bsdf:
                        color = tuple(bsdf.inputs["Base Color"].default_value)
                elif m:
                    color = tuple(m.diffuse_color)
                clave = lin_hex(color)
                tm = toon_por_mat.get(clave) or material_toon(f"T_mod_{clave[1:]}", clave)
                toon_por_mat[clave] = tm
            if tm not in mats_finales:
                mats_finales.append(tm)
            mapa.append(mats_finales.index(tm))
        if not mapa:
            tm = material_fijo or material_toon("T_mod_gris", "#CCCCCC")
            if tm not in mats_finales:
                mats_finales.append(tm)
            mapa = [mats_finales.index(tm)]
        for p in me.polygons:
            p.material_index = mapa[min(p.material_index, len(mapa) - 1)]
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    for o in mallas:
        bpy.data.objects.remove(o)
    # Algunos modelos de Poly Pizza traen normales invertidas: recalcular hacia fuera
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # En mallas abiertas (p. ej. la muñeca) recalc puede dejarlas hacia dentro:
    # volumen con signo (respecto al centro) negativo => invertir todas las caras.
    bm.normal_update()
    centro = sum((v.co for v in bm.verts), Vector()) / max(1, len(bm.verts))
    vol = sum((f.calc_center_median() - centro).dot(f.normal) * f.calc_area() for f in bm.faces)
    if vol < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        print(f"NORMALES_INVERTIDAS {nombre}")
    ob = objeto_desde_bmesh(nombre, bm, coleccion, None, suave=suave)
    for m in mats_finales:
        ob.data.materials.append(m)
    xs = [v.co.x for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    zs = [v.co.z for v in ob.data.vertices]
    dz = -min(zs) if base_en_cero else -(min(zs) + max(zs)) / 2
    ob.data.transform(Matrix.Translation(Vector((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, dz))))
    mayor = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    ob.scale = (tamano / mayor,) * 3
    return ob


def importar_blend(ruta, coleccion, tamano, nombre, material_fijo=None, base_en_cero=True):
    with bpy.data.libraries.load(ruta, link=False) as (src, dst):
        dst.objects = list(src.objects)
    mallas = [o for o in dst.objects if o is not None and o.type == "MESH"]
    for o in dst.objects:
        if o is not None and o.type != "MESH":
            bpy.data.objects.remove(o)
    for o in mallas:
        coleccion.objects.link(o)
    bpy.context.view_layer.update() if bpy.context.view_layer else None
    for o in mallas:
        o.matrix_world = o.matrix_world.copy()
    return _unir_y_normalizar(mallas, nombre, coleccion, tamano, material_fijo, base_en_cero)


def importar_glb(ruta, coleccion, tamano, nombre, base_en_cero=True, material_fijo=None, suave=False):
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=ruta)
    nuevos = [o for o in bpy.data.objects if o not in antes]
    bpy.context.view_layer.update()
    mallas = []
    for o in nuevos:
        if o.type == "MESH":
            mw = o.matrix_world.copy()
            o.parent = None
            o.matrix_world = mw
            for c in list(o.users_collection):
                c.objects.unlink(o)
            coleccion.objects.link(o)
            mallas.append(o)
    for o in nuevos:
        if o.type != "MESH":
            bpy.data.objects.remove(o)
    return _unir_y_normalizar(mallas, nombre, coleccion, tamano, material_fijo, base_en_cero, suave)


def barco_simple(coleccion, mat_casco, mat_cabina):
    """Respaldo si no hay modelo de Poly Pizza (no debería usarse en la v2)."""
    largo, ancho, alto = 1.3, 0.46, 0.3
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        x, y, z = v.co.x * largo, v.co.y * ancho, (v.co.z + 0.5) * alto
        if v.co.z < 0:
            y *= 0.45
            x *= 0.86
        if v.co.x > 0:
            y *= 0.08
            x += 0.16 if v.co.z > 0 else 0.0
        v.co = Vector((x, y, z))
    casco = objeto_desde_bmesh("Barco_casco", bm, coleccion, mat_casco)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((0.4, 0.34, 0.24)), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector((-0.26, 0.0, alto + 0.12)), verts=bm.verts)
    cabina = objeto_desde_bmesh("Barco_cabina", bm, coleccion, mat_cabina)
    raiz = bpy.data.objects.new("Barco", None)
    coleccion.objects.link(raiz)
    casco.parent = raiz
    cabina.parent = raiz
    return raiz


# ---------------------------------------------------------------- recursos externos (Poly Pizza)
RECURSOS = {
    # nombre lógico: (ruta relativa a biblioteca/modelos3d, tamaño mayor en m de escena)
    "barco": ("polypizza/barco/barco.glb", 1.6),
    "escala": ("polypizza/escala/escala.glb", 2.3),
}


def ruta_recurso(clave):
    rel, _ = RECURSOS[clave]
    r = os.path.join(MODELOS, *rel.split("/"))
    return r if os.path.exists(r) else None


# ---------------------------------------------------------------- escena
def preparar_escena():
    nombre = "Cable_Submarino_v2"
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
    return esc


def configurar_lineset(ls, coleccion, inclusiva):
    ls.select_by_visibility = True
    ls.select_silhouette = True
    ls.select_border = True
    ls.select_crease = True
    ls.select_contour = False
    ls.select_by_collection = True
    ls.collection = coleccion
    ls.collection_negation = "INCLUSIVE" if inclusiva else "EXCLUSIVE"
    ls.linestyle.color = hex_lin(P["linea"])[:3]
    ls.linestyle.thickness = 2.2


def construir():
    esc = preparar_escena()
    raiz = esc.collection
    col = bpy.data.collections.new("Escena_obj")
    col_agua = bpy.data.collections.new("Agua_col")
    raiz.children.link(col)
    raiz.children.link(col_agua)

    motores = {i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    esc.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in motores else "BLENDER_EEVEE_NEXT"
    esc.render.resolution_x, esc.render.resolution_y = ANCHO, ALTO
    esc.render.resolution_percentage = 100
    esc.render.fps = FPS
    esc.frame_start, esc.frame_end = 1, FRAMES
    esc.view_settings.view_transform = "Standard"
    esc.eevee.taa_render_samples = int(arg("--samples", 16))
    esc.render.film_transparent = True
    esc.render.image_settings.file_format = "PNG"
    esc.render.image_settings.color_mode = "RGBA"
    esc.render.image_settings.compression = 40
    # Desenfoque de movimiento (solo afecta a los tramos con cámara en movimiento)
    esc.render.use_motion_blur = True
    esc.render.motion_blur_shutter = 0.6
    try:
        esc.eevee.motion_blur_steps = 4
    except AttributeError:
        pass

    # Capas: "escena" (sin agua) y "agua" (resto en holdout)
    vl_escena = esc.view_layers[0]
    vl_escena.name = "escena"
    vl_agua = esc.view_layers.new("agua")
    for vl in (vl_escena, vl_agua):
        vl.use_freestyle = True
    vl_escena.layer_collection.children["Agua_col"].exclude = True
    vl_agua.layer_collection.children["Escena_obj"].holdout = True

    esc.render.use_freestyle = True
    esc.render.line_thickness_mode = "ABSOLUTE"
    esc.render.line_thickness = 2.2
    for vl, inclusiva_agua in ((vl_escena, False), (vl_agua, True)):
        fs = vl.freestyle_settings
        fs.crease_angle = math.radians(140)
        ls = fs.linesets[0] if fs.linesets else fs.linesets.new("Contorno")
        configurar_lineset(ls, col_agua if inclusiva_agua else col_agua, inclusiva_agua)

    # Mundo: invisible (film transparente); ambiente casi nulo para sombras índigo
    mundo = bpy.data.worlds.new("Mundo_cable_v2")
    mundo.use_nodes = True
    fondo = next(n for n in mundo.node_tree.nodes if n.type == "BACKGROUND")
    fondo.inputs["Color"].default_value = (0.03, 0.03, 0.05, 1)
    esc.world = mundo

    M = {
        "arena": material_toon("T2_arena", P["arena"]),
        "arena_corte": material_toon("T2_arena_corte", P["arena_corte"], rayado=(P["rayado"], 9.0)),
        "arcilla": material_toon("T2_arcilla", P["arcilla"]),
        "arcilla_corte": material_toon("T2_arcilla_corte", P["arcilla"], rayado=(P["rayado"], 9.0)),
        "agua": material_agua("T2_agua"),
        "casco": material_toon("T2_casco", P["casco"]),
        "cabina": material_toon("T2_cabina", P["cabina"]),
        "roca": material_toon("T2_roca", P["roca"]),
        "boya": material_toon("T2_boya", P["boya"]),
        "funda": material_toon("T2_funda", P["funda"]),
        "acero": material_toon("T2_acero", P["acero"]),
        "cobre": material_toon("T2_cobre", P["cobre"]),
        "gel": material_toon("T2_gel", P["gel"]),
        "fibra": material_toon("T2_fibra", P["fibra"]),
        "piel": material_toon("T2_piel", P["piel"]),
    }

    def idx_corte(n):
        return 1 if n.y < -0.9 else 0
    caja("Lecho_arena", X0, X1, Y0, Y1, Z_ARCILLA, Z_LECHO, col, [M["arena"], M["arena_corte"]], idx_corte)
    caja("Lecho_arcilla", X0, X1, Y0, Y1, Z_BASE, Z_ARCILLA, col, [M["arcilla"], M["arcilla_corte"]], idx_corte)

    bloque_agua(col_agua, M["agua"])

    # Cable: origen en el extremo trasero (y=Y1); se despliega escalando en Y
    largo = Y1 - Y0
    capas = [
        ("Cable_funda", lambda: cilindro_y_atras("Cable_funda", R_CABLE, largo, col, M["funda"]), 0.00),
        ("Cable_armadura", lambda: anillo_y_atras("Cable_armadura", 18, 0.087, 0.0125, largo, col, M["acero"]), 0.12),
        ("Cable_cobre", lambda: cilindro_y_atras("Cable_cobre", 0.074, largo, col, M["cobre"]), 0.22),
        ("Cable_gel", lambda: cilindro_y_atras("Cable_gel", 0.056, largo, col, M["gel"]), 0.31),
        ("Cable_fibras", lambda: anillo_y_atras("Cable_fibras", 8, 0.028, 0.0095, largo, col, M["fibra"]), 0.41),
    ]
    cable = []
    for i, (nombre, crear, salida) in enumerate(capas):
        ob = crear()
        ob.location = (0.0, Y1, R_CABLE)
        cable.append((ob, largo, salida, 0.003 * i))

    # Rocas Poly Haven (CC0)
    ph = os.path.join(MODELOS, "polyhaven")
    r1 = importar_blend(os.path.join(ph, "moon_rock_02", "moon_rock_02_1k.blend"), col, 0.55, "Roca_A", M["roca"])
    r1.location = (0.7, -0.6, -0.08)
    r1.rotation_euler = (0.1, 0.0, 0.7)
    r2 = importar_blend(os.path.join(ph, "moon_rock_03", "moon_rock_03_1k.blend"), col, 0.36, "Roca_B", M["roca"])
    r2.location = (-0.6, 0.6, -0.04)
    r3 = importar_blend(os.path.join(ph, "moon_rock_02", "moon_rock_02_1k.blend"), col, 0.32, "Roca_C", M["roca"])
    r3.location = (-0.95, -2.2, -0.05)
    r3.rotation_euler = (0.0, 0.2, 2.1)

    # Barco (Poly Pizza si existe) apoyado en la superficie, con leve balanceo
    rb = ruta_recurso("barco")
    if rb:
        barco = importar_glb(rb, col, RECURSOS["barco"][1], "Barco")
    else:
        barco = barco_simple(col, M["casco"], M["cabina"])
    calado = float(arg("--calado", 0.14))
    barco.location = (0.25, -0.3, Z_AGUA - calado)
    barco.rotation_euler = (0, 0, math.radians(-28))
    d = barco.driver_add("location", 2).driver
    d.type = "SCRIPTED"
    d.expression = f"{Z_AGUA - calado} + 0.02*sin(frame/9)"
    d = barco.driver_add("rotation_euler", 0).driver
    d.type = "SCRIPTED"
    d.expression = "0.03*sin(frame/11 + 1.2)"

    boya = importar_blend(os.path.join(ph, "ocean_buoy", "ocean_buoy_1k.blend"), col, 0.5, "Boya", M["boya"])
    boya.location = (-1.2, -1.9, Z_AGUA - 0.14)

    # Objeto de escala (Poly Pizza): entra al plano en la segunda frase
    re = ruta_recurso("escala")
    escala = None
    if re:
        escala = importar_glb(re, col, RECURSOS["escala"][1], "Escala", base_en_cero=False, material_fijo=M["piel"], suave=True)

    sol_d = bpy.data.lights.new("Sol", "SUN")
    sol_d.energy = 3.5
    sol_d.angle = math.radians(1.0)
    sol = bpy.data.objects.new("Sol", sol_d)
    col.objects.link(sol)
    # Sol desde delante-derecha (lado de la cámara): caras visibles iluminadas, sombras hacia la izquierda
    sol.rotation_euler = (math.radians(50), 0, math.radians(38))

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

    animar(cam, obj, cable, escala)
    esc.frame_set(1)
    return esc


# ---------------------------------------------------------------- animación
PLANOS = {
    "general": ((3.1, -7.8, 3.3), (0.0, -0.6, 1.3), 35),
    "medio":   ((1.9, -6.2, 1.6), (0.0, -1.2, 0.55), 35),
    "cable":   ((1.05, -4.3, 0.85), (0.0, -1.9, 0.15), 35),
    "corte":   ((0.95, -6.3, 0.9), (-0.14, -3.5, 0.1), 40),
}
# Voz (velocidad normal) desde el fotograma 0: "este" f137, "Y" f173, "delgado" f190,
# "imaginas" termina en f236. Movimientos de 0,7-0,8 s; pausas de 1,5 s.
TIEMPOS = [
    (1, "general"), (45, "general"),     # pausa 1,5 s  ("Más del 99 % del")
    (67, "medio"),                       # mov. 1 (0,73 s)
    (112, "medio"),                      # pausa 1,5 s  ("tráfico entre continentes viaja")
    (133, "cable"),                      # mov. 2 (0,7 s) -> termina antes de "este" (f137)
    (178, "cable"),                      # pausa 1,5 s  (etiqueta en "este")
    (202, "corte"),                      # mov. 3 (0,8 s) con "Y es más delgado"
    (FRAMES, "corte"),                   # mano + capas; final 1 s después de la voz
]
DESPLIEGUE = (200, 224)                  # capas durante "delgado de lo que"
ENTRADA_ESCALA = (182, 206)              # la mano entra con "es más delgado"


def _curvas(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return []
    try:
        return list(ad.action.fcurves)
    except AttributeError:
        out = []
        for capa in ad.action.layers:
            for tira in capa.strips:
                for bolsa in tira.channelbags:
                    out.extend(bolsa.fcurves)
        return out


def _suavizar(idbs):
    for idb in idbs:
        for fc in _curvas(idb):
            for k in fc.keyframe_points:
                k.interpolation = "BEZIER"
                k.handle_left_type = k.handle_right_type = "AUTO_CLAMPED"
            fc.update()


def animar(cam, obj, cable, escala):
    for f, plano in TIEMPOS:
        pos, objetivo, lente = PLANOS[plano]
        cam.location = pos
        cam.keyframe_insert("location", frame=f)
        obj.location = objetivo
        obj.keyframe_insert("location", frame=f)
        cam.data.lens = lente
        cam.data.keyframe_insert("lens", frame=f)

    for ob, largo, salida, hundido in cable:
        base = (largo - hundido) / largo
        ob.scale = (1, base, 1)
        ob.keyframe_insert("scale", index=1, frame=1)
        ob.keyframe_insert("scale", index=1, frame=DESPLIEGUE[0])
        ob.scale = (1, (largo + salida) / largo, 1)
        ob.keyframe_insert("scale", index=1, frame=DESPLIEGUE[1])

    if escala:
        # Mano palma abajo, dedos hacia el cable (+Y), a su izquierda y fuera del agua.
        # Escala: el dedo tiene el grosor del cable (cable real ~17-21 mm, PENDIENTES D-003).
        escala.rotation_euler = (0, 0, math.radians(180))
        dentro = Vector((-0.92, -4.3, 0.1))
        fuera = dentro + Vector((-0.5, -0.6, -1.9))
        escala.location = fuera
        escala.keyframe_insert("location", frame=1)
        escala.keyframe_insert("location", frame=ENTRADA_ESCALA[0])
        escala.location = dentro
        escala.keyframe_insert("location", frame=ENTRADA_ESCALA[1])

    _suavizar([cam, obj, cam.data] + [c[0] for c in cable] + ([escala] if escala else []))


# ---------------------------------------------------------------- render
def renderizar(esc):
    capa = arg("--capa", "escena")
    salida = arg("--out", os.path.join(PROYECTO, "04_blender", f"frames_v2_{capa}"))
    os.makedirs(salida, exist_ok=True)
    rango = arg("--frames")
    if isinstance(rango, str) and "-" in rango:
        a, b = (int(x) for x in rango.split("-"))
        esc.frame_start, esc.frame_end = a, b
    esc.frame_step = int(arg("--paso", 1))
    esc.render.use_single_layer = True
    esc.render.filepath = os.path.join(salida, "f_####")
    bpy.ops.render.render(animation=True, scene=esc.name, layer=capa)
    print(f"RENDER_OK capa={capa} {esc.frame_start}-{esc.frame_end} -> {salida}")


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
