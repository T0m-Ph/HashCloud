#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File name          : __main__.py
# Author             : TomPh
# Date created       : 29 May 2023

import argparse
from hashcloud.AWS_Resources import resources
from hashcloud import wordlist
from hashcloud import crack

def main():
    parser = argparse.ArgumentParser(description='Run hashcat in the cloud.')
    subparsers = parser.add_subparsers(required=True)

    ########### Setup subparser ###########
    setup_parser = subparsers.add_parser('setup', help='Manage setup.')
    setup_subparsers = setup_parser.add_subparsers(required=True)

    # Create command
    create_parser = setup_subparsers.add_parser('create', help='Create AWS resources required.')
    create_parser.set_defaults(func=resources.initialize)

    # Cleanup command
    cleanup_parser = setup_subparsers.add_parser('cleanup', help='Delete AWS resources created.')
    cleanup_parser.set_defaults(func=resources.cleanup)


    ########### Wordlists subparser ###########
    wordlists_parser = subparsers.add_parser('wordlists', help='Manage wordlists.')
    wordlists_subparsers = wordlists_parser.add_subparsers(required=True)

    # List command
    list_parser = wordlists_subparsers.add_parser('list', help='List all wordlists.')
    list_parser.set_defaults(func=wordlist.list_wordlists)

    # Upload command
    upload_parser = wordlists_subparsers.add_parser('upload', help='Upload a wordlist.')
    upload_parser.add_argument('-f', type=str, help='Path to the wordlist file.', required=True)
    upload_parser.set_defaults(func=wordlist.upload_wordlist)


    ########### Crack subparser ###########
    crack_parser = subparsers.add_parser('crack', help='Crack a file.')
    crack_subparsers = crack_parser.add_subparsers(required=True)

    # Initiate command
    initiate_parser = crack_subparsers.add_parser('initiate', help='Initiate a new cracking job.')
    initiate_parser.add_argument('-f', type=str, help='Path to the file to crack.', required=True)
    initiate_parser.add_argument('-w', type=str, help='Name of the wordlist to use for cracking.', required=True)
    initiate_parser.add_argument('--options', type=str, help='Specify additional hashcat options for cracking.', required=True)
    initiate_parser.set_defaults(func=crack.crack_hashes)

    # Satus command 
    status_parser = crack_subparsers.add_parser('status', help='Check cracking job status.')
    status_parser.set_defaults(func=crack.crack_jobs_status)

    # Result command
    result_parser = crack_subparsers.add_parser('result', help='Get the result from a completed cracking job.')
    result_parser.add_argument('-f', type=str, help='File to get the results for.', required=True)
    result_parser.set_defaults(func=crack.get_results)

    args = parser.parse_args()
    args.func(**vars(args))

if __name__ == '__main__':
    main()