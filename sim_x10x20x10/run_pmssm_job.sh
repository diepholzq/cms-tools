#!/bin/bash

shopt -s nullglob

# necessary for running cmsenv
shopt -s expand_aliases

# CMS ENV
cd /afs/desy.de/user/d/diepholq/CMSSW_13_3_3/src

export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh

cmsenv

#library path
. "$CMSSW_BASE/src/cms-tools/lib/def.sh"
# export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$CMSSW_BASE/src/cms-tools/lib/classes"
# export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/nfs/dust/cms/user/beinsam/NaturalSusy/CMSSW_11_3_1/src/cms-tools/lib/classes"
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$CMSSW_BASE/src/cms-tools/lib/classes"
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/nfs/dust/cms/user/beinsam/NaturalSusy/CMSSW_11_3_1/src/cms-tools/lib/classes"

python3 /afs/desy.de/user/d/diepholq/CMSSW_13_3_3/src/cms-tools/analysis/scripts/create_pmssm_hists.py -o pmssm_scan_PMSSM_set_1_prompt_1_TuneCP2_13TeV-pythia8.root