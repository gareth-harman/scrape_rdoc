#!/Users/harmang/anaconda3/bin/python

'''
Created: 07-11-2021

Script to parse and return structure of RDoc items
''' 


import numpy as np
import pandas as pd 
import requests
from bs4 import BeautifulSoup


#################################################

def ret_tag(s):

    ''' Function to return nice tags for constructs '''

    x = s.split(':')[-1]; x = x[1:]

    # Replace chars
    for c in [', ', '/', '; ', ' - ', ' ']:
        x = x.replace(c, '-')

    for c in ['(', ')', '"']:
        x = x.replace(c, '')

    # For some reason language...
    if x == 'language':
        x += '-behavior'

    return x 
    

#################################################

def validate_url(x):
   
    ''' Function to validate URLs '''

    return requests.head(x).status_code == 200


#################################################

def parse_constructs(URL, output, write = True):
    
    ''' 
    Function to parse RDoc constructs and subconstructs 
    and write the hierarchy to a csv
    '''
        
    # Load and return lines 
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")

    # Parse RDoc section
    rdoc_tree = soup.find('section', 'rdoc-tree')
    rdoc_tree = rdoc_tree.find('ul')
    
    # Store domain, construct, sub, url
    rdoc_full = {'domain': [],
                 'construct': [],
                 'subconstruct': [],
                 'url': []} 

    # Iterate through domains in RDoc_tree
    for domain in rdoc_tree.findChildren(recursive = False):
    
        # Get list of items and remove ' '
        vals = [x.lower() for x in domain.text.split('\n') if x != '']

        # Current domain
        curr_domain = ret_tag(vals[0]); const_list = vals[1:]

        print('Parsing RDoc domain: {}'.format(curr_domain))

        # Loop through items in list
        for ii in const_list:
       
            sub_const = '-' # Set to evaluate sub or const

            # Replace const if it is a construct 
            if ii[:3] == 'con':
                curr_const = ret_tag(ii)
            else:
                sub_const = ret_tag(ii)

            # Create URL 
            if sub_const != '-':
                const_url = URL + sub_const
            else:
                const_url = URL + curr_const

            rdoc_full['domain'].append(curr_domain)
            rdoc_full['construct'].append(curr_const)
            rdoc_full['subconstruct'].append(sub_const)
            rdoc_full['url'].append(const_url)

    # Write output if we want 
    if write:
        rdoc = pd.DataFrame(rdoc_full)
        rdoc.to_csv(output + 'rdoc.csv', index = None)


#################################################

def open_hier(filePath):

    ''' Load and return filepath from above '''

    rdoc = pd.read_csv(filePath)

    return rdoc


#################################################

def parse_features(rdoc):

    '''

    Function to return the below compoonents from each RDoc construct

    molecule    cell    circuit     physfunction
    behavior    selfreport  paradigm

    '''

    print('Parsing construct features...\n')

    d_full = {}

    for ii in ['molecule', 'cell', 'circuit', 'physfunction', 'behavior',
               'selfreport', 'paradigm']:
               d_full[ii] = {}

    for ind, url in enumerate(rdoc['url']):
           
        print('Parsing: {}'.format(url.split('/')[-1]))

        # Load and return lines 
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        for unit in soup.find_all(class_ = 'rdoc-unit'):

            val = unit.text.split('\n\n')[1].lower()
            d_full[unit.get('id').split('_')[0]][url.split('/')[-1]] = val.split('\n')

    return d_full 


#################################################

def ret_unique_elems(d_full):

    ''' Function to store all unique items from each component '''

    d = {} # Main dict

    print('Creating unique elements...\n')

    # Iterate through molecule, cell, etc
    for key, item in d_full.items():
        
        temp_hold = [] # Store items

        # Iterate through each construct
        for sub_key, sub_item in item.items():
           
            # Store each element
            [temp_hold.append(x) for x in sub_item]
        
        list_store = list(set(temp_hold))
        list_store.sort()

        d[key] = list_store

    return d
   

#################################################

def create_matrices(rdoc, d_full, d, output, write = True):

    ''' Function to create binary feature matrices for each construct and element '''

    final_d = {} # Store these matrices 

    # Loop through each element (circuit, molecule, etc...)
    for elem, elem_d in d.items():
   
        print('Parsing: {}'.format(elem))

        # Store each variable
        final_d[elem] = {'vals': elem_d}

        # Loop through each construct
        for const, conts_d in d_full[elem].items():
            
            x = np.zeros(len(elem_d))
            b = [ind for ind, x in enumerate(elem_d) if x in d_full[elem][const]]

            x[np.array(b)] = 1
            
            final_d[elem][const] = x
  
    # Write if told to
    if write:

        # Write each dataframe separately
        for name, dd in final_d.items():
            
            print('Writing: {}'.format(name + '.csv...'))

            df = pd.DataFrame(dd)
            df.to_csv(output + name + '.csv', index = None)
    else:
        return final_d


#################################################
# RUN 
#################################################

if __name__ == "__main__":

    # Parent url
    parent_url = 'https://www.nimh.nih.gov/research/research-funded-by-nimh/rdoc/constructs/'
    output_dir = '/Users/harmang/Desktop/git_home/labwork/scrape_RDoc/scraping_output/' 

    # Scrape the constructs and write
    parse_constructs(parent_url, output_dir) 

    # Open this file
    rdoc = open_hier(output_dir + 'rdoc.csv')

    # Parse construct elements (cicrcuits, cells, etc) 
    d_full = parse_features(rdoc) 

    # Get unique elements
    d = ret_unique_elems(d_full)

    # Write output
    create_matrices(rdoc, d_full, d, output_dir)
