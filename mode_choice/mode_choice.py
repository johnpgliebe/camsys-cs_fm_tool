# coding: utf-8
# CS FutureMobility Tool
# See full license in LICENSE.txt.

import numpy as np
import pandas as pd
import openmatrix as omx
import warnings
import tables
import time
import yaml

import mode_choice.matrix_utils as mtx
import mode_choice.model_defs as md
from mode_choice.mc_table_container import table_container
warnings.simplefilter('ignore', tables.NaturalNameWarning)

class Shared_Mobility(object):
    ''' Shared Mobility Values '''
    
    def __init__(self, sm_params):
        for key in sm_params:
            setattr(self,key,sm_params[key])
            
        self.OVTT_table = self.wait_time * np.ones((md.max_zone,md.max_zone))

class Mode_Choice(object):
    '''Mode choice class that computes mode probabilities and calculated trips by mode.
    
    This object takes in the skims, parameters, SE data, and trip tables by purpose and time period
    and outputs the trip tables by mode
    
    :param config: the scenario object defined in the config.py
    
    Summaries of the modal trip tables are provided by the functions in the mc_util.py module
    
    .. warning:: hardcoded skim names and vehicle/tod segments must match the modes defined in model_defs.py
    .. todo:: set skim names and market segments dynamically based on model_defs.py
    
    '''
    def __init__(self,config, scenario_file):
        ''' Initialization requires a scenario configuration file'''
        self.config = config
        self.table_container = table_container(self)
        with open(scenario_file, 'r') as stream:
            scen= yaml.load(stream, Loader = yaml.FullLoader)
        self.data_paths = scen['data_paths']
        
        # these values may be updated by the scenario editor
        self.cost_per_mile = md.cost_per_mile
        self.param_file = self.config.param_path + self.data_paths['param_file']
        
        self.start_time = time.time()
        
        self.sm = None
        

    def __read_taz_data(self):
        # Reads the zonal data into memory for processing
        md.taz = md._taz(self.data_paths)
        md.study_area = md._study_area(md.taz)
        
        self.taz = md.taz
        # land_use = pd.read_csv(self.config.data_path + self.data_paths['land_use_file'])
        # self.taz_lu = taz.merge(land_use,on='ID')
       
        print(f'✓ TAZ / land use / parking / zonal variables read. Time elapsed: {time.time()-self.start_time:.2f} seconds')

    def __read_skims(self):
        # Reads the skims into memory for processing
        
        self.skim_list = []
        for skim_fn in self.data_paths['skim_list']:
            exec('self.' + skim_fn +
                 ' = mtx.store_omx_as_dict(self.config.data_path + self.data_paths["'
                 +skim_fn+ '_file"])')    
            self.skim_list.append(skim_fn)
        
        print(f'✓ skims read. Time elapsed: {time.time()-self.start_time:.2f} seconds')
        
        self.skim_PK_dict = {'drive':self.drive_skim_PK,'DAT_B':self.DAT_B_skim_PK,'DAT_CR':self.DAT_CR_skim_PK,'DAT_RT':self.DAT_RT_skim_PK,'DAT_LB':self.DAT_LB_skim_PK,'WAT':self.WAT_skim_PK,'Walk':self.walk_skim,'Bike':self.bike_skim,'SM_RA':self.drive_skim_PK,'SM_SH':self.drive_skim_PK}
        
        self.skim_OP_dict = {'drive':self.drive_skim_OP,'DAT_B':self.DAT_B_skim_OP,'DAT_CR':self.DAT_CR_skim_OP,'DAT_RT':self.DAT_RT_skim_OP,'DAT_LB':self.DAT_LB_skim_OP,'WAT':self.WAT_skim_OP,'Walk':self.walk_skim,'Bike':self.bike_skim,'SM_RA':self.drive_skim_OP,'SM_SH':self.drive_skim_OP}
        
    def __read_trip_table(self):
        # Reads the zonal data into memory for processing
        self.pre_MC_trip_table = mtx.store_omx_as_dict(self.config.data_path + self.data_paths['pre_MC_trip_file'])
        print(f'✓ trip table read. Time elapsed: {time.time()-self.start_time:.2f} seconds')
        
    def __generate_zonal_var(self):
        #generates parking, PEV, pop density, emp density, hh size, vpw, wacc, wegr tables.
        self.parking = mtx.expand_attr(self.taz['Daily Parking Cost'])/2
        self.AccPEV = mtx.expand_prod(self.taz['Acc_PEV'].fillna(0.001))
        self.EgrPEV = mtx.expand_attr(self.taz['Egr_PEV'].fillna(0.001))
        self.PopD = np.sqrt(mtx.expand_prod( self.taz['Tot_Pop']/self.taz['Area'] ) )
        self.EmpD = np.sqrt(mtx.expand_attr( self.taz['Tot_Emp']/self.taz['Area'] ) )
        self.HHSize = mtx.expand_prod((self.taz['HH_Pop']/self.taz['HH']).fillna(0))
        self.VPW = mtx.expand_prod( self.taz['VehiclesPerWorker'].fillna(
        self.taz['VehiclesPerWorker'].mean()))
        self.wacc_PK = mtx.expand_prod( self.taz['AM_wacc_fact'])
        self.wacc_OP = mtx.expand_prod( self.taz['MD_wacc_fact'])
        self.wegr_PK = mtx.expand_attr( self.taz['AM_wacc_fact'])
        self.wegr_OP = mtx.expand_attr( self.taz['MD_wacc_fact'])
        self.Hwy_Prod_Term = mtx.expand_prod( self.taz['Hwy Prod Term Time']) 
        print(f'✓ zonal variable tables generated. Time elapsed: {time.time()-self.start_time:.2f} seconds')
        

    def __var_by_mode(self,pv,var,mode):
        # loads the coefficients by variable and mode
        drive_modes = md.drive_modes
        DAT_modes = md.DAT_modes
        WAT_modes = md.WAT_modes
        active_modes = md.active_modes
        smart_mobility_modes = md.smart_mobility_modes
        
        table = np.zeros((md.max_zone,md.max_zone))
        
        peak = pv[2:]
        if peak == 'PK':
            skim_dict = self.skim_PK_dict
        elif peak == 'OP':
            skim_dict = self.skim_OP_dict
        else:
            print('peak input incorrect!')

        if var == 'IVTT':
            if mode in drive_modes:
                skim = skim_dict['drive']
                table = skim['CongTime']
            elif mode in DAT_modes:
                skim = skim_dict[mode]
                table = skim['Total_IVTT']
                table[np.where(abs(table)>1e6)] = +1e6 # negative infinity indicates no path found
                table[np.where(table==0)]=+1e6 # 0 in DAT skims indicates no path found
            elif mode in WAT_modes:
                skim = skim_dict['WAT']
                table = skim['Total_IVTT']
                table[np.where(table==0)]=+1e6 # 0 in DAT skims indicates no path found
            elif mode in active_modes:
                pass
            elif mode in smart_mobility_modes:
                skim = skim_dict['drive']
                if mode == 'SM_RA':
                    table = skim['CongTime']
                elif mode == 'SM_SH':
                    table = skim['CongTime'] * self.sm.sh_los_overhead_factor
            else: print(mode,var,'not found in var_by_mode module')
            
        elif var == 'OVTT':
            if mode in drive_modes:
                skim = skim_dict['drive']
                table = skim['TerminalTimes']
            elif mode in DAT_modes: 
                skim = skim_dict[mode] 
                table = skim['Total_OVTT'] + self.Hwy_Prod_Term # add Hwy Prod Term Time
            elif mode in WAT_modes:
                skim = skim_dict['WAT']
                table = skim['Total_OVTT']
            elif mode in active_modes: # walk time, bike time from skims.
                skim = skim_dict[mode]
                table = skim[mode+'Time'][:md.max_zone,:md.max_zone]
            elif mode in smart_mobility_modes:
                skim = skim_dict['drive']
                if mode == 'SM_RA':
                    table = self.sm.OVTT_table
                elif mode == 'SM_SH':
                    table = self.sm.OVTT_table * self.sm.sh_los_overhead_factor
                #table = skim['TerminalTimes']              
            else: print(mode,var,'not found in var_by_mode module')

        elif var == 'Cost':
            if mode in drive_modes:
                skim = skim_dict['drive']
                toll = skim['Auto_Toll (Skim)'] 
                toll[np.where(abs(toll)>1e6)] = 0 # eliminate same-zone large value issues
                
                length = skim['Length (Skim)']
                AO = md.AO_dict[mode]
                
                table = (toll/AO + length * self.cost_per_mile)

            elif mode in DAT_modes: 
                skim = skim_dict[mode]
                table = skim['Total_Cost']
            elif mode in WAT_modes:
                skim = skim_dict['WAT']
                table = skim['Total_Cost']
            elif mode in active_modes:
                pass
            elif mode in smart_mobility_modes:
                skim = skim_dict['drive']
                toll = skim['Auto_Toll (Skim)']
                toll[np.where(abs(toll)>1e6)] = 0 # eliminate same-zone large value issues
                
                length = skim['Length (Skim)']
                time = skim['CongTime']
                
                if mode == 'SM_RA':
                    xsub = self.sm.cross_subsidy
                elif mode == 'SM_SH':
                    xsub = self.sm.cross_subsidy * -1
                
                total_cost = self.sm.base_fare + (self.sm.dist_fare + xsub) * length + self.sm.time_fare * time + toll
                
                if mode == 'SM_RA':
                    table = total_cost
                elif mode == 'SM_SH':
                    table = total_cost / self.sm.sh_cost_factor
            
            else: print(mode,var,'not found in var_by_mode module')    
        
        elif var == 'Parking': 
            if mode in drive_modes:
                table = self.parking
            elif mode in DAT_modes + WAT_modes + active_modes + smart_mobility_modes:
                pass
            else: print(mode,var,'not found in var_by_mode module')
        
        elif var == 'length':
            if mode in active_modes:
                skim = skim_dict[mode]
                table = skim['Length (Skim)'][:md.max_zone,:md.max_zone]
            elif mode in drive_modes + DAT_modes + WAT_modes + smart_mobility_modes:
                pass
            else: print(mode,var,'not found in var_by_mode module')
        
        elif var == 'Sqrlength':
            if mode in active_modes:
                skim = skim_dict[mode]
                table = np.sqrt(skim['Length (Skim)'][:md.max_zone,:md.max_zone])
            elif mode in drive_modes + DAT_modes + WAT_modes + smart_mobility_modes:
                pass
            else: print(mode,var,'not found in var_by_mode module')        
        
        elif var == 'AccPEV':
            if mode in active_modes + WAT_modes:
                table = self.AccPEV
            elif mode in drive_modes + DAT_modes + smart_mobility_modes:
                pass
            else: print(mode,var,'not found in var_by_mode module')    
                    
        elif var == 'EgrPEV':
            if mode in active_modes + WAT_modes + DAT_modes:
                table = self.EgrPEV
            elif mode in drive_modes + smart_mobility_modes:
                pass
            else: print(mode,var,'not found in var_by_mode module')           
                
        elif var == 'PopD': # sqrt population density production TAZ
            if mode in active_modes + WAT_modes:
                table = self.PopD
            elif mode in drive_modes + DAT_modes + smart_mobility_modes:
                pass
            else: print(mode,var,'not found in var_by_mode module')  

        elif var == 'EmpD': # sqrt employment density attraction TAZ
            if mode in active_modes + DAT_modes:
                table = self.EmpD
            elif mode in drive_modes + WAT_modes + smart_mobility_modes:
                pass
            else: print(mode,var,'not found in var_by_mode module')  
            
        elif var == 'HHSize':
            if mode in drive_modes:
                table = self.HHSize
            elif mode in active_modes + DAT_modes + WAT_modes + smart_mobility_modes:
                pass
            else: print(mode,var,'not found in var_by_mode module')  
        
        elif var == 'VPW':
            if mode in drive_modes:
                table = self.VPW
            elif mode in active_modes + DAT_modes + WAT_modes + smart_mobility_modes:
                pass
            else: print(mode,var,'not found in var_by_mode module')  
            
        elif var == 'wacc_fact':
            if mode in WAT_modes:
                table = self.wacc_PK * (peak == 'PK') + self.wacc_OP * (peak == 'OP')
            elif mode in drive_modes + active_modes + DAT_modes + smart_mobility_modes:
                pass
            else: print(mode,var, 'not found in var_by_mode module')
            
        elif var == 'wegr_fact':
            if mode in WAT_modes + DAT_modes:
                table = self.wegr_PK * (peak == 'PK') + self.wegr_OP * (peak == 'OP')
            elif mode in drive_modes + active_modes + smart_mobility_modes:
                pass
            else: print(mode,var, 'not found in var_by_mode module')
        
        else:
            print(mode, var, 'not implemented in var_by_mode module')
        
        # dimension check
        if table.shape!=(md.max_zone,md.max_zone):
            try: table = table[:md.max_zone,:md.max_zone]
            except: raise
        
        return table            
    
    def __mode_probability_tables(self,pv,modes):
        # calculates the utility for each mode alternative
        var_values = {}
        for mode in modes:
            var_values[mode]={}
            for var in self.var_list:
                var_values[mode][var] = self.__var_by_mode(pv,var,mode)

        # compute utility for each mode.
        mode_utils = {}
        for mode in modes: 
            util = np.zeros((md.max_zone,md.max_zone))
            util += self.param[self.param['mode']==mode]['ASC_'+pv].values
            for var in self.var_list:
                # coefficient values
                coeff = self.param[self.param['mode']==mode][var].values
                util += coeff * var_values[mode][var]
            mode_utils[mode] = np.exp(util)
            
        # compute logsums
        nests = self.param[self.param['mode'].isin(modes)].nest.unique()
        nest_logsums= dict(zip(nests,[np.zeros((md.max_zone,md.max_zone))]*len(nests)))
        
        for mode in modes:
            nest = dict(zip(self.param['mode'],self.param['nest']))[mode]
            nest_logsum = nest_logsums[nest]
            nest_logsums[nest] = nest_logsum + mode_utils[mode]
        
        zero_logsum = {}

        for nest in nests:
            zero_logsum[nest] = (nest_logsums[nest]==0) # apply the mask later in probability calculation
            (nest_logsums[nest])[~zero_logsum[nest]] = np.log((nest_logsums[nest])[~zero_logsum[nest]]) # if nest logsum is not zero, calculate log.
        
        # from logsums to mode probability
        nest_thetas = dict(zip(self.param['nest'],self.param['nest_coefficient']))
        mode_probs = {}
        
        all_nest_sum = np.zeros((md.max_zone,md.max_zone))
        # if a nest has entries with zero logsum, it will be excluded.
        for nest in nests:
            all_nest_sum[~zero_logsum[nest]] += np.exp(nest_thetas[nest] * nest_logsums[nest][~zero_logsum[nest]])
        
        for mode in modes:
            mode_probs[mode]={}
            
            nest = dict(zip(self.param['mode'],self.param['nest']))[mode]
            theta = nest_thetas[nest]
            #modes_in_nest = self.param[self.param['nest']==nest]['mode']

            prob_nest = np.zeros((md.max_zone,md.max_zone))
            prob_nest[~zero_logsum[nest]] = np.exp(theta * nest_logsums[nest][~zero_logsum[nest]]) / all_nest_sum[~zero_logsum[nest]]
            
            prob_mode_in_nest = np.zeros((md.max_zone,md.max_zone))
            prob_mode_in_nest[~zero_logsum[nest]] = (mode_utils[mode][~zero_logsum[nest]] / 
            np.exp((nest_logsums[nest]))[~zero_logsum[nest]])
                
            prob = prob_nest * prob_mode_in_nest
            mode_probs[mode] = prob
        
        return mode_probs, nest_logsums, mode_utils
####
# Public Functions
####
    def load_input(self):
        ''' Reads the skims, trip tables, and zonal data into memory for processing'''
        self.__read_taz_data()
        self.__read_skims()
        self.__read_trip_table()
        self.__generate_zonal_var()
    
    def read_param(self, purpose):
        ''' Reads associated parameters file with mode choice coefficients'''   
        param = pd.read_excel(self.param_file,sheet_name = purpose).fillna(0)
        trip_tables = [purpose+ i for i in ['_PK_0Auto','_PK_wAuto','_OP_0Auto','_OP_wAuto']]
        self.trip_tables_dict = dict(zip(md.peak_veh,trip_tables))
        
        coef_col = ['mode','nest','nest_coefficient'] +list(param.filter(regex='ASC'))
        self.coef_table = param[coef_col]
        self.var_list = param.columns.drop(coef_col)
        self.param = param
        self.AO_dict = md.AO_dict
        print(f'✓ Parameter table for {purpose} generated. Time elapsed: {time.time()-self.start_time:.2f} seconds')
        
    def calculate_trips_by_mode(self):
        ''' Applies trip tables to mode shares to generate modal trip tables''' 
        modes = self.param['mode']

        self._0_PK, self._1_PK, self._0_OP, self._1_OP = ({},{},{},{})
        
        self.trips_by_mode = dict(zip(md.peak_veh, [self._0_PK, self._1_PK, self._0_OP, self._1_OP]))
        
        for pv in md.peak_veh:
            [mode_probs,x,y] = self.__mode_probability_tables(pv,modes)
            print(f'✓ Trips for {pv} calculated. Time elapsed: {time.time()-self.start_time:.2f} seconds')
            for mode in modes:
                trip_table = self.pre_MC_trip_table[self.trip_tables_dict[pv]][:md.max_zone,:md.max_zone]
                trips_MC = trip_table * mode_probs[mode]
                self.trips_by_mode[pv][mode] = trips_MC
    
    def run_for_purpose(self, purpose):
        ''' Runs mode choice model for selected purpose 
            and populates the table_container object of ModeChoice with the modal tables
            
            :param purpose: Purpose string (e.g. 'HBW') to run
        '''
        self.read_param(purpose)
        self.calculate_trips_by_mode()
        self.table_container.store_table(purpose)
    
    def run_model(self):
        ''' Runs mode choice model and populates the table_container object of ModeChoice with the modal tables
        '''
        print('Running for all purposes...')
        for purpose in md.purposes:
            print(f'Mode choice for {purpose} started.')
            self.run_for_purpose(purpose)
            #write_mode_share_to_excel(self,purpose)


# Diagnostic methods
    def call_var_by_mode(self,pv='0_PK',var='OVTT',mode='DA'):
        return self.__var_by_mode(pv,var,mode)

    def call_mode_probability_tables(self,pv='0_PK',modes=['DA']):
        return self.__mode_probability_tables(pv,modes)[0]