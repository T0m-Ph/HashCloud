# HashCloud

## Installation

Use the command below to install the dependencies required for the project.
```
pip install -r requirements.txt
```

## Usage

The HashCloud uses an S3 bucket to store the wordlists used by hashcat, and Fargate to run the crack batch jobs. Before using the tool, we need to spin up all required cloud resources. Use the setup command (see below) to do so.

Once resources have been setup, the standard way of using the tool is:
- Uploading a wordlist to the S3 bucket (use the `wordlists` command to manage wordlists).
- Running crack jobs and checking on the results (see the `crack` command below).

### Spin up and tear down resources

```
usage: main.py setup [-h] {create,cleanup} ...

positional arguments:
  {create,cleanup}
    create          Create AWS resources required.
    cleanup         Delete AWS resources created.

```

### Manage wordlists

```
usage: main.py wordlists [-h] {list,upload} ...

positional arguments:
  {list,upload}
    list         List all wordlists.
    upload       Upload a wordlist.
```

### Crack files

```
usage: main.py crack [-h] {initiate,status,result} ...

positional arguments:
  {initiate,status,result}
    initiate            Initiate a new cracking job.
    status              Check cracking job status.
    result              Get the result from a completed cracking job.
```