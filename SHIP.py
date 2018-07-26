import os
from multiprocessing import Pool as PoolMP
from multiprocessing.dummy import Pool
from multiprocessing import freeze_support
from datetime import datetime
import subprocess
import csv
import urllib.request
"""from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage"""
from io import StringIO
import unicodedata
import ctypes
import requests
import sqlite3
import json
import re
from http.cookiejar import CookieJar
from bs4 import BeautifulSoup
import pandas as pd
import shutil


"""BEGIN RUBY pudmebid2pdf INTERACTION FUNCTIONS"""
"""*********************************************"""

#func to process id in ruby script
def _process_line(line):
    #output PubMed id of document being run through ruby script
    print(line.strip())
    #pass id to ruby script and save output in buffer
    p = subprocess.Popen("ruby pubmedid2pdf.rb "+line,shell = False,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    p.wait()
    #the ruby script uses alot of console warnings that mainly come to stderr
    #if the dl failed return the id to be added to list of failed ids
    if "failed" in str(p.stderr.read()):
        return line
    #if the dl is successful return no id (empty string)
    return ""

#run ruby script on list of ids at file_path and output failed ids
#to kickback_loc. Optional num_threads number of threads to run- default 10
def run_id_ruby(file_path,kickback_path,num_threads=10):
    #record start time to calculate total runtime later
    start = datetime.now()

    #init pool of workers from specified number
    #this is how many downloads will run in parallel
    pool = Pool(num_threads)

    #use Pool.map to have the worker pool take ids in chunks from txt
    #and run them though ruby script using the _process_line function
    #results will be failed with the ids that failed to dl
    with open(file_path) as source_file:
        results = pool.map(_process_line, source_file)

    #write the list of failed ids to file
    with open(kickback_path,'w') as f:
        for i in results:
            f.write(i)
    return datetime.now()-start

#run ruby script on list of ids at file_path and output failed ids
#to kickback_loc. Optional num_threads number of threads to run- default 10
def run_id_ruby_mp(file_path,kickback_path,num_threads=10):
    #record start time to calculate total runtime later
    start = datetime.now()

    #init pool of workers from specified number
    #this is how many downloads will run in parallel
    pool = PoolMP(num_threads)

    #use Pool.map to have the worker pool take ids in chunks from txt
    #and run them though ruby script using the _process_line function
    #results will be failed with the ids that failed to dl
    with open(file_path) as source_file:
        results = pool.map(_process_line, source_file)

    #write the list of failed ids to file
    with open(kickback_path,'w') as f:
        for i in results:
            f.write(i)
    return datetime.now()-start


"""********************************************"""
"""END RUBY pudmebid2pdf INTERACTION FUNCTIONS"""


"""BEGIN URL SORTING FUNCTIONS"""
"""***************************"""

#func to process ids to if the from inacessable db liebert
def _process_liebert(line):
    try:
        #build request
        headers = {}
        #ie user-agent string
        headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
        #use nih eutil to get link that redirects to the doi url for each article
        url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&id="+line.strip()+"&retmode=ref&cmd=prlinks"
        print(url)
        req = urllib.request.Request(url, headers = headers)
        #site was refusing robot connection so cookie jar is used to bypass
        cj = CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        resp = opener.open(req)

        #check to see if the doi url redirected to liebert db site
        if "liebertpub" in resp.geturl():
            return line
        else:
            return ""
    except Exception as e:
        print(str(e))

    #this return is called if an error occurs while attempting to get the doi url
    #assume its not liebert so it can be checked again
    return ""

#takes input list of PubMed ids and splits based on which ids' doi link redirects to the journal site "liebertpub"
#articles on the site are paywalled and therefore ingnored during pdf collection
#id_txt path to txt with list of ids to b split
#out_txt output path of article ids that are located on liebert site
#not_out_txt output path of article ids that are not located on liebert site
def _get_liebert(id_txt,out_txt, not_out_txt,num_threads=10):
    pool = Pool(num_threads)

    #same Pool.map to map liebert process function to an input list of PubMed ids
    results = []
    with open(id_txt) as source_file:
        results = pool.map(_process_liebert, source_file)
    #write the list of failed ids to file
    with open(out_txt,'w') as f:
        for i in results:
            f.write(i)
    _txt_diff(id_txt,out_txt,not_out_txt)

#func to process urls for url domain sorting function
#line is PubMed id
def _sort_url_process(line):
    try:
        #build request
        headers = {}
        #ie user-agent
        headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
        #use nih eutil to get link that redirects to the doi url for each article
        url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&id="+line.strip()+"&retmode=ref&cmd=prlinks"
        print(line.strip())
        req = urllib.request.Request(url, headers = headers)
        #use cookie jar to bypass robot blockers
        cj = CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        resp = opener.open(req)
        #use urllib urlparse to extract domain name from url that the doi link redirected to
        found = urllib.parse.urlparse(resp.geturl()).netloc
        #return the the domain name of the doi link of the article and the PubMed id of that article delimeted by ||
        return (found+"||"+line.strip())
    except Exception as e:
        print(str(e))
        #if an error occurs return the domain name as "error:*the error mesage*"
        return ("error:"+str(e)+"||"+line.strip())


def sort_url(id_txt,out_csv,num_threads=10):
    pool = Pool(num_threads)

    #use Pool.map to have the worker pool take ids in chunks from txt
    #and run them though ruby script using the process_line function
    #results will be failed with the ids that failed to dl
    with open(id_txt) as source_file:
        results = pool.map(_sort_url_process, source_file)

    #write the list of failed ids to file
    f = csv.writer(open(out_csv,'w'),lineterminator="\n")
    for i in results:
        f.writerow(i.split("||"))

def sort_url_mp(id_txt,out_csv,num_threads=10):
    pool = PoolMP(num_threads)

    #use Pool.map to have the worker pool take ids in chunks from txt
    #and run them though ruby script using the process_line function
    #results will be failed with the ids that failed to dl
    with open(id_txt) as source_file:
        results = pool.map(_sort_url_process, source_file)
    pool.close()
    #write the list of failed ids to file
    f = csv.writer(open(out_csv,'w'),lineterminator="\n")
    for i in results:
        f.writerow(i.split("||"))

def count_domain(in_csv,out_csv):
    domains = {}
    for row in csv.reader(open(in_csv,'r')):
        if row[0] in domains:
            domains[row[0]] = domains[row[0]]+1
        else:
            domains[row[0]] = 1
    w = csv.writer(open(out_csv,'w'),lineterminator="\n")
    for k in domains.keys():
        w.writerow([k,domains[k]])

def _get_ox_paywall(id_txt,out_txt,num_threads=10):
    pool = Pool(num_threads)

    #use Pool.map to have the worker pool take ids in chunks from txt
    #and run them though ruby script using the process_line function
    #results will be failed with the ids that failed to dl
    with open(id_txt) as source_file:
        results = pool.map(_get_ox_paywall_process, source_file)

    #write the list of failed ids to file
    f =open(out_txt,'w')
    for i in results:
        f.write(i)

def _get_ox_txt(in_csv,out_txt):
    out = open(out_txt,'a')
    for row in csv.reader(open(in_csv,'r')):
        if row[0]=="academic.oup.com":
            out.write(row[1]+"\n")
    out.close()

def _get_ox_paywall_process(line):
    headers = {}
    headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
    url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&id="+line.strip()+"&retmode=ref&cmd=prlinks"
    print(line.strip())
    req = urllib.request.Request(url, headers = headers)
    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    resp = opener.open(req)
    soup = BeautifulSoup(resp.read(), 'html.parser')
    if soup.find(id="PermissionsLink"):
        return line
    return ""

"""*************************"""
"""END URL SORTING FUNCTIONS"""


"""BEGIN PMC DOWLOAD FUNCTIONS"""
"""***************************"""

#Download pdf at download_url from PMC website.
#Save pdf to folder at pdf_output_dir and name pdf pmed_id.
#Output failed downloads to kickback_path txt.
def _download_pdf_fromid(download_url,pmed_id,pdf_output_dir,kickback_path):
    kick = open(kickback_path,'a')
    try:
        #assemble http request. PMC is sus if you don't have User-Agent header
        headers = {}
        #set agent to IE
        headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
        req = urllib.request.Request(download_url, headers = headers)
        resp = urllib.request.urlopen(req)
        with open("./"+pdf_output_dir+pmed_id+".pdf",'wb') as f:
            f.write(resp.read())
            f.close()
    except Exception as e:
        print(str(e))
        kick.write(download_url[download_url.index("PMC"):download_url.index("/pdf/")]+"+"+pmed_id+"\n")
    kick.close()


#PREREQ: id file in format "PMCID+PUBMEDID".
#Download pdfs of entries in txt at id_file_path.
#Downloads pdfs to pdf_output_dir.
#Output failed downloads to kickback_path.
def _get_from_pmcid(id_file_path,pdf_output_dir,kickback_path):
    pdf_output_dir = _clean_path(pdf_output_dir)
    with open(id_file_path,'r') as f:
        for line in f:
            a = line.split("+")
            _download_pdf_fromid("https://www.ncbi.nlm.nih.gov/pmc/articles/"+a[0]+"/pdf/",
                          a[1].strip(),pdf_output_dir,kickback_path)
            print(a[0]+" "+a[1].strip())

#helper func for threaded dl
def _unpack(s):
    a = s.split("+")
    print(a[0]+" "+a[1].strip())
    _download_pdf_fromid("https://www.ncbi.nlm.nih.gov/pmc/articles/"+a[0]+"/pdf/",
                        a[1].strip(),a[2],a[3])
#Get_from_pmcid threaded version.
#Default 10 threads.
def get_from_pmcid(id_file_path,pdf_output_dir,kickback_path,num_thread=10):
    pdf_output_dir = _clean_path(pdf_output_dir)
    pool = Pool(num_thread)
    pack = []
    for line in open(id_file_path,'r'):
        pack.append(line+"+"+pdf_output_dir+"+"+kickback_path)
    results = pool.map(_unpack,pack)

#Get_from_pmcid threaded version.
#Default 10 threads.
def get_from_pmcid_mp(id_file_path,pdf_output_dir,kickback_path,num_thread=10):
    pdf_output_dir = _clean_path(pdf_output_dir)
    pool = PoolMP(num_thread)
    pack = []
    for line in open(id_file_path,'r'):
        pack.append(line+"+"+pdf_output_dir+"+"+kickback_path)
    results = pool.map(_unpack,pack)
    pool.close()

def _download_pdf_errors(download_url,pmed_id,pdf_output_dir):
    e404 = open("error_404.txt",'a')
    e403_ban = open("error_403_ipBan.txt",'a')
    e403_rem = open("error_403_rem.txt",'a')
    try:
        headers = {}
        headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
        req = urllib.request.Request(download_url, headers = headers)
        resp = urllib.request.urlopen(req)
        with open("./"+pdf_output_dir+pmed_id+".pdf",'wb') as f:
            f.write(resp.read())
            f.close()
    except Exception as e:
        print(str(e))
        if e.code == 404:
            e404.write(download_url[download_url.index("PMC"):download_url.index("/pdf/")]+"+"+pmed_id+"\n")
        if e.code == 403:
            if "Internet connection (IP address) was used to download content in bulk" in str(e.read()):
                e403_ban.write(download_url[download_url.index("PMC"):download_url.index("/pdf/")]+"+"+pmed_id+"\n")
            else:
                e403_rem.write(download_url[download_url.index("PMC"):download_url.index("/pdf/")]+"+"+pmed_id+"\n")
    e404.close()
    e403_ban.close()
    e403_rem.close()

def _unpack_error(s):
    a = s.split("+")
    print(a[0]+" "+a[1].strip())
    _download_pdf_errors("https://www.ncbi.nlm.nih.gov/pmc/articles/"+a[0]+"/pdf/",
                        a[1].strip(),a[2])

def get_error(id_file_path,pdf_output_dir,num_thread=2):
    pdf_output_dir = _clean_path(pdf_output_dir)
    pool = Pool(num_thread)
    pack = []
    for line in open(id_file_path,'r'):
        pack.append(line+"+"+pdf_output_dir)
    results = pool.map(_unpack_error,pack)

def get_error_mp(id_file_path,pdf_output_dir,num_thread=2):
    pdf_output_dir = _clean_path(pdf_output_dir)
    pool = PoolMP(num_thread)
    pack = []
    for line in open(id_file_path,'r'):
        pack.append(line+"+"+pdf_output_dir)
    results = pool.map(_unpack_error,pack)
    pool.close()
    
"""*************************"""
"""END PMC DOWLOAD FUNCTIONS"""


"""BEGIN MATERIALS SECTION PARSER FUNCTIONS"""
"""****************************************"""
def _extract_materials_section(pdf_path,output_path,sec_header_good,sec_header_bad):
    f = open(output_path, "w")
    text= _convert_pdf_to_txt(pdf_path)
    lineiterator = iter(text.splitlines())
    for line in lineiterator:
        if len(unicodedata.normalize("NFD",line.casefold()).replace("  "," ").strip()) > 0:
            if _any_rev(sec_header_good,unicodedata.normalize("NFD",line.casefold()).replace("  "," ")):
                #print(line+"******************")
                print(next(lineiterator))
                for i in range(1000):
                    l = next(lineiterator)
                    print(l)
                    if not _ny_rev(sec_header_bad,unicodedata.normalize("NFD",l.casefold()).replace("  "," ")):
                        f.write(l+"\n")
                    else:  
                        break
                break
    f.close()

def _get_materials_folder(pdf_dir,output_dir,sec_header_good,sec_header_bad):
    pdf_dir = _clean_path(pdf_dir)
    output_dir = _clean_path(output_dir)
    for f in os.listdir(pdf_dir):
        if f.endswith(".pdf"):
            print(pdf_dir+f)
            _extract_materials_section(pdf_dir+f,output_dir+f.split(".pdf")[0]+".txt",sec_header_good,sec_header_bad)

def _unpack_pdfextract(s):
    a = s.split(",")
    print(a[0])
    extract_materials_section(a[0],a[1],a[2].split('$'),a[3].split('$'))

def get_materials_folder(pdf_dir,output_dir,sec_header_good,sec_header_bad,num_threads=10):
    pdf_dir = _clean_path(pdf_dir)
    output_dir = _clean_path(output_dir)
    pool = Pool(num_threads)
    pack = []
    for f in os.listdir(pdf_dir):
        if f.endswith(".pdf"):
            pack.append(pdf_dir+f+","+output_dir+f.split(".pdf")[0]+".txt,"+'$'.join(sec_header_good)+","+'$'.join(sec_header_bad))
    results = pool.map(_unpack_pdfextract, pack,4)

def get_materials_folder_mp(pdf_dir,output_dir,sec_header_good,sec_header_bad,num_threads=10):
    pdf_dir = _clean_path(pdf_dir)
    output_dir = _clean_path(output_dir)
    pool = PoolMP(num_threads)
    pack = []
    for f in os.listdir(pdf_dir):
        if f.endswith(".pdf"):
            pack.append(pdf_dir+f+","+output_dir+f.split(".pdf")[0]+".txt,"+'$'.join(sec_header_good)+","+'$'.join(sec_header_bad))
    results = pool.map(_unpack_pdfextract, pack,4)
    pool.close()

"""**************************************"""
"""END MATERIALS SECTION PARSER FUNCTIONS"""


"""BEGIN SCIENCE-PARSE SERVER FUNCTIONS"""
"""*****************************"""

def _post_science_parse(s):
    a=s.split("+")
    print(a[0])
    try:
        with open(a[0], 'rb') as f:
            r = requests.post('http://localhost:8080/v1', files={a[0]: f})
            open(a[1]+a[0].split('/')[-1][0:-4]+'.json','w',encoding='utf-8').write(r.text)
    except Exception as e:
        print("ERROR "+str(e))

def get_pdf_json(pdf_dir,out_dir,num_thread=2):
    pdf_dir = _clean_path(pdf_dir)
    out_dir = _clean_path(out_dir)
    pool = Pool(num_thread)
    pack = []
    for line in os.listdir(pdf_dir):
        pack.append(pdf_dir+line+"+"+out_dir)
    results = pool.map(_post_science_parse,pack)

def get_pdf_json_mp(pdf_dir,out_dir,num_thread=2):
    pdf_dir = _clean_path(pdf_dir)
    out_dir = _clean_path(out_dir)
    pool = PoolMP(num_thread)
    pack = []
    for line in os.listdir(pdf_dir):
        pack.append(pdf_dir+line+"+"+out_dir)
    results = pool.map(_post_science_parse,pack)
    pool.close()

"""***************************"""
"""END SCIENCE-PARSE SERVER FUNCTIONS"""


"""BEGIN JSON PARSING FUNCTIONS"""
"""****************************"""

def run_json_folder(json_path,exclude_path,char_path,bkup_csv_path,csv_out_path):
	json_path = _clean_path(json_path)

	#init sqlite db in memory
	#sql db structure:
	##Table: temp_table
	###Columns: sec_head, text, id, sec_num, inferred, split_num upper_to_lower, digit_to_char, special_to_char
	conn = sqlite3.connect(':memory:')
	cur = conn.cursor()
	cur.execute('CREATE TABLE temp_table (sec_head varchar(255), text TEXT, id INT, sec_num INT, split_num INT, inferred BIT, upper_to_lower FLOAT, digit_to_char FLOAT, special_to_char FLOAT);')

	#go through json files and add their data to table
	for file_path in os.listdir(json_path):
		file_path=json_path+file_path
		print(file_path)
		f = json.load(open(file_path,'r',encoding='utf-8'))
		c=1
		#add title and author entry to table
		if f['metadata']['title']:
			cur.execute("INSERT INTO temp_table VALUES (?, ?, ?, ?, 1, 0, 0, 0, 0)", ('title', _clean_sql(f['metadata']['title']),file_path.split('/')[-1].split('.pdf.json')[0],c))
			c+= 1
		if f['metadata']['authors']:
			cur.execute("INSERT INTO temp_table VALUES (?, ?, ?, ?, 1, 0, 0, 0, 0)", ('authors', _clean_sql(str(f['metadata']['authors'])),file_path.split('/')[-1].split('.pdf.json')[0],c))
			c+= 1

		if f['metadata']['sections']:
			for sec in f['metadata']['sections']:
				text_clean = _clean_sql(sec['text']).replace("N IH -PA Author M anuscript\n",'').replace("N IH -PA Author M anuscript",'')
				heading_clean = ""
				if sec['heading']:
					heading_clean = _clean_sql(sec['heading'])
				else:
					heading_clean = "null"
				cmd = "INSERT INTO temp_table VALUES (?, ?, ?, ?, ?, ?, ?, ? ,? )"
				cur.execute(cmd, (heading_clean, text_clean,file_path.split('/')[-1].split('.pdf.json')[0],c,1,0,_upper_ratio(text_clean),_digit_ratio(text_clean),_special_ratio(text_clean)))
				c+= 1


	
	#Dump unedited table into backup csv
	pd.read_sql(sql='SELECT * FROM temp_table ORDER BY id,sec_num,split_num', con=conn).to_csv(bkup_csv_path, index=False,sep = ',',quoting=csv.QUOTE_NONNUMERIC)

	#read unwanted headers from csv file
	re = csv.reader(open(exclude_path,'r',encoding='utf-8'))
	for row in re:
		#delete where section header like word in csv
		cur.execute("DELETE from temp_table WHERE sec_head like '%"+row[0]+"%';")
	#remove all sections where the section text is less than certain length-- currently: 600 chars
	#added catch for authors and title since they are most likely too short but still should be included
	cur.execute("DELETE from temp_table WHERE length(text) < 600 AND sec_head!='title' AND sec_head !='authors';")

	#defragment indexing
	cur.execute("SELECT * FROM temp_table ORDER BY id,sec_num,split_num")
	rows = cur.fetchall()
	cur_id = rows[0][2]
	c =1
	for row in rows:
		if not row[2] == cur_id:
			cur_id = row[2]
			c = 1
		cur.execute("UPDATE temp_table SET sec_num = ? WHERE sec_head = ? AND id = ?", (c, row[0], cur_id))
		c+=1
	
	#go through and split up entries where the section text is longer than split_on characters
	#select all entries with sec. text longer than split_on characters
	split_on = "3000"
	cur.execute('SELECT * FROM temp_table WHERE length(text) > '+split_on+' ORDER BY id,sec_num,split_num;')

	for row in cur.fetchall():
		#split the sec. text of entry into split_on character chunks and interate
		bs = ""
		c_split = 1
		for s in [e+". " for e in row[1].split(". ") if e]:
			#insert chunk of text into table
			if len(bs + s) > int(split_on):  
				cur.execute("INSERT INTO temp_table VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",(row[0],bs,str(row[2]),row[3],c_split,row[5],_upper_ratio(bs),_digit_ratio(bs),_special_ratio(bs)))
				c_split+= 1
				bs = s
			else:
				bs+=s
		#remove old entry
		cur.execute("DELETE from temp_table WHERE sec_head like ? AND id=? AND length(text)>"+split_on+";",(row[0],str(row[2]))) 
		
	##try to fix null headers
	#get all rows with sec_head as null
	cur.execute("SELECT * FROM temp_table WHERE sec_head like 'null'")
	rows = cur.fetchall()
	#set variables with wider scope that names can persist
	cur_head = 'null'
	cur_id = rows[0][2]
	inf = 0
	for row in rows:
		#if new doc reset
		if cur_id != row[2]:
			cur_id = row[2]
			cur_head = 'null'
			inf=0
		text = row[1].strip()
		#if the first word is all caps it's probably a title
		#check if all caps
		
		if (' ' in text and text[:text.index(' ')].upper().strip() == text[:text.index(' ')].strip() and text[:text.index(' ')].isalpha()):
			a=text.split(' ')
			c=0
			bs = ""
			#read words until words are no longer all caps
			while(c < len(a) and a[c]==a[c].upper()):
				bs += a[c]+" "
				c+=1
			#set to be header
			if len(bs[:-1])>1:
                            cur_head = bs[:-1]
                            inf = 1
		else:
			#open csv with characters that denote heading
			#for each character see if that character comes before the end of the first sentence
			for line in csv.reader(open(char_path, 'r')):
				try:
					i = text.index(line[0].strip())
					#check to see if text in this format
					#Subheading in line: It is important that the character after the colon(or any char in csv) is captial. More text...
					if(i<text.index('.') and text[i+1:i+3].strip().isupper()):
						cur_head = text[:i]
						inf = 1 
				except:
					#idk python
					s='||-//'		
		#update entry in table with new sec_head and if that sec_head was inferred (i.e changed by this code block)
		cur.execute("UPDATE temp_table SET sec_head = ?, inferred = ? WHERE sec_num = ? AND id = ? AND split_num = ?", (cur_head, inf, row[3], row[2], row[4]))

	#delete entries based on text statistics
	#the both constants are for when entries have both text stats greater than a given value
	both_upper = .1
	both_digit = .1
	#for when just upper_to_lower is greater than certain ratio
	uppper = .15
	#for when just digit_to_char is greater than certain ratio
	digit = .12
	cur.execute("DELETE from temp_table WHERE (upper_to_lower > ? AND digit_to_char > ?) OR upper_to_lower > ? OR digit_to_char > ?;",(both_upper,both_digit,uppper,digit)) 

	#get the remaining entries in the table and write them to csv
	pd.read_sql(sql='SELECT * FROM temp_table ORDER BY id,sec_num,split_num', con=conn).to_csv(csv_out_path, index=False,sep = ',',quoting=csv.QUOTE_NONNUMERIC) 

def partition_jsons(json_dir,partition_dir,json_per_folder):
    files = [os.path.join(json_dir, f) for f in os.listdir(json_dir)]
    i = 0
    curr_subdir = None
    name = ""
    if len(json_dir.split("/")[-1])>1:
        name = json_dir.split("/")[-1]
    else:
        name=json_dir.split("/")[-2]
    
    for f in files:
        # create new subdir if necessary
        if i % json_per_folder == 0:
            subdir_name = os.path.join(partition_dir, name+'{0:04d}'.format(int(i / json_per_folder + 1)))
            if not os.path.exists(subdir_name):
                os.mkdir(subdir_name)
            curr_subdir = subdir_name

        # move file to current dir
        f_base = os.path.basename(f)
        shutil.copy(f, os.path.join(subdir_name, f_base))
        i += 1

def run_partition_folders(part_folder_dir,out_csv_dir,exclude_path,char_path,limit=-1):
    c = 0
    out_csv_dir = _clean_path(out_csv_dir)
    for f in os.listdir(part_folder_dir):
        folder = os.path.join(part_folder_dir, f)
        print(folder)
        run_json_folder(folder,exclude_path,char_path,out_csv_dir+f+"bkup.csv",out_csv_dir+f+"data.csv")
        if limit>0 and c>=limit:
            break

"""**************************"""
"""END JSON PARSING FUNCTIONS"""



"""BEGIN CSV PARSING FUNCTIONS"""
"""***************************"""
#make list of PubMed ids from PubMed csv
def get_pmedid_csv(csv_file_path,output_path):
    out = open(output_path,'w')
    with open(csv_file_path, encoding='utf-8') as csvf:
        re = csv.reader(csvf, delimiter=',')
        for row in re:
            out.write(row[9]+"\n")
    out.close()

#Take PubMed csv at csv_file_path.
#Make list of entries with PMCID format "PMCID+PUBMEDID" at pmc_path.
#Make list of entries with no PMCID at nopmc_path.
def get_pmcid_csv(csv_file_path,pmc_path,nopmc_path):
    pmc = open(pmc_path,'w')
    nopmc = open(nopmc_path,'w')
    with open(csv_file_path, encoding='utf-8') as csvf:
        re = csv.reader(csvf, delimiter=',')
        for row in re:
            if "PMCID:" in row[7]:
                pmc.write(row[7].split("PMCID:")[1]+"+"+row[9]+"\n")
            else:
                nopmc.write(row[9]+"\n")
    pmc.close()
    nopmc.close()

#Add PMCID to PUBMEDIDs in pmed_id_path txt.
#Output results in format "PMCID+PUBMEDID" to output_path.
def csv_add_pcmid(csv_file_path,pmed_id_path,output_path):
    out = open(output_path,'w')
    for i in open(pmed_id_path,'r'):
        print(i.strip())
        with open(csv_file_path, encoding='utf-8') as csvf:
               re = csv.reader(csvf, delimiter=',')
               for row in re:
                   if(row[9] in i):
                       print("good")
                       out.write(row[7].split("PMCID:")[1]+"+"+row[9]+"\n")
                       break
    out.close()

def count_heads(csv_file_path):
    seen = []
    for row in csv.reader(open(csv_file_path,'r')):
        if row[0] not in seen:
            seen.append(row[0])
    return len(seen)


"""*************************"""
"""END CSV PARSING FUNCTIONS"""


"""BEGIN UTILITY FUNCTIONS"""
"""***********************"""

#Removes duplicate lines in txt file located at in_path
#Outputs to out_path
def _remove_dupes_txt(in_path, out_path):
    lines_seen = set()
    outfile = open(out_path, "w")
    for line in open(in_path, "r"):
        if line not in lines_seen:
            outfile.write(line)
            lines_seen.add(line)
    outfile.close()

#Counts the number of txts in id_txt_list.
#Counts the number of pdfs in pdf_dir_list.
#Returns the sum of pdf and txts: sum should equal 96961.
def get_count(id_txt_list, pdf_dir_list):
    c=0
    for txt in id_txt_list:
        c+= sum(1 for line in open(txt))
    for d in pdf_dir_list:
        c+=len(os.listdir(d))
    return c

def _any_rev(array,string):
    for i in array:
        if i in string:
            return True
    return False

def _convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos=set()

    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    fp.close()
    device.close()
    retstr.close()
    return text

def rem_pmcid(in_path,out_path):
    with open(in_path,'r') as inF:
        with open(out_path,'w') as outF:
            for line in inF:
                outF.write(line.split('+')[1])

def _split_every(n, s):
    return [ s[i:i+n] for i in range(0, len(s), n) ]

def _clean_path(path):
    if path[-1]!="/":
        return path+"/"
    else:
        return path

def _clean_sql(s):
    return ''.join([i if ord(i) < 128 else '' for i in s]).replace("\t",' ').replace("\n",' ').replace("\r"," ")

def get_empty_files(pdf_dir,out_path):
    out = open(out_path,'w')
    for f in os.listdir(os.fsencode(pdf_dir)):
        if os.stat(str(pdf_dir)+"/"+f.decode('utf-8')).st_size == 0:
            out.write(f.decode('utf-8').split("/")[-1].split(".pdf")[0]+"\n")
    out.close()

def sort_nonretrievable(csv_file_path, good_out_path, bad_out_path):
    good_pdf= open(good_out_path, 'w')
    bad_pdf = open(bad_out_path, 'w')
    with open(csv_file_path, encoding='utf-8') as csvf:
        readCSV = csv.reader(csvf, delimiter=',')
        for row in readCSV:
            if "doi:" not in row[3] and "PMCID" not in row[7]:
                print("BAD: "+row[9])
                bad_pdf.write(row[9]+"\n")
            else:
                print("GOOD: "+row[9])
                good_pdf.write(row[9]+"\n")
    
        good_pdf.close()
        bad_pdf.close()
        
def _txt_diff(txt1,txt2,out_txt):
    t1 = open(txt1,'r').readlines()
    t2 = open(txt2,'r').readlines()
    open(out_txt,'w').writelines(list(set(t1)-set(t2)))

def _upper_ratio(s):
    if len(s)==0:
        return 0
    u = len(re.findall('[A-Z]',s))
    l = len(re.findall('[a-z]',s))
    if u+l==0:
        return 0
    return u/(u+l)

def _digit_ratio(s):
    if len(s)==0:
        return 0
    d = len(re.findall('[0-9]',s))
    c = len(re.findall('[A-z]',s))
    if c+d==0:
        return 0
    return d/(c+d)

def _special_ratio(s):
    if len(s)==0:
        return 0
    c = len(re.findall('[A-z]',s))
    s = len(re.findall('[\\.\\!\\@\\#\\$\\%\\^\\&\\*\\(\\)\\_\\+\\-\\=]',s))
    if c+s==0:
        return 0
    return s/(c+s)

"""*********************"""
"""END UTILITY FUNCTIONS"""

if __name__ == '__main__':
    freeze_support()
    #run_id_ruby('ids_run_next.txt','kick_third_run.txt',num_threads=7)
    #run_json_folder("C:/Users/jnt11/Documents/SHIPFiles/outJSONsmall",'C:/Users/jnt11/Documents/SHIPFiles/exclude.csv','C:/Users/jnt11/Documents/SHIPFiles/char.csv','bkup.csv','sample_data.csv')
    #partition_jsons("C:/Users/jnt11/Documents/SHIPFiles/outJSONsmall","C:/Users/jnt11/Documents/SHIPFiles/testPart",10)
    run_json_folder('json0001','exclude.csv','char.csv','bk.csv','data01.csv')
