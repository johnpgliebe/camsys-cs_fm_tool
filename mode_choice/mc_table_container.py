# CS FutureMobility Tool
# See full license in LICENSE.txt.

import numpy as np
import pandas as pd
import mode_choice.model_defs as md

class table_container(object):
    '''
    Defines an object that contains post-mode choice trip tables.
    '''
    def __init__(self, mc_obj):
        self.model = mc_obj
        self.container = dict.fromkeys(md.purposes)
        for purpose in self.container:
            self.container[purpose] = {'0_PK':{},'1_PK':{},'0_OP':{},'1_OP':{}}
        
    def store_table(self,purpose):
        self.container[purpose] = self.model.trips_by_mode
    def get_table(self,purpose):
        if purpose in self.container.keys():
            return self.container[purpose]
        else:
            return None
	
	def aggregate_by_mode_segment(self,mode, pv):
		trip_sum = np.zeros((2730,2730))
		for purpose in ['HBW', 'HBO', 'NHB', 'HBSc1', 'HBSc2', 'HBSc3']:
			try: trip_sum += self.container[purpose][pv][mode]
			except: pass
		return trip_sum