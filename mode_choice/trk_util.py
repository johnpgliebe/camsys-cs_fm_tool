# coding: utf-8
# CS FutureMobility Tool
# See full license in LICENSE.txt.

import numpy as np
import pandas as pd
import openmatrix as omx
import mode_choice.model_defs as md

def __mt_prod_attr_nhood(mc_obj, trip_table, skim): # miles traveled. For VMT and PMT, by neighborhood
    # sum prodct of trip_table - skims
    mt_total = trip_table * skim['Length (Skim)'] 
    
    # calculate marginals
    prod = pd.DataFrame(np.sum(mt_total,axis = 1)/2, columns = ['Production'])
    attr = pd.DataFrame(np.sum(mt_total,axis = 0)/2, columns = ['Attraction'])
    
    towns = mc_obj.taz_lu.sort_values('TAZ_ID').iloc[0:md.max_zone]
    mt_taz = pd.concat([towns[['TAZ_ID','BOSTON_NB']],prod,attr],axis = 1,join = 'inner')
    mt_taz.index.names=['Boston Neighborhood']
    return mt_taz.groupby(['BOSTON_NB']).sum()[['Production','Attraction']].reset_index()
    
def __trip_prod_attr_nhood(mc_obj, trip_table): 
    mt_total = trip_table
    
    # calculate marginals
    prod = pd.DataFrame(np.sum(mt_total,axis = 1), columns = ['Production'])
    attr = pd.DataFrame(np.sum(mt_total,axis = 0), columns = ['Attraction'])
    
    towns = mc_obj.taz_lu.sort_values('TAZ_ID').iloc[0:md.max_zone]
    mt_taz = pd.concat([towns[['TAZ_ID','BOSTON_NB']],prod,attr],axis = 1,join = 'inner')
    mt_taz.index.names=['Boston Neighborhood']
    return mt_taz.groupby(['BOSTON_NB']).sum()[['Production','Attraction']].reset_index()
    
def trip_by_neighborhood(mc_obj, out_fn = None):
    '''
    Summarizes Truck trips production and attraction by the 26 Boston neighborhoods.
    :param mc_obj: mode choice module object as defined in the IPython notebook
    :param out_fn: output csv filename; if None specified, in the output path defined in config.py  
    :param by: grouping used for the summary; if None specified, only aggregate production and attraction will be provided.
    '''
    trk_trip = omx.open_file(mc_obj.config.data_path + mc_obj.data_paths['truck_trip_table'],'r')
    
    if out_fn is None:
        out_fn = mc_obj.config.out_path + f'trk_trip_by_neighborhood.csv'

    master_table = pd.DataFrame(columns = ['Production','Attraction','truck'])
    for truck in md.truck_categories:
        if trk_trip[truck]:
            trk_trip_table = np.array(trk_trip[truck])[0:md.max_zone,0:md.max_zone]
            trip_table = __trip_prod_attr_nhood(mc_obj,trk_trip_table)
            trip_table['truck'] = truck
            master_table = master_table.append(trip_table, sort = True)
    trip_summary = pd.concat([
            master_table.groupby(['truck','BOSTON_NB']).sum().loc[truck] 
            for truck in md.truck_categories], axis = 1, keys = md.truck_categories)
    trip_summary.to_csv(out_fn)
    trk_trip.close()

def vmt_by_neighborhood(mc_obj, out_fn = None):
    '''
    Summarizes Truck VMT production and attraction by the 26 Boston neighborhoods.
    :param mc_obj: mode choice module object as defined in the IPython notebook
    :param out_fn: output csv filename; if None specified, in the output path defined in config.py  
    :param by: grouping used for the summary; if None specified, only aggregate production and attraction will be provided.
    '''
    trk_trip = omx.open_file(mc_obj.config.data_path + mc_obj.data_paths['truck_trip_table'],'r')
    
    if out_fn is None:
        out_fn = mc_obj.config.out_path + f'trk_vmt_by_neighborhood.csv'

    vmt_master_table = pd.DataFrame(columns = ['Production','Attraction','truck'])
    for truck in md.truck_categories:
        if trk_trip[truck]:
            trk_trip_table = np.array(trk_trip[truck])[0:md.max_zone,0:md.max_zone]
            vmt_table = __mt_prod_attr_nhood(mc_obj,trk_trip_table,mc_obj.drive_skim_PK)
            vmt_table['truck'] = truck
            vmt_master_table = vmt_master_table.append(vmt_table, sort = True)
    vmt_summary = pd.concat([
            vmt_master_table.groupby(['truck','BOSTON_NB']).sum().loc[truck] 
            for truck in md.truck_categories], axis = 1, keys = md.truck_categories)
    vmt_summary.to_csv(out_fn)
    trk_trip.close()
    
def compute_summary_by_subregion(mc_obj,metric = 'VMT',subregion = 'neighboring'):
    ''' Computing function used by write_summary_by_subregion(), does not produce outputs'''
    trk_trip = omx.open_file(mc_obj.config.data_path + mc_obj.data_paths['truck_trip_table'],'r')
    taz_fn = mc_obj.config.data_path + r"..\TAZ_by_interstate.csv"
    if metric.lower() not in ('vmt','trip'):
        print('Only supports trip, and VMT calculations.')
        return
    if subregion.lower() not in ('boston','neighboring','i93','i495','region'):
        print('Only supports within boston, "neighboring" for towns neighboring Boston, I93, I495 or Region.')
        return
    
    taz = pd.read_csv(taz_fn).sort_values(['ID_FOR_CS']).reset_index(drop = True)[0:md.max_zone][['TOWN','in_i95i93','in_i495']]
    taz['BOS_AND_NEI'] = taz['TOWN'].isin([n+',MA' for n in ['WINTHROP','CHELSEA','REVERE','SOMERVILLE','CAMBRIDGE','WATERTOWN','NEWTON',
              'BROOKLINE','NEEDHAM','DEDHAM','MILTON','QUINCY','BOSTON']])
    taz['BOSTON'] = taz['TOWN'].str.contains('BOSTON')
    subregion_dict = {'boston':'BOSTON','neighboring':'BOS_AND_NEI','i93':'in_i95i93','i495':'in_i495'}
    
    type_table = dict(zip(md.truck_categories,[0,0,0,0]))
            
    if metric.lower() == 'vmt':
        if subregion.lower() in subregion_dict:
            field = subregion_dict[subregion.lower()]
            for truck in md.truck_categories:
                if trk_trip[truck]:
                    trk_trip_table = np.array(trk_trip[truck])[0:md.max_zone,0:md.max_zone]
                    trip_table = trk_trip_table * mc_obj.drive_skim_PK['Length (Skim)']
                    trips = trip_table[taz['TOWN']=='BOSTON,MA',:][:, taz[field]== True].sum() + trip_table[taz[field]== True,:][:,taz['TOWN']=='BOSTON,MA'].sum()
                    type_table[truck] = trips/2
        elif subregion.lower() == 'region':
            for truck in md.truck_categories:
                if trk_trip[truck]:
                    trk_trip_table = np.array(trk_trip[truck])[0:md.max_zone,0:md.max_zone]
                    trip_table = trk_trip_table * mc_obj.drive_skim_PK['Length (Skim)'] 
                    boston_ii_trips = trip_table[taz['TOWN']=='BOSTON,MA',:][:,taz['TOWN']=='BOSTON,MA'].sum()
                    trips = trip_table[taz['TOWN']=='BOSTON,MA',:][:].sum() + trip_table[:][:,taz['TOWN']=='BOSTON,MA'].sum()
                    type_table[truck] = trips/2
    elif metric.lower() == 'trip':
        if subregion.lower() in subregion_dict:
            field = subregion_dict[subregion.lower()]
            for truck in md.truck_categories:
                if trk_trip[truck]:
                    trk_trip_table = np.array(trk_trip[truck])[0:md.max_zone,0:md.max_zone]
                    trip_table = trk_trip_table
                    boston_ii_trips = trip_table[taz['TOWN']=='BOSTON,MA',:][:,taz['TOWN']=='BOSTON,MA'].sum()
                    trips = trip_table[taz['TOWN']=='BOSTON,MA',:][:, taz[field]== True].sum() + trip_table[taz[field]== True,:][:,taz['TOWN']=='BOSTON,MA'].sum() - boston_ii_trips
                    type_table[truck] = trips
        elif subregion.lower() == 'region':
            for truck in md.truck_categories:
                if trk_trip[truck]:
                    trk_trip_table = np.array(trk_trip[truck])[0:md.max_zone,0:md.max_zone]
                    trip_table = trk_trip_table
                    boston_ii_trips = trip_table[taz['TOWN']=='BOSTON,MA',:][:,taz['TOWN']=='BOSTON,MA'].sum()
                    trips = trip_table[taz['TOWN']=='BOSTON,MA',:][:].sum() + trip_table[:][:,taz['TOWN']=='BOSTON,MA'].sum() - boston_ii_trips
                    type_table[truck] = trips
    
    return [type_table[truck].sum() for truck in  md.truck_categories]
        
        
def write_summary_by_subregion(mc_obj):

    '''
    Summarizes Truck VMT and trips by subregions of Massachusetts surrounding Boston (neighboring towns of Boston / within I-93/95 / within I-495).
    :param mc_obj: mode choice module object as defined in the IPython notebook
    :param taz_fn: TAZ file that contains subregion definition
    :param out_path: output path.
    '''
    subregion_dict = dict(zip(['boston','neighboring','i93','i495','region'],['Within Boston','Boston and Neighboring Towns', 'Within I-93/95', 'Within I-495', 'Entire Region']))
    vmt_summary_df = pd.DataFrame(index = subregion_dict.values(), columns = md.truck_categories)
    trip_summary_df = pd.DataFrame(index = subregion_dict.values(),columns = md.truck_categories)
    for subregion in subregion_dict:
        vmt_summary_df.loc[subregion_dict[subregion]] = compute_summary_by_subregion(mc_obj, metric = 'VMT',subregion = subregion)
        trip_summary_df.loc[subregion_dict[subregion]] = compute_summary_by_subregion(mc_obj, metric = 'trip',subregion = subregion)
    vmt_summary_df.to_csv(mc_obj.config.out_path + 'trk_vmt_summary_subregions.csv')
    trip_summary_df.to_csv(mc_obj.config.out_path + 'trk_trip_summary_subregions.csv')
        
