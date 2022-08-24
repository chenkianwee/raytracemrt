import os
import sys
import stat
import shutil
import subprocess
from time import perf_counter

import multiprocessing as mp
#=================================================================
#INPUTS
#=================================================================
scan_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm.ply'
pts_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\pts\\example1.pts'
# pts_path = ''
rm_dim = [4, 5, 3.5]#length(m) x width(m) x height(m)
sensor_pos = [-0.62, 0.46, 1.5]
voxel_size = 0.3#m
grid_dim = [0.5, 0.5, 1, 0.5]#xdim(m), ydim(m), height(m), buffer(m)
#=================================================================
#INPUTS
#=================================================================
t1_start = perf_counter()
current_path = os.path.dirname(__file__)
py_exe = sys.executable
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
#=================================================================
#split the ply file if it is too big
#=================================================================
split_py = os.path.join(current_path, 'split_ply.py')
split_call_ls = [py_exe, split_py,
                  '-s', scan_path,
                  '-a', str(10000),
                  '-r', split_dir]

split_paths = subprocess.Popen(split_call_ls, stdout=subprocess.PIPE).communicate()[0]
split_paths = split_paths.decode()
split_paths = split_paths.split('\r\n')
split_paths = [i for i in split_paths if i] # rmv any empty strings
t1_end = perf_counter()
t_taken = t1_end - t1_start
t_taken_min = round(t_taken/60, 2)
print('Time Taken to Split the File (mins)', t_taken_min)
#=================================================================
#execute the projection script
#=================================================================
cpu_cnt = mp.cpu_count()
voxel_paths = []
# print(intersect_dir, voxel_dir)
if pts_path != '':
    #--------------------------------------------------------
    #execute the projection script with geometrical point clouds
    #--------------------------------------------------------
    proj_py = os.path.join(current_path, 'project.py')
    proj_call_ls = [py_exe, proj_py, 
                    '-s', None,
                    '-p', pts_path,
                    '-r', None, 
                    '-f', None,
                    '-x', str(sensor_pos[0]), str(sensor_pos[1]), str(sensor_pos[2]),
                    '-z', str(voxel_size)
                    ]
    
    proj_processes = []
    for cnt,p in enumerate(split_paths):
        div = int(cnt/cpu_cnt)
        mulof = cnt%cpu_cnt
        proj_call_ls[3] = p
        intersection_path = os.path.join(intersect_dir, 'projected_intersections' + str(cnt) + '.ply')
        proj_call_ls[7] = intersection_path
        voxel_path = os.path.join(voxel_dir, 'projected_voxels' + str(cnt) + '.json')
        proj_call_ls[9] = voxel_path
        # print(proj_call_ls)
        # proj_res = subprocess.Popen(proj_call_ls, stdout=subprocess.PIPE).communicate()[0]
        # print(proj_res)
        sp = subprocess.Popen(proj_call_ls)
        proj_processes.append(sp)
        voxel_paths.append(voxel_path)
        print('Sending ... ply file', cnt)
        if div > 0 and mulof == 0:
            print('Projecting ... ...')
            proj_processes[-1].wait()

    print('Projecting ... ...')
    proj_processes[-1].wait()
    print('Done Projecting ... ...')
        
    t2_end = perf_counter()
    t_taken = t2_end - t1_end
    t_taken_min = round(t_taken/60,1)
    print('Time Taken to Project the Points (mins)', t_taken_min)
else:
    #--------------------------------------------------------
    #execute the projection script for a simple box
    #--------------------------------------------------------
    proj_py = os.path.join(current_path, 'project2box.py')
    proj_call_ls = [py_exe, proj_py, 
                    '-s', None, 
                    '-r', None,
                    '-x', str(sensor_pos[0]), str(sensor_pos[1]), str(sensor_pos[2]),
                    '-d', str(rm_dim[0]), str(rm_dim[1]), str(rm_dim[2]),
                    ]
    
    proj_processes = []
    for cnt,p in enumerate(split_paths):
        div = int(cnt/cpu_cnt)
        mulof = cnt%cpu_cnt
        proj_call_ls[3] = p
        intersection_path = os.path.join(intersect_dir, 'projected_intersections' + str(cnt) + '.ply')
        proj_call_ls[5] = intersection_path
        # proj_res = subprocess.Popen(proj_call_ls, stdout=subprocess.PIPE).communicate()[0]
        # print(proj_res)
        sp = subprocess.Popen(proj_call_ls)
        proj_processes.append(sp)
        print('Sending ... ply file', cnt)
        if div > 0 and mulof == 0:
            print('Projecting ... ...')
            proj_processes[-1].wait()
                
    print('Projecting ... ...')
    proj_processes[-1].wait()
    print('Done Projecting ... ...')
    #--------------------------------------------------------
    #merge all the intersections and voxelised the intersections
    #--------------------------------------------------------
    voxel_path = os.path.join(voxel_dir, 'projected_voxels0.json')
    voxbx_py = os.path.join(current_path, 'voxelize_box.py')
    voxbx_call_ls = [py_exe, voxbx_py, 
                     '-d', intersect_dir, 
                     '-f', voxel_path,
                     '-z', str(voxel_size)
                    ]
    
    subprocess.call(voxbx_call_ls)
    voxel_paths.append(voxel_path)
    t2_end = perf_counter()
    t_taken = t2_end - t1_end
    t_taken_min = round(t_taken/60,1)
    print('Time Taken to Project the Points (mins)', t_taken_min)
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
        merge_py = os.path.join(current_path, 'merge_vox.py')
        merge_call_ls = [py_exe, merge_py, 
                        '-d', voxel_dir]
        
        subprocess.call(merge_call_ls)
        vpath2process = os.path.join(voxel_dir, 'projected_voxels_merged.json')
    #--------------------------------------------------------
    # generate the grid points
    #--------------------------------------------------------
    grid_py = os.path.join(current_path, 'gen_grids.py')
    grid_call_ls = [py_exe, grid_py, 
                   '-e', vpath2process,
                   '-r', grid_dir,
                   '-a', str(10000),
                   '-g', str(grid_dim[0]), str(grid_dim[1]), 
                   str(grid_dim[2]), str(grid_dim[3])]
    
    # print(grid_call_ls)
    grid_paths = subprocess.Popen(grid_call_ls, stdout=subprocess.PIPE).communicate()[0]
    grid_paths = grid_paths.decode()
    grid_paths = grid_paths.split('\r\n')
    grid_paths = [i for i in grid_paths if i] # rmv any empty strings
    #--------------------------------------------------------
    # calculate mrt
    #--------------------------------------------------------
    mrt_py = os.path.join(current_path, 'calc_mrt.py')
    mrt_call_ls = [py_exe, mrt_py, 
                   '-e', vpath2process,
                   '-g', None,
                   '-r', None]
    mrt_paths = []
    mrt_processes = []
    for cnt,p in enumerate(grid_paths):
        div = int(cnt/cpu_cnt)
        mulof = cnt%cpu_cnt
        mrt_call_ls[5] = p
        mrt_path = os.path.join(mrt_dir, 'mrt'+str(cnt)+'.csv')
        mrt_call_ls[7] = mrt_path
        # print(mrt_call_ls)
        sp = subprocess.Popen(mrt_call_ls)
        mrt_processes.append(sp)
        mrt_paths.append(mrt_path)
        print('Sending ... grid file', cnt)
        if div > 0 and mulof == 0:
            print('Calculating MRT ... ...')
            mrt_processes[-1].wait()

    print('Calculating MRT ... ...')
    mrt_processes[-1].wait()
    print('Done Calculating ... ...')
    #--------------------------------------------------------
    # merge all the mrt results
    #--------------------------------------------------------
    viz_py = os.path.join(current_path, 'merge_viz.py')
    viz_call_ls = [py_exe, viz_py, 
                   '-m', mrt_dir,
                   '-g', grid_dir,
                   '-f', vpath2process, '-v']
    
    subprocess.call(viz_call_ls)
    
    t3_end = perf_counter()
    t_taken = t3_end - t2_end
    t_taken_min = round(t_taken/60,1)
    print('Time Taken to Caculate MRT (mins)', t_taken_min)
    
    t4_end = perf_counter()
    t_taken = t4_end - t1_start
    t_taken_min = round(t_taken/60,1)
    print('Total Time Taken (mins)', t_taken_min)
    