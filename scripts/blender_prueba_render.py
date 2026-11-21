"""Prueba de Blender sin interfaz: renderiza un fotograma con Eevee.

Uso (la ruta de Blender está en scripts/config.json):
  "<blender.exe>" -b --factory-startup --python "scripts/blender_prueba_render.py" -- "out/prueba_blender.png"

Es solo una prueba de humo del motor: usa geometría básica a propósito.
Las escenas de producción usan modelos con licencia (D-002), no primitivas.
"""

import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
salida = os.path.abspath(argv[0] if argv else "out/prueba_blender.png")
os.makedirs(os.path.dirname(salida), exist_ok=True)

# Escena limpia
bpy.ops.wm.read_factory_settings(use_empty=True)
escena = bpy.context.scene

# Motor Eevee (el identificador cambió entre versiones de Blender)
motores = {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
escena.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in motores else "BLENDER_EEVEE_NEXT"

escena.render.resolution_x = 1080
escena.render.resolution_y = 1920
escena.render.resolution_percentage = 100
escena.render.image_settings.file_format = "PNG"
escena.render.filepath = salida

# Color plano, sin la desaturación de AgX/Filmic
escena.view_settings.view_transform = "Standard"

# Fondo limpio: la cámara ve un color claro, pero el fondo apenas ilumina la escena
mundo = bpy.data.worlds.new("Mundo")
mundo.use_nodes = True
wn = mundo.node_tree.nodes
wl = mundo.node_tree.links
wn.clear()
fondo_visto = wn.new("ShaderNodeBackground")
fondo_visto.inputs["Color"].default_value = (0.93, 0.89, 0.82, 1.0)
fondo_luz = wn.new("ShaderNodeBackground")
fondo_luz.inputs["Color"].default_value = (0.05, 0.05, 0.08, 1.0)
camino = wn.new("ShaderNodeLightPath")
mezcla = wn.new("ShaderNodeMixShader")
salida_mundo = wn.new("ShaderNodeOutputWorld")
wl.new(camino.outputs["Is Camera Ray"], mezcla.inputs["Fac"])
wl.new(fondo_luz.outputs["Background"], mezcla.inputs[1])
wl.new(fondo_visto.outputs["Background"], mezcla.inputs[2])
wl.new(mezcla.outputs["Shader"], salida_mundo.inputs["Surface"])
escena.world = mundo


def material_toon(nombre, color):
    """Principled -> Shader to RGB -> ColorRamp constante: sombreado en bandas."""
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nodos = mat.node_tree.nodes
    enlaces = mat.node_tree.links
    nodos.clear()
    bsdf = nodos.new("ShaderNodeBsdfDiffuse")
    a_rgb = nodos.new("ShaderNodeShaderToRGB")
    rampa = nodos.new("ShaderNodeValToRGB")
    emision = nodos.new("ShaderNodeEmission")
    salida_mat = nodos.new("ShaderNodeOutputMaterial")
    rampa.color_ramp.interpolation = "CONSTANT"
    rampa.color_ramp.elements[0].position = 0.0
    rampa.color_ramp.elements[0].color = (color[0] * 0.45, color[1] * 0.35, color[2] * 0.6, 1.0)
    rampa.color_ramp.elements[1].position = 0.5
    rampa.color_ramp.elements[1].color = (*color, 1.0)
    enlaces.new(bsdf.outputs["BSDF"], a_rgb.inputs["Shader"])
    enlaces.new(a_rgb.outputs["Color"], rampa.inputs["Fac"])
    enlaces.new(rampa.outputs["Color"], emision.inputs["Color"])
    enlaces.new(emision.outputs["Emission"], salida_mat.inputs["Surface"])
    return mat


bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 0, 1.0), segments=64, ring_count=32)
esfera = bpy.context.active_object
bpy.ops.object.shade_smooth()
esfera.data.materials.append(material_toon("Toon_Naranja", (0.89, 0.34, 0.18)))

bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(material_toon("Toon_Suelo", (0.85, 0.82, 0.76)))

bpy.ops.object.light_add(type="SUN", location=(4, -4, 8))
sol = bpy.context.active_object
sol.rotation_euler = (0.7, 0.2, 0.8)
sol.data.energy = 4.0

bpy.ops.object.camera_add(location=(0, -7.5, 2.2), rotation=(1.45, 0, 0))
escena.camera = bpy.context.active_object
escena.camera.data.lens = 40

bpy.ops.render.render(write_still=True)
print(f"PRUEBA_BLENDER_OK {escena.render.engine} {salida}")
