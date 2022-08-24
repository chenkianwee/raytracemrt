import os
import sys
import csv
import json
import argparse
# from time import perf_counter

#add the path to geomie3d
sys.path.append('F:\\kianwee_work\\spyder_workspace\\geomie3d')
import geomie3d
import utils
#----------------------------------------------------------------
def read_csv(csv_path):
    with open(csv_path, mode ='r')as file:
        # reading the CSV file
        csvFile = csv.reader(file)
        
        # displaying the contents of the CSV file
        csvFile = list(csvFile)
        return csvFile
    
def parse_args():
    # create parser object
    parser = argparse.ArgumentParser(description = "Project your Chaosense Data")
 
    # defining arguments for parser object
    parser.add_argument('-m', '--mrt_dir', type = str, nargs = 1,
                        metavar = 'directory', default = None,
                        help = "The directory where all the MRT are")
    
    parser.add_argument('-g', '--grid_dir', type = str, nargs = 1,
                        metavar = 'directory', default = None,
                        help = "The directory where all the MRT are")
    
    parser.add_argument('-f', '--voxel_path', type = str, nargs = 1,
                        metavar = 'filepath', default = None,
                        help = 'The path of the voxel file')
    
    parser.add_argument('-v', '--viz', action = 'store_true',
                        help = 'Open a 3D window to see the result')
    
    # parse the arguments from standard input
    args = parser.parse_args()
    
    return args
#----------------------------------------------------------------
if __name__=='__main__':
    # t1_start = perf_counter()
    args = parse_args()
    mrt_dir = args.mrt_dir[0]
    grid_dir = args.grid_dir[0]
    vx_path = args.voxel_path[0]
    viz = args.viz
    
    # mrt_dir = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\mrt'
    # grid_dir = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\grid'
    # vx_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\voxel\\projected_voxels0.json'
    # viz = True
    
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
        utils.write2csv(merge, mrt_path)
        
    elif nfs == 1:
        csv_path = os.path.join(mrt_dir, flist[0])
        merge = read_csv(csv_path)
    
    # t1_stop = perf_counter()
    # counter = t1_stop - t1_start
    # print('Time taken 2 Merge (mins)', round(counter/60, 1))
    #----------------------------------------------------------------
    #visualize the result
    #----------------------------------------------------------------
    if viz == True:
        viz_dlist = []
        print('Visualizing ...')
        #----------------------------------------------------------------
        # viz the bbox
        #----------------------------------------------------------------
        bbx_ls = utils.vox2bbox(vx_path)
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
        