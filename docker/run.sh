#!/bin/bash

# Copy file to crack
to_crack=${@: -2: 1}
echo "TO_CRACK: $to_crack"
aws s3 cp "${to_crack}" - > "/tmp/tocrack.txt"

# Copy dictionnary file
wordlist=${!#}
echo "WORDLIST: $wordlist"
aws s3 cp "${wordlist}" - > "/tmp/wordlist.txt"

args=${@:1:($#-2)}
echo "ARGS: $args"

crack_filename="${to_crack##*/}"
mkdir -p ~/.local/share/hashcat/sessions
hashcat $args -o /tmp/${crack_filename} /tmp/tocrack.txt /tmp/wordlist.txt

bucket_path="${wordlist#s3://}"
bucket_name="${bucket_path%%/*}"
aws s3 cp /tmp/${crack_filename} s3://${bucket_name}/cracked/