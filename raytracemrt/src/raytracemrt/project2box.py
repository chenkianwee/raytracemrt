import multiprocessing as mp

import geomie3d
import numpy as np

import raytracemrt.utils as utils
# import utils
#----------------------------------------------------------------
def process_projection(projection_results, other_ls):
    hrs = projection_results[0]
    mrs = projection_results[1]
    intvs = []
    temp_ls = []
    for hr in hrs:
        att = hr.attributes['rays_faces_intersection']
        intersect = att['intersection']
        temp = hr.attributes['temperature']
        if len(intersect) == 1:
            temp_ls.append(temp)
            intvs.append(intersect[0])
        else:
            unq = np.unique(intersect, axis=0)
            if len(unq) == 1:
                intvs.append(intersect[0])
                temp_ls.append(temp)
            else:
                print('not sure what is happening please debug')
    
    if len(mrs) != 0:
        e_ls = []
        for mr in mrs:
            orig = mr.origin
            dirx = mr.dirx
            mv_xyz = geomie3d.calculate.move_xyzs([orig], [dirx], 10)[0]
            vlist = geomie3d.create.vertex_list([orig,mv_xyz])
            e = geomie3d.create.pline_edge_frm_verts(vlist)
            e_ls.append(e)
        other_ls.append({'topo_list':e_ls, 'colour': 'red'})
    return intvs, temp_ls

def proj2box(therm_arr_path, res_path, sensor_pos, rm_dim, viz):
    # t1_start = perf_counter()
    other_ls = []
    #read the file and get all the vert data
    verts_data, temp_ls, headers = utils.read_therm_arr_ply(therm_arr_path)
    ndir = len(verts_data)
    if ndir == 0:
        print('The PLY file specified is not produce from a Chaosense Sensor')
    else:
        #create the room based on the room dim
        bx = geomie3d.create.box(rm_dim[0], rm_dim[1], rm_dim[2], centre_pt=[0,0,rm_dim[2]/2])
        # bedges = geomie3d.get.edges_frm_solid(bx)
        # other_ls.append({'topo_list':bedges, 'colour': 'red'})
        #triangulate the box
        bfaces = geomie3d.get.faces_frm_solid(bx)
        nbfaces = []
        tri_ls = []
        for f in bfaces:
            rf = geomie3d.modify.reverse_face_normal(f)
            tris = geomie3d.modify.triangulate_face(rf)
            tri_ls.extend(tris)
            nbfaces.append(rf)
            
        tri_cmp = geomie3d.create.composite(tri_ls)
        tri_edges = geomie3d.get.edges_frm_composite(tri_cmp)
        other_ls.append({'topo_list':tri_edges, 'colour': 'red'})
        #convert the verts to rays and 
        rays = []
        for v in verts_data:
            temp = v.attributes['temperature']
            ray = geomie3d.create.ray(sensor_pos, v.point.xyz, attributes = {'temperature':temp})
            rays.append(ray)
        
        aloop = 36000
        nfaces = len(nbfaces)
        ttl = ndir*nfaces
        nparallel = int(ttl/aloop)
        # print('numpber of splits:', nparallel)
        if nparallel != 0:
            # print('number of splits:', nparallel)
            rays_ls = utils.separate_rays(rays, nparallel)
        else:
            rays_ls = [rays]
        #------------------------------------------------------------------
        #project!!!
        #------------------------------------------------------------------
        # #project them to the triangulated faces
        # results = []
        # for rays in rays_ls:
        #     hfs, mfs, hrs, mrs = geomie3d.calculate.rays_faces_intersection(rays, nbfaces)
        #     results.append([hfs, mfs, hrs, mrs])
        #------------------------------------------------------------------
        # parallel processing version
        #------------------------------------------------------------------
        # Step 1: Init multiprocessing.Pool()
        pool = mp.Pool(mp.cpu_count())
        results = pool.starmap(geomie3d.calculate.rays_faces_intersection, [(ray, nbfaces) for ray in rays_ls])
        pool.close()
        #------------------------------------------------------------------
        #process the results
        #------------------------------------------------------------------
        int_xyz_ls = []
        temp_ls = []
        for result in results:
            xyzs, temps = process_projection(result, other_ls)
            int_xyz_ls.extend(xyzs)
            temp_ls.extend(temps)
        
        print('Writing to file ...', res_path)
        utils.write2ply(res_path, int_xyz_ls, temp_ls, headers)
        #-----------------------------------------------------------------
        if viz == True:
            print('Visualizing ...')
            #for viz purpose
            #move the verts to the position of the sensor
            cmp = geomie3d.create.composite(verts_data)
            mv_cmp = geomie3d.modify.move_topo(cmp, sensor_pos)
            mv_verts = geomie3d.get.vertices_frm_composite(mv_cmp)
            other_ls.append({'topo_list':mv_verts, 'colour': 'white'})
            
            intvs = geomie3d.create.vertex_list(int_xyz_ls)
            geomie3d.utility.viz_falsecolour(intvs, temp_ls, 
                                              other_topo_dlist=other_ls)
        
#----------------------------------------------------------------
if __name__=='__main__':
    therm_arr_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm.ply'
    res_path = 'F:\\kianwee_work\\princeton\\2022_06_to_2022_12\\chaosense\\example1\\ply\\example1_therm_result\\intersect\\intersect.ply'
    sensor_pos = [0,0,0]
    rm_dim = [4, 5, 3.5]
    viz = True
    proj2box(therm_arr_path, res_path, sensor_pos, rm_dim, viz)
    