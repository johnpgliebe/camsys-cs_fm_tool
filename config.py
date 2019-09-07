# CS FutureMobility Tool
# See full license in LICENSE.txt.

#
# File needs to be updated for each installation with paths 
# to data, parameters, working folder, and archive
#

import numpy as np
import os

# input path
data_path = 'C:/Egnyte/Shared/Projects/190077/1 - Existing Conditions/4 - CTPS/model_data/Seaport_data/data/2018/' # will be removed. not used in baseline model run.
param_path = 'C:/Egnyte/Shared/Projects/190077/1 - Existing Conditions/4 - CTPS/model_data/Seaport_data/param/' # will be removed. not used in baseline model run.

# scenario path is for outputs
scen_path =  os.path.dirname(os.path.realpath(__file__)) + "\\..\\output\\"
archive_path = os.path.dirname(os.path.realpath(__file__)) + "\\..\\scenarios\\"


# output path
out_path = scen_path



