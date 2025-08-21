##########
ci_lsstcam
##########

Description
===========

``ci_lsstcam`` provides test scripts to run the LSST Science
Pipelines on LSSTCam data.  As of Aug 20 2025, this package only runs at the
USDF where the test data is available at `/sdf/group/rubin/shared/data/test_data`. Work is underway to enable running on Jenkins.

Test Data
=========

``ci_lsstcam`` requires access to the test data in the ``testdata_ci_lsstcam_m49`` and ``testdata_ci_imsim`` directories (as the source of the pretrained models collection) at the USDF.


Running Tests
=============

To run this package at the USDF, follow these steps:

1) Clone this package, `ci_builder <https://github.com/lsst-dm/ci_builder>`_, and
`ci_lsstcam <https://github.com/lsst/ci_lsstcam>`_.
2) ``setup -r ci_builder``
3) ``setup -kr ci_lsstcam``
4) From the root of the ``ci_lsstcam`` directory run ``bin/rewrite.sh`` to rewrite python shebang lines.
5) Run ``bin/ci_lsstcam_run.py``. See available options with ``--help``, as steps may be run individually.

To cleanup after a run, use either ``bin/ci_lsstcam_run.py --clean`` or ``rm -rf DATA/``.

Note that there are 20 detector visits across 4 (ugri) bands and 1 patch in
`testdata_ci_lsstcam`. Thus, running with
up to `-j 20` will speed up visit-level processing. Single-band coadd-level
processing will benefit from up to `-j 4`.
