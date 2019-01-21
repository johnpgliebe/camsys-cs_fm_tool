# -*- coding: utf-8 -*-
# CS FutureMobility Tool
# See full license in LICENSE.txt.

import yaml
import os, sys
import shutil
import mode_choice.mode_choice as mode_choice
import mode_choice.mc_util as mc_util
import mode_choice.trk_util as trk_util
import mode_choice.scenario_editor as se

class CS_FM_Tool():
    '''
    Tool definition class that manages the model runs from a definition.
    
    A Mode Choice object is created that contains the modified
        inputs and outputs from the model process
    
    :param config: the model paths defined in the config.py
    :param scenario_file: the defined scenario values
    :param perf_meas_file: the performance measures to generate
    :param scen_prefix: the string prefix to affix to the output folder
           
    Example: 
        import cs_fm_tool
        import param.config as config
        fm = cs_fm_tool.CS_FM_Tool(config, r'param\price_adj.yaml',
                           r'param\perf_meas_nosm.yaml')
        fm.load_inputs()
        fm.setup()
        fm.run()
        fm.post_process()
        fm.archive()
    
    '''
    
    mc = None

    def __init__(self, 
                 config, 
                 scenario_file, 
                 perf_meas_file, 
                 scen_prefix = 'UltScen'):
        
        self.scenario_file = scenario_file

        self.mc = mode_choice.Mode_Choice(config)

        stream = open(scenario_file, 'r')
        
        scen= yaml.load(stream)
        self.name = scen['name']      
        self.exp_vars = scen['experiment_variables']
        
        stream = open(perf_meas_file, 'r')
        pm= yaml.load(stream)
        self.perf_meas = pm['performance_measures']
        
        # check to see if scenario exists and prompt to rename
        out_folder = (config.archive_path + scen_prefix +
                          "_" + self.name)
        
        if os.path.exists(out_folder):        
            overwrite = input("Scenario results for {0} already exists in the archive overwrite? (y/n)"
                              .format(self.name))
            if overwrite.lower() != 'y':
                print('Change scenario name in yaml file and restart')
                sys.exit()
        
    def load_inputs(self):
        ''' reads inputs into mode choice object
        
            reads zonal data, skim data, and trip tables
            
            paths to data is set in config.py
            
            data must be loaded before setting up scenario
        '''
        self.mc.load_input()
        
        
    def setup(self):
        ''' run experiment variable setup routines
        
        setup routines to be called are defined in the model scenario
        yaml file        
        
        '''
        for expv in self.exp_vars:
            evar = self.exp_vars[expv]
            if evar['active']:
                print('Setting parameters for {} variable' .format(expv))
                kwargs = evar['params']
                eval('se.' + evar['function'] + '(self.mc, **kwargs)')
                
    def run(self):
        ''' run mode choice model 
        
        All scenario settings need to be conducted before running the 
        mode choice model
        '''
        
        self.mc.run_model()
        
        
    def post_process(self):
        ''' run performance measurement summary routines
        
        The routines to run are defined in the performance measure
        yaml file
        '''
        for pm in self.perf_meas:
            pm_def = self.perf_meas[pm]
            if pm_def['active']:
                print('Running summaries for {}' .format(pm))
                kwargs = pm_def['params']
                eval('mc_util.' + pm_def['function'] + '(self.mc, **kwargs)')

        
    def archive(self, out_folder = None):
        ''' copy model output files to the archive
        
        archive path is defined in the model config file
        '''
        if out_folder is None:
            out_folder = (self.mc.config.scen_path + 
                          r"..\\scenarios\\UltScen_" + 
                          self.name)
        
        if os.path.exists(out_folder):
            shutil.rmtree(out_folder)
        
        os.makedirs(out_folder)
            
        source = self.mc.config.scen_path
        files = os.listdir(source)

        for f in files:
                shutil.move(source+f, out_folder)
                
        # copy scenario definition file
        shutil.copy(self.scenario_file, out_folder)
