#!/usr/bin/env python

#
#	Clair Kronk
#	14 June 2021
#	workshop_v1.py
#

from PIL import Image
from pprint import pprint
from tika import parser

import argparse
import img2pdf
    # https://www.geeksforgeeks.org/python-convert-image-to-pdf-using-img2pdf-module/

import json

import ocrmypdf
    # This import causes `[WinError 2] The system cannot find the file specified`
    # for some unknown reason.

    # (requires running in 3.6 or 3.7; I used an Anaconda virtual environment
    # named python37, see details here:)
    # https://uoa-eresearch.github.io/eresearch-cookbook/recipe/2014/11/20/conda/

    # conda init python37
    # conda activate python37
    
    # Things you need: https://ocrmypdf.readthedocs.io/en/latest/installation.html#installing-with-python-pip
    
    # GhostScript: https://www.ghostscript.com/download/gsdnld.html
    # Tesseract: https://github.com/simonflueckiger/tesserocr-windows_build/releases
    #  ^ https://digi.bib.uni-mannheim.de/tesseract/
    #   Set env variables:
    #       - OCRMYPDF_TESSERACT
    #       - TESSDATA_PREFIX
    #           (see: https://github.com/jbarlow83/OCRmyPDF/issues/124)
    # qpdf: https://sourceforge.net/projects/qpdf/files/
    #  ^ https://stackoverflow.com/questions/41570633/how-to-build-qpdf-on-windows
    
import os
    
import owlready2

import re

import requests
    
import wordninja


import urllib.request, urllib.error, urllib.parse

# https://github.com/ncbo/ncbo_rest_sample_code/blob/master/python/python3/annotate_text.py
# http://data.bioontology.org/documentation
REST_URL = "http://data.bioontology.org" #/search
API_KEY = "4c0278fe-7057-4b43-a569-995e0c234ce4"
    

def main():
	
    parser = argparse.ArgumentParser(description="Get text from image.")
    parser.add_argument("image_path", metavar="i", help="The path to the image being used.")
    args = parser.parse_args()
    image_path = args.image_path
    
    pdf_from_image_file_name = convert_to_pdf(image_path)
    pdf_w_ocr_file_name = ocr_pdf()
    raw_text_from_ocr_pdf = get_text_from_pdf()
    print(raw_text_from_ocr_pdf)
    
    print("\n\n")

    wordninja_array_from_raw_text = correct_text(raw_text_from_ocr_pdf) 
    wordninja_string_from_raw_text = " ".join(wordninja_array_from_raw_text)
    print(wordninja_string_from_raw_text)
    
    # Annotate using the provided text
    ontology_name = "GSSO"
    annotations = get_json(REST_URL + "/annotator?ontologies=" + ontology_name + "&text=" + urllib.parse.quote(wordninja_string_from_raw_text))

    # Print out annotation details
    pref_label_array = print_annotations(annotations)
    
    for x in pref_label_array:
        print("- " + make_printable(x))
    
    exit()
    
def convert_to_pdf(image_path, new_pdf_file_name="pdf_from_image"):
    temp_image = Image.open(image_path)
    pdf_bytes = img2pdf.convert(temp_image.filename)
    new_file = open('./' + new_pdf_file_name + '.pdf', 'wb')
    new_file.write(pdf_bytes)
    temp_image.close()
    new_file.close()
    return new_pdf_file_name

def ocr_pdf(pdf_file_path="./pdf_from_image.pdf", new_pdf_file_name="pdf_w_ocr.pdf"):
    ocrmypdf.ocr(pdf_file_path, './'+new_pdf_file_name, deskew=True)
    return new_pdf_file_name

def get_text_from_pdf(pdf_file_path="./pdf_w_ocr.pdf"):
    raw_pdf = parser.from_file(pdf_file_path)
    return raw_pdf['content']
    
def correct_text(text_string):
    return wordninja.split(text_string)
    
def get_json(url):
    opener = urllib.request.build_opener()
    opener.addheaders = [('Authorization', 'apikey token=' + API_KEY)]
    #params = '?ontologies=GSSO'
    params = ""
    return json.loads(opener.open(url+params).read())

def print_annotations(annotations, get_class=True):
    pref_label_array = []
    pref_label_dict = {}

    for result in annotations:
        class_details = result["annotatedClass"]
        if get_class:
            try:
                class_details = get_json(result["annotatedClass"]["links"]["self"])
            except urllib.error.HTTPError:
                print(f"Error retrieving {result['annotatedClass']['@id']}")
                continue
        
        print("Class details")
        print("\tid: " + make_printable(class_details["@id"]))
        print("\tprefLabel: " + make_printable(class_details["prefLabel"]))
        pref_label_array.append(str(class_details["prefLabel"]).lower())
        pref_label_dict[make_printable(class_details["@id"])] = make_printable(class_details["prefLabel"])
        
        print("\n\n")
    
    pref_label_array = list(set(pref_label_array))
    return(pref_label_array)
    
def make_printable(text):
	regex = re.compile(r'[^\x00-\x7F]+')
	printable = re.sub(regex, '?', str(text))
	return printable
    
if __name__ == '__main__':
	main()