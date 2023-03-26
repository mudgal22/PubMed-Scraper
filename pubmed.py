#PubMed Webscraping tool
##This code works with PubMed API endpoint "eutils", Beautiful Soup and Selenium Python - for the extraction of data(article title, author name, affiliation, corresponding email, etc) through web pages of PubMed

#Load the required Libraries
import sys
import csv
import urllib.parse
import requests
from bs4 import BeautifulSoup
import numpy as np
import urllib3
import lxml
import selenium
import html5lib
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

#Creating an empty dataframe to store the extracted results
final_df = pd.DataFrame(columns=['title', 'author_name', 'affiliation', 'doi', 'date', 'email'])

# This chunk uses Beautiful Soup to extract the PMIDs of articles of interest from the article information pulled by the "eutils" endpoint of the Pubmed API 
# The articles of interest are first sorted based on the Pubmed Advanced search term queries, which are defined as search_terms1 and search_terms2 in this code. 

#Empty list to store PMIDs of the results
pmids=[]

# Define the search terms for the articles of interest from PubMed Advanced  
search_terms1 = "((((((((((((single cell analyses[MeSH Terms]) OR (single cell analysis[MeSH Terms])) OR (CITE-Seq[Title/Abstract])) OR (ATAC-Seq[Title/Abstract])) OR (RNA-Seq[Title/Abstract])) OR (umap[Title/Abstract])) OR (seurat[Title/Abstract])) OR (scanpy[Title/Abstract])) OR (bioconductor[Title/Abstract])) ) OR (spatial transcriptomics[Title/Abstract])) AND (homo sapiens[MeSH Terms])) AND 2022:2022[dp])"
search_terms2= "((((((((((cryo electron microscopies[MeSH Terms]) OR (cryo electron microscopy[MeSH Terms])) OR (microscopies, cryo electron[MeSH Terms])) OR (microscopies, cryoelectron[MeSH Terms])) OR (cryo-em[Title/Abstract])) OR (cryoem[Title/Abstract])) OR (cryogenic electron microscopy[Title/Abstract])) OR (cryo microscopy[Title/Abstract])) OR (cryo electron microscopy[Title/Abstract])) AND (homo sapiens[MeSH Terms])) AND ((\"2022\"[Date - Publication] : \"2022\"[Date - Publication]))"

# Define the current search term to use
curr_search= search_terms2

# Construct the PubMed API URL for the search
ustr1= "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={"
ustr3= "}&retmode=xml"
number_of_uids=10000
retmax_param = f"&retmax={number_of_uids}"
url= ustr1 +urllib.parse.quote(curr_search)+ ustr3+ retmax_param
#print(url)

# Send the API request and parse the response
s1 = requests.session()
response= s1.get(url)
soup = BeautifulSoup(response.content, features="html.parser")
s1.close()

#store PMIDs as a list
texts = soup.find_all('id')

for text in texts:
    pmids.append(text.get_text())

#This Chunk uses Selenium package to extract the required information from each of the extracted articles by going to their respective PubMed webpage using the list of PMIDs 

# Loop through the PMIDs and retrieve the details of each article
# This Try Except clause enables Saving the output as CSV until the latest scraped result even if the scraper errors out in the middle of the code run.
try:
    for pmid in pmids[0:25]:
        browser = webdriver.Chrome()
        article_url = "https://pubmed.ncbi.nlm.nih.gov/"+ pmid +"/"
        s2 = browser.get(article_url)

        # Wait for the expand button to be visible and click it
        try:
            expand_button = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "more-details")))
            expand_button.click()
        except:
            pass

        # Wait for the article information to be visible and extract the necessary details
        #Article information
        title_element = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, "heading-title")))
        title = title_element.text.strip()
        doi_element = browser.find_element(By.CLASS_NAME, "citation-doi")
        doi = doi_element.text.strip()
        date_element = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, "cit")))
        date = date_element.text.split(";")[0]

        #Author information
        author_super_element = WebDriverWait(browser, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, "authors-list")))
        ref_elements = author_super_element.find_elements(By.CLASS_NAME, "affiliation-link")
        author_list = author_super_element.find_elements(By.CLASS_NAME, "authors-list-item")
        author_info_list = []

        # Creating a dictionary to save author names and their respective reference numbers to extract the associated affiliation
        ref_to_author_dict = {}

        for author in author_list:
            author_name= re.sub("[^A-Za-z ]", " ", author.text)
            ref_val= re.findall(r'\d+', author.text)
            ref_to_author_dict[author_name]=ref_val

        #Affiliation information
        aff_super_element = browser.find_element(By.CLASS_NAME, 'affiliations')
        aff_elements = aff_super_element.find_elements(By.TAG_NAME, 'li')

        auth_affil = []

        # Finally associating the reference, author, and article information with the respective affiliations and storing in a temporary list "auth_affil"
        for aff_element in aff_elements:
            affiliation_text = aff_element.text
            affiliation = re.sub(r'\d+\n', '', affiliation_text)
            m = re.search(r'(\d+)\s*', affiliation_text)
            if m:
                ref_num = m.group(1)
                for auth, num in ref_to_author_dict.items():
                    if ref_num in num:
                        email_regex = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
                        email_match = re.findall(email_regex, affiliation)
                        if email_match:
                            email = email_match[0]
                        else:
                            email = ''
                        auth_affil.append([title, auth, affiliation, doi, date, email])

        df2 = pd.DataFrame(auth_affil)
        df2 = df2.rename(columns={0: 'title', 1: 'author_name', 2: 'affiliation', 3:'doi', 4:'date', 5:'email'})
        print(df2)
        final_df = final_df.append(df2)
        browser.quit()

except:
    final_df.to_csv("pubmed_out.csv", index=False)

else:
    final_df.to_csv("pubmed_out.csv", index=False)
