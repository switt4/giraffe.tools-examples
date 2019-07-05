#This is a Nipype generator. Warning, here be dragons.
#!/usr/bin/env python

import sys
import nipype
import nipype.pipeline as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.io as io
import nipype.interfaces.afni as afni
import nipype.algorithms.confounds as confounds

#Wraps the executable command ``mcflirt``.
fsl_mcflirt = pe.MapNode(interface = fsl.MCFLIRT(), name='fsl_mcflirt', iterfield = ['in_file'])

#Flexibly collect data from disk to feed into workflows.
io_select_files = pe.Node(io.SelectFiles(templates={'anat':'sub-{subID}/anat/sub-{subID}_*_T1w.nii.gz','func':'sub-{subID}/func/sub-{subID}_*_bold.nii.gz'}), name='io_select_files', iterfield = ['subID'])
io_select_files.inputs.base_directory = bidsDir
io_select_files.inputs.anat = 'sub-{subID}/anat/sub-{subID}_*_T1w.nii.gz'
io_select_files.inputs.func = 'sub-{subID}/func/sub-{subID}_*_bold.nii.gz'
io_select_files.iterables = [('subID', subID)]

#Generic datasink module to store structured outputs
io_data_sink = pe.MapNode(interface = io.DataSink(), name='io_data_sink', iterfield = ['smoothedEPI', 'framewiseDisplacement', 'mcflirtPar', 'aCompCorComponents'])
io_data_sink.inputs.base_directory = outDir
io_data_sink.inputs.parameterization = True

#Wraps the executable command ``bet``.
fsl_bet = pe.MapNode(interface = fsl.BET(), name='fsl_bet', iterfield = ['in_file'])
fsl_bet.inputs.frac = 0.6

#Wraps the executable command ``flirt``.
flirt_EPItoT1 = pe.MapNode(interface = fsl.FLIRT(), name='flirt_EPItoT1', iterfield = ['in_file', 'reference'])

#Wraps the executable command ``flirt``.
flirt_T1toMNI = pe.Node(interface = fsl.FLIRT(), name='flirt_T1toMNI')
flirt_T1toMNI.inputs.reference = $FSLDIR/data/standard/MNI152_T1_2mm_brain.nii.gz

#Wraps the executable command ``convert_xfm``.
fsl_convert_xfm = pe.MapNode(interface = fsl.ConvertXFM(), name='fsl_convert_xfm', iterfield = ['in_file', 'in_file2'])
fsl_convert_xfm.inputs.concat_xfm = True

#Wraps the executable command ``flirt``.
flirt_EPItoMNI = pe.MapNode(interface = fsl.FLIRT(), name='flirt_EPItoMNI', iterfield = ['in_file', 'in_matrix_file'])
flirt_EPItoMNI.inputs.reference = $FSLDIR/data/standard/MNI152_T1_2mm_brain.nii.gz

#Wraps the executable command ``3dBlurToFWHM``.
afni_blur_to_fwhm = pe.Node(interface = afni.BlurToFWHM(), name='afni_blur_to_fwhm')
afni_blur_to_fwhm.inputs.fwhm = 6

#Calculate the :abbr:`FD (framewise displacement)` as in [Power2012]_.
confounds_framewise_displacement = pe.MapNode(interface = confounds.FramewiseDisplacement(), name='confounds_framewise_displacement', iterfield = ['in_file'])
confounds_framewise_displacement.inputs.parameter_source = 'FSL'

#Anatomical compcor: for inputs and outputs, see CompCor.
confounds_acomp_cor = pe.MapNode(interface = confounds.ACompCor(), name='confounds_acomp_cor', iterfield = ['realigned_file', 'mask_files'])
confounds_acomp_cor.inputs.merge_method = 'union'

#Wraps the executable command ``fast``.
fsl_fast = pe.MapNode(interface = fsl.FAST(), name='fsl_fast', iterfield = ['in_files'])
fsl_fast.inputs.number_classes = 3

#Create a workflow to connect all those nodes
analysisflow = nipype.Workflow('MyWorkflow')
analysisflow.connect(io_select_files, "func", fsl_mcflirt, "in_file")
analysisflow.connect(io_select_files, "anat", fsl_bet, "in_file")
analysisflow.connect(fsl_bet, "out_file", flirt_EPItoT1, "reference")
analysisflow.connect(fsl_mcflirt, "mean_img", flirt_EPItoT1, "in_file")
analysisflow.connect(fsl_bet, "out_file", flirt_T1toMNI, "in_file")
analysisflow.connect(flirt_EPItoT1, "out_matrix_file", fsl_convert_xfm, "in_file")
analysisflow.connect(flirt_T1toMNI, "out_matrix_file", fsl_convert_xfm, "in_file2")
analysisflow.connect(fsl_mcflirt, "out_file", flirt_EPItoMNI, "in_file")
analysisflow.connect(fsl_convert_xfm, "out_file", flirt_EPItoMNI, "in_matrix_file")
analysisflow.connect(flirt_EPItoMNI, "out_file", afni_blur_to_fwhm, "in_file")
analysisflow.connect(fsl_mcflirt, "par_file", confounds_framewise_displacement, "in_file")
analysisflow.connect(fsl_bet, "out_file", fsl_fast, "in_files")
analysisflow.connect(fsl_mcflirt, "out_file", confounds_acomp_cor, "realigned_file")
analysisflow.connect(fsl_fast, "partial_volume_files", confounds_acomp_cor, "mask_files")
analysisflow.connect(afni_blur_to_fwhm, "out_file", io_data_sink, "smoothedEPI")
analysisflow.connect(confounds_framewise_displacement, "out_file", io_data_sink, "framewiseDisplacement")
analysisflow.connect(fsl_mcflirt, "par_file", io_data_sink, "mcflirtPar")
analysisflow.connect(confounds_acomp_cor, "components_file", io_data_sink, "aCompCorComponents")

#Run the workflow
plugin = 'MultiProc' #adjust your desired plugin here
plugin_args = {'n_procs': 1} #adjust to your number of cores
analysisflow.write_graph(graph2use='flat', format='png', simple_form=False)
analysisflow.run(plugin=plugin, plugin_args=plugin_args)
