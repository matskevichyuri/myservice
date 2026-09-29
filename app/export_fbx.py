import bpy
import numpy as np
import sys

# Blender's bundled glTF importer in this image still references np.bool.
if not hasattr(np, "bool"):
    np.bool = bool

input_path, output_path = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=input_path)
bpy.ops.export_scene.fbx(filepath=output_path, path_mode="COPY", embed_textures=True, apply_unit_scale=True)
