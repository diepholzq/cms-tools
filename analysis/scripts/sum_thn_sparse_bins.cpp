#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <cmath>
#include <cstdlib>
#include <TFile.h>
#include <THnSparse.h>
#include <TROOT.h>
#include <TStyle.h>
#include <TSystem.h>
#include <TAxis.h>

void sum_thn_sparse_bins(const std::string& file_name, bool is_test) {
    // Open the ROOT file
    TFile *root_file = TFile::Open(file_name.c_str(), "READ");
    TFile *root_file_weighted = TFile::Open((file_name.substr(0, file_name.find(".root")) + "_weighted.root").c_str(), "RECREATE");

    // Get the THnSparse object
    THnSparseF *thn_sparse = (THnSparseF*)root_file->Get("pMSSM Scan uni");
    THnSparseF *thn_sparse_nuni = (THnSparseF*)root_file->Get("pMSSM Scan nuni");

    if (!thn_sparse) {
        std::cerr << "Error: THnSparse object 'pMSSM Scan uni' not found in the file." << std::endl;
        return;
    }

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
        if (time2break) break;

        for (int bin_y = 1; bin_y <= num_y_bins; ++bin_y) {
            double total_sum_uni = 0;
            double total_sum_nuni = 0;

            std::vector<int> rescalable_bins(num_z_bins, -1);

            // Uni
            for (int bin_z = 1; bin_z <= num_z_bins; ++bin_z) {
                int global_bin_index = thn_sparse->GetBin(bin_x, bin_y, bin_z);
                double bin_content = thn_sparse->GetBinContent(global_bin_index);

                if (bin_content > 0) {
                    std::cout << "bin_content: " << bin_content << " for global bin index " << global_bin_index << " UNI" << std::endl;
                    rescalable_bins[bin_z - 1] = bin_z;
                }
                total_sum_uni += bin_content;
            }
            if (total_sum_uni > 0) std::cout << "total sum uni: " << total_sum_uni << std::endl;

            // Nuni
            for (int bin_z = 1; bin_z <= num_z_bins_nuni; ++bin_z) {
                int global_bin_index_nuni = thn_sparse_nuni->GetBin(bin_x, bin_y, bin_z);
                double bin_content_nuni = thn_sparse_nuni->GetBinContent(global_bin_index_nuni);

                if (bin_content_nuni > 0) std::cout << "bin_content: " << bin_content_nuni << " for global bin index " << global_bin_index_nuni << " NUNI" << std::endl;
                total_sum_nuni += bin_content_nuni;
            }
            if (total_sum_nuni > 0) std::cout << "total sum nuni: " << total_sum_nuni << std::endl;

            // Rescale
            for (auto& bin_idx : rescalable_bins) {
                if (bin_idx < 0) continue;

                int global_bin_index = thn_sparse->GetBin(bin_x, bin_y, bin_idx);
                double bin_content = thn_sparse->GetBinContent(global_bin_index);
                if (total_sum_uni > 0) {
                    thn_sparse->SetBinContent(global_bin_index, bin_content * total_sum_nuni / total_sum_uni);
                }
                if (bin_content > 0) std::cout << "bin_content: " << bin_content << " for global bin index " << global_bin_index << " RESCALE" << std::endl;
            }

            if (is_test && total_sum_nuni != 0) {
                std::cout << "Just normalized with total integral: " << total_sum_nuni << std::endl;
                time2break = true;
                break;
            }
        }
    }

    root_file_weighted->cd();
    thn_sparse->Write();
    root_file_weighted->Close();
    root_file->Close();
}

int main(int argc, char* argv[]) {
    gROOT->SetBatch(true);
    gStyle->SetOptStat(0);

    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " -i input_file [--is_test]" << std::endl;
        return 1;
    }

    std::string input_file;
    bool is_test = false;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "-i" && i + 1 < argc) {
            input_file = argv[++i];
        } else if (arg == "--is_test") {
            is_test = true;
        }
    }

    if (input_file.empty()) {
        std::cerr << "Error: Input file is required" << std::endl;
        return 1;
    }

    if (!is_test) {
        std::cout << "THIS IS NOT A DRILL" << std::endl;
    }

    sum_thn_sparse_bins(input_file, is_test);

    return 0;
}
