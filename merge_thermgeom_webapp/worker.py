import io
import geomie3d
import numpy as np
from plyfile import PlyData

from pyscript import sync

def read_ply(ply_bytes: bytes):
    ply_bytes = ply_bytes.to_py()
    bstream = io.BytesIO(ply_bytes)
    plydata = PlyData.read(bstream)
    vertices = plydata['vertex'].data
    vertices = list(map(list, vertices))
    bbox = geomie3d.calculate.bbox_frm_xyzs(vertices)
    bbox_arr = bbox.bbox_arr
    verts_ls = np.concatenate(vertices).tolist()
    return {'xyzs': verts_ls, 'bbox_arr': bbox_arr}

sync.read_ply = read_ply