import sys
import csv
import json
#add the path to geomie3d
sys.path.append('F:\\kianwee_work\\spyder_workspace\\geomie3d')
import geomie3d

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
