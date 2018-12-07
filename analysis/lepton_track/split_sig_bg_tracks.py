#!/usr/bin/env python

from ROOT import *
from glob import glob
from math import *
from sys import exit
from array import array
import argparse
import sys
import numpy as np
import os

sys.path.append("/afs/desy.de/user/n/nissanuv/cms-tools")
from lib import utils
from lib import analysis_ntuples
from lib import analysis_tools

gROOT.SetBatch(1)

####### CMDLINE ARGUMENTS #########

parser = argparse.ArgumentParser(description='Split tracks into signal and background trees.')
parser.add_argument('-i', '--input_file', nargs=1, help='Input Filename', required=True)
parser.add_argument('-o', '--output_file', nargs=1, help='Output Filename', required=False)
args = parser.parse_args()

input_file = None
output_file = None
if args.input_file:
	input_file = args.input_file[0]
if args.output_file:
	output_file = args.output_file[0]
	
######## END OF CMDLINE ARGUMENTS ########

def main():

	tracksVars = (
		{"name":"dxyVtx", "type":"D"},
		{"name":"dzVtx", "type":"D"},
		{"name":"chi2perNdof", "type":"D"},
		{"name":"trkMiniRelIso", "type":"D"},
		{"name":"trkRelIso", "type":"D"},
	)
	
	otherVars = (
		{"name":"track", "type2":'TLorentzVector'},
		{"name":"deltaEtaLL", "type":"D"},
		{"name":"deltaEtaLJ", "type":"D"},
		{"name":"deltaRLL", "type":"D"},
		{"name":"deltaRLJ", "type":"D"}	
	)
	
	vars = otherVars + tracksVars
	
	varsDict = {}
	for i,v in enumerate(vars):
		varsDict[v["name"]] = i
	
	utils.addMemToTreeVarsDef(vars)
	
	tSig = TTree('tEvent','tEvent')
	utils.barchTreeFromVarsDef(tSig, vars)
	tBg = TTree('tEvent','tEvent')
	utils.barchTreeFromVarsDef(tBg, vars)
	
	c = TChain('tEvent')
	print "Going to open the file"
	print input_file
	c.Add(input_file)

	nentries = c.GetEntries()
	print 'Analysing', nentries, "entries"
	
	notCorrect = 0
	noReco = 0
	for ientry in range(nentries):
		if ientry % 5000 == 0:
			print "Processing " + str(ientry)
		c.GetEntry(ientry)
		rightProcess = analysis_ntuples.isX1X2X1Process(c)
		if not rightProcess:
			print "No"
			notCorrect += 1
			continue
		
		if len(c.Electrons) + len(c.Muons) < 1:
			#print "No reco"
			noReco += 1
			continue
		
		genZL, genNonZL = analysis_ntuples.classifyGenZLeptons(c)
		if genZL is None or len(genZL) == 0:
			#print "genZL is None"
			continue
		#if len(genNonZL) == 0:
			#print "genNonZL is None"
		
		ll = analysis_ntuples.leadingLepton(c)
		
		for ti in range(c.tracks.size()):
			if c.tracks_trkRelIso[ti] > 0.1:
				continue 

			t = c.tracks[ti]
			minZ, minCanZ = analysis_ntuples.minDeltaRGenParticles(t, genZL, c)
			minNZ, minCanNZ = analysis_ntuples.minDeltaRGenParticles(t, genNonZL, c)
			
			#if minNZ is None:
			#	print "minNZ is None for " + str(genNonZL)
				
			min = None
			if minNZ is None or minZ < minNZ:
				min = minZ
			else:
				min = minNZ
			
			result = ""
			
			if min > 0.1:
				result = "MM"
			elif minNZ is None or minZ < minNZ:
				if c.tracks_charge[ti] * c.GenParticles_PdgId[minCanZ] < 0:
					result = "Zl"
				else:
					result = "MM"
			else:
				result = "MM"
			
			vars[varsDict["track"]]["var"] = t
			for j, v in enumerate(tracksVars):
				i = len(otherVars) + j
				vars[i]["var"][0] = eval("c.tracks_" + vars[i]["name"] + "[" + str(ti) + "]")
			
			vars[varsDict["deltaEtaLL"]]["var"][0] = abs(t.Eta()-ll.Eta()) 
			vars[varsDict["deltaRLL"]]["var"][0] = abs(t.DeltaR(ll))
			vars[varsDict["deltaEtaLJ"]]["var"][0] = abs(t.Eta() - c.LeadingJet.Eta())
			vars[varsDict["deltaRLJ"]]["var"][0] = abs(t.DeltaR(c.LeadingJet))
			
			tree = None
			if result == "Zl":
				tree = tSig
				#print "Pt=" + str(vars[varsDict["track"]]["var"].Pt())
			else:
				tree = tBg
			
			tree.SetBranchAddress('track', vars[varsDict["track"]]["var"])
			tree.Fill()
	
	print "notCorrect=" + str(notCorrect)
	print "noReco=" + str(noReco)
	
	fnew = TFile(output_file + "_sig.root",'recreate')
	tSig.Write()
	fnew.Close()
	
	fnew = TFile(output_file + "_bg.root",'recreate')
	tBg.Write()
	fnew.Close()
			
main()
exit(0)


