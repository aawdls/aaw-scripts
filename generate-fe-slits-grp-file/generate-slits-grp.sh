#!/bin/bash
# Script to generate an archiver .grp file for the front-end slits for a beamline
# 
# Debug: 
# set -ex
if [[ $# != 1 || $1 == '-h' || $1 == '--help' ]]; then
    echo -e "Script to generate an archiver .grp file for the front-end slits for a beamline"
    echo -e "Usage: $0 <beamline>"
    echo -e "e.g. $0 13I"
    exit 0
fi
OUTFILE=output/FE$1_slits.grp
echo "Generating grp file for FE$1-AL-SLITS-01 in $OUTFILE"

sed "s/FE{bl}-AL-SLITS-01/FE$1-AL-SLITS-01/" <slits.grp.src >$OUTFILE
exit $?