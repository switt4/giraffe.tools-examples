#This is a Nipype generator. Warning, here be dragons.
#!/usr/bin/env python

import sys
import nipype
import nipype.pipeline as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.io as io

#Wraps the executable command ``mcflirt``.
fsl_mcflirt = pe.MapNode(interface = fsl.MCFLIRT(), name='fsl_mcflirt', iterfield = ['in_file'])

#Flexibly collect data from disk to feed into workflows.
io_select_files = pe.Node(io.SelectFiles(templates={'anat':'sub-{subID}/anat/sub-{subID}_acq-MPRAGE_run-01_T1w.nii.gz,'func':'sub-{subID}/func/sub-{subID}_task-{taskID}_run-{runID}_bold.nii.gz}), name='io_select_files', iterfield = ['subID", "funcRun", "taskName'])
io_select_files.inputs.base_directory = 'bids'
io_select_files.inputs.anat = 'sub-{subID}/anat/sub-{subID}_acq-MPRAGE_run-01_T1w.nii.gz
io_select_files.inputs.func = 'sub-{subID}/func/sub-{subID}_task-{taskID}_run-{runID}_bold.nii.gz

#Generic datasink module to store structured outputs
io_data_sink = pe.Node(interface = io.DataSink(), name='io_data_sink')

#Wraps the executable command ``bet``.
fsl_bet = pe.MapNode(interface = fsl.BET(), name='fsl_bet', iterfield = ['in_file'])

#Wraps the executable command ``flirt``.
fsl_flirt = pe.MapNode(interface = fsl.FLIRT(), name='fsl_flirt', iterfield = ['in_file', 'reference'])

#Create a workflow to connect all those nodes
analysisflow = nipype.Workflow('MyWorkflow')
analysisflow.connect(io_select_files, "func", fsl_mcflirt, "in_file")
analysisflow.connect(io_select_files, "anat", fsl_bet, "in_file")
analysisflow.connect(fsl_bet, "out_file", fsl_flirt, "reference")
analysisflow.connect(fsl_mcflirt, "mean_img", fsl_flirt, "in_file")

#Run the workflow
plugin = 'MultiProc' #adjust your desired plugin here
plugin_args = {'n_procs': 1} #adjust to your number of cores
analysisflow.write_graph(graph2use='flat', format='png', simple_form=False)
analysisflow.run(plugin=plugin, plugin_args=plugin_args)
