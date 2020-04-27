#!/bin/bash
BASE_PATH=$(dirname "${BASH_SOURCE}")
BASE_PATH=$(cd "${BASE_PATH}"; pwd)

# source ISCE env
export GMT_HOME=/usr/local/gmt
export ARIAMH_HOME=$HOME/ariamh
source $ARIAMH_HOME/isce.sh
export UTILS_HOME=$ARIAMH_HOME/utils

#export LD_LIBRARY_PATH=/usr/local/gdal/lib:$LD_LIBRARY_PATH
#export GDAL_DATA=/usr/local/gdal/share/gdal

export PYTHONPATH=.:$ISCE_HOME/applications:$ISCE_HOME/components:$BASE_PATH:$ARIAMH_HOME:$ARIAMH_HOME/slc:$TROPMAP_HOME:$UTILS_HOME:$PYTHONPATH
export PATH=$ISCE_HOME/applications:$ISCE_HOME/bin:/usr/local/gdal/bin:$ISCE_HOME/bin:/opt/conda/bin/:/opt/conda/pkgs/libgdal-2.3.2-h9d4a965_0/bin:$PATH
export PATH=$BASE_PATH:$GMT_HOME/bin:$PATH
echo $PYTHONPATH
# source environment
source $HOME/verdi/bin/activate

echo "##########################################" 1>&2
echo -n "Running ALOS2 slc ingest : " 1>&2
date 1>&2
python3 $BASE_PATH/ingest_alos2_download_url.py > ingest_alos2_download_url.log 2>&1
STATUS=$?
echo -n "Finished running ALOS2 slc ingest: " 1>&2
date 1>&2
if [ $STATUS -ne 0 ]; then
  echo "Failed to run ALOS2 slc ingest." 1>&2
  echo "# ----- errors|exception found in log -----" >> _alt_traceback.txt && grep -i "error\|exception" ingest_alos2_download_url.log >> _alt_traceback.txt
  cat ingest_alos2_download_url.log 1>&2
  echo "{}"
  exit $STATUS
fi
