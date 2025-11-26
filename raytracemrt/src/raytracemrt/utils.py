import os
import csv
import json

import geomie3d
import numpy as np

def check_ply_file(header):
    ref_h = ['ply', 'format ascii 1.0',
             'comment date',
             'comment time',
             'comment sensorid',
             'comment sensortype',
             'element vertex',
             'property float32 x', 
             'property float32 y', 
             'property float32 z', 
             'property float32 temperature', 
             'end_header']
    
    check = 0
    for h in header:
        h = h.lower()
        h = h.replace('\n','')
        hsplit = h.split(' ')
        if hsplit[0] == 'comment':
            ctype = hsplit[1]
            if ctype=='date' or ctype=='time' or ctype=='sensorid' or ctype=='sensortype':
                h = hsplit[0] + ' ' + ctype
        
        elif hsplit[0] == 'element':
            if hsplit[1] == 'vertex':
                h = hsplit[0] + ' ' + hsplit[1]
                
        if h in ref_h:
            # print(h)
            check+=1

    if check == 12:
        return True
    else:
        return False

def read_therm_arr_ply(file_path):    
    with open(file_path) as f:
        lines = f.readlines()
    nheaders = 12
    #check if this is a valid chaosense file
    headers = lines[0:nheaders]
    isValid = check_ply_file(headers)
    if isValid:
        xyzs = []
        verts_data = lines[nheaders:]
        temp_ls = []
        temp_dls = []
        for v in verts_data:
            v = v.replace('\n', '')
            v = v.replace('\t', ' ')
            vsplit = v.split(' ')
            vsplit = list(map(float, vsplit))
            xyzs.append(vsplit[0:3])
            temp_dls.append({'temperature':vsplit[3]})
            temp_ls.append(vsplit[3])
        
        v_ls = geomie3d.create.vertex_list(xyzs, attributes_list=temp_dls)
        return v_ls, temp_ls, headers
    else:
        return [], [], headers

def write2ply(res_path, xyz_ls, temp_ls, header):
    nvs = len(xyz_ls)
    nvs_line = 'element vertex ' + str(nvs) + '\n'
    v_cnt = 0
    for cnt, h in enumerate(header):
        hsplit = h.split(' ')
        if hsplit[0] == 'element':
            if hsplit[1] == 'vertex':
                v_cnt = cnt
    
    header_w = header[:]
    header_w[v_cnt] = nvs_line
    for cnt,xyz in enumerate(xyz_ls):
        temp = temp_ls[cnt]
        v_str = str(xyz[0]) + ' ' + str(xyz[1]) + ' ' + str(xyz[2]) + ' ' + str(temp) + '\n'
        header_w.append(v_str)
    
    f = open(res_path, "w")
    f.writelines(header_w)
    f.close()
    
def separate_rays(rays, nparallel):
    rays_ls = []
    nrays = len(rays)
    interval = nrays/nparallel
    for i in range(nparallel):
        start = int(interval*i)
        end = int(interval*(i+1))
        rays_ls.append(rays[start:end])
    return rays_ls

def write_bbox2json(bbox_ls, vx_path):
    ijks = []
    bbx_arrs = []
    midpts = []
    temps = []
    for bbox in bbox_ls:
        att = bbox.attributes
        ijks.append(att['ijk'])
        bbx_arrs.append(bbox.bbox_arr.tolist())
        midpts.append(att['midpt'])
        if 'temperature'in att:
            temps.append(att['temperature'])
        else:
            temps.append(None)
    vx_d = {'ijk':ijks, 'bbox_arr':bbx_arrs, 'midpt':midpts, 
            'temperature': temps}
    
    with open(vx_path, "w") as outfile:
        json.dump(vx_d, outfile)
        
def write2csv(rows, csv_path):
    # writing to csv file 
    with open(csv_path, 'w', newline='') as csvfile: 
        # creating a csv writer object 
        csvwriter = csv.writer(csvfile) 
        # writing the data rows 
        csvwriter.writerows(rows)
        
def vox2bbox(voxel_path):
    with open(voxel_path, "r") as outfile:
        voxs = json.load(outfile)
    ijks = voxs['ijk']
    bbx_arrs = voxs['bbox_arr']
    midpts = voxs['midpt']
    temps = voxs['temperature']
    nvoxs = len(ijks)
    bbx_ls = []
    for i in range(nvoxs):
        bbx_arr = bbx_arrs[i]
        ijk = ijks[i]
        midpt = midpts[i]
        temp = temps[i]
        if temp != None:
            bbx = geomie3d.create.bbox(bbx_arr, attributes = {'ijk':ijk,
                                                              'midpt':midpt,
                                                              'temperature':temp})
        else:
            bbx = geomie3d.create.bbox(bbx_arr, attributes = {'ijk':ijk,
                                                              'midpt':midpt})
        bbx_ls.append(bbx)

    return bbx_ls

def split_ply(scan_path, dirs_afile, res_dir):
    v_ls, temp_ls, headers = read_therm_arr_ply(scan_path)
    xyz_ls = [v.point.xyz for v in v_ls]
    afile = dirs_afile
    ndirs = len(v_ls)
    spath_ls = []
    if ndirs > afile:
        #split the file
        nsplits = int(ndirs/afile)
        interval = ndirs/nsplits
        for i in range(nsplits):
            start = int(interval*i)
            end = int(interval*(i+1))
            res_path = os.path.join(res_dir, 'split'+str(i)+'.ply')
            write2ply(res_path, xyz_ls[start:end], temp_ls[start:end], headers)
            spath_ls.append(res_path)
    else:
        spath_ls.append(scan_path)
    return spath_ls

def vox_bx(int_dir, vx_path, v_size, viz):
    flist = os.listdir(int_dir)
    nfs = len(flist)
    if nfs > 1:
        v_ls = []
        temp_ls = []
        for f in flist:
            vs, temps, headers = read_therm_arr_ply(os.path.join(int_dir, f))
            v_ls.extend(vs)
            temp_ls.extend(temps)
        
    elif nfs == 1:
        v_ls, temp_ls, headers = read_therm_arr_ply(os.path.join(int_dir, flist[0]))
    
    int_xyz_ls = [v.point.xyz for v in v_ls]
    xdim = v_size
    ydim = v_size
    zdim = v_size
    vx_dict = geomie3d.modify.xyzs2voxs(int_xyz_ls, xdim, ydim, zdim)
    # print(vx_dict)
    #convert the voxels to bboxes
    bbx_ls = []
    for cnt,key in enumerate(vx_dict.keys()):
        vx = vx_dict[key]
        midpt = vx['midpt']
        idx = vx['idx']
        temps = np.take(temp_ls, idx, axis=0)
        avg_temp = sum(temps)/len(temps)
        att = {'idx': idx, 'ijk': key, 'midpt':midpt, 'temperature':avg_temp}
        bbx = geomie3d.create.bbox_frm_midpt(midpt, v_size, v_size, v_size, attributes = att)
        bbx_ls.append(bbx)
        
    write_bbox2json(bbx_ls, vx_path)
    # t1_stop = perf_counter()
    # counter = t1_stop - t1_start
    # print('Time taken 2 Merge (mins)', round(counter/60, 1))
    if viz == True:
        print('Visualizing ...')
        viz_dlist = []
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

def read_csv(csv_path):
    with open(csv_path, mode ='r')as file:
        # reading the CSV file
        csvFile = csv.reader(file)
        
        # displaying the contents of the CSV file
        csvFile = list(csvFile)
        return csvFile

def merge_viz(mrt_dir, grid_dir, vx_path, viz):
    flist = os.listdir(mrt_dir)
    nfs = len(flist)
    if nfs > 1:
        merge = []
        for f in flist:
            csv_path = os.path.join(mrt_dir, f)
            lines = read_csv(csv_path)
            header = lines[0]
            rows = lines[1:]
            # rows = list(map(float, rows))
            merge.extend(rows)
        
        merge.insert(0, header)
        mrt_path = os.path.join(mrt_dir, 'mrt_merged.csv')
        write2csv(merge, mrt_path)
        
    elif nfs == 1:
        csv_path = os.path.join(mrt_dir, flist[0])
        merge = read_csv(csv_path)
        
    #----------------------------------------------------------------
    #visualize the result
    #----------------------------------------------------------------
    if viz == True:
        viz_dlist = []
        print('Visualizing ...')
        #----------------------------------------------------------------
        # viz the bbox
        #----------------------------------------------------------------
        bbx_ls = vox2bbox(vx_path)
        v_size = round(bbx_ls[0].maxx - bbx_ls[0].minx, 1)
        viz_ls = []
        bbox_temps = []
        temp_viz = []
        viz_pt = True
        for bbx in bbx_ls:
            midpt = geomie3d.calculate.bbox_centre(bbx)
            if viz_pt == True:
                viz_topo = [geomie3d.create.vertex(midpt)]
                if 'temperature' in bbx.attributes:
                    bbox_temps.append(bbx.attributes['temperature'])
                    temp_viz.extend(viz_topo)
            else:
                viz_topo = [geomie3d.create.box(v_size, v_size, v_size, centre_pt=midpt)]
                # viz_topo = geomie3d.get.edges_frm_solid(bx)
                if 'temperature' in bbx.attributes:
                    bbox_temps.append(bbx.attributes['temperature'])
                    temp_v = geomie3d.create.vertex(midpt)
                    temp_viz.append(temp_v)
                    
            viz_ls.extend(viz_topo)
        
        # print(bbox_temps)
        viz_dlist.append({'topo_list': viz_ls, 'colour': [0,0,1,0.2], 'px_mode': False, 'point_size': v_size})
        #----------------------------------------------------------------
        # viz the grid
        #----------------------------------------------------------------
        glist = os.listdir(grid_dir)
        grid_path = os.path.join(grid_dir, glist[0])
        with open(grid_path, "r") as outfile:
            grids = json.load(outfile)
            
        dimx = grids['xdim']
        dimy = grids['ydim']
        del merge[0]
        grid_faces = []
        temp_ls = []
        for row in merge:
            row = list(map(float, row))
            temp = row[3]
            if temp != -999:
                f = geomie3d.create.polygon_face_frm_midpt(row[0:3], dimy, dimx)
                grid_faces.append(f)
                temp_ls.append(row[3])
        
        # grid_faces.extend(temp_viz)
        # temp_ls.extend(bbox_temps)
        geomie3d.utility.viz_falsecolour(grid_faces, temp_ls, other_topo_dlist = viz_dlist)
        
#----------------------------------------------------------------
if __name__ == '__main__':
    # scan_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm.ply'
    # dirs_afile = 10000
    # res_dir = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\split'
    # spaths = split_ply(scan_path, dirs_afile, res_dir)
    
    # int_dir = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\intersect'
    # vx_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\voxel\\projected_voxels0.json'
    # v_size = 0.3
    # viz = True
    # vox_bx(int_dir, vx_path, v_size, viz)
    
    mrt_dir = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\mrt'
    grid_dir = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\grid'
    vx_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\voxel\\projected_voxels0.json'
    viz = True
    merge_viz(mrt_dir, grid_dir, vx_path, viz)