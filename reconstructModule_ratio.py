
#!/usr/bin/python3

# -*- coding: utf-8 -*-

__version__ = '1.0.0'
__author__ = 'R. Ongaro','A. Mathieu'
__date__ = '23-01-2020'

import sys
import argparse
import textwrap
import requests as rq
from pathlib import Path
from bs4 import BeautifulSoup as bs
import re

import csv


# check python version
if sys.version_info < (3, 6):
    raise Exception("Please, run this script with a version of Python >= 3.6")

# default result directory path
_DEFAULT_RESULTS_DIR = Path("./results")

# url for scrapping data
_FIRST_URL = 'https://www.genome.jp/kegg-bin/find_pathway_object'
_FINAL_URL = 'https://www.genome.jp/kegg-bin/find_module_object'

# hidden <input> data to scrap
_SITE_HIDDEN_ATTR = ["uploadfile", "module_complete_file", "target",
                     "pathway_count", "brite_count", "brite_table_count", "module_count"]


def warn(msg):
    """Utils: print a warning
    """
    print(f"\033[93m{msg}\033[0m")


def create_directory(dirpath: Path = None):
    """Create result directory
    """
    if dirpath is None or not dirpath.is_dir():
        warn(
            f"Result directory missing, using '{_DEFAULT_RESULTS_DIR.resolve()}/' as result directory path.")
        dirpath = _DEFAULT_RESULTS_DIR
    dirpath.mkdir(exist_ok=True)
    return dirpath


def read_modules(modules_filepath: Path = None):
    """Read input module file.

    If it does not exist, give an empty list as expected modules.
    """
    mdata = None
    if modules_filepath is None:
        warn("Modules filepath is empty.")
        mdata = []
    else:
        if not modules_filepath.is_file():
            raise Exception(
                f"Modules file '{modules_filepath}' does not exist.")
        with modules_filepath.open("rt") as f:
            mdata = [line for line in f]
    return mdata


# def read_sample_data(sample_filepath: Path = None):
#     """Read input sample file.
#     """
#     if sample_filepath is None:
#         raise Exception("Sample filepath is empty.")
#     if not sample_filepath.is_file():
#         raise Exception(f"Sample file '{sample_filepath}' does not exist.")
#     # data = None
#     # with sample_filepath.open('rb') as f:
#     #     data = ''.join([line.decode("utf-8") for line in f])
#     data = {}
#     with sample_filepath.open('rt') as f:
#         for line in csv.reader(f):
#             k,v = line[0].split('\t')
#             data[k] = v
#     return data


def write_result_modules(result_filepath: Path = None, result_data=None):
    """Write end results to file

    Format for each line:
    <module_name> \\t <result_code> \\n
    """
    if result_filepath is None:
        raise Exception("Result filepath is empty.")
    if result_data is None:
        raise Exception("Result dataset is empty.")
    with result_filepath.open('wt') as f:
        for r in result_data:
            # module \t indice \n
            f.write(f"{r[0]}\t{r[1]}\n")


def process_sample(sample_filepath: Path = None, modules_filepath: Path = None, results_dir: Path = None):
    """Main process

    Create a sample codification for each module.
    """

    # result var
    final_results = []
    sample_modules = set()

    # headers
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://www.genome.jp",
        "DNT": "1",
        "Connection": "keep-alive",
        "Referer": "https://www.genome.jp/kegg/mapper/reconstruct.html",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }

    # modules
    modules = read_modules(modules_filepath=modules_filepath)

    # result file
    result_modules_filepath = results_dir.joinpath(
        f"{sample_filepath.stem}_modules.tsv")

    # sample data
    # sample_data_to_stream = {"unclassified": read_sample_data(
    #     sample_filepath=sample_filepath)}

    # print(sample_data_to_stream)
    # raise

    #
    html_text = None
    with rq.Session() as s:
        # send req
        # rq_content = s.post(_FIRST_URL, data=sample_data_to_stream, headers=headers)

        data_files= {
            "color_list": (
                sample_filepath.name, 
                open(sample_filepath, "rb"), 
                'multipart/form-data'
            )
        }
        rq_content = s.post(_FIRST_URL, files=data_files, headers=headers)
        content = rq_content.text

        # if status error
        if rq_content.status_code != 200:
            raise Exception("Service Error: request failed with code {} ({})",
                            rq_content.status_code, rq_content.text)

        # analyze first, get all hiddne inputs to use them in the next req
        soup = bs(content, features="html.parser")
        next_req_payload = {
            inp.attrs["name"]: inp.attrs["value"]
            for inp in soup.find_all('input')
            if inp.attrs["name"] in _SITE_HIDDEN_ATTR
        }
        next_req_payload = {**next_req_payload,
                            **{"mode": "all", "sort": "module"}}

        # final req
        rq_content = s.post(_FINAL_URL, data=next_req_payload, headers=headers)
        content = rq_content.text
        
        # if status error
        if rq_content.status_code != 200:
            raise Exception("Service Error: request failed with code {} ({})",
                            rq_content.status_code, rq_content.text)

        # parse final
        soup = bs(content, features="html.parser")
        html_text = soup.get_text().split('\n')
        
    # close session and parse webpage
    for html_line in html_text:
        # line = html_line.encode('ascii', 'ignore').strip(' ')
        line = html_line.strip(' ')
        # print(line)
        if line.startswith('M0'):
            # print(line)
            module = line[0:6]
            if not line.endswith(")"):
                raise Exception(f"Malformed line: '{line}'")
            # switch
            inc = "(incomplete"
            com = "(complete"
            l1 = "(1 block missing"
            l2 = "(2 blocks missing"
            missing = re.findall(r"\d+/\d+\)$", line)
            rat = missing[0].strip(")").split("/")[0]
            tot = missing[0].strip(")").split("/")[1]
            ratio = int(rat) / int(tot)
            # res
            final_results.append((module, ratio))
            sample_modules.add(module)

    # add missing modules
    for m in modules:
        if m not in sample_modules:
            final_results.append((m, '0'))

    # write result
    final_results.sort()
    write_result_modules(
        result_filepath=result_modules_filepath, result_data=final_results)


def get_argparser():
    """Create the argument parser
    """
    parser = argparse.ArgumentParser(prog="Reconstruct modules",
                                     add_help=True,
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent("""\
    Extract modules from KEGG Mapper Reconstruct Module via scraping and summarize output for subsequent analysis.

    Result codes are:
      0 ... complete
      1 ... 1 block missing
      2 ... 2 blocks missing
      3 ... incomplete
      4 ... not present
    """))
    # attr
    parser.add_argument("-s", "--sample-filepath", type=str,
                        help="A path to the sample filepath", required=True)
    parser.add_argument("-m", "--modules-filepath", type=str,
                        help="A path to the modules file")
    parser.add_argument("-r", "--result-directory", type=str,
                        help="A path to results directory, will be created if it does not exist")
    #
    return parser


def main(*args, **kwargs):
    """Main function
    """

    # create result dir
    res_dir = create_directory(kwargs["results_dirpath"])
    # exec
    process_sample(sample_filepath=kwargs["samples_filepath"],
                   modules_filepath=kwargs["modules_filepath"],
                   results_dir=res_dir)
    # yay
    print(f"Module reconstruction for '{kwargs['samples_filepath']}' done.")


if __name__ == '__main__':
    # build arg parser, top level parser
    parser = get_argparser()

    # parse arguments
    parsed_args, _ = parser.parse_known_args()

    # args and kwargs
    kw = {
        "samples_filepath": Path(parsed_args.sample_filepath) if parsed_args.sample_filepath is not None else None,
        "modules_filepath": Path(parsed_args.modules_filepath) if parsed_args.modules_filepath is not None else None,
        "results_dirpath": Path(parsed_args.result_directory) if parsed_args.result_directory is not None else None,
    }
    # exec
    main(**kw)
