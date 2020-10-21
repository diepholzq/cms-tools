#!/usr/bin/env python

from ROOT import *
from glob import glob
from sys import exit
import argparse
import sys
import numpy as np
import os
import xml.etree.ElementTree as ET

sys.path.append(os.path.expandvars("$CMSSW_BASE/src/cms-tools"))
sys.path.append(os.path.expandvars("$CMSSW_BASE/src/cms-tools/lib/classes"))
from lib import analysis_ntuples
from lib import analysis_tools
from lib import utils
from lib import cut_optimisation

gROOT.SetBatch(True)
gStyle.SetOptStat(0)

gSystem.Load('LumiSectMap_C')
from ROOT import LumiSectMap

####### CMDLINE ARGUMENTS #########

parser = argparse.ArgumentParser(description='Create skims for x1x2x1 process with BDTs.')
parser.add_argument('-i', '--input_file', nargs=1, help='Input Filename', required=True)
parser.add_argument('-bdt', '--bdt', nargs=1, help='Dilepton BDT Folder', required=True)

parser.add_argument('-s', '--signal', dest='signal', help='Signal', action='store_true')
parser.add_argument('-bg', '--background', dest='bg', help='Background', action='store_true')
parser.add_argument('-data', '--data', dest='data', help='Data', action='store_true')
parser.add_argument('-dy', '--dy', dest='dy', help='Drell-Yan', action='store_true')
parser.add_argument('-sc', '--same_charge', dest='sc', help='Same Charge', action='store_true')
parser.add_argument('-sam', '--sam', dest='sam', help='Sam Samples', action='store_true')
args = parser.parse_args()

print args

signal = args.signal
bg = args.bg

input_file = None
if args.input_file:
    input_file = args.input_file[0].strip()

if (bg and signal) or not (bg or signal):
    signal = True
    bg = False

bdt = None
if args.bdt:
    bdt = args.bdt[0]
    
data = args.data

######## END OF CMDLINE ARGUMENTS ########

vars = {}
bdt_vars_maps = {}
bdt_specs_maps = {}
bdt_readers = {}
branches = {}

def main():
    
    iFile = TFile(input_file, "update")
    #hHt = iFile.Get('hHt')
    tree = iFile.Get('tEvent')
    nentries = tree.GetEntriesFast()
    
    # CREATE VARS, BRANCHES, AND BDT READERS
              
    for iso in utils.leptonIsolationList:
        for cat in utils.leptonIsolationCategories:
            ptRanges = [""]
            if iso == "CorrJetIso":
                ptRanges = utils.leptonCorrJetIsoPtRange
            for ptRange in ptRanges:
                for DTypeObs in utils.commonPostBdtObservablesDTypesList:
                    for prefix in ["", "exTrack_"]:
                        vars[prefix + DTypeObs + iso + str(ptRange) + cat] = np.zeros(1,dtype=utils.commonPostBdtObservablesDTypesList[DTypeObs])
                        if tree.GetBranchStatus(prefix + DTypeObs + iso + str(ptRange) + cat):
                            print "Reseting branch", prefix + DTypeObs + iso + str(ptRange) + cat
                            branches[prefix + DTypeObs + iso + str(ptRange) + cat] = tree.GetBranch(prefix + DTypeObs + iso + str(ptRange) + cat)
                            branches[prefix + DTypeObs + iso + str(ptRange) + cat].Reset()
                            tree.SetBranchAddress(prefix + DTypeObs + iso + str(ptRange) + cat, vars[prefix + DTypeObs + iso + str(ptRange) + cat])
                        else:
                            print "Branching", prefix + DTypeObs + iso + str(ptRange) + cat
                            branches[prefix + DTypeObs + iso + str(ptRange) + cat] = tree.Branch(prefix + DTypeObs + iso + str(ptRange) + cat, vars[prefix + DTypeObs + iso + str(ptRange) + cat], prefix + DTypeObs + iso + str(ptRange) + cat + "/" + utils.typeTranslation[utils.commonPostBdtObservablesDTypesList[DTypeObs]])
                            tree.SetBranchAddress(prefix + DTypeObs + iso + str(ptRange) + cat, vars[prefix + DTypeObs + iso + str(ptRange) + cat])
                                
                for DTypeObs in utils.exclusiveTrackPostBdtObservablesDTypesList:
                    vars[DTypeObs + iso + str(ptRange) + cat] = np.zeros(1,dtype=utils.exclusiveTrackPostBdtObservablesDTypesList[DTypeObs])
                    if tree.GetBranchStatus(DTypeObs + iso + str(ptRange) + cat):
                        print "Reseting branch", DTypeObs + iso + str(ptRange) + cat
                        branches[DTypeObs + iso + str(ptRange) + cat] = tree.GetBranch(DTypeObs + iso + str(ptRange) + cat)
                        branches[DTypeObs + iso + str(ptRange) + cat].Reset()
                        tree.SetBranchAddress(DTypeObs + iso + str(ptRange) + cat, vars[DTypeObs + iso + str(ptRange) + cat])
                    else:
                        print "Branching", DTypeObs + iso + str(ptRange) + cat
                        branches[DTypeObs + iso + str(ptRange) + cat] = tree.Branch(DTypeObs + iso + str(ptRange) + cat, vars[DTypeObs + iso + str(ptRange) + cat], DTypeObs + iso + str(ptRange) + cat + "/" + utils.typeTranslation[utils.exclusiveTrackPostBdtObservablesDTypesList[DTypeObs]])
                        tree.SetBranchAddress(DTypeObs + iso + str(ptRange) + cat, vars[DTypeObs + iso + str(ptRange) + cat])
                        
                for prefix in ["reco", "exTrack"]:
                    for lep in ["Muons", "Electrons"]:
                        dirname = prefix + lep + iso + cat + str(ptRange)
                        name = prefix + lep + iso + str(ptRange) + cat
                        bdt_weights = bdt + "/" + dirname + "/dataset/weights/TMVAClassification_" + name + ".weights.xml"
                        bdt_vars = cut_optimisation.getVariablesFromXMLWeightsFile(bdt_weights)
                        bdt_vars_map = cut_optimisation.getVariablesMemMap(bdt_vars)
                        bdt_specs = cut_optimisation.getSpecSpectatorFromXMLWeightsFile(bdt_weights)
                        bdt_specs_map = cut_optimisation.getSpectatorsMemMap(bdt_specs)
                        bdt_reader = cut_optimisation.prepareReader(bdt_weights, bdt_vars, bdt_vars_map, bdt_specs, bdt_specs_map)

                        bdt_vars_maps[prefix + lep + iso + str(ptRange) + cat] = bdt_vars_map
                        bdt_specs_maps[prefix + lep + iso + str(ptRange) + cat] = bdt_specs_map
                        bdt_readers[prefix + lep + iso + str(ptRange) + cat] = bdt_reader

    print 'Analysing', nentries, "entries"
    
    iFile.cd()

    for ientry in range(nentries):
        if ientry % 1000 == 0:
            print "Processing " + str(ientry) + " out of " + str(nentries)
        tree.GetEntry(ientry)
        
        for iso in utils.leptonIsolationList:
            for cat in utils.leptonIsolationCategories:
                ptRanges = [""]
                if iso == "CorrJetIso":
                    ptRanges = utils.leptonCorrJetIsoPtRange
                for ptRange in ptRanges:
                    for prefix in ["reco", "exTrack"]:
                        prefixVars = ""
                        if prefix == "exTrack":
                            prefixVars = "exTrack_"
                        eventPassed = False
                        leptonFlavour = ""
                        if prefix == "reco":
                            if eval("tree.twoLeptons"  + iso + str(ptRange) + cat) == 1 and tree.BTagsDeepMedium == 0 and eval("tree.leptons"  + iso + str(ptRange) + cat).size() == 2:
                                eventPassed = True
                                leptonFlavour = eval("tree.leptonFlavour"  + iso + str(ptRange) + cat)
                        elif eval("tree.exclusiveTrack"  + iso + str(ptRange) + cat) == 1 and tree.BTagsDeepMedium == 0:
                            eventPassed = True
                            leptonFlavour = eval("tree.exclusiveTrackLeptonFlavour"  + iso + str(ptRange) + cat)
                        if eventPassed:
                            leptonFlavour = str(leptonFlavour)
                            name = prefix + leptonFlavour + iso + str(ptRange) + cat
                            #print bdt_vars_maps[prefix + iso + str(ptRange) + cat]
                            #print name, eval("tree.twoLeptons"  + iso + str(ptRange) + cat), eval("tree.exclusiveTrack"  + iso + str(ptRange) + cat)
                            for k, v in bdt_vars_maps[prefix + leptonFlavour + iso + str(ptRange) + cat].items():
                                #print k, v
                                try:
                                    v[0] = eval("tree." + k)
                                except:
                                    print ientry, k, name, eval("tree.twoLeptons"  + iso + str(ptRange) + cat), eval("tree.exclusiveTrack"  + iso + str(ptRange) + cat)
                                    print "ERROR!!! GIVING UP..."
                                    exit(0)
                            for k, v in bdt_specs_maps[prefix + leptonFlavour + iso + str(ptRange) + cat].items():
                                v[0] = eval("tree." + k)
                            vars[prefixVars + "dilepBDT" + iso + str(ptRange) + cat][0] = bdt_readers[prefix + leptonFlavour+ iso + str(ptRange) + cat].EvaluateMVA("BDT")
                        else:
                            vars[prefixVars + "dilepBDT" + iso + str(ptRange) + cat][0] = -1
                        
        # Selection
        #if dilep_tmva_value < -0.3 or tree.Met < 200 or tree.univBDT < -0.4 or tree.tracks[0].Pt() < 3 or tree.tracks[0].Pt() > 15 or tree.tracks_dzVtx[0] > 0.1 or tree.tracks_dxyVtx[0] > 0.1 or abs(tree.tracks[0].Eta()) > 2.4:
        #if dilep_tmva_value < -0.3 or tree.Met < 200 or tree.univBDT < -0.4 or tree.tracks[0].Pt() < 3 or tree.tracks[0].Pt() > 15 or abs(tree.tracks[0].Eta()) > 2.4:
        #    continue
        #if tree.Mht < 200:
        #    continue
                    
                    
                        if eval("tree.exclusiveTrack"  + iso + str(ptRange) + cat) == 1:
                            min, minCan = analysis_ntuples.minDeltaRGenParticles(eval("tree.lepton" + iso + str(ptRange) + cat), gens, tree.GenParticles)
                            #print min, m inCan
                            pdgId = tree.GenParticles_ParentId[minCan]
                            if min > 0.05:
                             #   print "BAD GEN LEPTON!!!"
                                pdgId = 0
                            #else:
                            #    print "GOOD LEPTON ", pdgId
                            vars["leptonParentPdgId" + iso + str(ptRange) + cat][0] = pdgId
                            min, minCan = analysis_ntuples.minDeltaRGenParticles(eval("tree.track"+ iso + str(ptRange) + cat), gens, tree.GenParticles)
                            pdgId = tree.GenParticles_ParentId[minCan]
                            if min > 0.05:
                                #print "BAD GEN TRACK!!!"
                                pdgId = 0
                            #else:
                            #    print "GOOD TRACK ", pdgId
                            vars["trackParentPdgId" + iso + str(ptRange) + cat][0] = pdgId
                        else:
                            vars["leptonParentPdgId" + iso + str(ptRange) + cat][0] = -1
                            vars["trackParentPdgId" + iso + str(ptRange) + cat][0] = -1
                            
                    for DTypeObs in utils.commonPostBdtObservablesDTypesList:
                        for prefix in ["", "exTrack_"]:
                            branches[prefix + DTypeObs + iso + str(ptRange) + cat].Fill()
                    if bg:
                        for DTypeObs in utils.dileptonBgPostBdtObservablesDTypesList:
                            branches[DTypeObs + iso + str(ptRange) + cat].Fill()
                    for DTypeObs in utils.exclusiveTrackPostBdtObservablesDTypesList:
                        branches[DTypeObs + iso + str(ptRange) + cat].Fill()
            
    tree.Write("tEvent",TObject.kOverwrite)
        
    print "DONE SKIMMING"
    iFile.Close()

main()