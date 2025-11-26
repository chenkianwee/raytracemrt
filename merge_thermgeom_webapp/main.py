import io
import random
import asyncio

import geomie3d
import numpy as np
from plyfile import PlyData

from pyodide.ffi.wrappers import add_event_listener
from pyscript.ffi import create_proxy
from pyscript import window, document, PyWorker

from libthree import get_scene, get_camera, get_renderer, get_orbit_ctrl, get_lights, viz_pts

# get the renderer and append it to index.html
renderer = get_renderer()
renderer.setSize(window.innerWidth, window.innerHeight)
bottom_side = document.getElementById('bottomSide')
bottom_side.appendChild(renderer.domElement)
# get the camera and scene
camera = get_camera()
camera.position.set(1, 1, 5)
# get the scene
scene = get_scene()
# get lights and put in the scene
lights = get_lights()
for light in lights:
    scene.add(light)
#orbit controls
controls = get_orbit_ctrl(camera, renderer)
# generate points
poss = []
for _ in range(1500):
    poss.append((random.random() + 0.5) * 6) 
    poss.append((random.random() + 0.5) * 6) 
    poss.append((random.random() + 0.5) * 6)

poss2 = np.array(poss)
poss2 = np.reshape(poss2, (1500,3))
bbox = geomie3d.calculate.bbox_frm_xyzs(poss2)
bbox_arr = bbox.bbox_arr
threejs_pts = viz_pts(poss, 0.1, [1,1,1])
scene.add(threejs_pts)
camera.position.set(bbox_arr[3], bbox_arr[4], bbox_arr[5])
camera.lookAt(threejs_pts.position)

def animate(*args):
    controls.update()
    renderer.render(scene, camera)
    # Call the animation loop recursively
    window.requestAnimationFrame(animate_proxy)

animate_proxy = create_proxy(animate)
window.requestAnimationFrame(animate_proxy)

async def get_bytes_from_file(item) -> bytes:
    array_buf = await item.arrayBuffer()
    return array_buf.to_bytes()

async def on_pts_submit(e):
    try:
        output_p = document.querySelector("#stpts-output")
        output_p.textContent = 'Reading ...'
        file_input = document.querySelector("#pts-file-upload")
        file_list = file_input.files
        nfiles = len(file_list)
        if nfiles != 0:
            # loading dialog to inform users processing in progress
            loading_dialog = document.getElementById("loading")
            loading_dialog.showModal()
            item = file_list.item(0)
            my_bytes: bytes = await get_bytes_from_file(item)
            worker_config = {
                                "packages": ["plyfile>=1.1.3", "geomie3d==0.0.10"]
                            }
            worker = PyWorker("./worker.py", type="pyodide", config = worker_config )
            # Await for the worker
            await worker.ready
            ply_dict = await worker.sync.read_ply(my_bytes)
            bbox_arr = ply_dict.bbox_arr
            print(bbox_arr[5])
            verts = ply_dict.xyzs
            print(len(verts))
            threejs_pts = viz_pts(verts, size=10, rgb_color=[1,1,1])
            scene.add(threejs_pts)
            camera.position.set(bbox_arr[3], bbox_arr[4], bbox_arr[5])
            camera.lookAt(threejs_pts.position)
            output_p.textContent = 'Success'
            worker.terminate()
            loading_dialog.close()
            
    except Exception as e:
        print(e)

if __name__ == "__main__":
    animate()
    add_event_listener(document.getElementById("stpts-submit"), "click", lambda e: asyncio.create_task(on_pts_submit(e)) )