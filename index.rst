.. SHIP documentation master file, created by
   sphinx-quickstart on Wed Jun 20 15:34:13 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to SHIP's documentation!
================================

RUBY 'pubmedid2pdf' Interactions
--------------------------------



.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. automodule:: SHIP

.. autofunction:: _process_line

Function to process IDs in ruby script
If the download fails, the ID is returned to a list of failed IDs

.. autofunction:: run_id_ruby
 
Run ruby script on list of ids at file_path and output failed ids
The IDs are taken in chunks and run in parallel

.. autofunction:: run_id_ruby_mp

Multiprocessing version of run_id_ruby - uses processes which opens multiple windows, not neccesary for ruby function

URL Sorting Functions
--------------------------------------

.. autofunction:: _process_liebert

Function to process IDs from the databse 'Liebert', which is inacessible

.. autofunction:: _get_liebert

Takes input list of PubMed ids and splits based on which ids' doi link redirects to the journal site "liebertpub"
Articles on the site are paywalled and therefore ingnored during pdf collection

.. autofunction:: _sort_url_process

Function to process urls for url domain sorting function
If an error occurs return the domain name as "error:*the error mesage*"

.. autofunction:: sort_url

Writes failed IDs to a CSV

.. autofunction:: sort_url_mp

Multiprocessing version of "sort_url"
Faster than the threaded version and opens several different windows

.. autofunction:: count_domain

Counts the number of domains in the CSV

.. autofunction:: _get_ox_paywall

Sorts out the paywalled articles that are inaccesible on the Oxford Journal Website

.. autofunction:: _get_ox_txt

Writes list of failed (paywalled) IDs from Oxford Journal Website to a CSV



.. autofunction:: _get_ox_paywall_process

Uses the tool 'Beautiful Soup' to parse the HTML of the website
Checks to see if the document is inaccesible

PMC Download Functions
----------------------------------------------

.. autofunction:: _download_pdf_fromid

Download pdf at download_url from PMC website.
Save pdf to folder at pdf_output_dir and name pdf pmed_id.

.. autofunction:: _get_from_pmcid

PREREQ: id file in format "PMCID+PUBMEDID"
Downloads pdfs of entries in txt at id_file_path and sends to pdf_output_dir

.. autofunction:: get_from_pmcid

Get_from_pmcid threaded version. Default number of threads 10.


.. autofunction:: get_from_pmcid_mp

Get_from_pmcid multiprocessing version
Faster than get_from_pmcid, but opens multiple windows    

.. autofunction:: _download_pdf_errors

Trys to download from URLs that have previously failed
PubMed Central Website bans batch downloading after a period of time
If the computer's IP gets banned by PMC, all left over ID's are written to a txt

.. autofunction:: get_error

function to name PDFs

.. autofunction:: get_error_mp

multiprocessing version of get_error


Science-Parse Server Functions
---------------------------------------------------


.. autofunction:: _post_science_parse

Connects to the science-parse server
Server is hosted locally on the machine
Science-parse creates JSON files which contain the PDF contents seperated by section




.. autofunction:: get_pdf_json

Gets JSON file from science parse server and saves it to directory

.. autofunction:: get_pdf_json_mp

Multiproccesing version of "get_pdf_json"

JSON Parsing Functions
---------------------------------------------------------------

.. autofunction:: run_json_folder

Creates an SQLite DataBase in memory
Adds the data of the JSON files to the table
Removes the unwanted sections and only keeps the authors and materials section
Splits the entries into 3000 character chunks
If the header reads as 'null' tries to find a header using capital letters
Deletes sections based on their digit to alphabetic ratios

.. autofunction:: partition_jsons

Splits the JSONs into multiple folders

.. autofunction:: run_partition_folders

Passes each partioned JSON folder through 'run_json_folder'

CSV Parsing Functions
----------------------------------------------------------------------

.. autofunction:: get_pmedid_csv

Make list of PubMed ids from PubMed csv

.. autofunction::get_pmcid_csv

Take PubMed csv at csv_file_path.
Make list of entries with PMCID format "PMCID+PUBMEDID" at pmc_path.
Make list of entries with no PMCID at nopmc_path.

.. autofunction:: csv_add_pcmid

Add PMCID to PUBMEDIDs in pmed_id_path txt.
Output results in format "PMCID+PUBMEDID" to output_path.

.. autofunction:: count_heads

Counts the number of IDs that have been processed

Utility Functions
---------------------------------------------------------------------

.. autofunction:: _remove_dupes_txt

Removes duplicate lines in txt file located at in_path
Outputs to out_path

.. autofunction::get_count

Counts the number of txts in id_txt_list.
Counts the number of pdfs in pdf_dir_list.
Returns the sum of pdf and txts

.. autofunction::sort_nonretrievable

Sorts out the flies which do not have a DOI or PMCID
These files are unretrievable

.. autofunction:: _upper_ratio

Computes the ratio of uppercase letters to all characters
Used to sort the parsed JSON sections 

.. autofunction:: _digit_ratio

Computes the ratio of numerical characters to characters in a section of parsed PDF
Used to sort sections that are not needed

.. autofunction::_special_ratio

Computes the ratio of special characters to characters in a section of parsed PDF

.. autofunction::
.. autofunction::

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
