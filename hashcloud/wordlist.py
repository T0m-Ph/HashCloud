#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : wordlist.py
# Author             : TomPh
# Date created       : 29 May 2023

import boto3
import json

s3 = boto3.client('s3')

wordlist_folder = 'passlists'
bucket_name = None

try:
    with open('build/resources.json', 'r') as file:
        created_resources = json.load(file)
        bucket_name = created_resources.get('bucket_name')
except:
    pass

def list_wordlists(**kwargs):
    if not bucket_name:
        print("Missing resources, run the setup command first.")
        return
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=wordlist_folder)
    if response['KeyCount'] > 0:
        for obj in response['Contents']:
            print(obj['Key'].split('/')[-1])
    else:
        print("No wordlists availale")

def upload_wordlist(f, **kwargs):
    if not bucket_name:
        print("Missing resources, run the setup command first.")
        return
    file_name = f.split('/')[-1]
    res = s3.upload_file(f, bucket_name, f"{wordlist_folder}/{file_name}")
    print(f"File uploaded successfully to s3://{bucket_name}/{wordlist_folder}/{file_name}")