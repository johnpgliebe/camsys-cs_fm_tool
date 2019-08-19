# Cambridge Systematics Future Mobility Tool

The CS FM Tool has been initially developed using the Boston MPO (CTPS) regional model
Trip tables and skims were converted into OMX format for a generic implemenation. 

# Carbon Free Boston Input Data
Available (until February 1, 2020) for download here: 
https://camsys.egnyte.com/fl/AwnhMmiDsT

# Documentation

https://camsys.github.io/cs_fm_tool/

# Quick Start

## Setup
Update the config.py with paths to the data and folders to hold the active scenario and archive

Make a copy of the param\baseline.yaml file and configure settings to represent the desired scenario

### Python Packages Required

- openmatrix
- numpy
- pandas
- openpyxl

## Run
An example is provided using Jupyter notebook (CS FM Tool Demo.ipynb). The tool may also be run directly from the python command line: 

import cs_fm_tool

import param.config as config

fm = cs_fm_tool.CS_FM_Tool(config, r'param\price_adj.yaml',
                   r'param\perf_meas_nosm.yaml')

fm.load_inputs()

fm.setup()

fm.run()

fm.post_process()

fm.archive()



