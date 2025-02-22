# Copyright 2018-2019 Andrew Myers, Luca Fedeli, Maxence Thevenet
# Remi Lehe
#
# This file is part of WarpX.
#
# License: BSD-3-Clause-LBNL

import os

# This script modifies `WarpX-test.ini` (which is used for nightly builds)
# and creates the file `ci-test.ini` (which is used for continuous
# integration)
# The subtests that are selected are controlled by WARPX_TEST_DIM
# The architecture (CPU/GPU) is selected by WARPX_TEST_ARCH
import re

# Get relevant environment variables
arch = os.environ.get('WARPX_TEST_ARCH', 'CPU')

ci_regular_cartesian_1d = os.environ.get('WARPX_CI_REGULAR_CARTESIAN_1D') == 'TRUE'
ci_regular_cartesian_2d = os.environ.get('WARPX_CI_REGULAR_CARTESIAN_2D') == 'TRUE'
ci_regular_cartesian_3d = os.environ.get('WARPX_CI_REGULAR_CARTESIAN_3D') == 'TRUE'
ci_psatd = os.environ.get('WARPX_CI_PSATD', 'TRUE') == 'TRUE'
ci_single_precision = os.environ.get('WARPX_CI_SINGLE_PRECISION') == 'TRUE'
ci_rz_or_nompi = os.environ.get('WARPX_CI_RZ_OR_NOMPI') == 'TRUE'
ci_qed = os.environ.get('WARPX_CI_QED') == 'TRUE'
ci_eb = os.environ.get('WARPX_CI_EB') == 'TRUE'
ci_openpmd = os.environ.get('WARPX_CI_OPENPMD') == 'TRUE'
ci_ccache = os.environ.get('WARPX_CI_CCACHE') == 'TRUE'
ci_num_make_jobs = os.environ.get('WARPX_CI_NUM_MAKE_JOBS', None)

# Find the directory in which the tests should be run
current_dir = os.getcwd()
test_dir = re.sub('warpx/Regression', '', current_dir )

with open('WarpX-tests.ini') as f:
    text = f.read()

# Replace default folder name
text = re.sub('/home/regtester/AMReX_RegTesting', test_dir, text)
# Remove the web directory
text = re.sub('[\w\-\/]*/web', '', text)

# Add doComparison = 0 for each test
text = re.sub( '\[(?P<name>.*)\]\nbuildDir = ',
               '[\g<name>]\ndoComparison = 0\nbuildDir = ', text )

# Change compile options when running on GPU
if arch == 'GPU':
    text = re.sub( 'addToCompileString =',
                   'addToCompileString = USE_GPU=TRUE USE_OMP=FALSE ', text)
print('Compiling for %s' %arch)

# Extra dependencies
if ci_openpmd:
    text = re.sub('addToCompileString =',
                  'addToCompileString = USE_OPENPMD=TRUE ', text)

# always build with PSATD support (runtime controlled if used)
if ci_psatd:
    text = re.sub('addToCompileString =',
                  'addToCompileString = USE_FFT=TRUE ', text)
    text = re.sub('USE_FFT=FALSE',
                  '', text)

# CCache
if ci_ccache:
    text = re.sub('addToCompileString =',
                  'addToCompileString = USE_CCACHE=TRUE ', text)

# Add runtime options:
# > crash for unused variables
# > trap NaNs, divisions by zero, and overflows
# > abort upon any warning message by default
text = re.sub('runtime_params =',
              'runtime_params = amrex.abort_on_unused_inputs=1 '+
              'amrex.fpe_trap_invalid=1 amrex.fpe_trap_zero=1 amrex.fpe_trap_overflow=1 '+
              'warpx.always_warn_immediately=1 warpx.abort_on_warning_threshold=low',
              text)

# Add runtime options for CPU:
# > serialize initial conditions and no dynamic scheduling in OpenMP
if arch == 'CPU':
    text = re.sub('runtime_params =',
                  'runtime_params = '+
                  'warpx.do_dynamic_scheduling=0 warpx.serialize_initial_conditions=1',
                  text)

# Use less/more cores for compiling, e.g. public CI only provides 2 cores
if ci_num_make_jobs is not None:
    text = re.sub( 'numMakeJobs = \d+', 'numMakeJobs = {}'.format(ci_num_make_jobs), text )

# Prevent emails from being sent
text = re.sub( 'sendEmailWhenFail = 1', 'sendEmailWhenFail = 0', text )

# Select the tests to be run
# --------------------------

# - Extract test blocks (they are identified by the fact that they contain "inputFile")
select_test_regex = r'(\[(.+\n)*inputFile(.+\n)*)'
test_blocks =  [ match[0] for match in re.findall(select_test_regex, text) ]
# - Remove the test blocks from `text` (only the selected ones will be added back)
text = re.sub( select_test_regex, '', text )

def select_tests(blocks, match_string_list, do_test):
    """Remove or keep tests from list in WarpX-tests.ini according to do_test variable"""
    if do_test not in [True, False]:
        raise ValueError("do_test must be True or False")
    if (do_test is False):
        for match_string in match_string_list:
            print('Selecting tests without ' + match_string)
            blocks = [ block for block in blocks if match_string not in block ]
    else:
        for match_string in match_string_list:
            print('Selecting tests with ' + match_string)
            blocks = [ block for block in blocks if match_string in block ]
    return blocks

if ci_regular_cartesian_1d:
    test_blocks = select_tests(test_blocks, ['dim = 1'], True)
    test_blocks = select_tests(test_blocks, ['USE_RZ=TRUE'], False)
    test_blocks = select_tests(test_blocks, ['PRECISION=FLOAT', 'USE_SINGLE_PRECISION_PARTICLES=TRUE'], False)
    test_blocks = select_tests(test_blocks, ['useMPI = 0'], False)
    test_blocks = select_tests(test_blocks, ['QED=TRUE'], False)
    test_blocks = select_tests(test_blocks, ['USE_EB=TRUE'], False)

if ci_regular_cartesian_2d:
    test_blocks = select_tests(test_blocks, ['dim = 2'], True)
    test_blocks = select_tests(test_blocks, ['USE_RZ=TRUE'], False)
    test_blocks = select_tests(test_blocks, ['PRECISION=FLOAT', 'USE_SINGLE_PRECISION_PARTICLES=TRUE'], False)
    test_blocks = select_tests(test_blocks, ['useMPI = 0'], False)
    test_blocks = select_tests(test_blocks, ['QED=TRUE'], False)
    test_blocks = select_tests(test_blocks, ['USE_EB=TRUE'], False)

if ci_regular_cartesian_3d:
    test_blocks = select_tests(test_blocks, ['dim = 3'], True)
    test_blocks = select_tests(test_blocks, ['PRECISION=FLOAT', 'USE_SINGLE_PRECISION_PARTICLES=TRUE'], False)
    test_blocks = select_tests(test_blocks, ['useMPI = 0'], False)
    test_blocks = select_tests(test_blocks, ['QED=TRUE'], False)
    test_blocks = select_tests(test_blocks, ['USE_EB=TRUE'], False)

if ci_single_precision:
    test_blocks = select_tests(test_blocks, ['PRECISION=FLOAT', 'USE_SINGLE_PRECISION_PARTICLES=TRUE'], True)

if ci_rz_or_nompi:
    block1 = select_tests(test_blocks, ['USE_RZ=TRUE'], True)
    block2 = select_tests(test_blocks, ['useMPI = 0'], True)
    test_blocks = block1 + block2

if ci_qed:
    test_blocks = select_tests(test_blocks, ['QED=TRUE'], True)

if ci_eb:
    test_blocks = select_tests(test_blocks, ['USE_RZ=TRUE'], False)
    test_blocks = select_tests(test_blocks, ['USE_EB=TRUE'], True)

# - Add the selected test blocks to the text
text = text + '\n' + '\n'.join(test_blocks)

with open('ci-tests.ini', 'w') as f:
    f.write(text)
