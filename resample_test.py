#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 13:21:33 2020

@author: wcrum
"""

import Resample2BC

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 13:21:33 2020

@author: wcrum
"""
import Resample2BC

lggpath = 'C:\\Users\\Mitch\\OneDrive - Imperial College London\\Documents\\Cardiac Radiomics\\RBCTest'

#lggpath = 'C:/Users/mchen/Downloads/LCconvert/uploaded - 231120/rs/ori/'

# origdir   = os.path.join(lggpath, 'forTexLABtest')
# resampled = os.path.join(lggpath, 'forTexLABtestOUT')
# Resample2BC.Resample2BC(origdir, resampled, voxel=[1, 1, 7], smooth_if_larger=False)

origdir = lggpath

resampled = 'C:\\Users\\Mitch\\OneDrive - Imperial College London\\Documents\\Cardiac Radiomics\\RBCRS'

#resampled = 'C:/Users/mchen/Downloads/LCconvert/uploaded - 231120/rs/rs/'

# So resampled dimensions in this example are 0.5x0.5x5.0mm
# We are applying an image smoothing if resampling to larger voxel dimension in any direction
# The 0.375 smoothing parameter is empirically sensible and is in units of the resampled voxel
# size in any particular direction
# You can set dirfilter = None - otherwise it allows you to only process subdirectories
# with names which end with dirfilter

Resample2BC.Resample2BC(origdir, resampled, voxel=[1, 1, 2], smooth_if_larger=True, smooth_sd = 0.375, copyX = False)

