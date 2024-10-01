#! /usr/bin/env python3

from ROOT import *
from glob import glob
import argparse
import sys
import numpy as np
import os

sys.path.append(os.path.expandvars("$CMSSW_BASE/src/cms-tools/lib"))
sys.path.append(os.path.expandvars("$CMSSW_BASE/src/cms-tools/"))
sys.path.append(os.path.expandvars("$CMSSW_BASE/src/cms-tools/lib/classes"))

import utils
import analysis_ntuples
import analysis_selections

gROOT.SetBatch(True)
gStyle.SetOptStat(0)

gSystem.Load('LumiSectMap_C')
from ROOT import LumiSectMap

#lumi = 5746.370
#weight = lumi / utils.LUMINOSITY

####### CMDLINE ARGUMENTS #########

parser = argparse.ArgumentParser(description='Scales pMSSM thnsparse with nuni/uni weights ratio')
parser.add_argument('-i', '--input_file', nargs=1, help='Input Filename', required=True)
parser.add_argument('--is_test', help='Testing Mode', required=False, action='store_true')
args = parser.parse_args()
input_file = args.input_file
is_test = args.is_test

if not is_test:
    print("THIS IS NOT A DRILL")

def sum_thn_sparse_bins(file_name):
    # Open the ROOT file
    root_file = TFile.Open(file_name, "read")
    root_file_weighted = TFile.Open(file_name.replace(".root", "_weighted.root"), "recreate")

    # Get the THnSparse object
    thn_sparse = root_file.Get("pMSSM Scan uni")
    thn_sparse_nuni = root_file.Get("pMSSM Scan nuni")
    

    if not thn_sparse:
        print(f"Error: THnSparse object '{thn_sparse_name}' not found in the file.")
        return

    bin_indices = np.zeros(thn_sparse.GetNdimensions(), dtype = "double")
    bin_indices_nuni = np.zeros(thn_sparse_nuni.GetNdimensions(), dtype = "double")

    # Set the bin indices
    x_axis = thn_sparse.GetAxis(0)
    y_axis = thn_sparse.GetAxis(1)
    z_axis = thn_sparse.GetAxis(2)

    x_axis_nuni= thn_sparse_nuni.GetAxis(0)
    y_axis_nuni= thn_sparse_nuni.GetAxis(1)
    z_axis_nuni= thn_sparse_nuni.GetAxis(2)

    num_x_bins = x_axis.GetNbins()
    num_y_bins = y_axis.GetNbins()
    num_z_bins = z_axis.GetNbins()

    num_x_bins_nuni = x_axis_nuni.GetNbins()
    num_y_bins_nuni = y_axis_nuni.GetNbins()
    num_z_bins_nuni = z_axis_nuni.GetNbins()
    print(f"For uni: num_x_bins: {num_x_bins}, num_y_bins: {num_y_bins}, num_z_bins: {num_z_bins}")
    print(f"For nuni: num_x_bins: {num_x_bins_nuni}, num_y_bins: {num_y_bins_nuni}, num_z_bins: {num_z_bins_nuni}")

    # Sum the contents of the third axis for the specified bin indices
    time2break = False
    found_sth = False
    for bin_x in range(1, int(num_x_bins+1)):
        if time2break:
            break
        bin_indices[0] = x_axis.FindBin(bin_x)
        bin_indices_nuni[0] = x_axis_nuni.FindBin(bin_x)
        for bin_y in range(int(1), int(num_y_bins +1)):
            bin_indices[1] = y_axis.FindBin(bin_y)
            bin_indices_nuni[1] = y_axis_nuni.FindBin(bin_y)
            total_sum_uni = 0
            total_sum_nuni = 0


            #uni
            rescalable_bins = np.ones(num_z_bins)*(-1)
            for bin_z in range(1, int(num_z_bins + 1)):
                bin_indices[2] = z_axis.FindBin(bin_z)

                global_bin_index = thn_sparse.GetBin(bin_indices)
                bin_content = thn_sparse.GetBinContent(global_bin_index)

                # if global_bin_index > 0: print(global_bin_index)
                if bin_content > 0:
                    print(f"bin_content: {bin_content} for global bin index {global_bin_index} \n bin indices = {bin_indices} UNI")
                    rescalable_bins[bin_z-1] = z_axis.FindBin(bin_z)
                total_sum_uni += bin_content
            if bin_content > 0: print(f"total sum uni: {total_sum_uni}")


            #nuni
            for bin_z in range(1, int(num_z_bins + 1)):
                bin_indices_nuni[2] = z_axis_nuni.FindBin(bin_z)

                global_bin_index_nuni = thn_sparse_nuni.GetBin(bin_indices_nuni)
                bin_content_nuni = thn_sparse_nuni.GetBinContent(global_bin_index_nuni)

                if bin_content_nuni > 0: print(f"bin_content: {bin_content_nuni} for global bin index {global_bin_index_nuni} \n bin indices = {bin_indices_nuni} NUNI")
                total_sum_nuni += bin_content_nuni
            if bin_content_nuni > 0: print(f"total sum nuni: {total_sum_nuni}")

            #rescale
            for bin_idx in rescalable_bins:
                if bin_idx < 0:
                    continue
                bin_indices[2] = bin_idx
                global_bin_index = thn_sparse.GetBin(bin_indices)
                bin_content = thn_sparse.GetBinContent(global_bin_index)
                if total_sum_uni > 0:
                    print(f"total sum uni: {total_sum_uni} \n total sum nuni: {total_sum_nuni}")
                    thn_sparse.SetBinContent(global_bin_index, bin_content*total_sum_nuni/total_sum_uni)
                if bin_content > 0: print(f"bin_content: {bin_content} for global bin index {global_bin_index} RESCALE")

            # found_sth = False
            if is_test:
                if total_sum_nuni == 0:
                    continue
                else:
                    print(f"Just normalized with total integral: {total_sum_nuni}")
                    time2break = True
                    break

    root_file_weighted.cd()
    thn_sparse.Write()
    root_file_weighted.Close()
    root_file.Close()


file_name = input_file[0]

sum_thn_sparse_bins(file_name)

