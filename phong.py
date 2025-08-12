import bpy
import os
import math
import sys

C = bpy.context
D = bpy.data
scene = D.scenes['Scene']

# Camera orientations (theta, phi)
# cameras = [
#    (60, 0), (60, 90), (60, 180), (60, 270),
#    (0, 0)
#]

cameras = [(60, i) for i in range(0, 360, 30)]

# Render settings
w, h = 2000, 2000
scene.render.resolution_x = w
scene.render.resolution_y = h


def main():
    argv = sys.argv
    argv = argv[argv.index('--') + 1:]

    if len(argv) != 2:
        print('phong.py args: <3d mesh path> <image dir>')
        exit(-1)

    model = argv[0]
    image_dir = argv[1]

    install_off_addon()
    init_camera()
    fix_camera_to_origin()
    do_model(model, image_dir)


def install_off_addon():
    try:
        bpy.ops.preferences.addon_install(
            overwrite=False,
            filepath=os.path.join(os.path.dirname(__file__), 'blender-off-addon', 'import_off.py')
        )
        bpy.ops.preferences.addon_enable(module='import_off')
    except Exception:
        print("""Import blender-off-addon failed.
              Did you pull the blender-off-addon submodule?
              $ git submodule update --recursive --remote
              """)
        exit(-1)


def init_camera():
    cam = D.objects['Camera']
    C.view_layer.objects.active = cam
    cam.select_set(True)

    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 2.0


def fix_camera_to_origin():
    origin_name = 'Origin'

    if origin_name not in D.objects:
        bpy.ops.object.empty_add(type='SPHERE')
        D.objects['Empty'].name = origin_name
    origin = D.objects[origin_name]
    origin.location = (0, 0, 0)

    cam = D.objects['Camera']
    C.view_layer.objects.active = cam
    cam.select_set(True)

    if not any(c.type == 'TRACK_TO' for c in cam.constraints):
        track_to = cam.constraints.new(type='TRACK_TO')
        track_to.target = origin
        track_to.track_axis = 'TRACK_NEGATIVE_Z'
        track_to.up_axis = 'UP_Y'


def do_model(path, image_dir):
    name = load_model(path)
    center_model(name)
    normalize_model(name)
    image_subdir = os.path.join(image_dir, name)
    os.makedirs(image_subdir, exist_ok=True)
    # setup_lighting() 
    setup_phong_white_no_texture_black_bg()
    for i, c in enumerate(cameras):
        move_camera(c)
        #reduce_brightness(factor=0.5)
        render()
        save(image_subdir, f'{name}_{i}')

    delete_model(name)
    
def load_off(path):
    """Simple OFF file loader that returns vertices and faces."""
    with open(path, 'r') as f:
        first_line = f.readline().strip()
        if first_line != 'OFF':
            raise ValueError("Not a valid OFF file")

        # Read vertex & face counts
        nv, nf, _ = map(int, f.readline().strip().split())

        # Read vertices
        verts = []
        for _ in range(nv):
            verts.append(tuple(map(float, f.readline().strip().split())))

        # Read faces
        faces = []
        for _ in range(nf):
            parts = list(map(int, f.readline().strip().split()))
            count = parts[0]
            face_indices = parts[1:count+1]
            faces.append(face_indices)

    return verts, faces


def load_model(path):
    """Load a model (STL, OBJ, OFF) directly into Blender."""
    name = os.path.basename(path).split('.')[0]
    ext = path.split('.')[-1].lower()

    if ext == 'stl':
        bpy.ops.import_mesh.stl(filepath=path)
    elif ext == 'obj':
        bpy.ops.import_scene.obj(filepath=path)
    elif ext == 'off':
        verts, faces = load_off(path)

        # Create mesh
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts, [], faces)
        mesh.update()

        # Create object
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
    else:
        raise ValueError(f"Unsupported file format: .{ext}")

    return name


def delete_model(name):
    for ob in list(scene.objects):
        if ob.type == 'MESH' and ob.name.startswith(name):
            ob.select_set(True)
        else:
            ob.select_set(False)
    bpy.ops.object.delete()


def center_model(name):
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
    D.objects[name].location = (0, 0, 0)


def normalize_model(name):
    obj = D.objects[name]
    dim = obj.dimensions
    print('Original dim:', dim)
    if max(dim) > 0:
        scale_factor = 1.0 / max(dim)
        obj.scale = (obj.scale[0] * scale_factor,
                     obj.scale[1] * scale_factor,
                     obj.scale[2] * scale_factor)
        bpy.context.view_layer.update()
    print('New dim:', obj.dimensions)


def move_camera(coord):
    def deg2rad(deg):
        return deg * math.pi / 180.0

    r = 3.0
    theta, phi = deg2rad(coord[0]), deg2rad(coord[1])
    loc_x = r * math.sin(theta) * math.cos(phi)
    loc_y = r * math.sin(theta) * math.sin(phi)
    loc_z = r * math.cos(theta)

    D.objects['Camera'].location = (loc_x, loc_y, loc_z)
    
def setup_lighting():
    # Remove existing lights
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)

    # Key light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 5))
    key = bpy.context.object
    key.data.energy = 5.0
    key.rotation_euler = (math.radians(45), 0, math.radians(45))

    # Fill light (softer, less intense)
    bpy.ops.object.light_add(type='POINT', location=(-3, 2, 2))
    fill = bpy.context.object
    fill.data.energy = 1.5

    # Back light (to create rim light effect)
    bpy.ops.object.light_add(type='POINT', location=(0, -5, 3))
    back = bpy.context.object
    back.data.energy = 1.5
    
    
def reduce_brightness(factor=0.5):
    # Reduce all lights energy
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            obj.data.energy *= factor
    
    # Set filmic color management
    scene = bpy.context.scene
    scene.view_settings.exposure = 0.5

    # Reduce background strength
    world = scene.world
    if world and world.node_tree:
        for node in world.node_tree.nodes:
            if node.type == 'BACKGROUND':
                node.inputs['Strength'].default_value *= factor
    else:
        if world:
            world.color = (0.5, 0.5, 0.5)
def setup_phong_white_no_texture_black_bg():
    scene = bpy.context.scene
    world = scene.world

    # --- Set black background ---
    if not world:
        world = bpy.data.worlds.new("World")
        scene.world = world

    world.use_nodes = True
    bg_node = world.node_tree.nodes.get('Background')
    if bg_node:
        bg_node.inputs['Color'].default_value = (0, 0, 0, 1)  # black
        bg_node.inputs['Strength'].default_value = 1.0

    # --- Set up white Phong-like material ---
    mat = bpy.data.materials.new(name="PhongWhite")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    # Clear existing nodes
    for n in nodes:
        nodes.remove(n)

    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    mat.node_tree.links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])

    principled_node.inputs['Base Color'].default_value = (1, 1, 1, 1)  # white
    principled_node.inputs['Specular'].default_value = 0.5
    principled_node.inputs['Roughness'].default_value = 0.2

    # Assign material to all meshes
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            if len(obj.data.materials) > 0:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)

    # Smooth shading for phong effect
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            mesh = obj.data
            for f in mesh.polygons:
                f.use_smooth = True

    # Adjust lights (optional tweak)
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            obj.data.energy = 100  # adjust as needed

    # Color management
    #scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0

def render():
    bpy.ops.render.render()


def save(image_dir, name):
    path = os.path.join(image_dir, name + '.png')
    bpy.data.images['Render Result'].save_render(filepath=path)
    print('Saved to', path)


if __name__ == '__main__':
    main()

