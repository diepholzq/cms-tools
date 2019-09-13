#!/usr/bin/env python

from ROOT import *
from glob import glob
from sys import exit
from array import array
import argparse
import sys

####### CMDLINE ARGUMENTS #########

parser = argparse.ArgumentParser(description='Run TMVA.')
parser.add_argument('-i', '--input', nargs='*', help='Signal Files', required=True)
parser.add_argument('-o', '--output_file', nargs=1, help='Output Filename', required=True)
parser.add_argument('-bg', '--bg', nargs=1, help='Input Background Directory', required=False)
parser.add_argument('-nn', '--no_norm', dest='no_norm', help='No renormalization of weights', action='store_true')
parser.add_argument('-all', '--all', dest='all', help='All methods', action='store_true')
args = parser.parse_args()


input_files = args.input

output_file_name = None
if args.output_file:
    output_file_name = args.output_file[0]
else:
    output_file_name = "tmva_output.root"
bg_dir = None
if args.bg:
    bg_dir = args.bg[0]

no_norm = args.no_norm
all = args.all

print "No norm=" + str(no_norm)
print "All=" + str(all)


######## END OF CMDLINE ARGUMENTS ########

gROOT.SetBatch(1)
TMVA.Tools.Instance()
outputFile = TFile(output_file_name,'RECREATE')
factory = TMVA.Factory("TMVAClassification", outputFile,
                            ":".join([
                                "!V",
                                "!Silent",
                                "Color",
                                "DrawProgressBar",
                                "Transformations=I;D;P;G,D",
                                "AnalysisType=Classification"]
                                     ))
                                     
dataloader = TMVA.DataLoader("dataset")

bgFiles = []
bTrees = []
sFiles = []
sTrees = []

totalEvents = 0
weights = 0

for input_file in input_files:
    print "Opening File " + input_file
    fsignal = TFile(input_file, "update")
    sTree = fsignal.Get("tEvent")
    nEvents = sTree.GetEntries()
    if nEvents == 0:
        print "Emtpy. Skipping"
        continue
    totalEvents += nEvents
    sTree.GetEntry(0)
    weight = sTree.Weight
    weights += weight * nEvents
    print "nEvents=" + str(nEvents) + " weight=" + str(weight)
    sFiles.append(fsignal)
    sTrees.append(sTree)

signalWeight = weights / totalEvents
print "Average weight=" + str(signalWeight)

for sTree in sTrees:
    dataloader.AddSignalTree(sTree, signalWeight);

dataloader.SetBackgroundWeightExpression("Weight")
bFileNames =  glob(bg_dir + "/*");
for f in bFileNames:
    bFile = TFile(f, "update")
    bgFiles.append(bFile)
    bTree = bFile.Get("tEvent")
    bTrees.append(bTree)
    dataloader.AddBackgroundTree(bTree, 1)

# Variables
dataloader.AddVariable('univBDT', 'F')
dataloader.AddVariable('trackBDT', 'F')
#dataloader.AddVariable('dileptonPt', 'F')
dataloader.AddVariable('deltaPhi', 'F')
dataloader.AddVariable('deltaEta', 'F')
dataloader.AddVariable('deltaR', 'F')
#dataloader.AddVariable('pt3', 'F')
#dataloader.AddVariable('mtautau', 'F')
#dataloader.AddVariable('mt1', 'F')
dataloader.AddVariable('mt2', 'F')
dataloader.AddVariable('DeltaEtaLeadingJetDilepton', 'F')
dataloader.AddVariable('DeltaPhiLeadingJetDilepton', 'F')
#dataloader.AddVariable('dilepHt', 'F')
#dataloader.AddVariable('l1.Pt()', 'F')
#dataloader.AddVariable('l2.Pt()', 'F')
dataloader.AddVariable('l1.Eta()', 'F')
dataloader.AddVariable('l2.Eta()', 'F')
dataloader.AddVariable('l1.Phi()', 'F')
dataloader.AddVariable('l2.Phi()', 'F')

# Spectators
dataloader.AddSpectator('invMass','F')

# cuts defining the signal and background sample
preselectionCut = TCut("")
if no_norm:
	dataloader.PrepareTrainingAndTestTree(preselectionCut, "SplitMode=random:!V:NormMode=None")
else:
	dataloader.PrepareTrainingAndTestTree(preselectionCut, "SplitMode=random:!V")
factory.BookMethod(dataloader, TMVA.Types.kBDT, "BDT", "NTrees=200:MaxDepth=4")
if all:
	factory.BookMethod(dataloader, TMVA.Types.kMLP, "MLP", "H:!V:NeuronType=tanh:VarTransform=N:NCycles=600:HiddenLayers=N+5:TestRate=5:!UseRegulator" )
#factory.BookMethod(dataloader, TMVA.Types.kMLP, "MLP_ANN", "" );
factory.TrainAllMethods()
factory.TestAllMethods()
factory.EvaluateAllMethods()
outputFile.Close()





