# SHIP 2018
SHIP 2018 contains utilities to batch assemble databases of scientific articles and parse article contents.

Currently available utilities
 - Automated PDF downloading from PubMed using  Pubmed-Batch-Download
 - Extraction of article sections from PDFs
 - PubMed CSV parsing utilities
 - Miscellaneous related functions

## Example Usage

This repository can be used to download PDF documents from the NIH PubMed database.
Ex:
`run_id_ruby('id_file.txt','failed_ids.txt',num_threads=10)`


This repository can be used to get JSON formatted data from scientific articles using a Science-Parse server hosted on localhost:8080
Ex:
`get_pdf_json('pdfs/','outJSONS',num_thread=2)`

>Written by Jonah Tash and Pavan Bhat