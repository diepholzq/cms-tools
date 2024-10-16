#include <iostream>
#include <THnSparse.h>
#include <TFile.h>
#include <TROOT.h>
#include <TStyle.h>
#include <TSystem.h>
#include <TAxis.h>

void sum_thn_sparse_bins(const std::string& file_name) {
    TFile *root_file = TFile::Open(file_name.c_str(), "READ");
    TFile *root_file_weighted = TFile::Open((file_name.substr(0, file_name.find(".root")) + "_weighted.root").c_str(), "RECREATE");

    THnSparseF *thn_sparse = (THnSparseF*)root_file->Get("pMSSM Scan uni");
    THnSparseF *thn_sparse_nuni = (THnSparseF*)root_file->Get("pMSSM Scan nuni");

    if (!thn_sparse) {
        std::cerr << "Error: THnSparse object 'pMSSM Scan uni' not found in the file." << std::endl;
        return;
    }

    int n_dims = thn_sparse->GetNdimensions();
    int *bin_indices = new int[n_dims];
    int *bin_indices_nuni = new int[n_dims];

    int num_x_bins = thn_sparse->GetAxis(0)->GetNbins();
    int num_y_bins = thn_sparse->GetAxis(1)->GetNbins();
    int num_z_bins = thn_sparse->GetAxis(2)->GetNbins();

    int num_x_bins_nuni = thn_sparse_nuni->GetAxis(0)->GetNbins();
    int num_y_bins_nuni = thn_sparse_nuni->GetAxis(1)->GetNbins();
    int num_z_bins_nuni = thn_sparse_nuni->GetAxis(2)->GetNbins();

    std::cout << "For uni: num_x_bins: " << num_x_bins << ", num_y_bins: " << num_y_bins << ", num_z_bins: " << num_z_bins << std::endl;
    std::cout << "For nuni: num_x_bins: " << num_x_bins_nuni << ", num_y_bins: " << num_y_bins_nuni << ", num_z_bins: " << num_z_bins_nuni << std::endl;

    bool time2break = false;


    for (int bin_x = 1; bin_x <= num_x_bins; ++bin_x) {
	std::cout<<"now processing x bin "<<bin_x<<" of "<<num_x_bins<<std::endl;
        // if (time2break) break;
        
        bin_indices[0] = bin_x;
        bin_indices_nuni[0] = bin_x;

        for (int bin_y = 1; bin_y <= num_y_bins; ++bin_y) {
            bin_indices[1] = bin_y;
            bin_indices_nuni[1] = bin_y;

            double total_sum_uni = 0;
            double total_sum_nuni = 0;

            int *rescalable_bins = new int[num_z_bins];
            for (int i = 0; i < num_z_bins; ++i) {
                rescalable_bins[i] = -1;
            }

            for (int bin_z = 1; bin_z <= num_z_bins; ++bin_z) {
                bin_indices[2] = bin_z;

                int global_bin_index = thn_sparse->GetBin(bin_indices);

                if (global_bin_index < 0) {
                    std::cerr << "Error: Invalid global bin index for UNI at (x, y, z) = (" 
                            << bin_x << ", " << bin_y << ", " << bin_z << ")" << std::endl;
                    continue; // Skip this iteration
                }


                double bin_content = thn_sparse->GetBinContent(global_bin_index);
                if (std::isnan(bin_content) || std::isinf(bin_content)) {
                    std::cerr << "Error: Invalid bin content for global bin index " 
                            << global_bin_index << " (content: " << bin_content << ")" << std::endl;
                    continue; // Skip this iteration
                }
                if (bin_content > 0) {
                    // std::cout << "bin_content: " << bin_content << " for global bin index " << global_bin_index << " UNI" << std::endl;
                    rescalable_bins[bin_z - 1] = bin_z;
                }
                total_sum_uni += bin_content;
            }
            if (total_sum_uni > 0) std::cout << "total sum uni: " << total_sum_uni << std::endl;

            for (int bin_z = 1; bin_z <= num_z_bins_nuni; ++bin_z) {
                bin_indices_nuni[2] = bin_z;

                int global_bin_index_nuni = thn_sparse_nuni->GetBin(bin_indices_nuni);
                double bin_content_nuni = thn_sparse_nuni->GetBinContent(global_bin_index_nuni);

                // if (bin_content_nuni > 0) std::cout << "bin_content: " << bin_content_nuni << " for global bin index " << global_bin_index_nuni << " NUNI" << std::endl;
                total_sum_nuni += bin_content_nuni;
            }
            if (total_sum_nuni > 0) std::cout << "total sum nuni: " << total_sum_nuni << std::endl;

            for (int i = 0; i < num_z_bins; ++i) {
                int bin_idx = rescalable_bins[i];
                if (bin_idx < 0) continue;

                bin_indices[2] = bin_idx;
                int global_bin_index = thn_sparse->GetBin(bin_indices);
                double bin_content = thn_sparse->GetBinContent(global_bin_index);
                if (total_sum_uni > 0) {
                    thn_sparse->SetBinContent(global_bin_index, bin_content * total_sum_nuni / total_sum_uni);
                    std::cout << "global_bin_index " << global_bin_index << ", new content = " << bin_content * total_sum_nuni / total_sum_uni << std::endl;
                }
                // if (bin_content > 0) std::cout << "bin_content: " << bin_content << " for global bin index " << global_bin_index << " RESCALE" << std::endl;
            }

            delete[] rescalable_bins;

        }
    }

    root_file_weighted->cd();
    thn_sparse->Write();
    root_file_weighted->Close();
    root_file->Close();

    delete[] bin_indices;
    delete[] bin_indices_nuni;
}

void run_macro(const std::string& input_file) {
    gROOT->SetBatch(true);
    gStyle->SetOptStat(0);

    sum_thn_sparse_bins(input_file);
}
