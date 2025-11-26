import random

from pyscript import window

from pyscript.js_modules import three as THREE
from pyscript.js_modules.oc import OrbitControls

def get_renderer():
    renderer = THREE.WebGLRenderer.new(antialias=True)
    renderer.shadowMap.enabled = False
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    renderer.shadowMap.needsUpdate = True
    return renderer

def get_scene():
    return THREE.Scene.new()

def get_camera():
    camera = THREE.PerspectiveCamera.new(
        45,
        window.innerWidth / window.innerHeight,
        0.1,
        500000,
    )
    return camera

def get_lights():
    light_back_green = THREE.PointLight.new(0x00FF00, 1, 1000)
    light_back_green.decay = 3.0
    light_back_green.position.set(5, 0, 2)

    light_back_white = THREE.PointLight.new(0xFFFFFF, 5, 1000)
    light_back_white.decay = 20.0
    light_back_white.position.set(5, 0, 2)
    return light_back_green, light_back_white

def get_orbit_ctrl(camera: THREE.PerspectiveCamera, renderer: THREE.WebGLRenderer) -> OrbitControls:
    controls = OrbitControls.new(camera, renderer.domElement)
    controls.enableDamping = True
    controls.dampingFactor = 0.04
    return controls

def viz_pts(positions: list, size: float = 0.03, rgb_color: list = [1,1,1]) -> THREE.Points:
    """
    create threejs point clouds for visualization

    Parameters
    ----------
    positions : list
        a flat list defined as [x1, y1, z1, x2, y2, z2, ... , xn, yn, zn]
    
    size : float, optional
        the size of the points. Default is 0.03

    rgb_color : list, optional
        list[shape(3)] rgb color in a list.

    Returns
    -------
    points : THREE.Points
        threejs points that can be visualize
    """
    poss = window.Float32Array.new(positions)
    geometry = THREE.BufferGeometry.new()
    geometry.setAttribute('position', THREE.BufferAttribute.new(poss, 3))

    material = THREE.PointsMaterial.new(color = THREE.Color.new(rgb_color[0], rgb_color[1], rgb_color[2]), size = size, sizeAttenuation = True)
    points = THREE.Points.new(geometry, material)
    return points
    
def create_color(r: float, g: float, b: float) -> THREE.Color:
    """
    create threejs color

    Parameters
    ----------
    r : float
        a number between 0-1 specifying the red of rgb 
    
    g : float
        a number between 0-1 specifying the green of rgb 
    
    b : float
        a number between 0-1 specifying the blue of rgb 

    Returns
    -------
    three_color : THREE.Color
        threejs color 
    """
    three_color = THREE.Color.new(r,g,b)
    return three_color