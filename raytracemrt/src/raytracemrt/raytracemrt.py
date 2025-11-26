import os
import stat
import shutil
import argparse
from time import perf_counter

import raytracemrt.utils as utils
import raytracemrt.project as project
import raytracemrt.project2box as project2box
import raytracemrt.merge_vox as merge_vox
import raytracemrt.gen_grids as gen_grids
import raytracemrt.calc_mrt as calc_mrt

# import utils
# import project
# import project2box
# import merge_vox
# import gen_grids
# import calc_mrt
#----------------------------------------------------------------
def parse_args():
    # create parser object
    parser = argparse.ArgumentParser(description = "Project & Caculate MRT of your Chaosense Data")
 
    # defining arguments for parser object
    parser.add_argument('-s', '--scan', type = str, nargs = 1,
                        metavar = 'filepath', default = None,
                        help = 'The ply file to process')
    
    parser.add_argument('-p', '--points', type = str, nargs = 1,
                        metavar = 'filepath', default = [None],
                        help = 'The path of the .pts point cloud file')
    
    parser.add_argument('-x', '--xyz', type = float, nargs = 3,
                        metavar = ('posX', 'posY', 'posZ'), default = None,
                        help = "The position of the sensor")
    
    parser.add_argument('-d', '--space_dim', type = float, nargs = 3,
                        metavar = ('Length(m)','Width(m)','Height(m)'), help = 'Dimensions of the scanned space')
    
    
    parser.add_argument('-z', '--voxel_size', type = float, nargs = 1,
                        metavar = 'voxel size', default = None,
                        help = "The size of the voxel")
    
    parser.add_argument('-g', '--grid', type = float, nargs = 4,
                        metavar = ('Length(m)','Width(m)','Height(m)', 'Buffer(m)'), 
                        help = 'Defining the grid with these dimensions')
    
    parser.add_argument('-v', '--viz', action = 'store_true', default=False,
                        help = 'visualize the calculation procedure if turned on')
    
    # parse the arguments from standard input
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    scan_path = args.scan[0]
    pts_path = args.points[0]
    sensor_pos = args.xyz
    rm_dim = args.space_dim
    voxel_size = args.voxel_size[0]
    grid_dim = args.grid
    viz = args.viz
    print(viz)
    # scan_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm.ply'
    # # pts_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\pts\\example1.pts'
    # pts_path = None
    # rm_dim = [4, 5, 3.5]#length(m) x width(m) x height(m)
    # # sensor_pos = [-0.62, 0.46, 1.5]
    # sensor_pos = [0,0,1.5]
    # voxel_size = 0.3#m
    # grid_dim = [0.5, 0.5, 1, 0.5]#xdim(m), ydim(m), height(m), buffer(m)
    #=================================================================
    #INPUTS
    #=================================================================
    t1_start = perf_counter()
    scan_dir = os.path.dirname(scan_path)
    scan_filename = os.path.basename(scan_path)
    scan_filename = os.path.splitext(scan_filename)[0]
    res_foldername = scan_filename + '_result'
    res_dir = os.path.join(scan_dir, res_foldername)
    split_dir = os.path.join(res_dir, 'split')
    voxel_dir = os.path.join(res_dir, 'voxel')
    intersect_dir = os.path.join(res_dir, 'intersect')
    grid_dir = os.path.join(res_dir, 'grid')
    mrt_dir = os.path.join(res_dir, 'mrt')    
    
    if not os.path.isdir(res_dir):
        #create the folder
        os.makedirs(res_dir)
        
    else:
        #remove everything in it and create it again
        flist = os.listdir(res_dir)
        if len(flist) != 0:
            os.chmod(res_dir, stat.S_IWRITE)
            os.chmod(split_dir, stat.S_IWRITE)
            os.chmod(voxel_dir, stat.S_IWRITE)
            os.chmod(intersect_dir, stat.S_IWRITE)
            os.chmod(mrt_dir, stat.S_IWRITE)
            os.chmod(grid_dir, stat.S_IWRITE)
            shutil.rmtree(res_dir)
            os.makedirs(res_dir)
    
    os.makedirs(split_dir)
    os.makedirs(voxel_dir)
    os.makedirs(intersect_dir)
    os.makedirs(grid_dir)
    os.makedirs(mrt_dir)
    print('========================')
    print('Ignore following error')
    print('Attribute Qt::AA_ShareOpenGLContexts must be set before QCoreApplication is created.')
    print('========================')
    #=================================================================
    #split the ply file if it is too big
    #=================================================================
    dirs_afile = 10000 # the number of directions in the splitted ply file
    split_paths = utils.split_ply(scan_path, dirs_afile, split_dir)
    nsplits = len(split_paths)
    t1_end = perf_counter()
    t_taken = t1_end - t1_start
    t_taken_min = round(t_taken/60, 2)
    print('Time Taken to Split the File (mins)', t_taken_min)
    #=================================================================
    #execute the projection script
    #=================================================================
    voxel_paths = []
    # print(intersect_dir, voxel_dir)
    if pts_path != None:
        #--------------------------------------------------------
        #execute the projection script with geometrical point clouds
        #--------------------------------------------------------
        print('========================')
        print('Projecting ... ...')
        print('========================')
        for cnt,p in enumerate(split_paths):
            print('Projecting ... ...', cnt+1, '/', nsplits)
            intersection_path = os.path.join(intersect_dir, 'projected_intersections' + str(cnt) + '.ply')
            voxel_path = os.path.join(voxel_dir, 'projected_voxels' + str(cnt) + '.json')
            project.project(p, pts_path, sensor_pos, intersection_path, voxel_path, voxel_size, viz)
            voxel_paths.append(voxel_path)
            
        print('========================')
        print('Done Projecting ... ...')
        print('========================')
        t2_end = perf_counter()
        t_taken = t2_end - t1_end
        t_taken_min = round(t_taken/60,1)
        print('Time Taken to Project the Points (mins)', t_taken_min)
    else:
        #--------------------------------------------------------
        #execute the projection script for a simple box
        #--------------------------------------------------------
        print('========================')
        print('Projecting2box ... ...')
        print('========================')
        for cnt,p in enumerate(split_paths):
            print('Projecting ... ...', cnt+1, '/', nsplits)
            intersection_path = os.path.join(intersect_dir, 'projected_intersections' + str(cnt) + '.ply')
            project2box.proj2box(p, intersection_path, sensor_pos, rm_dim, viz)
        print('========================')
        print('Done Projecting ... ...')
        print('========================')
        #--------------------------------------------------------
        #merge all the intersections and voxelised the intersections
        #--------------------------------------------------------
        print('========================')
        print('Voxelizing ... ...')
        print('========================')
        voxel_path = os.path.join(voxel_dir, 'projected_voxels0.json')
        utils.vox_bx(intersect_dir, voxel_path, voxel_size, viz)
        voxel_paths.append(voxel_path)
        print('========================')
        print('Done Voxelizing')
        print('========================')
        t2_end = perf_counter()
        t_taken = t2_end - t1_end
        t_taken_min = round(t_taken/60,1)
        print('Time Taken to Project & Voxelize the Points (mins)', t_taken_min)
    #=================================================================
    #execute mrt calculation
    #=================================================================
    #check the result directory and list out the files 
    flist = os.listdir(voxel_dir)
    nvp = len(flist)
    #--------------------------------------------------------
    #merge all the voxels into a single voxel environment
    #--------------------------------------------------------
    if nvp == len(voxel_paths):
        if nvp == 1:
            vpath2process = voxel_paths[0]
        else:
            merge_vox.processed_merge_vx(voxel_dir, viz)
            vpath2process = os.path.join(voxel_dir, 'projected_voxels_merged.json')
        #--------------------------------------------------------
        # generate the grid points
        #--------------------------------------------------------
        print('========================')
        print('Gridding ... ...')
        print('========================')
        grid_paths = gen_grids.gen_grids(vpath2process, grid_dir, grid_dim, 10000, viz)
        ngrids = len(grid_paths)
        print('Done Gridding ... ...')
        #--------------------------------------------------------
        # calculate mrt
        #--------------------------------------------------------
        print('========================')
        print('Calculating MRT ... ...')
        print('========================')
        mrt_paths = []
        for cnt,p in enumerate(grid_paths):
            print('Calculating MRT ... ...', cnt+1, '/', ngrids)
            mrt_path = os.path.join(mrt_dir, 'mrt'+str(cnt)+'.csv')
            calc_mrt.calc_mrt(vpath2process, p, mrt_path, viz)
            mrt_paths.append(mrt_path)    
        
        t3_end = perf_counter()
        t_taken = t3_end - t2_end
        t_taken_min = round(t_taken/60,1)
        print('Time Taken to Caculate MRT (mins)', t_taken_min)
        
        print('========================')
        print('Done Calculating ... ...')
        print('========================')
        #--------------------------------------------------------
        # merge all the mrt results
        #--------------------------------------------------------
        print('========================')
        print('Processing Results ... ...')
        print('========================')
        utils.merge_viz(mrt_dir, grid_dir, vpath2process, viz)
        
        t4_end = perf_counter()
        t_taken = t4_end - t1_start
        t_taken_min = round(t_taken/60,1)
        print('Total Time Taken (mins)', t_taken_min)
        print('========================')
        print('Ignore following error')
        print('Attribute Qt::AA_ShareOpenGLContexts must be set before QCoreApplication is created.')
        print('========================')
        print('Success !!')
        print('========================')
#----------------------------------------------------------------
if __name__=='__main__':
    main()