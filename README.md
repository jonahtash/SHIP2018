# SHIP 2018
SHIP 2018 contains utilities to batch assemble databases of scientific articles and parse article contents.

Currently available utilities
 - Automated PDF downloading from PubMed using  Pubmed-Batch-Download
 - Automated PDF downloading from PMC
 - Extraction of article sections from PDFs
 - PubMed CSV parsing utilities
 - Miscellaneous related functions

## Example Usage

This repository can be used to download PDF documents from the NIH PubMed database.
Ex:
`run_id_ruby('id_file.txt','failed_ids.txt',num_threads=10)`

For articles available on the NIH PMC website.
Ex:
`get_from_pmcid_thread('id_file.txt','pdfs/,'failed_ids.txt',num_thread=10)`
>Note: id_file requires format PMCID+PUBMEDID"
 
 Or with better error distinction
 `get_error_thread('id_file.txt','pdf/,num_thread=10)`

This repository can be used to get JSON formatted data from scientific articles using a Science-Parse server hosted on localhost:8080
Ex:
`get_pdf_json('pdfs/','outJSONS',num_thread=2)`

>Written by Jonah Tash and Pavan Bhat