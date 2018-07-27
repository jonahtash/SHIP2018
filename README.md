# SHIP 2018
SHIP 2018 contains utilities to batch assemble databases of scientific articles and parse article contents.

### Currently available utilities

 - Automated PDF downloading from PubMed ids
 - Automated PDF downloading from PMC  ids
 - Retrieving journal domain name from PubMed id 
 - Extraction of article sections from PDFs using Science-Parse
 - File folder partitioning for Science-Parse JSONs
 - PubMed CSV parsing utilities
 - Miscellaneous related functions

## Example Usage

From start to finish here is how one can download and process articles from a given PubMed search.
### Get a CSV from PubMed
Search for something on the PubMed website, in this example we search for the phrase "engineering biology"

<img src="https://raw.githubusercontent.com/jonahtash/SHIP2018/master/img/pmed.png" width="786">

After searching for a query on the PubMed website select "Send To" > "File" > Format: CSV and press "Create File"
>Written by Jonah Tash and Pavan Bhat