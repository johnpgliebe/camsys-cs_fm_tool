# -*- coding: utf-8 -*-
# CS FutureMobility Tool
# See full license in LICENSE.txt.

"""
Created on Tue Sep 18 12:16:37 2018

@author: mmilkovits
"""
import numpy as np
import openmatrix as omx
import mode_choice.model_defs as md

def store_omx_as_dict(infile_path):
    '''
    Given an omx file, it stores the matrices in a dictionary.
    
    :param infile_path: path of the omx file.
    :returns: dict
    '''
    store_dict = {}
    with omx.open_file(infile_path,'r') as f:
        for name in f.list_matrices():
            store_dict[name] = np.array(f[name])
    return store_dict

    
def expand_prod(var_vector):
    '''
    This returns a md.max_zone x md.max_zone table for a zonal variable vector that applies to the production side.
    
    :param var_vector: either a pandas series or a numpy array with at least md.max_zone entries
    :returns: numpy array md.max_zone x md.max_zone
    :raises: ValueError
    '''
    try:
        return np.repeat(var_vector.values[:md.max_zone].reshape(md.max_zone,1),md.max_zone,axis= 1)
    except:
        try: return np.repeat(var_vector[:md.max_zone].reshape(md.max_zone,1),md.max_zone,axis= 1)
        except: raise ValueError('error expanding vector, check size and input type')

def expand_attr(var_vector):
    '''
    This returns a md.max_zone x md.max_zone table for a zonal variable vector that applies to the attraction side.
    
    :param var_vector: either a pandas series or a numpy array with at least md.max_zone entries
    :returns: numpy array md.max_zone x md.max_zone
    :raises: ValueError
    ''' 

    try:
        return np.repeat(var_vector.values[:md.max_zone].reshape(1,md.max_zone),md.max_zone,axis= 0)
    except:
        try: return np.repeat(var_vector[:md.max_zone].reshape(1,md.max_zone),md.max_zone,axis = 0)
        except: raise ValueError('error expanding vector')
    
def write_trip_tables(mc_obj,out_fn):
    '''
    This writes the resulting trip tables of mode choice to a .omx file.
    
    :param mc_obj: mode choice module object as defined in the IPython notebook
    :param out_fn: path of output .omx file
    '''

    modes = mc_obj.param['mode']
    with omx.open_file(out_fn,'w') as ttmc:
        for pv in mc_obj.peak_veh:
            for mode in modes:
                ttmc[f'{mode}_{pv}'] = mc_obj.table_container.aggregate_by_mode_segment(mode, pv)
    
def sum_unequal_length(a,b):
    if len(a)>len(b):
        b.resize(a.shape, refcheck=False)
    else:
        a.resize(b.shape, refcheck=False)
    return a+b                  
    

def OD_slice(trip_table, O_slice = np.ones(md.max_zone).astype(bool), D_slice = np.ones(md.max_zone).astype(bool), max_zone = md.max_zone):
    if len(O_slice) == max_zone and len(D_slice) == max_zone:
        sliced = np.zeros((md.max_zone,md.max_zone))
        sliced[np.outer(O_slice,D_slice)] = trip_table[np.outer(O_slice,D_slice)]
        return sliced