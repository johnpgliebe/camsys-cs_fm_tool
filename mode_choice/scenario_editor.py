# coding: utf-8
# CS FutureMobility Tool
# See full license in LICENSE.txt.

import numpy as np
import pandas as pd
import openmatrix as omx
import mode_choice.model_defs as md
import mode_choice.matrix_utils as mtx
import mode_choice.mode_choice as mode_choice
import copy
import re
import os
from mode_choice.mc_table_container import table_container


def clean_vehicle_costs(mc_obj, clean_savings):
    ''' Decrease the cost per mile for clean vehicles
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param clean_savings: adjustment value (cents per mile) added to op cost
    '''
    mc_obj.cost_per_mile += clean_savings

def land_use_growth_shift(mc_obj, growth_shift_factor, zone_factor_file):
    ''' shifts growth in trips to zones identified in zone factor file
    
    Growth is shifted to zones identified in the input file from Boston 
    zones not included in the file
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param growth_shift_factor: amount of growth to shift
    :param zone_factor_file: file containing zones to shift growth to 
    '''
    modified_trips = mc_obj.config.scen_path + r"growth_shift_trip_tables.omx"
    factor = growth_shift_factor
    
    # if file is already in place, just use it, else derive it from baseline
    if os.path.isfile(modified_trips):
        mc_obj.pre_MC_trip_table = mtx.store_omx_as_dict(modified_trips)
    else:
        pre_MC_trip_file_2016 = mc_obj.config.data_path + r"..\2016\pre_MC_trip_6_purposes.omx"
        pre_MC_trip_file_future = mc_obj.config.data_path + r".\pre_MC_trip_6_purposes.omx"
        
        dense_taz = pd.read_csv(mc_obj.config.param_path + zone_factor_file).sort_values('ID_FOR_CS')[['ID_FOR_CS']]
        dense_taz['dense'] = 1
        all_taz = pd.read_csv(mc_obj.config.taz_file)
        dense_taz_list = all_taz[['ID_FOR_CS','TOWN']].merge(dense_taz,on = 'ID_FOR_CS',how = 'left').fillna(0)[:md.max_zone]
        with omx.open_file(pre_MC_trip_file_2016) as f1 , omx.open_file(pre_MC_trip_file_future) as f2, omx.open_file(modified_trips,'w') as fout:
            for name in f1.list_matrices():
                tt_2016 = np.array(f1[name])[:md.max_zone,:md.max_zone]
                tt_future = np.array(f2[name])[:md.max_zone,:md.max_zone]
                diff = np.maximum(tt_future - tt_2016,0)
                prod_sum_future = tt_future.sum(axis = 1)
                prod_sum_diff = diff.sum(axis = 1)
                prod_sum_diff[(dense_taz_list['TOWN']!='BOSTON,MA')]=0
                sum_to_transfer = prod_sum_diff[(dense_taz_list['TOWN']=='BOSTON,MA')&(dense_taz_list['dense']==0)].sum() * factor
                prod_sum_diff[(dense_taz_list['TOWN']=='BOSTON,MA')&(dense_taz_list['dense']==0)] = (
                    prod_sum_diff[(dense_taz_list['TOWN']=='BOSTON,MA')&(dense_taz_list['dense']==0)] * (factor - 1))
                prod_sum_diff[(dense_taz_list['TOWN']=='BOSTON,MA')&(dense_taz_list['dense']==1)] = (
                        sum_to_transfer * (prod_sum_future[(dense_taz_list['TOWN']=='BOSTON,MA')&(dense_taz_list['dense']==1)] 
                        / prod_sum_future[(dense_taz_list['TOWN']=='BOSTON,MA')&(dense_taz_list['dense']==1)].sum()))
                # distribute prod_sum to each attraction zone
                tt_new = pd.DataFrame(tt_future).divide(pd.Series(prod_sum_future), axis = 0).fillna(0).multiply(prod_sum_future + prod_sum_diff,axis = 0).values
                #print('writing {0} trips to table {1}' .format(tt_new.sum(), name))
                fout[name] = tt_new
        mc_obj.pre_MC_trip_table = mtx.store_omx_as_dict(modified_trips)
  
def compact_land_use(mc_obj, zone_factor_file, ):
    ''' shifts growth in trips according to zones and factors defined in file
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param zone_factor_file: file containing zones and growth factor 
    '''    
    modified_trips = mc_obj.config.scen_path + r"growth_shift_trip_tables.omx"
 
    pre_MC_trip_file_2016 = mc_obj.config.data_path + r"..\2016\pre_MC_trip_6_purposes.omx"
    pre_MC_trip_file_future = mc_obj.config.data_path + r".\pre_MC_trip_6_purposes.omx"
    
    zone_factors = pd.read_csv(mc_obj.config.param_path + zone_factor_file).sort_values('ID')
    
    all_taz = pd.read_csv(mc_obj.config.taz_file)
    taz_factors = all_taz[['ID','TOWN']].merge(zone_factors,on = 'ID',how = 'left').fillna(1)[:md.max_zone]

        
# ==DEBUG===========================================================================
#         margs_2016 = {}
#         margs_2040_base = {}
#         margs_2040_new = {}
# 
#         margs_2016['ID'] = taz_factors['ID']
#         margs_2016['BOSTON_NB'] = taz_factors['BOSTON_NB']
#         margs_2040_base['ID'] = taz_factors['ID']
#         margs_2040_base['BOSTON_NB'] = taz_factors['BOSTON_NB']        
#         margs_2040_new['ID'] = taz_factors['ID']
#         margs_2040_new['BOSTON_NB'] = taz_factors['BOSTON_NB']     
# =============================================================================
        
    with omx.open_file(pre_MC_trip_file_2016) as f1 , omx.open_file(pre_MC_trip_file_future) as f2, omx.open_file(modified_trips,'w') as fout:
        for name in f1.list_matrices():

            tt_2016 = np.array(f1[name])[:md.max_zone,:md.max_zone]
            tt_future = np.array(f2[name])[:md.max_zone,:md.max_zone]
                
            # only apply to home-based productions
            if (name[:3]!='NHB'): 
                diff = np.maximum(tt_future - tt_2016,0)
                adj_diff = np.multiply(diff.T, (np.array(taz_factors['POP_FACTOR']) - 1)).T
                tt_newfuture = tt_future + adj_diff
            else:
                tt_newfuture = tt_future
            
# =DEBUG============================================================================
#                 margs_2016[name] = tt_2016.sum(axis = 1)
#                 margs_2040_base[name] = tt_future.sum(axis = 1)
#                 margs_2040_new[name] = tt_newfuture.sum(axis = 1)                
# =============================================================================
            fout[name] = tt_newfuture
            
    mc_obj.pre_MC_trip_table = mtx.store_omx_as_dict(modified_trips)
# =DEBUG============================================================================
        #pd.DataFrame(margs_2016).to_csv(mc_obj.config.scen_path + r"base.csv")
        #pd.DataFrame(margs_2040_new).to_csv(mc_obj.config.scen_path + r"newfuture.csv")
        #pd.DataFrame(margs_2040_base).to_csv(mc_obj.config.scen_path + r"origfuture.csv")
# =============================================================================
        
def transit_ivt_modify_skim(mc_obj, transit_ivt_factor):
    ''' apply transit travel time factor to skims
    
    Factor transit invehicle time across all modes and time periods
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param transit_ivt_factor: factor to be applied to transit ivt 
    '''    
    mc_obj.DAT_B_skim_PK['Total_IVTT'] = mc_obj.DAT_B_skim_PK['Total_IVTT'] * transit_ivt_factor
    mc_obj.DAT_B_skim_OP['Total_IVTT'] = mc_obj.DAT_B_skim_OP['Total_IVTT'] * transit_ivt_factor
    mc_obj.DAT_CR_skim_PK['Total_IVTT'] = mc_obj.DAT_CR_skim_PK['Total_IVTT'] * transit_ivt_factor
    mc_obj.DAT_CR_skim_OP['Total_IVTT'] = mc_obj.DAT_CR_skim_OP['Total_IVTT'] * transit_ivt_factor
    mc_obj.DAT_RT_skim_PK['Total_IVTT'] = mc_obj.DAT_RT_skim_PK['Total_IVTT'] * transit_ivt_factor
    mc_obj.DAT_RT_skim_OP['Total_IVTT'] = mc_obj.DAT_RT_skim_OP['Total_IVTT'] * transit_ivt_factor
    mc_obj.DAT_LB_skim_PK['Total_IVTT'] = mc_obj.DAT_LB_skim_PK['Total_IVTT'] * transit_ivt_factor
    mc_obj.DAT_LB_skim_OP['Total_IVTT'] = mc_obj.DAT_LB_skim_OP['Total_IVTT'] * transit_ivt_factor
    mc_obj.WAT_skim_PK['Total_IVTT'] = mc_obj.WAT_skim_PK['Total_IVTT'] * transit_ivt_factor
    mc_obj.WAT_skim_OP['Total_IVTT'] = mc_obj.WAT_skim_OP['Total_IVTT'] * transit_ivt_factor
    
def __transit_time_reduction(skim, idx_list, time_saving_list, factor):
    # apply benefit of new transit projects - factor to account for aggregate zone effect
    
    for i in range(len(idx_list)):
        skim[tuple(idx_list[i])] -= min(time_saving_list[i],skim[tuple(idx_list[i])] * factor)
    return skim
    
def transit_improvement_projects(mc_obj, project_impact_file, transit_project_factor):
    ''' reduce transit OVTT and IVTT according to transit project impacts
    
    Adjust transit times based on transit projects
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param project_impact_file: file with transit projects
    :param transit_project_factor: factor to apply to zones with transit projects
    '''       
    factor = transit_project_factor
    TAZ_savings = pd.read_csv(mc_obj.config.param_path + project_impact_file)
    ivtt_idx_list = ( TAZ_savings[TAZ_savings['IVTT difference']!=0][['TAZ_0_skim','TAZ_1_skim']].values.tolist()
                    +  TAZ_savings[TAZ_savings['IVTT difference']!=0][['TAZ_1_skim','TAZ_0_skim']].values.tolist())

    ivtt_list = TAZ_savings[TAZ_savings['IVTT difference']!=0]['IVTT difference'].values.tolist() * 2

    ovtt_idx_list = ( TAZ_savings[TAZ_savings['OVTT difference']!=0][['TAZ_0_skim','TAZ_1_skim']].values.tolist()
                    +  TAZ_savings[TAZ_savings['OVTT difference']!=0][['TAZ_1_skim','TAZ_0_skim']].values.tolist())

    ovtt_list = TAZ_savings[TAZ_savings['OVTT difference']!=0]['OVTT difference'].values.tolist() * 2
    
    mc_obj.DAT_B_skim_PK['Total_IVTT'] = __transit_time_reduction(mc_obj.DAT_B_skim_PK['Total_IVTT'], ivtt_idx_list, ivtt_list,factor)
    mc_obj.DAT_B_skim_OP['Total_IVTT'] = __transit_time_reduction(mc_obj.DAT_B_skim_OP['Total_IVTT'], ivtt_idx_list, ivtt_list,factor)
    mc_obj.DAT_CR_skim_PK['Total_IVTT'] = __transit_time_reduction(mc_obj.DAT_CR_skim_PK['Total_IVTT'], ivtt_idx_list, ivtt_list,factor) 
    mc_obj.DAT_CR_skim_OP['Total_IVTT'] = __transit_time_reduction(mc_obj.DAT_CR_skim_OP['Total_IVTT'], ivtt_idx_list, ivtt_list,factor)
    mc_obj.DAT_RT_skim_PK['Total_IVTT'] = __transit_time_reduction(mc_obj.DAT_RT_skim_PK['Total_IVTT'], ivtt_idx_list, ivtt_list,factor)
    mc_obj.DAT_RT_skim_OP['Total_IVTT'] = __transit_time_reduction(mc_obj.DAT_RT_skim_OP['Total_IVTT'], ivtt_idx_list, ivtt_list,factor)
    mc_obj.DAT_LB_skim_PK['Total_IVTT'] = __transit_time_reduction(mc_obj.DAT_LB_skim_PK['Total_IVTT'], ivtt_idx_list, ivtt_list,factor)
    mc_obj.DAT_LB_skim_OP['Total_IVTT'] = __transit_time_reduction(mc_obj.DAT_LB_skim_OP['Total_IVTT'], ivtt_idx_list, ivtt_list,factor)
    mc_obj.WAT_skim_PK['Total_IVTT'] = __transit_time_reduction(mc_obj.WAT_skim_PK['Total_IVTT'], ivtt_idx_list, ivtt_list,factor)
    mc_obj.WAT_skim_OP['Total_IVTT'] = __transit_time_reduction(mc_obj.WAT_skim_PK['Total_IVTT'], ivtt_idx_list, ivtt_list,factor)
    
    mc_obj.DAT_B_skim_PK['Total_OVTT'] = __transit_time_reduction(mc_obj.DAT_B_skim_PK['Total_OVTT'], ovtt_idx_list, ovtt_list,factor)
    mc_obj.DAT_B_skim_OP['Total_OVTT'] = __transit_time_reduction(mc_obj.DAT_B_skim_OP['Total_OVTT'], ovtt_idx_list, ovtt_list,factor)
    mc_obj.DAT_CR_skim_PK['Total_OVTT'] = __transit_time_reduction(mc_obj.DAT_CR_skim_PK['Total_OVTT'], ovtt_idx_list, ovtt_list,factor) 
    mc_obj.DAT_CR_skim_OP['Total_OVTT'] = __transit_time_reduction(mc_obj.DAT_CR_skim_OP['Total_OVTT'], ovtt_idx_list, ovtt_list,factor)
    mc_obj.DAT_RT_skim_PK['Total_OVTT'] = __transit_time_reduction(mc_obj.DAT_RT_skim_PK['Total_OVTT'], ovtt_idx_list, ovtt_list,factor)
    mc_obj.DAT_RT_skim_OP['Total_OVTT'] = __transit_time_reduction(mc_obj.DAT_RT_skim_OP['Total_OVTT'], ovtt_idx_list, ovtt_list,factor)
    mc_obj.DAT_LB_skim_PK['Total_OVTT'] = __transit_time_reduction(mc_obj.DAT_LB_skim_PK['Total_OVTT'], ovtt_idx_list, ovtt_list,factor)
    mc_obj.DAT_LB_skim_OP['Total_OVTT'] = __transit_time_reduction(mc_obj.DAT_LB_skim_OP['Total_OVTT'], ovtt_idx_list, ovtt_list,factor)
    mc_obj.WAT_skim_PK['Total_OVTT'] = __transit_time_reduction(mc_obj.WAT_skim_PK['Total_OVTT'], ovtt_idx_list, ovtt_list,factor)
    mc_obj.WAT_skim_OP['Total_OVTT'] = __transit_time_reduction(mc_obj.WAT_skim_PK['Total_OVTT'], ovtt_idx_list, ovtt_list,factor)

def __bike_time_distance_reduction(time_skim, dist_skim, idx_list, factor_list):
    # change bike time and distance skims by factor
    for i in range(len(idx_list)):
        time_skim[tuple(idx_list[i])] -= time_skim[tuple(idx_list[i])]*factor_list[i]
        dist_skim[tuple(idx_list[i])] -= dist_skim[tuple(idx_list[i])]*factor_list[i]
    return time_skim, dist_skim
    
def bike_advantage_modify_skim(mc_obj, bike_skim_factor):
    ''' cross the board factoring of bike time and distance
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param bike_skim_factor: factor to apply to bike time and distance
    '''          
    mc_obj.bike_skim['BikeTime'] = mc_obj.bike_skim['BikeTime'] * bike_skim_factor
    mc_obj.bike_skim['Length (Skim)'] =  mc_obj.bike_skim['Length (Skim)'] * bike_skim_factor

def active_transportation_modify_skim(mc_obj,bike_project_file):
    ''' improve bike and walk skims according to new projects
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param bike_project_file: file with zones and factors to adjust bike time and distance
    '''  
    TAZ_pair_df = pd.read_csv(mc_obj.config.param_path + bike_project_file)
    idx_list = TAZ_pair_df[['TAZ_0_skim','TAZ_1_skim']].values.tolist()
    factor_list = TAZ_pair_df['factor_avg'].values.tolist()

    mc_obj.bike_skim['BikeTime'], mc_obj.bike_skim['Length (Skim)'] = (
            __bike_time_distance_reduction(mc_obj.bike_skim['BikeTime'], 
                                           mc_obj.bike_skim['Length (Skim)'],
                                           idx_list, 
                                           factor_list))
    
    mc_obj.bike_skim['OneMileorLess'] = 1*(mc_obj.bike_skim['Length (Skim)']<=1)
    
    
def boston_pev(mc_obj, pev_factor):
    ''' reduce PEV variable by factor for zones within Boston
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param pev_factor: adjustments to PEV for all Boston zones
    '''  
    mc_obj.AccPEV[0:447,0:447] *= pev_factor
    mc_obj.EgrPEV[0:447,0:447] *= pev_factor

def parking_cost_change(mc_obj, parking_charge):
    ''' increase parking costs for trips ending in Boston
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param parking_charge: value to add to parking charge for all zones in Boston
    '''  
    mc_obj.parking[0:md.max_zone,0:447] += parking_charge

def vmt_fee(mc_obj, per_mile_fee):
    ''' adjust vehicle cost per mile to represent VMT fee
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param per_mile_fee: value to add to vehicle operating cost
    '''      
    mc_obj.cost_per_mile = mc_obj.cost_per_mile + per_mile_fee

def congestion_charge(mc_obj, cordon_area, charge):
    ''' apply a congestion charge for all trips to the cordon area
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param cordon_area: cordon area neighborhoods
    :param charge: charge to be applied for trips to the cordon area
    '''         
    cong_zones = mc_obj.taz_lu[mc_obj.taz_lu['BOSTON_NB'].isin(cordon_area)]['ID'].values
    
    cong_charge_table = np.zeros((md.max_zone,md.max_zone))
    cong_charge_table[np.ix_(np.where(np.logical_not(mc_obj.taz_lu['ID'].iloc[:md.max_zone].isin(cong_zones).values))[0],
      np.where(mc_obj.taz_lu['ID'].iloc[:md.max_zone].isin(cong_zones).values)[0])] = charge
    
    mc_obj.drive_skim_PK['Auto_Toll (Skim)'] += cong_charge_table
    mc_obj.drive_skim_OP['Auto_Toll (Skim)'] += cong_charge_table

def transit_mode_fare_factor(mc_obj, lb_fact, rt_fact, cr_fact, boat_fact, walk_fact):
    ''' adjust transit fares by sub-mode
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param lb_fact: drive to local bus fare factor
    :param rt_fact: drive to rapid transit fare factor
    :param cr_fact: drive to commuter rail fare factor
    :param boat_fact: drive to ferry fare factor
    :param walk_fact: walk to any transit mode fare factor
    '''      
    mc_obj.DAT_B_skim_PK['Total_Cost'] *= boat_fact
    mc_obj.DAT_CR_skim_PK['Total_Cost'] *= cr_fact
    mc_obj.DAT_RT_skim_PK['Total_Cost'] *= rt_fact
    mc_obj.DAT_LB_skim_PK['Total_Cost'] *= lb_fact
    mc_obj.WAT_skim_PK['Total_Cost'] *= walk_fact
    
    mc_obj.DAT_B_skim_OP['Total_Cost'] *= boat_fact
    mc_obj.DAT_CR_skim_OP['Total_Cost'] *= cr_fact
    mc_obj.DAT_RT_skim_OP['Total_Cost'] *= rt_fact
    mc_obj.DAT_LB_skim_OP['Total_Cost'] *= lb_fact
    mc_obj.WAT_skim_OP['Total_Cost'] *= walk_fact

def reduce_hbw_peak_trips(mc_obj, tdm_rate):
    ''' reduce HBW trips
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param tdm_rate: adjustment to hbw peak trips
    '''      
    mc_obj.pre_MC_trip_table['HBW_PK_0Auto'] *= 1-tdm_rate
    mc_obj.pre_MC_trip_table['HBW_PK_wAuto'] *= 1-tdm_rate   
    
    
def reduce_boston_veh_ownership(mc_obj, boston_veh_decrease):
    ''' shift HH from 1+ to zero vehicles for Boston only
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param boston_veh_decrease: factor to shift boston trips from with/vehicle
        to zero vehicle
    '''      
    veh_segments = list(filter(re.compile('.*_0Auto').match, list(mc_obj.pre_MC_trip_table.keys())))
    for segment in veh_segments:
        mc_obj.pre_MC_trip_table[segment][0:447,0:md.max_zone] += (
                   mc_obj.pre_MC_trip_table[re.sub('0Auto','wAuto',segment)][0:447,0:md.max_zone] 
                   * boston_veh_decrease)
        mc_obj.pre_MC_trip_table[re.sub('0Auto','wAuto',segment)][0:447,0:md.max_zone]  *= (1 - boston_veh_decrease) 

def reduce_outside_boston_veh_ownership(mc_obj, veh_decrease):
    ''' shift HH from 1+ to zero vehicles for areas outside Boston
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param boston_veh_decrease: factor to shift trips from with/vehicle
        to zero vehicle
    '''      
    veh_segments = list(filter(re.compile('.*_0Auto').match, list(mc_obj.pre_MC_trip_table.keys())))
    for segment in veh_segments:
        mc_obj.pre_MC_trip_table[segment][448:md.max_zone,0:md.max_zone] += (
                   mc_obj.pre_MC_trip_table[re.sub('0Auto','wAuto',segment)][448:md.max_zone,0:md.max_zone] * veh_decrease)
        mc_obj.pre_MC_trip_table[re.sub('0Auto','wAuto',segment)][448:md.max_zone,0:md.max_zone] *= (1 - veh_decrease) 
 
def shared_mobility(mc_obj, param_file, coeffs):
    ''' setup shared mobility scenarios
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param param_file: parameter file with shared mobility alternatives
    :param coeffs: shared mobility fare, waiting time, and subsidy terms
    '''        
    mc_obj.sm = mode_choice.Shared_Mobility(coeffs)
    mc_obj.param_file = mc_obj.config.param_path + param_file
    
def trip_pricing(mc_obj, trip_price): 
    ''' set per-trip pricing
    
    create a new parameter file with the modified constant values 
    to reflect additional trip pricing for auto modes
    
    :param mc_obj: the mode choice object containing parameters and inputs
    :param trip_price: trip price value
    '''     
    new_param_file = mc_obj.config.scen_path + r"param_with_pricing.xlsx"
    writer1 = pd.ExcelWriter(new_param_file,engine = 'openpyxl')

    for purpose in md.purposes:
        param = pd.read_excel(mc_obj.param_file, sheet_name = purpose,index_col = 0)
        for mode in (md.drive_modes + md.smart_mobility_modes):
            if mode in param.index:
                for asc in ['ASC_0_PK','ASC_1_PK','ASC_0_OP','ASC_1_OP']:
                    cost_coeff = param.loc[mode, 'Cost']
                    param.loc[mode,asc] += (trip_price / mc_obj.config.AO_dict[purpose][mode]) * cost_coeff
        param.to_excel(writer1, sheet_name = purpose)
    writer1.save()
    mc_obj.param_file = new_param_file
   
    
# ====CAV Functionality - needs to be restructured=================================================
#     
#     param_out, trip_table_conventional, trip_table_CAV = __CAV_input_generator(mc_obj, switches)
#     mc2 = mode_choice.Mode_Choice(config,run_now = False)
#     mc2.load_input()
#     
#     mc_obj.pre_MC_trip_table = copy.deepcopy(trip_table_conventional)
#     mc2.pre_MC_trip_table = copy.deepcopy(trip_table_CAV)
#     
#     if (switches.get('CAV_management_policy',False) == False):
#         mc2.param_file = mc_obj.config.param_file_av
#         mc2.cost_per_mile -= 0.05 # should only be applied to CAVs
#     
#     print('Running CAV scenario for families with no vehicle or no access to CAV...')
#     mc_obj.run_model()
#     print('Running CAV scenario for families with access to CAV...')
#     mc2.run_model()
#     
#     # combine post mode choice trip tables
#     for purpose in ['HBW','HBO','NHB', 'HBSc1','HBSc2','HBSc3']:
#         for peak in ['PK','OP']:
#             for veh_own in ['0','1']:
#                 for mode in mc_obj.table_container.get_table(purpose)[f'{veh_own}_{peak}']:
#                     mc_obj.table_container.get_table(purpose)[f'{veh_own}_{peak}'][mode] += mc2.table_container.get_table(purpose)[f'{veh_own}_{peak}'][mode]
#     
# def __CAV_input_generator(mc_obj, switches):
#     # point to AV modified parameter file, split by adoption rate
#     AV_adoption = mc_obj.config.AV_adoption
#     
#     # set param for CAV households, alternative baseline and mangement policies
#     if switches.get('smart_mobility',False) == True:
#         if switches.get('smart_mobility_management_policy',False):
#             param_file = mc_obj.config.SM_calib_param_file
#         else:
#             param_file = mc_obj.config.SM_calib_param_mngpol_file
#     else:
#         param_file = mc_obj.config.param_file
# 
#     # create two sets of trip tables: one with all 0-veh HHs and 1-x% of the 1+ veh HHs, the other with x% of the 1+ veh HHs
#     trip_table_conventional = copy.deepcopy(mc_obj.pre_MC_trip_table)
#     trip_table_CAV = copy.deepcopy(mc_obj.pre_MC_trip_table)
#     
#     hh_0_veh = list(filter(re.compile('.*_0Auto').match, list(trip_table_conventional.keys())))
#     hh_1_veh = list(filter(re.compile('.*_wAuto').match, list(trip_table_conventional.keys())))
#     for segment in hh_1_veh:
#         trip_table_conventional[segment] *= (1-AV_adoption)
#         trip_table_CAV[segment] *= AV_adoption
#     
#     for segment in hh_0_veh:
#         trip_table_CAV[segment] *= 0
# 
#     return param_file, trip_table_conventional, trip_table_CAV
#     
# =============================================================================
