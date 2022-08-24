import os
import argparse
import utils
#----------------------------------------------------------------
def parse_args():
    # create parser object
    parser = argparse.ArgumentParser(description = "Split your Chaosense Ply file")
 
    # defining arguments for parser object
    parser.add_argument('-s', '--scan', type = str, nargs = 1,
                        metavar = 'filepath', default = None,
                        help = 'The ply file to process')
    
    parser.add_argument('-a', '--afile', type = int, nargs = 1,
                        metavar = 'Directions in a file', default = [10000],
                        help = 'Specify the number of directions in a file')
     
    parser.add_argument('-r', '--result', type = str, nargs = 1,
                        metavar = 'directory', default = None,
                        help = 'The path to save to after the processing')
    
    # parse the arguments from standard input
    args = parser.parse_args()
    return args
#----------------------------------------------------------------
if __name__ == '__main__':
    args = parse_args()
    scan_path = args.scan[0]#'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\3dmodel\\ply\\SMART_raw.ply'
    dirs_afile = args.afile[0]
    res_dir = args.result[0]#'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\3dmodel\\ply'
    v_ls, temp_ls, headers = utils.read_therm_arr_ply(scan_path)
    xyz_ls = [v.point.xyz for v in v_ls]
    afile = dirs_afile
    ndirs = len(v_ls)
    if ndirs > afile:
        #split the file
        nsplits = int(ndirs/afile)
        vs_ls = []
        interval = ndirs/nsplits
        for i in range(nsplits):
            start = int(interval*i)
            end = int(interval*(i+1))
            res_path = os.path.join(res_dir, 'split'+str(i)+'.ply')
            utils.write2ply(res_path, xyz_ls[start:end], temp_ls[start:end], headers)
            print(res_path)
    else:
        print(scan_path)
            