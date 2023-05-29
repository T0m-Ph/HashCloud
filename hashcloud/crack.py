#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : crack.py
# Author             : TomPh
# Date created       : 29 May 2023

import boto3
import json
from tabulate import tabulate
import datetime

s3 = boto3.client('s3')

wordlist_folder = 'passlists'
to_crack_folder = 'to_crack'

bucket_name = None
job_definition_arn = None
job_queue_arn = None

try:
    with open('build/resources.json', 'r') as file:
        created_resources = json.load(file)
        bucket_name = created_resources.get('bucket_name')
        job_definition_arn = created_resources.get('job_definition_arn')
        job_queue_arn = created_resources.get('job_queue_arn')
except Exception as e:
    print(e)

def get_wordlist_s3(file_name):
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=f"{wordlist_folder}/{file_name}")
    if response['KeyCount'] > 0:
        for obj in response['Contents']:
            if obj['Key'] == f"{wordlist_folder}/{file_name}":
                return f"s3://{bucket_name}/{wordlist_folder}/{file_name}"
    return None

def crack_hashes(f, w, options, **kwargs):
    if not bucket_name or not job_definition_arn or not job_queue_arn:
        print("Missing resources, run the setup first.")
        return
    
    batch = boto3.client('batch')
    job_name = "crack_job"

    file_name = f.split('/')[-1]
    s3.upload_file(f, bucket_name, f"{to_crack_folder}/{file_name}")
    to_crack_file_path = f"s3://{bucket_name}/{to_crack_folder}/{file_name}"
    wordlist_file_path = get_wordlist_s3(w)
    if wordlist_file_path is None:
        print("Wordlist was not found on the S3 bucket")
        return
    
    vCPU = 1
    MEMORY = 2048

    try:
        with open('config.json', 'r') as file:
            config = json.load(file)
            vCPU = config['vCPU']
            MEMORY = config['MEMORY']  
    except Exception as e:
        print("No config file found, using default.")

    command = ["/tmp/run.sh"]
    command.extend(options.split(" "))
    command.append("-w")
    command.append("4")
    command.append(to_crack_file_path)
    command.append(wordlist_file_path)

    response = batch.submit_job(
        jobName=job_name,
        jobQueue=job_queue_arn,
        jobDefinition=job_definition_arn,
        containerOverrides={
            'command': command,
            'resourceRequirements': [
                {
                    'value': f"{vCPU}",
                    'type': 'VCPU'
                },
                {
                    'value': f"{MEMORY}",
                    'type': 'MEMORY'
                },
            ],
        }
    )

    job_id = response['jobId']
    jobs = []

    try:
        with open('build/jobs.json', 'r') as file:
            jobs = json.load(file)
    except Exception as e:
        jobs = []
    finally:
        jobs.append({
            "id": job_id,
            "file": f
        })

    try:
        with open('build/jobs.json', 'w') as file:
            file.write(json.dumps(jobs))
    except Exception as e:
        print(e)

    return job_id

def crack_jobs_status(**kwargs):
    try:
        with open('build/jobs.json', 'r') as file:
            file_content = file.read()
            jobs = json.loads(file_content)
    except:
        jobs = []
    
    if jobs:
        job_ids = [j['id'] for j in jobs]

        batch = boto3.client('batch')
        response = batch.describe_jobs(
            jobs=job_ids
        )
        job_statuses = response['jobs']

    jobs_list = []
    headers = ['Hash File', 'Status', 'Runtime']

    for j in jobs:
        for js in job_statuses:
            if j['id'] == js['jobId']:
                status = js['status']
                interval_dt = None
                time_taken = '-'
                if status == 'SUCCEEDED' or status == 'FAILED':
                    started_dt = datetime.datetime.fromtimestamp(js['startedAt']/1000)
                    stopped_dt = datetime.datetime.fromtimestamp(js['stoppedAt']/1000)
                    interval_dt = stopped_dt - started_dt
                elif status == 'RUNNING':
                    started_dt = datetime.datetime.fromtimestamp(js['startedAt']/1000)
                    now = datetime.datetime.now()
                    interval_dt = now - started_dt

                if interval_dt != None:
                    hours = interval_dt.seconds // 3600
                    minutes = interval_dt.seconds // 60
                    seconds = interval_dt.seconds % 60
                    time_taken =  f"{hours}h:{minutes}m:{seconds}s"
                jobs_list.append([j['file'], status, time_taken])
                break
    print(tabulate(jobs_list, headers=headers))
         
def get_results(f, **kwargs):
    s3 = boto3.client('s3')
    try:
        s3.download_file(bucket_name, f"cracked/{f}", f"cracked.txt")
    except Exception as e:
        print(f"Cracked file not available. Either the job is still running or the hash was not cracked.")
    else:
        try:
            with open('cracked.txt', 'r') as file:
                file_content = file.read()
                print(file_content)
        except:
            print("Unknown error happened")