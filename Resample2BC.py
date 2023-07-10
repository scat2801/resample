# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 10:52:46 2020

@author: wcrum
"""

# Adapted by Bill Crum from the original Resample2 by Kristofer Linton-Reid
# for forTexLAB directory structure

#@author: wcrum. Modified by Mitch Chen on 08/01/2021
#"""
#And again on 09/02/2021 to adapt smoothing to ImageJ produced NIFTI

#
# Original Resample2 code:
#       imagedir : [image1, ..., imageM]
#       segdir : [seg1, ..., segN]
# This code::
#       imagedir : [case1dir, ..., caseNdir]
#       case1dir : [case1.nii/.nii.gz seg1.nii/.nii.gz ... segM.nii/.nii.gz]
#                   ...
#       caseNdir
# Otherwise functionally the same with some code refinement
#

import os
import os.path
import numpy
import nibabel
import nibabel.processing

def Resample2BC(img_path, output_path, method1='cubic', method2='neighbours', voxel=1, smooth_if_larger=False,
                smooth_sd=0.5, dirfilter=None, force=False, copyX=False, skipto=False):
    # img_path is an existing directory with data formatted for TexLAB
    # i.e. one directory per case, each containing case.nii(.gz) and one or more
    # segmentation files: somemask.nii(.gz) someothermask.nii(.gz) with one mask
    # label per segmentation file
    # method1 = interpolation method used for images ('cubic')
    # method2 = interpolation method used for masks ('neighbours')
    #   interpolation methods are 'neighbours', 'trilinear', 'cubic'
    # voxel = resliced voxel dimensions
    #   voxel = [sx, sy, sz]
    #   voxel = 1, 2, 3, 4 or 5 implies voxel = [1, 1, voxel]
    # smooth_if_larger = flag for including smoothing step before interpolation to larger voxels
    # smooth_sd = standard deviation of Gaussian smoothing kernel in units of resliced voxel width
    # dirfilter specifies a suffix for filtering image directories (None = no filtering by default)
    # force = True enables overwrite of existing images
    # copyX = True copies qform and sform from image to all segmentations

    # Get slice-thickness for resampling
    # In-plane is 1x1 unless specified explicitly e.g. [0.5, 0.5, 1.25]
    if isinstance(voxel, list):
        voxel_shape = voxel
    elif voxel > 5:
        print
        'voxel default ranges 1:5, alternatively provide list of voxel dims i.e voxel=[1,1,6]'
        return
    else:
        voxel_shape = [1, 1, voxel]

    # Resampling types
    order_dict = {'neighbours': 0, 'trilinear': 1, 'cubic': 3}
    if method1 in order_dict:
        order1 = order_dict[method1]
    else:
        print
        'error - method1 must be one of', order_dict.keys()
        return
    if method2 in order_dict:
        order2 = order_dict[method2]
    else:
        print
        'error - method2 must be one of', order_dict.keys()
        return

    # Don't allow output over input
    if img_path == output_path:
        print
        'error - output_path must be different to img_path', img_path
        return

    # Check main image directory exists
    if not os.path.isdir(img_path):
        print
        'error -', img_path, 'directory cannot be found'
        return

    # Make main output directory if necessary
    if not os.path.isdir(output_path):
        os.mkdir(output_path)

    # Get (filtered) list of image directories
    input_list = os.listdir(img_path)
    input_list = [f for f in input_list if os.path.isdir(os.path.join(img_path, f))]
    if not (dirfilter is None):
        input_list = [f for f in input_list if str.endswith(f, dirfilter)]

    # Main loop over image directories
    for im in input_list:

        if skipto != False:
            if skipto == im:
                skipto = False
            else:
                print
                ' skipping case', im
                continue

        # Get input directory and filename
        input_dir = os.path.join(img_path, im)
        this_input_file = im + '.nii'
        input_file = os.path.join(input_dir, this_input_file)
        if not os.path.isfile(input_file):
            this_input_file = im + '.nii.gz'
            input_file = os.path.join(input_dir, this_input_file)
            if not os.path.isfile(input_file):
                print
                'error - image file', im, 'not found so skipping'
                continue

        # Check output exists and forced condition
        output_dir = os.path.join(output_path, im)
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        outputfile = os.path.join(output_dir, this_input_file)
        if os.path.isfile(outputfile) and not force:
            print
            outputfile, 'exists so skipping'
            continue

            # Load input image
        try:
            input_img = nibabel.load(input_file)
        except nibabel.filebasedimages.ImageFileError:
            print
            'error opening', input_file, 'so skipping'
            continue

        # Apply smoothing if requested when output voxel dimension > input
        if smooth_if_larger:
            # Get rid of empty image dimensions which crash smooth_image
            input_img = nibabel.squeeze_image(input_img);
            ipaffine = input_img.affine
            pixdim = input_img.header.get_zooms()
            pixdim = pixdim[0:3]
            sds = numpy.array([0.0 if pixdim[i] > voxel_shape[i] else smooth_sd * voxel_shape[i] for i in range(3)])
            fwhm = nibabel.processing.sigma2fwhm(sds)
            print
            sds, fwhm, pixdim
            input_img = nibabel.processing.smooth_image(input_img, fwhm)

        # Apply resampling
        resampled = nibabel.processing.resample_to_output(input_img, voxel_shape, order=order1)
        resampled = resampled.slicer[:, ::-1, :]

        # Save in new directory tree
        nibabel.save(resampled, outputfile)
        opaffine = resampled.affine

        if copyX:
            print
            'Copying resampled image qform and sform'
            imgqform = resampled.get_qform(coded=True)
            imgsform = resampled.get_sform(coded=True)
            sformaffine = imgsform[0];
            sformcode = int(imgsform[1])
            qformaffine = imgqform[0]
            qformcode = int(imgqform[1])

        # Deal with segmentations in same directory
        allfiles = os.listdir(input_dir)
        for thisfile in allfiles:
            # Already processed image
            thisfullfile = os.path.join(input_dir, thisfile)
            if thisfullfile == input_file:
                continue
            if not (str.endswith(thisfile, '.nii') or str.endswith(thisfile, '.nii.gz')):
                continue
            # Check if image exists and overwrite enabled
            outputfile = os.path.join(output_dir, thisfile)
            if os.path.isfile(outputfile) and not force:
                print
                outputfile, 'exists so skipping'
                continue

                # Load input image
            try:
                input_seg = nibabel.load(thisfullfile)
            except nibabel.filebasedimages.ImageFileError:
                print
                'error opening', thisfile, 'so skipping'
                continue

            # Apply smoothing if requested when output voxel dimension > input
            if smooth_if_larger:
                ipheader = input_seg.header
                ipaffine = input_seg.affine
                sdata = input_seg.get_fdata()
                sdata = 100.0 * numpy.asarray(sdata)
                sdata = numpy.minimum(sdata, 100);
                sdata = numpy.maximum(sdata, 0);
                sdata = nibabel.Nifti1Image(sdata, affine=ipaffine)
                input_seg = nibabel.processing.smooth_image(sdata, fwhm)
                input_seg = input_seg.get_fdata()
                input_seg = 0.01 * numpy.asarray(input_seg)
                input_seg = numpy.where(input_seg < 0.5, 0, input_seg)
                input_seg = numpy.where(input_seg >= 0.5, 1, input_seg)
                input_seg = nibabel.Nifti1Image(input_seg, affine=ipaffine, header=ipheader)

            # Apply resampling
            resampled_seg0 = nibabel.processing.resample_to_output(input_seg, voxel_sizes=voxel_shape, order=order2)
            opaffine = resampled_seg0.affine
            resampled_seg_data = resampled_seg0.get_data()

            # This is in case a non-default mask interpolation was chosen
            # and makes sure the mask remains binary
            resampled_seg = numpy.asarray(resampled_seg_data)
            resampled_seg = numpy.where(resampled_seg < 0.5, 0, resampled_seg)
            resampled_seg = numpy.where(resampled_seg >= 0.5, 1, resampled_seg)
            resampled_seg = nibabel.Nifti1Image(resampled_seg, opaffine, header=resampled_seg0.header)

            # Attempt to copy sform and qform info from image
            if copyX:
                resampled_seg.set_qform(qformaffine, code=qformcode)
                resampled_seg.set_sform(sformaffine, code=sformcode)

            # Save segmentation
            nibabel.save(resampled_seg, outputfile)

    return
