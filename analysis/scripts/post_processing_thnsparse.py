#! /usr/bin/env python3

import ROOT
from ROOT import TFile
import argparse

import numpy as np


####### CMDLINE ARGUMENTS #########

parser = argparse.ArgumentParser(description='Scales pMSSM thnsparse with nuni/uni weights ratio')
parser.add_argument('-i', '--input_file', nargs=1, help='Input Filename', required=True)
parser.add_argument('--is_test', help='Testing Mode', required=False, action='store_true')
args = parser.parse_args()
input_file = args.input_file[0]
is_test = args.is_test

#open the root file
ROOT_FILE = TFile.Open(input_file, "read")
ROOT_FILE_WEIGHTED = TFile.Open(input_file.replace(".root", "_weighted.root"), "recreate")
THN_SPARSE_UNI = ROOT_FILE.Get("pMSSM Scan uni")
THN_SPARSE_NUNI = ROOT_FILE.Get("pMSSM Scan nuni")


def update_dict(dict, thn_sparse, global_bin_index, num_z_bins):
    """Updates the dictionary containing the bin contents, ordered by their coordinates.
        The last entry stored in the z-array is the global bin index, for rescaling purposes.
    """
    if thn_sparse.GetBinContent(global_bin_index) != 0:# break
        bin_coordinates = np.empty(thn_sparse.GetNdimensions(), dtype = np.int32)
        bin_content = thn_sparse.GetBinContent(global_bin_index, bin_coordinates)

        print(bin_coordinates)
        print("Content:",bin_content)
        x_coord = bin_coordinates[0]
        y_coord = bin_coordinates[1]
        z_coord = bin_coordinates[2]
        if dict.get(x_coord) is None:
            dict[x_coord] = {}
            dict[x_coord][y_coord] = np.zeros(num_z_bins)
            dict[x_coord][y_coord][z_coord] = bin_content
        elif dict[x_coord].get(y_coord) is None:
            dict[x_coord][y_coord] = np.zeros(num_z_bins)
            dict[x_coord][y_coord][z_coord] = bin_content
        else:
            dict[x_coord][y_coord][z_coord] = bin_content
    else:
        print(f"uh-oh: global bin index {global_bin_index} has value {0}")

def rescale(dict_uni, dict_nuni, thn_sparse, global_bin_index):
    if thn_sparse.GetBinContent(global_bin_index) != 0:
        #get bin coordinates from global linear bin idx
        bin_coordinates = np.empty(thn_sparse.GetNdimensions(), dtype = np.int32)
        bin_content = thn_sparse.GetBinContent(global_bin_index, bin_coordinates)
        x_coord = bin_coordinates[0]
        y_coord = bin_coordinates[1]
        z_coord = bin_coordinates[2]

        #Sum bin contents along z:
        total_sum_uni = np.sum(dict_uni[x_coord][y_coord])
        total_sum_nuni = np.sum(dict_nuni[x_coord][y_coord])

        #rescale:
        thn_sparse.SetBinContent(global_bin_index, bin_content*total_sum_nuni/total_sum_uni)

        print(f"global_bin_index {global_bin_index}, new content = {bin_content*total_sum_nuni/total_sum_uni}")


def sum_thn_sparse_bins():
    """Main function. Loops over filled bins, updates dicts and rescales uni with nuni/uni
    """
    # bin_indices = np.zeros(THN_SPARSE_UNI.GetNdimensions(), dtype = "double")
    # bin_indices_nuni = np.zeros(THN_SPARSE_NUNI.GetNdimensions(), dtype = "double")

    # Set the bin indices
    x_axis_uni = THN_SPARSE_UNI.GetAxis(0)
    y_axis_uni = THN_SPARSE_UNI.GetAxis(1)
    z_axis_uni = THN_SPARSE_UNI.GetAxis(2)

    x_axis_nuni= THN_SPARSE_NUNI.GetAxis(0)
    y_axis_nuni= THN_SPARSE_NUNI.GetAxis(1)
    z_axis_nuni= THN_SPARSE_NUNI.GetAxis(2)

    num_x_bins_uni = x_axis_uni.GetNbins()
    num_y_bins_uni = y_axis_uni.GetNbins()
    num_z_bins_uni = z_axis_uni.GetNbins()

    num_x_bins_nuni = x_axis_nuni.GetNbins()
    num_y_bins_nuni = y_axis_nuni.GetNbins()
    num_z_bins_nuni = z_axis_nuni.GetNbins()
    print(f"For uni: num_x_bins: {num_x_bins_uni}, num_y_bins: {num_y_bins_uni}, num_z_bins: {num_z_bins_uni}")
    print(f"For nuni: num_x_bins: {num_x_bins_nuni}, num_y_bins: {num_y_bins_nuni}, num_z_bins: {num_z_bins_nuni}")

    bin_contents_uni = {}
    bin_contents_nuni = {}

    #update dicts
    for global_bin_index in range(1,20000):
        #uni
        update_dict(bin_contents_uni, THN_SPARSE_UNI, int(global_bin_index), num_z_bins_uni)

        #nuni
        update_dict(bin_contents_nuni, THN_SPARSE_NUNI, int(global_bin_index), num_z_bins_nuni)

    #rescale
    for global_bin_index in range(1,20000):
        rescale(bin_contents_uni, bin_contents_nuni, THN_SPARSE_UNI, global_bin_index)

    ROOT_FILE_WEIGHTED.cd()
    THN_SPARSE_UNI.Write()
    ROOT_FILE_WEIGHTED.Close()
    ROOT_FILE.Close()



sum_thn_sparse_bins()

