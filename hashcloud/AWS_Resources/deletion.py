#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : deletion.py
# Author             : TomPh
# Date created       : 29 May 2023

import boto3
import time

def delete_s3_bucket(bucket_name):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    bucket.objects.all().delete()
    s3 = boto3.client('s3')
    s3.delete_bucket(Bucket=bucket_name)
    print(f"S3 bucket '{bucket_name}' deleted successfully.")

def delete_iam_role(role_name):
    iam = boto3.client('iam')
    iam.detach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess')
    iam.detach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/CloudWatchLogsFullAccess')
    iam.detach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy')
    iam.delete_role(RoleName=role_name)

    print(f"IAM role '{role_name}' deleted successfully.")

def delete_batch_job_definition(job_definition_arn):
    batch = boto3.client('batch')
    batch.deregister_job_definition(
        jobDefinition=job_definition_arn
    )

    print(f"Batch job definition '{job_definition_arn}' deleted successfully.")

def delete_batch_job_queue(job_queue_arn):
    batch = boto3.client('batch')
    batch.update_job_queue(
        jobQueue=job_queue_arn,
        state='DISABLED'
    )

    while True:
        response = batch.describe_job_queues(jobQueues=[job_queue_arn])
        status = response['jobQueues'][0]['status']
        
        if status == 'VALID':
            break
        print("Waiting")
        time.sleep(5)

    batch.delete_job_queue(
        jobQueue=job_queue_arn
    )

    print(f"Batch job queue '{job_queue_arn}' deleted successfully.")

def delete_batch_compute_environment(compute_environment_arn):
    batch = boto3.client('batch')
    batch.update_compute_environment(
        computeEnvironment=compute_environment_arn,
        state='DISABLED'
    )

    while True:
        response = batch.describe_compute_environments(computeEnvironments=[compute_environment_arn])
        status = response['computeEnvironments'][0]['status']
        
        if status == 'VALID':
            break
        
        print(f"Waiting for compute environment '{compute_environment_arn}' to be in a valid state...")
        time.sleep(5)

    batch.delete_compute_environment(
        computeEnvironment=compute_environment_arn
    )

    print(f"Batch compute environment '{compute_environment_arn}' deleted successfully.")

def delete_subnet(subnet_id):
    ec2 = boto3.client('ec2')
    ec2.delete_subnet(
        SubnetId=subnet_id
    )

    print(f"Subnet '{subnet_id}' deleted successfully.")

def delete_security_group(group_id):
    ec2 = boto3.client('ec2')
    ec2.delete_security_group(
        GroupId=group_id
    )

    print(f"Security group '{group_id}' deleted successfully.")

def delete_ecr_repository(repository_name):
    ecr = boto3.client('ecr')
    ecr.delete_repository(
        repositoryName=repository_name,
        force=True
    )

    print(f"ECR repository '{repository_name}' deleted successfully.")