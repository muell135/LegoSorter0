import bpy
import time

filepath = '/Users/matthewmueller/FastAiProjects/LegoSorter/dataset/scenes/dropSim.blend'
bpy.ops.wm.open_mainfile(filepath=filepath)

bpy.context.scene.frame_set(1)
for i in range(1, 25):
    bpy.context.scene.frame_set(i)
    time.sleep(0.1)

try:
    bpy.context.scene.cycles.device = 'GPU'
except:
    print('No GPU found')
    bpy.context.scene.cycles.device = 'CPU'
bpy.ops.render.render(animation=False)
bpy.context.scene.render.filepath = '/Users/matthewmueller/FastAiProjects/LegoSorter/dataset/output/test.png'
bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_mainfile(filepath=filepath)
bpy.ops.wm.quit_blender()