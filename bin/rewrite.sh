# need to manually copy and update the python path
echo "#!$(command -v python)" > bin/ci_lsstcam_run.py
cat bin.src/ci_lsstcam_run.py >> bin/ci_lsstcam_run.py

# verify that the file is executable
chmod ug+x bin/ci_lsstcam_run.py
