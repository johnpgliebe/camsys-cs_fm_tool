#model_defs.py
# CS FutureMobility Tool
# See full license in LICENSE.txt.

import numpy as np
import pandas as pd
import config

peak_veh = ['0_PK','1_PK','0_OP','1_OP'] # vehicle ownership + peak: market segments used in trip tables
drive_modes = ['DA','SR2','SR3+','SR2+']
da_mode = ['DA']
sr_mode = ['SR2','SR3+','SR2+']
DAT_modes = ['DAT_CR','DAT_RT','DAT_LB','DAT_B']
WAT_modes = ['WAT']
transit_modes = WAT_modes + DAT_modes
active_modes = ['Walk','Bike']
smart_mobility_modes = ['SM_RA','SM_SH']
auto_modes = drive_modes + smart_mobility_modes
sm_ride_alone = ['SM_RA']
sm_shared_ride = ['SM_SH']
modes = drive_modes + active_modes + transit_modes + smart_mobility_modes
mode_categories = {'DA':'drive','SR2':'drive','SR3+':'drive','Bike':'non-motorized','Walk':'non-motorized','WAT':'transit','DAT_CR':'transit','DAT_B':'transit','DAT_LB':'transit','DAT_RT':'transit','SM_RA':'smart mobility','SM_SH':'smart mobility'}
truck_categories = ['HeavyTruck','MediumTruck','LightTruck']
seaport = ['Seaport Blvd', 'Design Center',
       'Southeast Seaport', 'BCEC', 'Fort Point', 'Broadway']

purposes = ['HBW','HBO','NHB', 'HBSc1','HBSc2','HBSc3']

max_zone = 1403

# used for VMT summaries
AO_dict = {'DA':1,'SR2':2,'SR2+':2,'SR3+':3.5,'SM_RA':1, 'SM_SH':2}

# cost per mile
cost_per_mile = 0.184

# study area definitions
def _taz(data_paths):
    taz = pd.read_csv(data_paths['data_path']+ data_paths['taz_interstate_file']).sort_values(['SPRT_ID']).reset_index(drop = True)[0:max_zone]
    
    taz = taz.merge(pd.read_csv(data_paths['data_path'] + data_paths['taz_file']).sort_values(['SPRT_ID'])[0:max_zone][['SPRT_ID','BOSTON_NB','TOWN']], how = 'left') 
    taz['BOS_AND_NEI'] = taz['TOWN'].isin([n+',MA' for n in ['WINTHROP','CHELSEA','REVERE','SOMERVILLE','CAMBRIDGE','WATERTOWN','NEWTON',
          'BROOKLINE','NEEDHAM','DEDHAM','MILTON','QUINCY','BOSTON']])
    taz['BOSTON'] = taz['TOWN'].str.contains('BOSTON')
    
    taz_parking = pd.read_csv(data_paths['data_path'] + data_paths['taz_parking_file']).fillna(0)
    taz_zonal = pd.read_csv(data_paths['data_path'] + data_paths['taz_zonal_file']).sort_values('SPRT_ID')
    
    taz = taz.merge(taz_parking, on = 'SPRT_ID', how = 'left').merge(taz_zonal, on = 'SPRT_ID', how = 'left')
    
    return taz

taz_ID_field = 'SPRT_ID'

def _study_area(taz):
    
    return taz['REPORT_AREA'].isin(seaport).values