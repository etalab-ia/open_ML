'''
This script uploads our datasets into openml with its API. It then produces a python snippet
to be pasted in the web page to import the dataset via sklearn through openml

Usage:
    my_script.py <datasets_folder> <output_snippet_folder> <main_csv_file> [options]

Arguments:
    <datasets_folder>                     A folder with dgf resources ids and csv files within
    <output_snippet_folder>               A folder with dgf resources ids and csv files within
    <main_csv_file>                       The path of the main csv file used in the website
'''
from dotenv import load_dotenv

load_dotenv(verbose=True)
import logging
import os
openml_apikey = os.getenv("openml_apikey")
from pathlib import Path

import pandas as pd
from csv_detective.explore_csv import routine
from argopt import argopt
from tqdm import tqdm
import openml
from openml.datasets.functions import create_dataset

from open_ml_app.apps.utils import slugify

# openml.config.start_using_configuration_for_example()
openml.config.apikey = openml_apikey

def run(doc_path):
    return 1

# TO DO: This code retrieves the info from the main_csv, we need to include it directly into full_auto_openml.py

def main(datasets_folder: Path, output_snippet_folder: Path, main_csv_file: Path):
    doc_paths = []
    job_output = []
    if not datasets_folder.exists():
        raise FileNotFoundError(datasets_folder.as_posix())
    if not output_snippet_folder.exists():
        raise FileNotFoundError(output_snippet_folder.as_posix())
    if not main_csv_file.exists():
        raise FileNotFoundError(main_csv_file.as_posix())


    main_csv = pd.read_csv(main_csv_file)
    list_subfolders_with_paths = [Path(f.path) for f in os.scandir(datasets_folder.as_posix()) if f.is_dir()]
    for path in list_subfolders_with_paths:
        id_dataset = path.name
        dataset_file = [Path(f) for f in path.glob(f"{id_dataset}.*")]
        if not dataset_file:
            logging.debug(f"There was not dataset for {id_dataset}")
        dataset_metadata = routine(dataset_file[0], user_input_tests=None)
        df_dataset = pd.read_csv(dataset_file[0], sep=dataset_metadata["separator"],
                                 encoding=dataset_metadata["encoding"])
        renamed_cols = {k: slugify(k) for k in df_dataset.columns}
        df_dataset.rename(columns=slugify, inplace=True)
        # enforce the categorical column to have a categorical dtype
        for cat_var in df_dataset.select_dtypes(include='object').columns.to_list():
            df_dataset[cat_var] = df_dataset[cat_var].astype('category')
        name = f"dgf_{id_dataset}"
        dataset_info=main_csv[main_csv['dgf_resource_id']==id_dataset]
        description=dataset_info['title'][dataset_info.index.to_list()[0]]
        target_var = slugify(dataset_info['target_variable'][dataset_info.index.to_list()[0]])
        try:
            new_dataset = create_dataset(
                name=name,
                description=description,
                creator="dgml_test",
                contributor="dgml_test",
                collection_date="20-05-2021",
                language="French",
                licence="Undefined",
                default_target_attribute=target_var,
                row_id_attribute=None,
                ignore_attribute=None,
                citation="dgf test",
                attributes='auto',
                data=df_dataset,
                version_label="example",
            )
            data_id = new_dataset.publish()
            main_csv.loc[main_csv['dgf_resource_id'] == id_dataset, 'openml_id'] = data_id.id
            main_csv.to_csv(main_csv_file,index=False)
        except Exception:
            pass





    for doc_path in tqdm(doc_paths):
        tqdm.write(f"Converting file {doc_path}")
        job_output.append(run(doc_path))

    logging.info(
        f"{sum(job_output)} DOC files were converted to TXT. {len(job_output) - sum(job_output)} files "
        f"had some error.")

    return doc_paths


if __name__ == '__main__':
    parser = argopt(__doc__).parse_args()
    datasets_folder = Path(parser.datasets_folder)
    output_snippet_folder = Path(parser.output_snippet_folder)
    main_csv_file = Path(parser.main_csv_file)
    main(datasets_folder=datasets_folder, output_snippet_folder=output_snippet_folder,
         main_csv_file=main_csv_file)
