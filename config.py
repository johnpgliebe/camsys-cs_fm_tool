# CS FutureMobility Tool
# See full license in LICENSE.txt.

#
# File needs to be updated for each installation with paths 
# to data, parameters, working folder, and archive
#

import numpy as np
import os

param_path = os.path.dirname(os.path.realpath(__file__)) + "\\param\\"

# scenario path is for outputs
scen_path =  os.path.dirname(os.path.realpath(__file__)) + "\\..\\output\\"
archive_path = os.path.dirname(os.path.realpath(__file__)) + "\\..\\scenarios\\"

# skims
#todo: move the datapath to the yaml scenario file
data_path = r"C:\Projects\180021-CFB\CS_FM_Tool\data\2050\\"
drive_skim_PK_file = data_path + 'skims\SOV_skim_AM.omx'
drive_skim_OP_file = data_path + 'skims\SOV_skim_MD.omx'
DAT_B_skim_PK_file = data_path + 'skims\A_DAT_for_Boat_tr_skim_AM.omx'
DAT_B_skim_OP_file = data_path + 'skims\A_DAT_for_Boat_tr_skim_MD.omx'
DAT_CR_skim_PK_file = data_path + 'skims\A_DAT_for_CommRail_tr_skim_AM.omx'
DAT_CR_skim_OP_file = data_path + 'skims\A_DAT_for_CommRail_tr_skim_MD.omx'
DAT_RT_skim_PK_file = data_path + 'skims\A_DAT_for_Rapid_Transit_tr_skim_AM.omx'
DAT_RT_skim_OP_file = data_path + 'skims\A_DAT_for_Rapid_Transit_tr_skim_MD.omx'
DAT_LB_skim_PK_file = data_path + 'skims\A_DAT_for_LocalBus_tr_skim_AM.omx'
DAT_LB_skim_OP_file = data_path + 'skims\A_DAT_for_LocalBus_tr_skim_MD.omx'
WAT_skim_PK_file = data_path + 'skims\WAT_for_All_tr_skim_AM.omx'
WAT_skim_OP_file = data_path + 'skims\WAT_for_All_tr_skim_MD.omx'
bike_skim_file = data_path + r"skims\2040_Bike_Skim.omx"
walk_skim_file = data_path + r"skims\2040_Walk_Skim.omx"

skim_list = ['drive_skim_PK',
'drive_skim_OP',
'DAT_B_skim_PK',
'DAT_B_skim_OP',
'DAT_CR_skim_PK',
'DAT_CR_skim_OP',
'DAT_RT_skim_PK',
'DAT_RT_skim_OP',
'DAT_LB_skim_PK',
'DAT_LB_skim_OP',
'WAT_skim_PK',
'WAT_skim_OP',
'bike_skim',
'walk_skim']

# pre-MC trip table
pre_MC_trip_file = data_path + "pre_MC_trip_6_purposes.omx"
truck_trip_table = data_path + "truck_trips.omx"

# land use
taz_file = data_path + "SW_TAZ_2010.csv"
land_use_file = data_path + "Land_Use_2040.csv"
taz_parking_file = data_path + "Land_Use_Parking_Costs.csv"
taz_zonal_file = data_path + "TAZ_zonal_2040.csv"

# model purpose
purpose = 'HBSc1'

# model parameter
param_file = param_path + 'param_calib_0716.xlsx'

# drive mode average occupancy
# TODO: move to model defs
AO_dict = {'HBW':{'DA':1,'SR2':2,'SR3+':3.5,'SM_RA':1,'SM_SH':2},
	'HBO':{'DA':1,'SR2':2,'SM_RA':1,'SM_SH':2},
	'NHB':{'DA':1,'SR2':2,'SM_RA':1,'SM_SH':2},
	'HBSc1':{'DA':1,'SR2':2,'SM_RA':1,'SM_SH':2},
	'HBSc2':{'DA':1,'SR2':2,'SM_RA':1,'SM_SH':2},
	'HBSc3':{'DA':1,'SR2':2,'SM_RA':1,'SM_SH':2}
	}

# cost per mile
cost_per_mile = 0.184

# output path
out_path = scen_path



