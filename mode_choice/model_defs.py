#model_defs.py
# CS FutureMobility Tool
# See full license in LICENSE.txt.

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


purposes = ['HBW','HBO','NHB', 'HBSc1','HBSc2','HBSc3']

max_zone = 2730

# used for VMT summaries
AO_dict = {'DA':1,'SR2':2,'SR2+':2,'SR3+':3.5,'SM_RA':1, 'SM_SH':2}