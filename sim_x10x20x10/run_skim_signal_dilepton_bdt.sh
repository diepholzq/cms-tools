#!/bin/bash

. "$CMSSW_BASE/src/cms-tools/lib/def.sh"

shopt -s nullglob
shopt -s expand_aliases

#---------- GET OPTIONS ------------
POSITIONAL=()
while [[ $# -gt 0 ]]
do
    key="$1"

    case $key in
        -sc)
        SC=true
        POSITIONAL+=("$1")
        shift
        ;;
        --sam)
        SAM=true
        POSITIONAL+=("$1")
        shift
        ;;
        --phase1)
        PHASE1=true
        POSITIONAL+=("$1")
        shift
        ;;
        --onphase0 )
        ONPHASE0=true
        POSITIONAL+=("$1")
        shift
        ;;
        --phase1_2018)
        PHASE1_2018=true
        POSITIONAL+=("$1")
        shift
        ;;
        --pmssm_skims)
        PMSSM_SKIMS=true
        POSITIONAL+=("$1")
        shift
        ;;
        *)    # unknown option
        POSITIONAL+=("$1") # save it in an array for later
        shift # past argument
        ;;
    esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters
#---------- END OPTIONS ------------

# CMS ENV
cd $CMS_WD
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/afs/desy.de/user/d/diepholq/CMSSW_13_3_3/lib/el9_amd64_gcc12
. /etc/profile.d/modules.sh
module use -a /afs/desy.de/group/cms/modulefiles/
module load cmssw/el9_amd64_gcc11
cmsenv


INPUT_DIR=$SKIM_SIG_OUTPUT_DIR
BDT_DIR=$OUTPUT_WD/cut_optimisation/tmva/dilepton_bdt

if [ -n "$SAM" ]; then
    echo "GOT SAM"
    echo "HERE: $@"
    INPUT_DIR=$SKIM_SIG_SAM_OUTPUT_DIR
    if [ -n "$ONPHASE0" ]; then
        BDT_DIR=$OUTPUT_WD/cut_optimisation/tmva/dilepton_bdt_phase1
    fi
    #OUTPUT_DIR=$SKIM_SAM_SIG_BDT_OUTPUT_DIR
elif [ -n "$SC" ]; then
    echo "GOT SC"
    echo "HERE: $@"
    OUTPUT_DIR=$SKIM_SIG_DILEPTON_BDT_SC_OUTPUT_DIR
    INPUT_DIR=$SKIM_SIG_BDT_SC_OUTPUT_DIR
elif [ -n "$PHASE1" ]; then
    echo "GOT PHASE1"
    echo "HERE: $@"
    INPUT_DIR=$SKIM_SIG_PHASE1_OUTPUT_DIR
    BDT_DIR=$OUTPUT_WD/cut_optimisation/tmva/dilepton_bdt_phase1
elif [ -n "$PHASE1_2018" ]; then
    echo "GOT PHASE1_2018"
    echo "HERE: $@"
    INPUT_DIR=$SKIM_SIG_PHASE1_2018_OUTPUT_DIR
    BDT_DIR=$OUTPUT_WD/cut_optimisation/tmva/dilepton_bdt_phase1
elif [ -n "$ONPHASE0" ]; then
    echo "GOT ONPHASE0"
    BDT_DIR=$OUTPUT_WD/cut_optimisation/tmva/dilepton_bdt_phase1
elif [ -n "$PMSSM_SKIMS" ]; then
    echo "GOT PMSSM_SKIMS"
    INPUT_DIR=$SKIM_SIG_PMSSM_OUTPUT_DIR
    BDT_DIR="/afs/desy.de/user/n/nissanuv/nfs/x1x2x1/cut_optimisation/tmva/dilepton_bdt_phase1"
fi




timestamp=$(date +%Y%m%d_%H%M%S%N)
output_file="${WORK_DIR}/condor_submut.${timestamp}"
echo "output file: $output_file"

#request_memory = 16 GB
#+RequestRuntime = 86400

cat << EOM > $output_file
universe = vanilla
should_transfer_files = IF_NEEDED
executable = /bin/bash
notification = Never
+RequestRuntime = 86400
EOM

if [ -n "$SAM" ] || [ -n "$PHASE1" ] || [ -n "$PHASE1_2018" ]; then
    FILES=${INPUT_DIR}/sum/*
else
    echo HERE
    FILES=${INPUT_DIR}/single/*
fi
#FILES=(mChipm160GeV_dm0p44GeV.root mChipm140GeV_dm4p28GeV.root)

#FILES=(higgsino_mu100_dm0p18Chi20Chipm.root)
#FILES=(higgsino_mu115_dm9p82Chi20Chipm.root higgsino_mu115_dm7p44Chi20Chipm.root higgsino_mu130_dm7p49Chi20Chipm.root higgsino_mu130_dm9p91Chi20Chipm.root)

#FILES=(higgsino_mu115_dm4p31Chi20Chipm.root higgsino_mu100_dm4p30Chi20Chipm.root higgsino_mu130_dm5p68Chi20Chipm.root higgsino_mu130_dm4p32Chi20Chipm.root higgsino_mu100_dm12p84Chi20Chipm.root higgsino_mu115_dm13p01Chi20Chipm.root higgsino_mu100_dm7p39Chi20Chipm.root)

for sim in ${FILES[@]}; do
    #sim=${INPUT_DIR}/sum/$sim
    # if [ -n "$SAM" ]; then
#         filename=`echo $(basename $sim .root)`
#     else
#         filename=`echo $(basename $sim .root) | awk -F"_" '{print $1"_"$2"_"$3}'`
#     fi
    
    filename=`echo $(basename $sim .root)`
    echo $filename
    tb=all
    echo "Will run:"
    #echo $CONDOR_WRAPPER $SCRIPTS_WD/skimmer_x1x2x1_univ_bdt_track_bdt.py -i $sim -o ${OUTPUT_DIR}/single/${filename}.root -tb $LEPTON_TRACK_SPLIT_DIR/cut_optimisation/tmva/$tb  -ub $OUTPUT_WD/cut_optimisation/tmva/total_bdt $@
    echo $CONDOR_WRAPPER $SCRIPTS_WD/skimmer_x1x2x1_dilepton_bdt.py -i $sim -bdt $BDT_DIR $@
cat << EOM >> $output_file
arguments = $CONDOR_WRAPPER $SCRIPTS_WD/skimmer_x1x2x1_dilepton_bdt.py -i $sim -bdt $BDT_DIR $@
error = ${INPUT_DIR}/stderr/${filename}_dilepton_bdt.err
output = ${INPUT_DIR}/stdout/${filename}_dilepton_bdt.output
Queue
EOM
done

echo $output_file
# condor_submit $output_file
#rm $output_file
