# coding: utf-8
# CS FutureMobility Tool
# See full license in LICENSE.txt.

import os
import numpy as np
import pandas as pd
import openmatrix as omx
import mode_choice.matrix_utils as mtx
import mode_choice.model_defs as md
#from shutil import copyfile
#from spatialmodel.mc_table_container import table_container


def inter_extrap_triptable(config, year = 2030):
    '''interpolate or extrapolate trip tables
    
    :param config: the scenario object defined in the config.py - path to output trip table
    :param year: year of interpolated or extrapolated trip table
    '''
    new_table = config.data_path + r"..\\" + str(year) + "\pre_MC_trip_6_purposes.omx"
    pre_MC_trip_file_2016 = config.data_path + r"..\2016\pre_MC_trip_6_purposes.omx"
    pre_MC_trip_file_2040 = config.data_path + r"..\2040\pre_MC_trip_6_purposes.omx"
        
    with omx.open_file(pre_MC_trip_file_2016) as f1 , omx.open_file(pre_MC_trip_file_2040) as f2, omx.open_file(new_table,'w') as fout:
        for name in f1.list_matrices():
            tt_2016 = np.array(f1[name])[:md.max_zone,:md.max_zone]
            tt_2040 = np.array(f2[name])[:md.max_zone,:md.max_zone]
            diff = tt_2040 - tt_2016
            yearly_diff = diff / 24 # annual growth of trips
            growth_years = year - 2016
            tt_new = tt_2016 + (yearly_diff * growth_years)
            tt_new = tt_new.clip(min=0) # don't let trips go negative
            fout[name] = tt_new

def inter_extrap_trucktriptable(config, year = 2030):
    '''interpolate or extrapolate truck trip tables
    
    :param config: the scenario object defined in the config.py - path to output trip table
    :param year: year of interpolated or extrapolated trip table
    '''
    new_table = config.data_path + r"..\\" + str(year) + "\\truck_trips.omx"
    pre_MC_trip_file_2016 = config.data_path + r"..\2016\\truck_trips.omx"
    pre_MC_trip_file_2040 = config.data_path + r"..\2040\\truck_trips.omx"
        
    with omx.open_file(pre_MC_trip_file_2016) as f1 , omx.open_file(pre_MC_trip_file_2040) as f2, omx.open_file(new_table,'w') as fout:
        for name in f1.list_matrices():
            tt_2016 = np.array(f1[name])[:md.max_zone,:md.max_zone]
            tt_2040 = np.array(f2[name])[:md.max_zone,:md.max_zone]
            diff = tt_2040 - tt_2016
            yearly_diff = diff / 24 # annual growth of trips
            growth_years = year - 2016
            tt_new = tt_2016 + (yearly_diff * growth_years)
            tt_new = tt_new.clip(min=0) # don't let trips go negative
            fout[name] = tt_new
    
def land_use_growth_shift(config, factor = 0.5):
    '''apply land use growth shifts to tazs defined in Densified_TAZs.csv 
    
    :param config: the scenario object defined in the config.py - path to output trip table and zone files
    :param factor: share of growth to be reallocated
    '''
    modified_2040 = config.scen_path + r"growth_shift_trip_tables.omx"

    pre_MC_trip_file_2016 = config.data_path + r"..\2016\pre_MC_trip_6_purposes.omx"
    pre_MC_trip_file_2040 = config.data_path + r"..\2040\pre_MC_trip_6_purposes.omx"
    
    dense_taz = pd.read_csv(config.scen_path + r"Densified_TAZs.csv").sort_values('ID_FOR_CS')[['ID_FOR_CS']]
    dense_taz['dense'] = 1
    all_taz = pd.read_csv(config.taz_file)
    dense_taz_list = all_taz[['ID_FOR_CS']].merge(dense_taz,on = 'ID_FOR_CS',how = 'left').fillna(0).astype(bool)[:md.max_zone]

    with omx.open_file(pre_MC_trip_file_2016) as f1 , omx.open_file(pre_MC_trip_file_2040) as f2, omx.open_file(modified_2040,'w') as fout:
        for name in f1.list_matrices():
            tt_2016 = np.array(f1[name])[:md.max_zone,:md.max_zone]
            tt_2040 = np.array(f2[name])[:md.max_zone,:md.max_zone]
            diff = tt_2040 - tt_2016
            prod_sum_2016 = tt_2016.sum(axis = 1)
            prod_sum_2040 = tt_2040.sum(axis = 1)
            prod_sum_diff = diff.sum(axis = 1)
            sum_to_transfer = prod_sum_diff[~dense_taz_list['dense'].values].sum() * factor
            prod_sum_diff[~dense_taz_list['dense'].values] = prod_sum_diff[~dense_taz_list['dense'].values] * (1-factor)
            prod_sum_diff[dense_taz_list['dense'].values] = (prod_sum_diff[dense_taz_list['dense'].values] 
        + sum_to_transfer * prod_sum_2040[dense_taz_list['dense'].values] / prod_sum_2040[dense_taz_list['dense'].values].sum())
            # distribute prod_sum to each attraction zone
            tt_new = pd.DataFrame(tt_2040).divide(pd.Series(prod_sum_2040), axis = 0).fillna(0).multiply(prod_sum_2016 + prod_sum_diff,axis = 0).values
            fout[name] = tt_new
