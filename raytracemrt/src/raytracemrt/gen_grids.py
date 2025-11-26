import os
import json
#add the path to geomie3d
import geomie3d
import numpy as np

import raytracemrt.utils as utils
# import utils
#----------------------------------------------------------------
def aly_grid_frm_bbx(bbx, xdim, ydim, height, buffer):
    minx = bbx.minx + buffer
    maxx = bbx.maxx - buffer
    miny = bbx.miny + buffer
    maxy = bbx.maxy - buffer
    z = bbx.minz + height
    ctrl_pts = [[minx, maxy, z], [maxx, maxy, z],
                [minx, miny, z], [maxx, miny, z]]
    xrange = maxx-minx
    yrange = maxy-miny
    column = round(xrange/xdim)
    row = round(yrange/ydim)
    realx = yrange/column
    realy = xrange/row
    aly_face = geomie3d.create.bspline_face_frm_ctrlpts(ctrl_pts, 2, 2, 1, 1)
    grid_faces = geomie3d.create.grids_frm_bspline_face(aly_face, column, row)
    grid_xyzs = []
    for gf in grid_faces:
        mid_xyz = geomie3d.calculate.face_midxyz(gf)
        grid_xyzs.append(mid_xyz)
    
    return grid_xyzs, realx, realy, grid_faces

def gen_grids(voxel_path, res_dir, grid_dim, pts_afile, viz):
    bbx_ls = utils.vox2bbox(voxel_path)
    overall_bbx = geomie3d.calculate.bbox_frm_bboxes(bbx_ls)
    # create mrt grid from the overall bbx
    xdim = grid_dim[0]
    ydim = grid_dim[1]
    height = grid_dim[2]
    buffer = grid_dim[3]
    grid_xyzs, realx, realy, grid_faces = aly_grid_frm_bbx(overall_bbx, xdim, ydim, 
                                                           height, buffer)
    #--------------------------------------------------------------------
    #check if the grid points is within the space
    #--------------------------------------------------------------------
    #shoot down if it hits the floor
    up_ray_ls = []
    dn_ray_ls = []
    for xyz in grid_xyzs:
        up = geomie3d.create.ray(xyz, [0,0,1])
        dn = geomie3d.create.ray(xyz, [0,0,-1])
        up_ray_ls.append(up)
        dn_ray_ls.append(dn)
        
    geomie3d.calculate.rays_bboxes_intersect(up_ray_ls, bbx_ls)
    geomie3d.calculate.rays_bboxes_intersect(dn_ray_ls, bbx_ls)
    
    in_space = []
    for cnt, ur in enumerate(up_ray_ls):
        condition = False
        ur_att = ur.attributes
        dn_att = dn_ray_ls[cnt].attributes
        if 'rays_bboxes_intersection' in ur_att:
            condition = True
        
        if 'rays_bboxes_intersection' in dn_att:
            condition = True
        
        in_space.append(condition)
    
    grid_idx = np.where(in_space)[0]
    chosen_grid_xyz = np.take(grid_xyzs, grid_idx, axis=0).tolist()
    afile = pts_afile
    npts = len(chosen_grid_xyz)
    
    res_paths = []
    if npts > afile:
        #split the file
        nsplits = int(npts/afile)
        interval = npts/nsplits
        for i in range(nsplits):
            start = int(interval*i)
            end = int(interval*(i+1))
            res_path = os.path.join(res_dir, 'grid'+str(i)+'.json')
            grid_dt = {'grid_points': chosen_grid_xyz[start:end],
                       'xdim': realx, 'ydim': realy, 
                       'height': height}
            with open(res_path, "w") as outfile:
                json.dump(grid_dt, outfile)
            res_paths.append(res_path)
    else:
        res_path = os.path.join(res_dir, 'grid0.json')
        grid_dt = {'grid_points': chosen_grid_xyz,
                   'xdim': realx, 'ydim': realy, 
                   'height': height}
        with open(res_path, "w") as outfile:
            json.dump(grid_dt, outfile)
        res_paths.append(res_path)
    #--------------------------------------------------------------------
    #visualize
    #--------------------------------------------------------------------
    if viz == True:
        viz_dlist = []
        print('Visualizing ...')
        vs = geomie3d.create.vertex_list(chosen_grid_xyz)
        fs = []
        for xyz in chosen_grid_xyz:
            f = geomie3d.create.polygon_face_frm_midpt(xyz, realy, realx)
            fs.append(f)
            
        viz_dlist.append({'topo_list': vs, 'colour': [1,0,0,1]})
        # viz_dlist.append({'topo_list': fs, 'colour': [0,0,1,1]})
        # viz_dlist.append({'topo_list': chosen_faces, 'colour': [1,0,1,1]})
        
        # geomie3d.utility.viz(viz_dlist)
        v_size = round(bbx_ls[0].maxx - bbx_ls[0].minx, 1)
        viz_ls = []
        viz_pt = True
        for bbx in bbx_ls:
            midpt = geomie3d.calculate.bbox_centre(bbx)
            if viz_pt == True:
                viz_topo = [geomie3d.create.vertex(midpt)]
            else:
                viz_topo = [geomie3d.create.box(v_size, v_size, v_size, centre_pt=midpt)]
                # viz_topo = geomie3d.get.edges_frm_solid(bx)
                
            viz_ls.extend(viz_topo)
            
        viz_dlist.append({'topo_list': viz_ls, 'colour': [0,0,1,0.2], 'px_mode': False, 'point_size': v_size})
        geomie3d.utility.viz(viz_dlist)
    return res_paths
#----------------------------------------------------------------
if __name__ == '__main__':
    voxel_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\voxel\\projected_voxels0.json'
    res_dir = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\grid'
    grid_dim = [0.5, 0.5, 1, 0.5]
    pts_afile = 10000
    viz = True
    grid_paths = gen_grids(voxel_path, res_dir, grid_dim, pts_afile, viz)
    print(grid_paths)