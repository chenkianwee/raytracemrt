import json
import multiprocessing as mp

#add the path to geomie3d
import geomie3d
import numpy as np

import raytracemrt.utils as utils
# import utils
#----------------------------------------------------------------
def process_intersection(intersection_results, grid_temps):
    hrs = intersection_results[0]
    mrs = intersection_results[1]
    nhrs = len(hrs)
    if nhrs != 0:
        for hr in hrs:
            grid_id = hr.attributes['grid_id']
            att = hr.attributes['rays_bboxes_intersection']
            hit_bbxs = att['hit_bbox']
            if len(hit_bbxs) == 1:
                if 'temperature' in hit_bbxs[0].attributes:
                    temp = hit_bbxs[0].attributes['temperature']
                    grid_temps[grid_id].append(temp)
            else:
                ijks = [hb.attributes['ijk'] for hb in hit_bbxs]
                unq = np.unique(ijks, axis=0)
                if len(unq) == 1:
                    temp = hit_bbxs[0].attributes['temperature']
                    grid_temps[grid_id].append(temp)
                else:
                    print('not sure what is happening please debug')
                    #----------------------------------------------------
                    #for debugging uncomment this segment
                    #----------------------------------------------------
                    # intersect = att['intersection']
                    # print(intersect)
                    # print(unq)
                    # bx_ls = []
                    # for hb in hit_bbxs:
                    #     cp = geomie3d.calculate.bbox_centre(hb)
                    #     bx = geomie3d.create.box(0.3, 0.3, 0.3, centre_pt = cp)
                    #     be = geomie3d.get.edges_frm_solid(bx)
                    #     bx_ls.extend(be)
                    
                    # v_ls = geomie3d.create.vertex_list(intersect)
                    # orig = geomie3d.create.vertex(hr.origin)
                    # e = geomie3d.create.pline_edge_frm_verts([orig, v_ls[0]])
                    # geomie3d.utility.viz([{'topo_list': bx_ls, 'colour': 'blue'},
                    #                       {'topo_list': [e], 'colour': 'red'}])
    return hrs, mrs

def read_grid_json(grid_path):
    with open(grid_path, "r") as outfile:
        grids = json.load(outfile)
        
    grid_verts = geomie3d.create.vertex_list(grids['grid_points'])
    dimx = grids['xdim']
    dimy = grids['ydim']
    grid_faces = []
    for v in grid_verts:
        midpt = v.point.xyz
        f = geomie3d.create.polygon_face_frm_midpt(midpt, dimy, dimx)
        grid_faces.append(f)
    return grid_verts, grid_faces

def gen_rays(grid_verts, ndirs):
    unitball = geomie3d.d4pispace.tgDirs(ndirs)
    #create the rays for each analyse pts
    rays = []
    for cnt,v in enumerate(grid_verts):
        for dix in unitball.getDirList():
            ray = geomie3d.create.ray(v.point.xyz, [dix.x, dix.y, dix.z], attributes = {'grid_id': cnt})        
            rays.append(ray)
    return rays

def calc_mrt(voxel_path, grid_path, res_path, viz):
    #----------------------------------------------------------------
    #read the voxel & convert the voxels to bboxs
    #----------------------------------------------------------------
    bbx_ls = utils.vox2bbox(voxel_path)
    #read grid file 
    grid_verts, grid_faces = read_grid_json(grid_path)
    #generate 360 dirs
    rays = gen_rays(grid_verts, 360)
    
    aloop = 36000#30
    nvx = len(bbx_ls)
    ttl = len(rays)*nvx
    nparallel = int(ttl/aloop)
    if nparallel != 0:
        # print('number of splits:', nparallel)
        rays_ls = utils.separate_rays(rays, nparallel)
    else:
        rays_ls = [rays]
    
    #------------------------------------------------------------------
    # calculate the mrt at each spot
    #------------------------------------------------------------------
    # #project them to the triangulated faces
    # results = []
    # for rays in rays_ls:
    #     # print(rcnt)
    #     hfs, mfs, hrs, mrs = geomie3d.calculate.rays_bboxes_intersect(rays, bbx_ls)
    #     results.append([hfs, mfs, hrs, mrs])
    #------------------------------------------------------------------
    # project the thermal scan onto the geometry point clouds (parallel processing version)
    #------------------------------------------------------------------
    # Step 1: Init multiprocessing.Pool()
    pool = mp.Pool(mp.cpu_count())
    results = pool.starmap(geomie3d.calculate.rays_bboxes_intersect, 
                           [(ray, bbx_ls) for ray in rays_ls])
    pool.close()
    #------------------------------------------------------------------
    # process the intersection results
    #------------------------------------------------------------------
    grid_temps = []
    ngrids = len(grid_verts)
    for _ in range(ngrids):
        grid_temps.append([])
    
    hr_ls = []
    mr_ls = []
    for res in results:
        hrs, mrs = process_intersection(res, grid_temps)
        hr_ls.extend(hrs)
        mr_ls.extend(mrs)
    
    mrt_ls = []
    for gt in grid_temps:
        if len(gt) != 0:
            avg = sum(gt)/len(gt)
            mrt_ls.append(avg)
        else:
            mrt_ls.append(-1)
    
    # header = ['ply\n', 'format ascii 1.0\n', 'comment date DD/MM/YYY\n', 
    #           'comment time HH:MM:SS\n', 'comment sensorID xxxxxxxx\n', 
    #           'comment sensorType scanningSMART / fixedSMART\n', 
    #           'element vertex 6144\n', 'property float32 x\n', 
    #           'property float32 y\n', 'property float32 z\n', 
    #           'property float32 temperature\n', 'end_header\n']
    
    # utils.write2ply(res_path, grid_xyzs, mrt_ls, header)
    
    grid_xyzs = [v.point.xyz for v in grid_verts]
    rows = [['posx', 'posy', 'posz', 'mrt']]
    for gcnt,grid_xyz in enumerate(grid_xyzs):
        mrt = mrt_ls[gcnt]
        row = [str(grid_xyz[0]), str(grid_xyz[1]), str(grid_xyz[2]), str(round(mrt,2))]
        rows.append(row)
    utils.write2csv(rows, res_path)
    #----------------------------------------------------------------
    #for viz
    #----------------------------------------------------------------
    if viz == True:
        print('Visualizing ... ...')
        viz_dlist = []
        temp_viz = []
        vx_viz = []
        bbx_temp_ls = []
        for bbx in bbx_ls:
            v = geomie3d.create.vertex(bbx.attributes['midpt'])
            if 'temperature' in bbx.attributes:
                bbx_temp_ls.append(bbx.attributes['temperature'])
                temp_viz.append(v)
            else:
                vx_viz.append(v)
        
        v_size = round(bbx_ls[0].maxx - bbx_ls[0].minx,1)
        if len(temp_viz) != 0:
            viz_dlist.append({'topo_list':temp_viz, 'colour': [0,0,1,0.2], 'px_mode': False, 'point_size':v_size})
        
        if len(vx_viz) != 0:
            viz_dlist.append({'topo_list':vx_viz, 'colour': [0,0,1,0.2], 'px_mode': False, 'point_size':v_size})
        
        #viz the ray intersections
        e_ls = []
        for hr in hr_ls:
            origin = hr.origin
            intersect = hr.attributes['rays_bboxes_intersection']['intersection']
            vs = geomie3d.create.vertex_list([origin, intersect[0]])
            e = geomie3d.create.pline_edge_frm_verts(vs)
            e_ls.append(e)
        
        # viz_dlist.append({'topo_list':e_ls, 'colour': [1,1,1,0.3]})
        viz_dlist.append({'topo_list':grid_verts, 'colour': 'white'})
        geomie3d.utility.viz_falsecolour(grid_faces, mrt_ls, other_topo_dlist = viz_dlist)

#----------------------------------------------------------------
if __name__ == '__main__':
    voxel_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\voxel\\projected_voxels0.json'
    grid_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\grid\\grid0.json'
    res_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\mrt.csv'
    viz = True
    calc_mrt(voxel_path, grid_path, res_path, viz)