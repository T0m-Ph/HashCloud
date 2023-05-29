#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : creation.py
# Author             : TomPh
# Date created       : 29 May 2023

import boto3
import json
import subprocess
import docker
import base64
import time

def create_s3_bucket(bucket_name):
    s3 = boto3.client('s3')
    s3.create_bucket(
        Bucket=bucket_name,
        ACL='private'
    )

    print(f"S3 bucket '{bucket_name}' created successfully.")
    return  bucket_name

def create_iam_role(role_name, bucket_name):
    iam = boto3.client('iam')
    role_response = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ecs-tasks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        })
    )

    print(f"IAM role '{role_name}' created successfully.")

    iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess'
    )
    iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn='arn:aws:iam::aws:policy/CloudWatchLogsFullAccess'
    )
    iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn='arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy'
    )

    print(f"Policy attached to IAM role '{role_name}' successfully.")
    role_arn =  role_response['Role']['Arn']
    return role_name, role_arn


def create_batch_job_definition(job_definition_name, job_role_arn, execution_role_arn, container_image, command):
    batch = boto3.client('batch')
    response = batch.register_job_definition(
        jobDefinitionName=job_definition_name,
        type='container',
        platformCapabilities= ['FARGATE'],
        containerProperties={
            'image': container_image,
            'command': command,
            'jobRoleArn': job_role_arn,
            'executionRoleArn': job_role_arn,
            'user': 'hashcat',
            'networkConfiguration': {
                'assignPublicIp': 'ENABLED'
            },
            'resourceRequirements': [
                {
                    'value': '1',
                    'type': 'VCPU'
                },
                {
                    'value': '2048',
                    'type': 'MEMORY'
                },
            ],
        }
    )

    job_definition_arn = response['jobDefinitionArn']
    print(f"Batch job definition '{job_definition_name}' created successfully.")
    return job_definition_arn

def create_batch_job_queue(job_queue_name, compute_environment_order):
    batch = boto3.client('batch')
    compute_environment_arn = compute_environment_order[0]['computeEnvironment']

    while True:
        response = batch.describe_compute_environments(computeEnvironments=[compute_environment_arn])
        status = response['computeEnvironments'][0]['status']
        
        if status == 'VALID':
            break
        
        print(f"Waiting for compute environment '{compute_environment_arn}' to be in a valid state...")
        time.sleep(5)

    response = batch.create_job_queue(
        jobQueueName=job_queue_name,
        state='ENABLED',
        priority=1,
        computeEnvironmentOrder=compute_environment_order
    )

    job_queue_arn = response['jobQueueArn']
    print(f"Batch job queue '{job_queue_name}' created successfully.")
    return job_queue_arn


def create_batch_compute_environment(compute_environment_name, service_role_arn, subnet_ids, security_group_ids):
    batch = boto3.client('batch')
    response = batch.create_compute_environment(
        computeEnvironmentName=compute_environment_name,
        type='MANAGED',
        state='ENABLED',
        computeResources={
            'type': 'FARGATE_SPOT',
            'maxvCpus': 256,
            'subnets': subnet_ids,
            'securityGroupIds': security_group_ids,
        },
        serviceRole=service_role_arn
    )

    compute_environment_arn = response['computeEnvironmentArn']
    print(f"Batch compute environment '{compute_environment_name}' created successfully.")
    return compute_environment_arn

def create_subnet(vpc_id, cidr_block):
    ec2 = boto3.client('ec2')
    response = ec2.create_subnet(
        VpcId=vpc_id,
        CidrBlock=cidr_block
    )

    subnet_id = response['Subnet']['SubnetId']
    print(f"Subnet '{cidr_block}' created successfully.")

    return subnet_id

def create_security_group(group_name, description, vpc_id):
    ec2 = boto3.client('ec2')
    response = ec2.create_security_group(
        GroupName=group_name,
        Description=description,
        VpcId=vpc_id
    )

    group_id = response['GroupId']
    print(f"Security group '{group_name}' created successfully.")

    return group_id

def build_and_upload_image(dockerfile_path, ecr_repository_name, aws_region, image_name):
    client = docker.from_env()
    try:
        image, build_logs = client.images.build(path=dockerfile_path, tag=image_name, rm=True)
        for log in build_logs:
            print(log)
        
        print(f"Docker image '{image_name}' built successfully.")
        
    except docker.errors.BuildError as e:
        print(f"Failed to build Docker image: {str(e)}")
        return False

    # Authenticate to the ECR registry
    ecr = boto3.client('ecr', region_name=aws_region)
    response = ecr.get_authorization_token()
    authorization_data = response['authorizationData'][0]
    registry = authorization_data['proxyEndpoint']
    token = base64.b64decode(authorization_data['authorizationToken']).decode('utf-8')
    username = token.split(':')[0]
    password = token.split(':')[1]
    subprocess.run(['docker', 'login', '-u', username, '-p', password, registry], check=True)

    # Tag the Docker image
    registry = registry.strip("https://")
    image_tag = f"{registry}/{ecr_repository_name}:latest"
    client = docker.from_env()
    image = client.images.get(image_name)
    image.tag(image_tag)

    # Push the Docker image to ECR
    try:
        push_logs = client.images.push(repository=image_tag)
        print(push_logs)
        print(f"Docker image '{image_tag}' pushed to ECR successfully.")
    except docker.errors.APIError as e:
        print(f"Failed to push Docker image to ECR: {str(e)}")

    print(f"Docker image '{image_tag}' built and uploaded to ECR repository '{ecr_repository_name}'.")

def create_ecr_repository(repository_name):
    ecr = boto3.client('ecr')
    response = ecr.create_repository(
        repositoryName=repository_name
    )

    repository_uri = response['repository']['repositoryUri']
    print(f"ECR repository '{repository_name}' created successfully.")

    return repository_name, repository_uri