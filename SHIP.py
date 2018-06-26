import os
from multiprocessing import Pool
from datetime import datetime
import subprocess
import csv
import urllib.request
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
import unicodedata
import ctypes
import requests
import sqlite3
import json

"""BEGIN RUBY pudmebid2pdf INTERACTION FUNCTIONS"""
"""*********************************************"""

#func to process id in ruby script
def process_line(line):
    print(line.strip())
    p = subprocess.Popen("ruby pubmedid2pdf.rb "+line,shell = False,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    p.wait()
    if "failed" in str(p.stderr.read()):
        return line
    return ""

#run ruby script on list of ids at file_path and output failed ids
#to kickback_loc. Optional num_threads number of threads to run- default 10
def run_id_ruby(file_path,kickback_path,num_threads=10):
    start = datetime.now()
    pool = Pool(num_threads)
    with open(file_path) as source_file:
        results = pool.map(process_line, source_file)
    with open(kickback_path,'w') as f:
        for i in results:
            f.write(i)
    return datetime.now()-start

"""********************************************"""
"""END RUBY pudmebid2pdf INTERACTION FUNCTIONS"""


"""BEGIN PMC DOWLOAD FUNCTIONS"""
"""***************************"""
#Download pdf at download_url from PMC website.
#Save pdf to folder at pdf_output_dir and name pdf pmed_id.
#Output failed downloads to kickback_path txt.

def download_pdf_fromid(download_url,pmed_id,pdf_output_dir,kickback_path):
    kick = open(kickback_path,'a')
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
        kick.write(download_url[download_url.index("PMC"):download_url.index("/pdf/")]+"+"+pmed_id+"\n")
    kick.close()


#PREREQ: id file in format "PMCID+PUBMEDID".
#Download pdfs of entries in txt at id_file_path.
#Downloads pdfs to pdf_output_dir.
#Output failed downloads to kickback_path.
def get_from_pmcid(id_file_path,pdf_output_dir,kickback_path):
    if pdf_output_dir[-1]!="/":
        pdf_output_dir = pdf_output_dir+"/"
    with open(id_file_path,'r') as f:
        for line in f:
            a = line.split("+")
            download_pdf_fromid("https://www.ncbi.nlm.nih.gov/pmc/articles/"+a[0]+"/pdf/",
                          a[1].strip(),pdf_output_dir,kickback_path)
            print(a[0]+" "+a[1].strip())

#helper func for threaded dl
def unpack(s):
    a = s.split("+")
    print(a[0]+" "+a[1].strip())
    download_pdf_fromid("https://www.ncbi.nlm.nih.gov/pmc/articles/"+a[0]+"/pdf/",
                        a[1].strip(),a[2],a[3])
#Get_from_pmcid threaded version.
#Default 10 threads.
def get_from_pmcid_thread(id_file_path,pdf_output_dir,kickback_path,num_thread=10):
    if pdf_output_dir[-1]!="/":
        pdf_output_dir = pdf_output_dir+"/"
    pool = Pool(num_thread)
    pack = []
    for line in open(id_file_path,'r'):
        pack.append(line+"+"+pdf_output_dir+"+"+kickback_path)
    results = pool.map(unpack,pack)

def download_pdf_errors(download_url,pmed_id,pdf_output_dir):
    e404 = open("Error_404.txt",'a')
    e403_ban = open("Error_403_ipBan.txt",'a')
    e403_rem = open("Error_403_rem.txt",'a')
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

def unpack_error(s):
    a = s.split("+")
    print(a[0]+" "+a[1].strip())
    download_pdf_errors("https://www.ncbi.nlm.nih.gov/pmc/articles/"+a[0]+"/pdf/",
                        a[1].strip(),a[2])

def get_error_thread(id_file_path,pdf_output_dir,num_thread=2):
    if pdf_output_dir[-1]!="/":
        pdf_output_dir = pdf_output_dir+"/"
    pool = Pool(num_thread)
    pack = []
    for line in open(id_file_path,'r'):
        pack.append(line+"+"+pdf_output_dir)
    results = pool.map(unpack_error,pack)
    
"""*************************"""
"""END PMC DOWLOAD FUNCTIONS"""


"""BEGIN MATERIALS SECTION PARSER FUNCTIONS"""
"""****************************************"""
def extract_materials_section(pdf_path,output_path,sec_header_good,sec_header_bad):
    f = open(output_path, "w")
    text= convert_pdf_to_txt(pdf_path)
    lineiterator = iter(text.splitlines())
    for line in lineiterator:
        if len(unicodedata.normalize("NFD",line.casefold()).replace("  "," ").strip()) > 0:
            if any_rev(sec_header_good,unicodedata.normalize("NFD",line.casefold()).replace("  "," ")):
                print(line+"******************")
                print(next(lineiterator))
                for i in range(1000):
                    l = next(lineiterator)
                    print(l)
                    if not any_rev(sec_header_bad,unicodedata.normalize("NFD",l.casefold()).replace("  "," ")):
                        f.write(l+"\n")
                    else:  
                        break
                break
    f.close()

def get_materials_folder(pdf_dir,output_dir,sec_header_good,sec_header_bad):
    if pdf_dir[-1]!= "/":
        pdf_dir = pdf_dir+"/"
    if output_dir[-1] != "/":
        output_dir = output_dir+"/"
    for f in os.listdir(pdf_dir):
        if f.endswith(".pdf"):
            print(pdf_dir+f)
            extract_materials_section(pdf_dir+f,output_dir+f.split(".pdf")[0]+".txt",sec_header_good,sec_header_bad)

def unpack_pdfextract(s):
    a = s.split(",")
    print(a[0])
    extract_materials_section(a[0],a[1],a[2].split('$'),a[3].split('$'))

def get_materials_folder_thread(pdf_dir,output_dir,sec_header_good,sec_header_bad,num_threads=10):
    if pdf_dir[-1]!= "/":
        pdf_dir = pdf_dir+"/"
    if output_dir[-1] != "/":
        output_dir = output_dir+"/"
    pool = Pool(num_threads)
    pack = []
    for f in os.listdir(pdf_dir):
        if f.endswith(".pdf"):
            pack.append(pdf_dir+f+","+output_dir+f.split(".pdf")[0]+".txt,"+'$'.join(sec_header_good)+","+'$'.join(sec_header_bad))
    results = pool.map(unpack_pdfextract, pack,4)

"""**************************************"""
"""END MATERIALS SECTION PARSER FUNCTIONS"""


"""BEGIN SCIENCE-PARSE SERVER FUNCTIONS"""
"""*****************************"""

def post_science_parse(s):
    a=s.split("+")
    print(a[0])
    try:
        with open(a[0], 'rb') as f:
            r = requests.post('http://localhost:8080/v1', files={a[0]: f})
            open(a[1]+a[0].split('/')[-1][0:-4]+'.json','w',encoding='utf-8').write(r.text)
    except Exception as e:
        print("ERROR "+str(e))

def get_pdf_json(pdf_dir,out_dir,num_thread=2):
    if pdf_dir[-1]!="/":
        pdf_dir = pdf_dir+"/"
    if out_dir[-1]!="/":
        out_dir = out_dir+"/"
    pool = Pool(num_thread)
    pack = []
    for line in os.listdir(pdf_dir):
        pack.append(pdf_dir+line+"+"+out_dir)
    results = pool.map(post_science_parse,pack)

"""***************************"""
"""END SCIENCE-PARSE SERVER FUNCTIONS"""


"""BEGIN JSON PARSING FUNCTIONS"""
"""****************************"""

def run_json_folder(json_path,exclude_path):
    if json_path[-1]!="/":
        json_path = json_path+"/"
    conn = sqlite3.connect(':memory:',isolation_level=None)
    cur = conn.cursor()
    cur.execute('CREATE TABLE temp_table (sec_head varchar(255), text TEXT, id INT);')
    for file_path in os.listdir(json_path):
        file_path=json_path+file_path
        print(file_path)
        f = json.load(open(file_path,'r',encoding='utf-8'))
        if f['metadata']['sections']:
            for sec in f['metadata']['sections']:
                if sec['heading']:
                    text_clean = ''.join([i if ord(i) < 128 else '' for i in sec['text']]).replace("'",'')
                    heading_clean = ''.join([i if ord(i) < 128 else '' for i in sec['heading']]).replace("'",'')
                    cmd = "INSERT INTO temp_table VALUES ('"+heading_clean+"', '"+text_clean+"', "+file_path.split('/')[-1].split('.pdf.json')[0]+");"
                    cur.execute(cmd)

    re = csv.reader(open(exclude_path,'r',encoding='utf-8'))
    for row in re:
        cur.execute("DELETE from temp_table WHERE sec_head like '%"+row[0]+"%';")
    cur.execute("DELETE from temp_table WHERE length(text) < 500;")

    cur.execute('SELECT * FROM temp_table;')
    rows = cur.fetchall()
    for row in rows:
        print(row)

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

"""*************************"""
"""END CSV PARSING FUNCTIONS"""


"""BEGIN UTILITY FUNCTIONS"""
"""***********************"""

def remove_dupes_txt(in_path, out_path):
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

def any_rev(array,string):
    for i in array:
        if i in string:
            return True
    return False

def convert_pdf_to_txt(path):
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


"""*********************"""
"""END UTILITY FUNCTIONS"""

if __name__ == '__main__':
    run_json_folder('C:/Users/jnt11/Documents/SHIPFiles/outJSONsmall','exclude.csv')
