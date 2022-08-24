import sys
import argparse
from time import perf_counter
import multiprocessing as mp

#add the path to geomie3d
sys.path.append('F:\\kianwee_work\\spyder_workspace\\geomie3d')
import geomie3d
import numpy as np
import utils
#----------------------------------------------------------------
def process_intersection(intersection_results, ijk_ls, unq_bbx_ls):
    hrs = intersection_results[0]
    mrs = intersection_results[1]
    nhrs = len(hrs)

    intvs = []
    temp_ls = []
    if nhrs != 0:
        for hr in hrs:
            att = hr.attributes['rays_bboxes_intersection']
            intersect = att['intersection']
            hit_bbxs = att['hit_bbox']
            process_hit_bbxs(hit_bbxs, ijk_ls, unq_bbx_ls)
            temp = hr.attributes['temperature']
            if len(intersect) == 1:
                intv = geomie3d.create.vertex(intersect[0], attributes = {'temperature':temp})
                temp_ls.append(temp)
                intvs.append(intv)
            else:
                unq = np.unique(intersect, axis=0)
                if len(unq) == 1:
                    intv = geomie3d.create.vertex(unq[0], attributes = {'temperature':temp})
                    intvs.append(intv)
                    temp_ls.append(temp)
                else:
                    print('not sure what is happening please debug')
                    
            
    return intvs, temp_ls, mrs

def process_hit_bbxs(hit_bbxs, ijk_ls, unq_bbx_ls):
    for hb in hit_bbxs:
        ijk = hb.attributes['ijk']
        # print('---------------------------------')
        # print(ijk)
        # print(ijk_ls)
        if ijk not in ijk_ls:
            ijk_ls.append(ijk)
            unq_bbx_ls.append(hb)
        else:
            #---------------------------------------------------------
            # get the atts from the unq box and merge with current box
            #---------------------------------------------------------
            idx = ijk_ls.index(ijk)
            unq_bbx = unq_bbx_ls[idx]
            att = unq_bbx.attributes['rays_bboxes_intersection']
            ints1 = att['intersection']
            rays1 = att['ray']
            rids1 = [ray.attributes['id'] for ray in rays1]
            #-------------------------------------
            # get the atts from this current bbox
            #-------------------------------------
            rays2 = hb.attributes['rays_bboxes_intersection']['ray']
            ints2 = hb.attributes['rays_bboxes_intersection']['intersection']
            rids2 = [ray.attributes['id'] for ray in rays2]
            not_in_true = np.in1d(rids2, rids1)
            not_in_true = np.logical_not(not_in_true)
            not_in_indx = np.where(not_in_true)[0]
            if len(not_in_indx) != 0:
                not_in_intersections = np.take(ints2, not_in_indx, axis=0).tolist()
                ints1.extend(not_in_intersections)
                not_in_rays = np.take(rays2, not_in_indx, axis=0).tolist()
                rays1.extend(not_in_rays)
            
def calc_hit_bbx_temp(hit_bbx_ls):
    for ub in hit_bbx_ls:
        att = ub.attributes['rays_bboxes_intersection']
        rays = att['ray']
        # print(len(rays))
        temps = [ray.attributes['temperature'] for ray in rays]
        # print(temps)
        avg = sum(temps)/len(temps)
        ub.update_attributes({'temperature':avg})

def find_msbbx(all_bbxs, hit_bbxs):
    all_ijks = [list(bbx.attributes['ijk']) for bbx in all_bbxs]
    hit_ijks = [list(bbx.attributes['ijk']) for bbx in hit_bbxs]
    ms_idx_ls = []
    for cnt,ijk in enumerate(all_ijks):
        if ijk not in hit_ijks:
            ms_idx_ls.append(cnt)
            
    ms_bbxs = np.take(all_bbxs, ms_idx_ls, axis=0).tolist()
    return ms_bbxs  

def parse_args():
    # create parser object
    parser = argparse.ArgumentParser(description = "Project your Chaosense Data")
 
    # defining arguments for parser object
    parser.add_argument('-s', '--scan', type = str, nargs = 1,
                        metavar = 'filepath', default = None,
                        help = 'The ply file to process')
     
    parser.add_argument('-p', '--points', type = str, nargs = 1,
                        metavar = 'filepath', default = None,
                        help = 'The path of the .pts point cloud file')
    
    parser.add_argument('-x', '--xyz', type = float, nargs = 3,
                        metavar = ('posX', 'posY', 'posZ'), default = None,
                        help = "The position of the sensor")
    
    parser.add_argument('-r', '--result', type = str, nargs = 1,
                        metavar = 'directory', default = None,
                        help = "The directory to save to")
    
    parser.add_argument('-f', '--voxel_path', type = str, nargs = 1,
                        metavar = 'filepath', default = None,
                        help = 'The path to save to after the processing')
    
    parser.add_argument('-z', '--voxel_size', type = float, nargs = 1,
                        metavar = 'voxel size', default = None,
                        help = "The size of the voxel")
    
    parser.add_argument('-v', '--viz', action = 'store_true',
                        help = 'Open a 3D window to see the result')
    
    # parse the arguments from standard input
    args = parser.parse_args()
    
    return args
#----------------------------------------------------------------
if __name__ == '__main__':
    args = parse_args()
    therm_scan_path = args.scan[0]
    pts_path = args.points[0]
    sensor_pos = args.xyz
    res_path = args.result[0]
    vx_path = args.voxel_path[0]
    v_size = args.voxel_size[0]
    viz = args.viz
    
    # therm_scan_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm.ply'
    # pts_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\pts\\example1.pts'
    # sensor_pos = [0.5, 0.8, 1.5]#[1,0,1]
    # res_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\intersections.ply'
    # vx_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\projected_voxels0.json'
    # v_size = 0.3
    # viz = True
    #----------------------------------------------------------------
    #process the geometry point clouds
    #read the pts file and voxelise the pts
    #----------------------------------------------------------------
    t1_start = perf_counter()
    viz_dlist = []
    with open(pts_path) as f:
        lines = f.readlines()
    vlist = []
    xyzs_ls = []    
    for l in lines:
        l = l.split(',')
        xyz = l[0:3]
        xyz = list(map(float, xyz))
        xyzs_ls.append(xyz)
    #     v = geomie3d.create.vertex(xyz)
    #     vlist.append(v)
    # viz_dlist.append({'topo_list':vlist, 'colour':[1,1,1,1]})
    
    xdim = v_size
    ydim = v_size
    zdim = v_size
    vx_dict = geomie3d.modify.xyzs2voxs(xyzs_ls, xdim, ydim, zdim)
    
    #convert the voxels to bboxes
    bbx_ls = []
    vx_ls = []
    for cnt,key in enumerate(vx_dict.keys()):
        vx = vx_dict[key]
        midpt = vx['midpt']
        att = {'idx': vx['idx'], 'ijk': key, 'midpt':midpt}
        bbx = geomie3d.create.bbox_frm_midpt(midpt, v_size, v_size, v_size, attributes = att)
        bbx_ls.append(bbx)
    #     vx_v = geomie3d.create.vertex(midpt)
    #     vx_ls.append(vx_v)
        
    # viz_dlist.append({'topo_list':vx_ls, 'colour':[0,0,1,0.3], 'px_mode': False, 'point_size':v_size})
    # geomie3d.utility.viz(viz_dlist)
    t1_stop = perf_counter()
    counter = t1_stop - t1_start
    print('Time taken 2 Voxelize(mins)', round(counter/60, 1))
    #----------------------------------------------------------------
    # read the thermal scan
    #----------------------------------------------------------------
    #read the file and get all the vert data
    verts_data, temp_ls, headers = utils.read_therm_arr_ply(therm_scan_path)
    ndir = len(verts_data)
    if ndir == 0:
        print('The PLY file specified is not produce from a Chaosense Sensor')
    else:
        #convert the verts to rays and 
        rays = []
        for vcnt,v in enumerate(verts_data):
            temp = v.attributes['temperature']
            ray = geomie3d.create.ray(sensor_pos, v.point.xyz, attributes = {'temperature':temp, 'id': vcnt})
            rays.append(ray)
            
        aloop = 36000#30
        nvx = len(list(vx_dict.keys()))
        ttl = ndir*nvx
        nparallel = int(ttl/aloop)
        
        if nparallel != 0:
            rays_ls = utils.separate_rays(rays, nparallel)
        else:
            rays_ls = [rays]
        print('number of splits:', nparallel)
    #------------------------------------------------------------------
    # project the thermal scan onto the geometry point clouds
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
    
    t2_stop = perf_counter()
    counter = t2_stop - t1_stop
    print('Time taken 2 Project(mins)', round(counter/60, 1))
    #------------------------------------------------------------------
    #process the results
    #------------------------------------------------------------------
    ijk_ls = []
    unq_bbx_ls = []
    intvs = []
    temp_ls = []
    ms_ray_ls = []
    for result in results:
        intv,temps,ms_rays = process_intersection(result, ijk_ls, unq_bbx_ls)
        intvs.extend(intv)
        temp_ls.extend(temps)
        ms_ray_ls.extend(ms_rays)
    
    if len(unq_bbx_ls) != 0:
        calc_hit_bbx_temp(unq_bbx_ls)
        ms_bbx_ls = find_msbbx(bbx_ls, unq_bbx_ls)
        processed_bbx_ls = unq_bbx_ls + ms_bbx_ls
        # print(len(bbx_ls))
        # print(len(unq_bbx_ls), len(ms_bbx_ls))
    else:
        processed_bbx_ls = bbx_ls
    
    utils.write_bbox2json(processed_bbx_ls, vx_path)
    t3_stop = perf_counter()
    counter = t3_stop - t2_stop
    print('Time taken 2 Process(mins)', round(counter/60, 1))
    #------------------------------------------------------------------
    #viz the results
    #------------------------------------------------------------------
    if viz == True:
        sensor_v = geomie3d.create.vertex(sensor_pos)
        viz_dlist.append({'topo_list':[sensor_v], 'colour': [1,1,1,0.5], 'px_mode': False, 'point_size': 0.5})
        
        viz_pt = True
        int_viz = []
        es = []
        hbx_v = []
        mbx_v = []
        for bbx in processed_bbx_ls:
            midpt = geomie3d.calculate.bbox_centre(bbx)
            if viz_pt == True:
                viz_topo = [geomie3d.create.vertex(midpt)]
            else:
                viz_topo = [geomie3d.create.box(v_size, v_size, v_size, centre_pt=midpt)]
                # viz_topo = geomie3d.get.edges_frm_solid(bx)
            if 'temperature' in bbx.attributes:
                hbx_v.extend(viz_topo)
                ints_xyz = bbx.attributes['rays_bboxes_intersection']['intersection']
                for xyz in ints_xyz:
                    int_v = geomie3d.create.vertex(xyz)
                    int_e = geomie3d.create.pline_edge_frm_verts([sensor_v, int_v])
                    int_viz.append(int_v)
                    int_viz.append(int_e)
                    es.append(int_e)
            else:
                mbx_v.extend(viz_topo)
        
        if len(int_viz) != 0:
            viz_dlist.append({'topo_list': int_viz, 'colour': [1,1,1,0.3]})
        
        if len(hbx_v) != 0:
            viz_dlist.append({'topo_list': hbx_v, 'colour': [0,0,1,0.3], 'px_mode': False, 'point_size': v_size})
            
        if len(mbx_v) != 0:
            viz_dlist.append({'topo_list': mbx_v, 'colour': [0,0,1,0.3], 'px_mode': False, 'point_size': v_size})
                    
        
        print('Visualizing ...')
        # geomie3d.utility.viz(viz_dlist)
        geomie3d.utility.viz_falsecolour(intvs, temp_ls, 
                                          other_topo_dlist=viz_dlist)
        