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

###  Dependencies
[Install Ruby](https://www.ruby-lang.org/en/downloads/), then run:
```c
>python setup.py
```
### Get a CSV from PubMed
Search for something on the PubMed website, in this example we search for the phrase "engineering biology"

<img src="https://raw.githubusercontent.com/jonahtash/SHIP2018/master/img/pmed.png" width="700">

After searching select "Send To" > "File" > Format: CSV and press "Create File." You should now have a .csv file called pubmed_result.csv. You are now ready to use SHIP 2018 to fetch and process the PDFs for the articles you searched for.

### What to use in SHIP 2018
You're going to be collecting a lot of files while using SHIP 2018 (it's a batch downloader after all) so we recommend u use the following file structure just to keep things organized. 
```
./
├── SHIP.py
├── pdfetch.rb
├── pubmedid2pdf.rb
├── torun/
	└──id_lists_here
├── inaccessible/
	└──id_lists_here
├── pdf/
	└──article_pdfs_here
├── data/
	└──material_sec_csvs_here
└── json/
	└──science_parse_jsons_here

```
You'll see what everything is for as we go along.

#### Lets Go!
The first to do is remove any articles that don't have any external links. There may be a way to retrieve the articles,  that way just doesn't involve SHIP 2018. Run:
```python 
sort_inacessable_csv("pubmed_result.csv", "torun/pubmed_result.csv", "inacessable/pubmed_inacessable.csv")
```
Now you're going to want to split the ids in the csv like this:
```python 
get_pmcid_csv("torun/pubmed_result.csv","torun/ids_pmc.txt","torun/ids_pmed.txt")
```
This will make two ids list txts. One txt will be formatted correctly to download PDFs from the PMC and we will use the other list to interface with the Ruby script.

You are now going to want to run the PMC id list. **NOTE VERY IMPORTANT!!!!1!!** DO NOT,  use this next function without permission from NIH. It is a copyright violation to do so and your IP will be banned from the PMC website (but mainly its illegal). If you do have permission from NIH to batch download in this fashion run:
```python 
get_error_mp("torun/ids_pmc.txt","pdf/","inacessable/")
```
In the event that there are ids in `inacessable/error_403_ipBan.txt`
which there shouldn't be because you recieved the proper permissions from NIH. However if for *some* reason there are ids in this file replace `torun/ids_pmc.txt` with this file  and delete the original and rerun `get_error_mp` like before until there no longer ids in the `inacessable/error_403_ipBan.txt`. You might have to do this from a machine with a different IP, for, uhhhh, reasons. Not that you would ever have this problem however.

Next you want to run the PubMed id list. In order for this next function you will need Ruby. Then run:
```python 
run_id_ruby_mp("torun/ids_pmed.txt","inacessable/inacessable_pmed.txt")
```
You will now have every article pdf from your original csv that SHIP 2018 is capable of retrieving.

#### PDF Processing
First run your PDFs through [Science-Parse](https://github.com/allenai/science-parse):
```c
>java -jar cli-assembly.jar -o json/ pdf/
```
Now extract the material sections from the PDFs into csv
```python
run_json_folder("json/","exclude.csv","chars.csv","data/bkup.csv","data.csv")
```
That's all it takes! You now have a .csv file that contains the materials section of each PDF file for (*almost*) every article in a given PubMed search as well as a PDF file for every article retrieved.
### Summary
```python
sort_inacessable_csv("pubmed_result.csv", "torun/pubmed_result.csv", "inacessable/pubmed_inacessable.csv")

get_pmcid_csv("torun/pubmed_result.csv","torun/ids_pmc.txt","torun/ids_pmed.txt")

# Generate JSONs in ./json/ using Science-Parse

run_id_ruby_mp("torun/ids_pmed.txt","inacessable/inacessable_pmed.txt")

run_json_folder("json/","exclude.csv","chars.csv","data/bkup.csv","data.csv")
``` 


### Some final notes:

 - **Why are there so few PDFs?** There are certain situations in which SHIP 2018 will not be able to retrieve a PDF
	 - The PubMeb entry has neither a DOI nor a PMC id
	 - PubMed or PMC gives an error 404 or 403 file removed error for a given id
	 - The journal site requires a site subscription that you do not have
	 - The article is on a journal site that is not supported- see [Adding a Journal Site](#)
>Written by Jonah Tash and Pavan Bhat