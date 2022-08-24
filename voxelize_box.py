import os
import sys
import argparse
# from time import perf_counter

#add the path to geomie3d
sys.path.append('F:\\kianwee_work\\spyder_workspace\\geomie3d')
import geomie3d
import numpy as np
import utils
#----------------------------------------------------------------
def parse_args():
    # create parser object
    parser = argparse.ArgumentParser(description = "Project your Chaosense Data")
 
    # defining arguments for parser object
    parser.add_argument('-d', '--intersection_dir', type = str, nargs = 1,
                        metavar = 'directory', default = None,
                        help = "The directory where all the intersections.ply files are")
    
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
if __name__=='__main__':
    # t1_start = perf_counter()
    args = parse_args()
    int_dir = args.intersection_dir[0]
    vx_path = args.voxel_path[0]
    v_size = args.voxel_size[0]
    viz = args.viz
    
    # int_dir = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\3dmodel\\ply\\SMART_raw_result\\intersect'
    # vx_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\3dmodel\\ply\\SMART_raw_result\\voxel\\projected_voxels0.json'
    # v_size = 0.3
    # viz = True
    
    flist = os.listdir(int_dir)
    nfs = len(flist)
    if nfs > 1:
        v_ls = []
        temp_ls = []
        for f in flist:
            vs, temps, headers = utils.read_therm_arr_ply(os.path.join(int_dir, f))
            v_ls.extend(vs)
            temp_ls.extend(temps)
        
    elif nfs == 1:
        v_ls, temp_ls, headers = utils.read_therm_arr_ply(os.path.join(int_dir, flist[0]))
    
    int_xyz_ls = [v.point.xyz for v in v_ls]
    xdim = v_size
    ydim = v_size
    zdim = v_size
    vx_dict = geomie3d.modify.xyzs2voxs(int_xyz_ls, xdim, ydim, zdim)
    # print(vx_dict)
    #convert the voxels to bboxes
    bbx_ls = []
    vx_ls = []
    for cnt,key in enumerate(vx_dict.keys()):
        vx = vx_dict[key]
        midpt = vx['midpt']
        idx = vx['idx']
        temps = np.take(temp_ls, idx, axis=0)
        avg_temp = sum(temps)/len(temps)
        att = {'idx': idx, 'ijk': key, 'midpt':midpt, 'temperature':avg_temp}
        bbx = geomie3d.create.bbox_frm_midpt(midpt, v_size, v_size, v_size, attributes = att)
        bbx_ls.append(bbx)
        
    utils.write_bbox2json(bbx_ls, vx_path)
    # t1_stop = perf_counter()
    # counter = t1_stop - t1_start
    # print('Time taken 2 Merge (mins)', round(counter/60, 1))
    if viz == True:
        viz_dlist = []
        print('Visualizing ...')
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
        