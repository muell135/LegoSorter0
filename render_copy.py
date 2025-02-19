import argparse
import os
import bpy
import sys
import math
from random import random, choice
from datetime import datetime

lego_colours = {
    'White': 0xffffff,
    'Brick Yellow': 0xD9BB7B,
    'Nougat': 0xD67240,
    'Bright Red': 0xff0000,
    'Bright Blue': 0x0000ff,
    'Bright Yellow': 0xFfff00,
    'Black': 0x000000,
    'Dark Green': 0x009900,
    'Bright Green': 0x00cc00,
    'Dark Orange': 0xA83D15,
    'Medium Blue': 0x478CC6,
    'Bright Orange': 0xff6600,
    'Bright Bluish Green': 0x059D9E,
    'Bright Yellowish-Green': 0x95B90B,
    'Bright Reddish Violet': 0x990066,
    'Sand Blue': 0x5E748C,
    'Sand Yellow': 0x8D7452,
    'Earth Blue': 0x002541,
    'Earth Green': 0x003300,
    'Sand Green': 0x5F8265,
    'Dark Red': 0x80081B,
    'Flame Yellowish Orange': 0xF49B00,
    'Reddish Brown': 0x5B1C0C,
    'Medium Stone Grey': 0x9C9291,
    'Dark Stone Grey': 0x4C5156,
    'Light Stone Grey': 0xE4E4DA,
    'Light Royal Blue': 0x87C0EA,
    'Bright Purple': 0xDE378B,
    'Light Purple': 0xEE9DC3,
    'Cool Yellow': 0xFFFF99,
    'Medium Lilac': 0x2C1577,
    'Light Nougat': 0xF5C189,
    'Dark Brown': 0x300F06,
    'Medium Nougat': 0xAA7D55,
    'Dark Azur': 0x469bc3,
    'Medium Azur': 0x68c3e2,
    'Aqua': 0xd3f2ea,
    'Medium Lavender': 0xa06eb9,
    'Lavender': 0xcda4de,
    'White Glow': 0xf5f3d7,
    'Spring Yellowish Green': 0xe2f99a,
    'Olive Green': 0x77774E,
    'Medium-Yellowish green': 0x96B93B
}


class SceneNotPreparedException(Exception):
    pass


class BrickRenderer:
    def __init__(self, part_path, ldraw_path, pattern_scene_path, resolution, output_path, gpu_id):
        self.__part_path = part_path
        self.__ldraw_path = ldraw_path
        self.resolution = resolution
        self.__pattern_scene_path = pattern_scene_path
        self.__brick_object = None
        self.output_path = output_path
        self.gpu_id = gpu_id

    def load_pattern_scene(self):
        bpy.ops.wm.open_mainfile(filepath=self.__pattern_scene_path)

    def get_brick_object(self):
        if not self.__brick_object:
            raise SceneNotPreparedException()
        return self.__brick_object

    def import_brick_scene(self):
        try:
            bpy.ops.import_scene.importldraw(filepath=self.__part_path, ldrawPath=self.__ldraw_path,
                                            importCameras=False, positionCamera=False, addEnvironment=False)
            self.__brick_object = [x for x in bpy.data.objects if os.path.basename(self.__part_path) in x.name]
            if not self.__brick_object:
                print("No brick object found after import.")
                raise SceneNotPreparedException("Brick object not found after import.")
            self.__brick_object = self.__brick_object[0]  # Assuming only one object is imported
            print(f"Imported brick object: {self.__brick_object.name}")
        except Exception as e:
            print(f"Error importing LDraw part: {e}")
            raise SceneNotPreparedException()
        
        set_object_position(self.__brick_object, 0, 0, .25 + 1.5 * self.__brick_object.location.z)
        set_object_rotation(self.__brick_object, random() * 360, random() * 360, random() * 360)

        x = input("conintue")

    def prepare_scene(self):
        self.load_pattern_scene()

        self.import_brick_scene()

        self.set_physics()
        save(self, 'post_import')
        #self.__brick_object.active_material = bpy.data.objects["PatternBrick"].active_material
        #bpy.data.objects.remove(bpy.data.objects["00000_1.dat"])
        bpy.context.window.scene = bpy.data.scenes["Scene"]
        #bpy.context.scene.camera.location = (7.0, 0.0, 4.0)
        #bpy.context.scene.collection.objects.link(self.__brick_object)
        return True

    def render(self, samples_count=1, transformation=None, **kwargs):
        part_name = os.path.basename(self.__part_path).split(".")[0]  # Extract part name
        bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = self.resolution

        bpy.context.scene.camera = bpy.data.objects['Camera']
        bpy.context.scene.camera.data.sensor_fit = 'VERTICAL'
        bpy.context.scene.camera.data.lens = 15

        bpy.context.scene.cycles.device = 'GPU'
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.samples = 50

        # apply a random colour to the brick
        colour = get_random_colour()
        rgb_value = hex_to_rgb(colour[1])
        bpy.data.materials["Material_4_c"].node_tree.nodes["Group"].inputs[0].default_value = rgb_value

        transformation(obj=self.get_brick_object(), shift=kwargs["shift"]*3) if transformation \
            else print("Transformation not defined")
        self.force_cuda()
        save(self, 'pre_fall')
        # Skip animation
        for i in range(0, 150):
            bpy.context.scene.frame_set(i)

        #self.adjust_world_to_location(self.__brick_object.matrix_world.to_translation())

        save(self, 'post_fall')
        for i in range(samples_count):
            filename = "{:s}_{:s}_{:d}_{:d}.png".format(part_name, colour[0], i, int(datetime.now().timestamp()))
            bpy.context.scene.render.filepath = os.path.join(self.output_path, filename)
            print("------------------------------------------")
            print("Rendering {} of {}".format(i, samples_count))
            print("------------------------------------------")
            bpy.ops.render.render(write_still=True)
            transformation(obj=self.get_brick_object(), **kwargs) if transformation \
                else print("Transformation not defined")
        return

    def set_physics(self):
        scene = bpy.data.scenes['Scene']
        bpy.context.window.scene = scene

        ground = scene.objects['FunnelConveyor']
        ground.rigid_body.type = 'PASSIVE'
        ground.rigid_body.collision_shape = 'MESH'

        scene.rigidbody_world.collection.objects.link(self.__brick_object)
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
        self.__brick_object.rigid_body.collision_shape = 'CONVEX_HULL'
        self.__brick_object.rigid_body.type = 'ACTIVE'

        #ensure brick doesn't land above or below FunnelConveyor
        scene.rigidbody_world.substeps_per_frame = 10
        scene.rigidbody_world.solver_iterations = 30
        for obj in scene.objects:
            if obj.rigid_body:
                obj.rigid_body.collision_margin = .0001

    def adjust_world_to_location(self, location_zero):
        location_zero[2] = 0
        for o in bpy.data.objects:
            if o.name != self.__brick_object.name:
                o.location += location_zero

    def force_cuda(self):
        preferences = bpy.context.preferences
        cycles_preferences = preferences.addons['cycles'].preferences
        cycles_preferences.compute_device_type = 'METAL' #for matthew's mac

        print("Device type preference is {}".format(cycles_preferences.compute_device_type))

        cycles_preferences.get_devices()

        for device in cycles_preferences.devices:
            print("Available device: {}".format(device['id']))
            if not self.gpu_id or device['id'] == self.gpu_id:
                device.use = True
                print("{} set as the active device".format(device['id']))
            else:
                device.use = False
        pass


def main(args):
    brickRender = BrickRenderer(args.part, args.ldraw, args.scene, (args.width, args.height),
                                args.output_dir, args.gpu)
    brickRender.prepare_scene()
    brickRender.render(samples_count=args.samples, transformation=shift_horizontally, shift=args.shift)


def shift_horizontally(obj, shift=None):
    # It's tricky to move an object which is animated so I move a whole world except this object in the opposite
    # direction
    for o in bpy.data.objects:
        if o.name != obj.name:
            o.location.x -= shift


def rotate_object(obj, x=0.0, y=0.0, z=0.0):
    obj.rotation_euler[0] += degree_to_pi(x)
    obj.rotation_euler[1] += degree_to_pi(y)
    obj.rotation_euler[2] += degree_to_pi(z)


def set_object_rotation(obj, x=0.0, y=0.0, z=0.0):
    obj.rotation_euler[0] = degree_to_pi(x)
    obj.rotation_euler[1] = degree_to_pi(y)
    obj.rotation_euler[2] = degree_to_pi(z)
    print("Object rotation set to {} {} {}".format(obj.rotation_euler[0], obj.rotation_euler[1], obj.rotation_euler[2]))


def set_object_position(obj, x=0.0, y=0.0, z=0.0):
    obj.location = (x, y, z)


def degree_to_pi(degrees):
    return 2 * degrees / 360.0 * math.pi


def srgb_to_linear_rgb(c):
    if c < 0:
        return 0
    elif c < 0.04045:
        return c / 12.92
    else:
        return ((c + 0.055) / 1.055) ** 2.4


def hex_to_rgb(h, alpha=1):
    r = (h & 0xff0000) >> 16
    g = (h & 0x00ff00) >> 8
    b = (h & 0x0000ff)
    return tuple([srgb_to_linear_rgb(c / 0xff) for c in (r, g, b)] + [alpha])


def get_random_colour():
    return choice(list(lego_colours.items()))
 
def save(self, name):
    # Save the current Blender file
    blend_file_path = os.path.join(self.output_path, name + ".blend")  # Set your desired path and filename
    bpy.ops.wm.save_as_mainfile(filepath=blend_file_path)
    print(f"Blender file saved at: {blend_file_path}")


if __name__ == "__main__":
    LEGO_HOME = '/Users/matthewmueller/FastAiProjects/LegoSorter'
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, help="width of an output image", default=300)
    parser.add_argument("--height", type=int, help="height of an output image", default=300)
    parser.add_argument("--part", help="a path to the part to be rendered", default=LEGO_HOME+'/dataset/ldraw/parts/1.dat', required=False)
    parser.add_argument("--output_dir", help="a path to the output directory", default=LEGO_HOME+'/output', required=False)
    parser.add_argument("--ldraw", help="a path to the ldraw library", default=LEGO_HOME+'/dataset/ldraw', required=False)
    parser.add_argument("--scene", help="a path to the pattern scene", default=LEGO_HOME+'/dataset/scenes/dropSim.blend', required=False)
    parser.add_argument("--samples", type=int, help="how many images to render", default=1) #change back to 10 post testing
    parser.add_argument("--shift", type=float, help="block shift per sample", default=-0.0) #change to .1 or smtg post testing
    parser.add_argument("--gpu", type=str, help="identifier of GPU which will be used for rendering"
                                                "if not specified, every available device will be used", required=False)
   
    arguments = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])

    main(arguments)
