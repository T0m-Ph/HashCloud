#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : resources.py
# Author             : TomPh
# Date created       : 29 May 2023

import boto3
import json
import os

from hashcloud.AWS_Resources import creation
from hashcloud.AWS_Resources import deletion

def initialize(**kwargs):
    created_resources = {}

    unique_suffix = '_hashcloud_project'

    try:
        with open('config.json', 'r') as file:
            config = json.load(file)
            unique_suffix = config['unique_suffix']    
    except Exception as e:
        print("No config file found, using default.")
    
    try:
        with open('build/resources.json', 'r') as file:
            print("Loading existing config")
            created_resources = json.load(file)
    except:
        print("No existing resources found, building environment.")

    try:
        bucket_name = created_resources.get('bucket_name')
        if not bucket_name:
            # Create S3 bucket
            bucket_name = 'bucket' + unique_suffix
            bucket_name = creation.create_s3_bucket(bucket_name)
            created_resources['bucket_name'] = bucket_name

        role_name = created_resources.get('role_name')
        role_arn = created_resources.get('role_arn')
        if not role_name:
            # Create IAM role
            role_name = 'iam' + unique_suffix
            role_name, role_arn = creation.create_iam_role(role_name, bucket_name)
            created_resources['role_name'] = role_name
            created_resources['role_arn'] = role_arn

        repository_name = created_resources.get('repository_name')
        repository_uri = created_resources.get('repository_uri')
        if not repository_name or not repository_uri:
            # Create ECR repository
            repository_name = 'ecr_epo' + unique_suffix
            repository_name, repository_uri = creation.create_ecr_repository(repository_name)
            created_resources['repository_name'] = repository_name
            created_resources['repository_uri'] = repository_uri

        # Build and upload docker to ECR
        dockerfile_path = 'Docker'
        aws_region = 'us-east-1'
        image_name = 'docker' + unique_suffix
        creation.build_and_upload_image(dockerfile_path, repository_name, aws_region, image_name)

        job_definition_arn = created_resources.get('job_definition_arn')
        if not job_definition_arn:
            # Create Job definition
            job_definition_name = 'batch_job' + unique_suffix
            container_image = repository_uri + ":latest"
            command = []
            job_definition_arn = creation.create_batch_job_definition(job_definition_name, role_arn, role_arn, container_image, command)
            created_resources['job_definition_arn'] = job_definition_arn

        
        default_vpc = boto3.client('ec2').describe_vpcs(
            Filters=[
                {
                    'Name': 'isDefault',
                    'Values': ['true']
                }
            ]
        )['Vpcs'][0]
        default_vpc_id = default_vpc['VpcId']

        subnet_id = created_resources.get('subnet_id')
        if not subnet_id:
            # Create a subnet in the default VPC
            vpc_cidr_block = default_vpc['CidrBlock']
            subnet_cidr_block = f'{vpc_cidr_block[:-6]}100.0/24'
            subnet_id = creation.create_subnet(default_vpc_id, subnet_cidr_block)
            created_resources['subnet_id'] = subnet_id

        security_group_id = created_resources.get('security_group_id')
        if not security_group_id:
            # Create a security group in the default VPC
            group_name = 'sg' + unique_suffix
            description = 'Security Group for ' + unique_suffix
            security_group_id = creation.create_security_group(group_name, description, default_vpc_id)
            created_resources['security_group_id'] = security_group_id

        compute_environment_arn = created_resources.get('compute_environment_arn')
        if not compute_environment_arn:
            # Create Compute environment
            service_role_arn = boto3.client('iam').get_role(RoleName='AWSServiceRoleForBatch')['Role']['Arn']
            compute_environment_name = 'compute_env' + unique_suffix
            subnet_ids = [subnet_id]
            security_group_ids = [security_group_id]
            compute_environment_arn = creation.create_batch_compute_environment(compute_environment_name, service_role_arn, subnet_ids, security_group_ids)
            created_resources['compute_environment_arn'] = compute_environment_arn

        job_queue_arn = created_resources.get('job_queue_arn')
        if not job_queue_arn:
            # Create a Job Queue
            job_queue_name = 'job_q' + unique_suffix
            compute_environment_order = [
                {
                    'order': 1,
                    'computeEnvironment': compute_environment_arn
                }
            ]
            job_queue_arn = creation.create_batch_job_queue(job_queue_name, compute_environment_order)
            created_resources['job_queue_arn'] = job_queue_arn
    
    except Exception as e:
        print(e)
    finally:
        # Save resources to file
        resource_file_name = 'build/resources.json'
        with open(resource_file_name, 'w') as file:
            json.dump(created_resources, file)
        print(f"Resources information saved to '{resource_file_name}' file.")

def cleanup(**kwargs):
    with open('build/resources.json', 'r') as file:
        created_resources = json.load(file)

    bucket_name = created_resources.get('bucket_name')
    if bucket_name:
        deletion.delete_s3_bucket(bucket_name)

    role_name = created_resources.get('role_name')
    if role_name:
        deletion.delete_iam_role(role_name)

    job_definition_arn = created_resources.get('job_definition_arn')
    if job_definition_arn:
        deletion.delete_batch_job_definition(job_definition_arn)
    
    job_queue_arn = created_resources.get('job_queue_arn')
    if job_queue_arn:
        deletion.delete_batch_job_queue(job_queue_arn)
    
    compute_environment_arn = created_resources.get('compute_environment_arn')
    if compute_environment_arn:
        deletion.delete_batch_compute_environment(compute_environment_arn)

    subnet_id = created_resources.get('subnet_id')
    if subnet_id:
        deletion.delete_subnet(subnet_id)

    security_group_id = created_resources.get('security_group_id')
    if security_group_id:
        deletion.delete_security_group(security_group_id)

    repository_name = created_resources.get('repository_name')
    if repository_name:
        deletion.delete_ecr_repository(repository_name)

    # Remove the resources file
    os.remove('build/resources.json')
    os.remove('build/jobs.json')