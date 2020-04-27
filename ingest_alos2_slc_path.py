#!/usr/bin/env python3
"""
Ingest ALOS2 data from a source to a destination:

  1) download data from a source and verify,
  2) extracts data and creates metadata
  3) push data to repository


HTTP/HTTPS, FTP and OAuth authentication is handled using .netrc.
"""

import os, json, shutil, glob, re
import logging, traceback, argparse
import alos2_utils
import alos2_productize

log_format = "[%(asctime)s: %(levelname)s/%(funcName)s] %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)

BASE_PATH = os.path.dirname(__file__)

def cmdLineParse():
    '''
    Command line parser.
    '''

    parser = argparse.ArgumentParser( description='Getting ALOS-2 L2.1 / L1.1 data into ARIA')
    parser.add_argument('-d', dest='slc_path', type=str, default='',
            help = 'Download url if available')

    return parser.parse_args()

def copy_file(input_file, dest):
    if os.path.isdir(dest):
        shutil.copy(input_file, dest)
    else:
        shutil.copyfile(input_file, dest)

def process_slc_file(slc_file):
    wd = os.getcwd()
    slc_file_name = os.path.basename(slc_file)
    copy_file(slc_file, wd)
    
    this_slc_file = os.path.join(wd, slc_file_name)
    alos2_utils.extract_nested_zip(this_slc_file)
    os.remove(this_slc_file)
   
    raw_dir_list = []
    for root, subFolders, files in os.walk(os.getcwd()):
        if files:
            for x in files:
                m = re.search("IMG-[A-Z]{2}-ALOS2.{05}(.{04}-\d{6})-.{4}.*", x)
                if m:
                    logging.info("We found a ALOS2 dataset directory in: %s, adding to list" % root)
                    raw_dir_list.append(root)
                    break

    for raw_dir in raw_dir_list:
        dataset_name = alos2_utils.extract_dataset_name(raw_dir)
        # productize our extracted data
        metadata, dataset, proddir = alos2_productize.productize(dataset_name, raw_dir, slc_file)

        # dump metadata
        with open(os.path.join(proddir, dataset_name + ".met.json"), "w") as f:
            json.dump(metadata, f, indent=2)
            f.close()

        # dump dataset
        with open(os.path.join(proddir, dataset_name + ".dataset.json"), "w") as f:
            json.dump(dataset, f, indent=2)
            f.close()

        # cleanup raw_dir
        shutil.rmtree(raw_dir, ignore_errors=True)

    # cleanup downloaded zips in cwd
    for file in glob.glob('*.zip'):
        os.remove(file) 
    

def process_slc_path(slc_path):

    wd = os.getcwd()

    if os.path.isdir(slc_path):
        slc_files = glob.glob(os.path.join(slc_path, '*.zip'))
        print(slc_files)
        for slc_file in slc_files:
            print("Processing : {}".format(slc_file))
            process_slc_file(slc_file)
    else:
        process_slc_file(slc_path)           
          



if __name__ == "__main__":
    '''
    args = cmdLineParse()
    ctx = alos2_productize.load_context()
    print(ctx)
    '''
    try:
        '''
        # first check if we need to read from _context.json
        if not args.slc_path:
            # no inputs defined (as per defaults)
            # we need to try to load from context
            args.slc_path = ctx["slc_path"]

        # TODO: remember to bring back the download
        #alos2_utils.download(args.slc_path)
        #slc_path = args.slc_patha
        '''
        slc_path = '/data/data/'
        print(slc_path)
        process_slc_path(slc_path)
    except Exception as e:
        with open('_alt_error.txt', 'a') as f:
            f.write("%s\n" % str(e))
        with open('_alt_traceback.txt', 'a') as f:
            f.write("%s\n" % traceback.format_exc())
        raise
