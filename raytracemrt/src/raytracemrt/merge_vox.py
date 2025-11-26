import os
import json
from itertools import chain

import geomie3d
import numpy as np

import raytracemrt.utils as utils
# import utils
#----------------------------------------------------------------
def merge_vox(voxel_dir):
    flist = os.listdir(voxel_dir)
    vx_ls = []
    for cnt, fname in enumerate(flist):
        vx_path = os.path.join(voxel_dir,fname)
        with open(vx_path, "r") as outfile:
            voxs = json.load(outfile)
        ijks = voxs['ijk']
        bbx_arrs = voxs['bbox_arr']
        midpts = voxs['midpt']
        temps = voxs['temperature']
        if cnt == 0:
            vx_ls.append(ijks)
            vx_ls.append(bbx_arrs)
            vx_ls.append(midpts)
            vx_ls.append(temps)
        else:
            vx_ijk_cmp = vx_ls[0][:]
            vx_ijk_cmp.extend(ijks)
            vx_bbx_arr_cmp = vx_ls[1][:]
            vx_bbx_arr_cmp.extend(bbx_arrs)
            vx_midpt_cmp = vx_ls[2][:]
            vx_midpt_cmp.extend(midpts)
            vx_temp_cmp = vx_ls[3][:]
            vx_temp_cmp.extend(temps)
            
            val, idx, inv_idx = np.unique(vx_ijk_cmp, return_index = True, 
                                          return_inverse=True, axis=0)

            all_idxs = range(len(vx_ijk_cmp))
            dup_idxs = geomie3d.utility.id_dup_indices_1dlist(inv_idx)
            if len(dup_idxs) != 0:
                dup_idxs_flat = list(chain(*dup_idxs))
                # print(dup_idxs_flat)
                # print(all_idxs)
                unq_idxs = geomie3d.utility.find_xs_not_in_ys(all_idxs, dup_idxs_flat)
                # print(unq_idxs)
                zip_dups = list(zip(*dup_idxs))
                # print(len(vx_temp_cmp), zip_dups[0])
                dups1 = np.take(vx_temp_cmp, zip_dups[0], axis=0)
                dups1 = np.where(dups1 == None, np.inf, dups1)
                dups2 = np.take(vx_temp_cmp, zip_dups[1], axis=0)
                dups2 = np.where(dups2 == None, np.inf, dups2)
                
                none1 = np.logical_and(dups1 == np.inf, dups2 != np.inf)
                dups = np.where(none1, dups2, np.inf)
                none2 = np.logical_and(dups1 != np.inf, dups2 == np.inf)
                dups = np.where(none2, dups1, dups)
                no_none = np.logical_and(dups1 != np.inf, dups2 != np.inf)
                dups = np.where(no_none, (dups1+dups2)/2, dups)
                dups = np.where(dups==np.inf, None, dups)
                
                n_idxs = np.append(unq_idxs, np.array(zip_dups[0]))
                vx_ls[0] = np.take(vx_ijk_cmp, n_idxs, axis=0).tolist()
                vx_ls[1] = np.take(vx_bbx_arr_cmp, n_idxs, axis=0).tolist()
                vx_ls[2] = np.take(vx_midpt_cmp, n_idxs, axis=0).tolist()
                vx_ls[3] = np.take(vx_temp_cmp, unq_idxs, axis=0).tolist()
                vx_ls[3].extend(dups.tolist())
            else:
                vx_ls[0] = vx_ijk_cmp
                vx_ls[1] = vx_bbx_arr_cmp
                vx_ls[2] = vx_midpt_cmp
                vx_ls[3] = vx_temp_cmp
    return vx_ls

def processed_merge_vx(voxel_dir, viz):
    vx_ls = merge_vox(voxel_dir)
    ijks = vx_ls[0]
    bbx_arrs = vx_ls[1]
    midpts = vx_ls[2]
    temps = vx_ls[3]
    nvoxs = len(ijks)
    bbx_ls = []
    for i in range(nvoxs):
        ijk = ijks[i]
        bbx_arr = bbx_arrs[i]
        midpt = midpts[i]
        temp = temps[i]
        bbx = geomie3d.create.bbox(bbx_arr, attributes = {'ijk':ijk, 'midpt':midpt,
                                                          'temperature':temp})
        bbx_ls.append(bbx)
        
    vx_path = os.path.join(voxel_dir, 'projected_voxels_merged.json')
    utils.write_bbox2json(bbx_ls, vx_path)
    # print(vx_path)
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
        
#----------------------------------------------------------------
if __name__ == '__main__':    
    voxel_dir = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\3dmodel\\ply\\SMART_raw_result\\voxel'
    viz = True
    processed_merge_vx(voxel_dir, viz)