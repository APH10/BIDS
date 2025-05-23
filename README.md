# BIDS
BIDS (Binary Identification of Dependencies with Search). The BIDS project will deliver tooling to analyse ELF binaries and extract 
key features for indexing and searching. The tooling to index these binary features in a search engine uses an inverted index.

**NOTE** that BIDS is not designed to detect the presence of malware; it is intended to help understand the scope of a binary and to support vulnerability analysis activities.

This project is sponsored by NLNET https://nlnet.nl/project/BIDS/.

## Installation

To install use the following command:

`pip install bids-analyser`

Alternatively, just clone the repo and install dependencies using the following command:

`pip install -U -r requirements.txt`

The tool requires Python 3 (3.9+). It is recommended to use a virtual python environment especially
if you are using different versions of python. `virtualenv` is a tool for setting up virtual python environments which
allows you to have all the dependencies for the tool set up in a single environment, or have different environments set
up for testing using different versions of Python.

The installation process installs 4 separate tools:
- [bids-analyser]() which analyses an ELF binary and extracts dependency and symbolic information into a JSON file.
- bids-scan which analyses a set of ELF binaries in a directory.
- bids-search which provides a CLI to search through a set of binaries to extract dependency and symbolic information.
- sbom4bids which generates a Software Bill of Materials (SBOM) from a bids JSON file.

The tools can also be used as Python libraries.

Additional utilities can also be installed:



## Usage - Bids-analyser

```
usage: bids-analyser [-h] [-f FILE] [--description DESCRIPTION] [--library-path LIBRARY_PATH] [--exclude-dependency] [--exclude-symbol] [--exclude-callgraph] [--detect-version] [-d] [-o OUTPUT_FILE] [-V]

bids-analyser analyses a binary application in ELF format and extracts dependency, symbolic and call graph information into a JSON data stream

options:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit

Input:
  -f FILE, --file FILE  identity of binary file
  --description DESCRIPTION
                        description of file
  --library-path LIBRARY_PATH
                        path to search for library files
  --exclude-dependency  suppress reporting of dependencies
  --exclude-symbol      suppress reporting of symbols
  --exclude-callgraph   suppress reporting of call graph
  --detect-version      detect version of component

Output:
  -d, --debug           add debug information
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        output filename (default: output to stdout)

```
					
### Operation

The `--file` option is used to specify the binary file to be processed.

The `--description` option is used to provide a brief description of the binary being processed.

The `--library-path` option is used to provide the path for library files which are not located with the system library files. Multiple
locations can be specified as a list of paths spearated by ','. e.g. "/local/lib,/project/lib"

The `--exclude-dependency`, `--exclude-symbol`, and `--exclude-callgraph` option is used to disable
the capture of dependency, symbol or callgraph information respectively.

The `--detect-version` option is used to indicate that an attempt will be made to detect the version of each compopnent. This is disabled by default.
**NOTE** that detecting component versions may require that the component binary maybe executed. This can be protected, to some extent, by the use of a sandbox;
bids-analyser will use the [firejail sandbox](https://github.com/netblue30/firejail) if available although this can be overriden by setting the environment variable BIDS_SANDBOX to the pathname of the
sandbox to be used. 

The `--output-file` option is used to control the destination of the output generated by the tool. The
default is to report to the console but can be stored in a file (specified using `--output-file` option).

### Output File Format

The output file is in JSON format. The content depends on the contents of the file and the specified command line options.

```bash
bids-analyser -f go/bin/go --output gobin.json --description "Go binary"
```

```json
{
  "metadata": {
    "docFormat": "BIDS",
    "specVersion": "1.0",
    "id": "da4ef1aa-f9bb-49df-ab61-51224ea4bfc5",
    "version": 1,
    "timestamp": "2024-11-04T20:44:25Z",
    "tool": "bids_generator:0.1.0",
    "binary": {
      "class": "ELF64",
      "architecture": "x86_64",
      "bits": 64,
      "os": "linux",
      "filename": "go/bin/go",
      "filesize": 12983131,
      "filedate": "Thu Aug 15 19:50:32 2019",
      "checksum": {
        "algorithm": "SHA256",
        "value": "6ef479d2538373f31056cace657508359e39f31adf07a183f8b2d55be72c328c"
      }
    },
    "description": "Go binary"
  },
  "components": {
    "dynamiclibrary": [
      {
        "name": "libpthread.so.0",
        "location": "/usr/lib32/libpthread.so.0"
      },
      {
        "name": "libc.so.6",
        "location": "/usr/lib32/libc.so.6",
        "version": "2.38"
      }
    ],
    "globalsymbol": [
      "__errno_location",
      "abort",
      "fprintf",
      "fputc",
      "free",
      "freeaddrinfo",
      "fwrite",
      "gai_strerror",
      "getaddrinfo",
      "getnameinfo",
      "malloc",
      "nanosleep",
      "pthread_attr_destroy",
      "pthread_attr_getstacksize",
      "pthread_attr_init",
      "pthread_cond_broadcast",
      "pthread_cond_wait",
      "pthread_create",
      "pthread_detach",
      "pthread_mutex_lock",
      "pthread_mutex_unlock",
      "pthread_sigmask",
      "setenv",
      "sigfillset",
      "stderr",
      "strerror",
      "unsetenv",
      "vfprintf"
    ],
    "localsymbols": [
      "_cgo_panic",
      "_cgo_topofstack",
      "crosscall2"
    ]
  },
  "relationships": {
    "libpthread.so.0": [
      "__errno_location",
      "pthread_mutex_lock",
      "pthread_cond_wait",
      "pthread_mutex_unlock",
      "pthread_cond_broadcast",
      "pthread_create",
      "nanosleep",
      "pthread_detach",
      "pthread_attr_init",
      "pthread_attr_getstacksize",
      "pthread_attr_destroy",
      "pthread_sigmask"
    ],
    "libc.so.6": [
      "getnameinfo",
      "getaddrinfo",
      "freeaddrinfo",
      "gai_strerror",
      "stderr",
      "fwrite",
      "vfprintf",
      "fputc",
      "abort",
      "strerror",
      "fprintf",
      "free",
      "sigfillset",
      "setenv",
      "unsetenv",
      "malloc"
    ]
  }
}
```

### Return Values

The following values are returned:

- 0 - Binary analysis completed
- 1 - Error detected in analysis process

## Usage - bids-scan

```
usage: bids-scan [-h] [--directory DIRECTORY] [--pattern PATTERN] [-d] [-o OUTPUT] [-V]

bids-scan analyses ELF binaries in a directory and extracts dependency and symbolic information

options:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit

Input:
  --directory DIRECTORY
                        directory to scan
  --pattern PATTERN     files pattern (default is all files)

Output:
  -d, --debug           add debug information
  -o OUTPUT, --output OUTPUT
                        directory to store results
```

### Operation

**bids-scan** analyses a set of ELF binaries in a directory. It is the equivalent to calling bids-analyser for each file. within the directory.

The `--directory` option is used to specify the binary file to be processed.

The `--pattern` option is used to provide a file matching pattern to limit the number of files to be processed. The default is for all ELF files to be processed. 

The `--output` option is used to store the output generated by the tool. The generated files will be named based on the filename of the ELF file.

### Return Values

The following values are returned:

- 0 - Directory scan completed

## Usage - bids-search

```
usage: bids-search [-h] [--initialise] [--index INDEX] [--search SEARCH] [--verbose] [--debug] [--results RESULTS] [--export EXPORT] [--import IMPORT] [-V]

BIDS Search Tool

options:
  -h, --help         show this help message and exit
  -V, --version      show program's version number and exit

Input:
  --initialise       initialise dataset
  --index INDEX      directory to index
  --search SEARCH    search query
  --verbose          verbose reporting

Output:
  --debug            add debug information
  --results RESULTS  Maximum number of results to return (default 10)

Database Management:
  --export EXPORT    export database filename
  --import IMPORT    import database filename

```

### Operation

**bids-search** is used to search through a set of analysed ELF binaries to extract dependency and symbolic information.

The `--initialise` option is used to initialise the dataset. All data within an existing dataset is removed 

The `--index` option is used to add data to the dataset. All valid JSON bids-analysis files within the directory are added to the dataset.

The `--search` option is used to query the dataset. The search query canb include boolean logic e.g. "libc AND lipng". The `--verbose` option is used to
return more detailed information related to the quert. The `--results` option is used to limit the number of seach results returned (the default is 10 results).

The `--import` and `--export` options are used to import a previously pre-populated dataset or export the current dataset to a file. These options are intended to be used to transfer a dataset between platforms. 

### Example operation

The following shows a typical user session. 

The dataset is first initialised before adding a set of ELF analysis files in the directory samples/gdata.

```bash
bids-search --initialise
bids-search --index samples/gdata --debug
```
As the debug option is specified, details of each file being processed is shown on the console.

```bash
Indexing files in samples/gdata...
Find files in samples/gdata
Processing samples/gdata/gcov-10.json
Processing samples/gdata/grepjar.json
Processing samples/gdata/gcr-viewer.json
... SNIP
Processing samples/gdata/gouldtoppm.json
Process: samples/gdata/gcov-10.json
Process: samples/gdata/grepjar.json
Process: samples/gdata/gcr-viewer.json
...SNIP
Indexing complete!
```

Further sets of data files can be added to the dataset as they become available.

To search the dataset for all files for the string strcpy,

```bash
bids-search --search "strcpy" 
```

The following results are returned

```bash
bids-search --search "strcpy" 
```

```bash
Searching for: strcpy

Search Results:
--------------------------------------------------------------------------------
1. Score: 1.1422
   File: /usr/lib/grub/i386-pc/grub-ntldr-img
2. Score: 1.1241
   File: /usr/bin/gencnval
3. Score: 1.1008
   File: /usr/bin/gzip
4. Score: 1.0895
   File: /usr/bin/groff
5. Score: 1.0895
   File: /usr/bin/grotty
6. Score: 1.0784
   File: /usr/bin/grops
7. Score: 1.0363
   File: /usr/bin/grub-menulst2cfg
8. Score: 1.0363
   File: /usr/bin/grub-file
9. Score: 1.0165
   File: /usr/bin/grub-script-check
10. Score: 1.0165
   File: /usr/bin/grub-syslinux2cfg
--------------------------------------------------------------------------------
```

To get details of the results, add the `--verbose` option. The number of results returned can also be specified using the `--results` option; to only
return the top result, set the number of results to 1.

```bash
bids-search --search "strcpy" --verbose --results 1
```

```bash
Searching for: strcpy

Search Results:
--------------------------------------------------------------------------------
1. Score: 1.1422
   File: /usr/lib/grub/i386-pc/grub-ntldr-img
   Content: {
  "metadata": {
    "docFormat": "BIDS",
    "specVersion": "1.0",
    "id": "52033df6-8124-44a1-800d-7e2adf7d96a1",
    "version": 1,
    "timestamp": "2025-02-17T17:59:08Z",
    "tool": "bids_generator:0.1.0",
    "binary": {
      "class": "ELF64",
      "architecture": "x86_64",
      "bits": 64,
      "os": "linux",
      "filename": "/usr/lib/grub/i386-pc/grub-ntldr-img",
      "version": "2.2.40",
      "filesize": 35408,
      "filedate": "Tue Jun 13 14:25:11 2023",
      "checksum": {
        "algorithm": "SHA256",
        "value": "6bcb9781c412a822031f94a2470d6d420e9fa643e7ee8e921bc491d008aa2c19"
      }
    }
  },
  "components": {
    "dynamiclibrary": [
      {
        "name": "libc.so.6",
        "location": "/usr/lib32/libc.so.6",
        "version": "2.38",
        "algorithm": "SHA256",
        "checksum": "b9fa789b4c164f5028bebd1b95e73a4c1c2c72595e61c555a15a7fa7530e9deb"
      }
    ],
    "globalsymbol": [
      "__cxa_finalize",
      "__errno_location",
      "__fprintf_chk",
      "__libc_start_main",
      "__memcpy_chk",
      "__sprintf_chk",
      "__stack_chk_fail",
      "__strcpy_chk",
      "close",
      "fflush",
      "fgetc",
      "fwrite",
      "lseek64",
      "memcmp",
      "open64",
      "perror",
      "read",
      "stderr",
      "stdin",
      "strchr",
      "strcmp",
      "strcpy",
      "strlen",
      "strncmp",
      "strtol",
      "strtoul",
      "write"
    ],
    "localsymbols": [
      "_ITM_deregisterTMCloneTable",
      "_ITM_registerTMCloneTable",
      "__gmon_start__"
    ]
  },
  "callgraph": [],
  "relationships": {
    "libc.so.6": [
      "__libc_start_main",
      "__errno_location",
      "strncmp",
      "strcpy",
      "write",
      "strlen",
      "__stack_chk_fail",
      "strchr",
      "fgetc",
      "close",
      "read",
      "memcmp",
      "strcmp",
      "__memcpy_chk",
      "strtol",
      "fflush",
      "__strcpy_chk",
      "open64",
      "perror",
      "strtoul",
      "fwrite",
      "lseek64",
      "__fprintf_chk",
      "__sprintf_chk",
      "__cxa_finalize",
      "stdin",
      "stderr"
    ]
  }
}
```

### Return Values

The following values are returned:

- 0 - Search process completed
- 1 - Error detected in search process
- 2 - No results found

### Implementation Notes

Read/write access is required to a directory (`~/.cache/bids/`) for storing and reading the dataset. This can be overriden by the setting of an environment variable BIDS_DATASET.

## Usage - sbom4bids

```
usage: sbom4bids [-h] [-i INPUT] [-d] [--sbom {spdx,cyclonedx}] [--format {tag,json,yaml}] [-o OUTPUT_FILE] [-V]

Generates a Software Bill of Materials (SBOM) from a Bids JSON file

options:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit

Input:
  -i INPUT, --input INPUT
                        name of Bids file

Output:
  -d, --debug           add debug information
  --sbom {spdx,cyclonedx}
                        specify type of sbom to generate (default: spdx)
  --format {tag,json,yaml}
                        specify format of software bill of materials (sbom) (default: tag)
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        output filename (default: output to stdout)
```

### Operation

**sbom4bids** is used to generate a Software Bill of Materials (SBOM) for an analysed ELF binary.

The `--input` option is used to specify the name of the file contain the analysed data from the ELF binary, produced by bids-analyser.  

The `--sbom` option is used to specify the format of the generated SBOM (the default is SPDX). The `--format` option
can be used to specify the formatting of the SBOM (the default is Tag Value format for a SPDX SBOM). JSON format is supported for both
SPDX and CycloneDX SBOMs).

The `--output-file` option is used to control the destination of the output generated by the tool. The
default is to report to the console but can be stored in a file (specified using `--output-file` option).

### Return Values

The following values are returned:

- 0 - BOM generation process completed
- 1 - Error detected in generation process

## API

BIDs can be used as a library to analyse ELF binary files, store data in a dataset and to search for features within the dataset.

To analyse a binary file and store the results in a file, the following sequence of calls can be performed:

```python
from bids.analyser import BIDSAnalyser
analyser = BIDSAnalyser()
# Analyse a binary
analyser.analyse("test/test_assets/hello")
# Get details about the file
analyser.get_file_data()
{'location': '/root/Documents/git_repo/BIDS/test/test_assets/hello', 'checksum': {'size': 15952, 'date': 'Tue Nov 19 11:13:36 2024', 'sha256': '4434a9af25d451e4a9f4515d418a270b99f2362326245a06523c921e564cde21', 'sha384': '8088e53ee015ef9af1656e0426c1678cdb69bfd4abfb2e5593dfee0e7d6b22a13cd19f47ac124e5d90c721e4680383b9', 'sha512': 'd11bc10ed1ed367753eb5050fa4d78a543c5f4a2c9c6ab7fcce2d5f0804a4722de91689b51cf91b11a698b7ee26ccab703ab143c91afca9427fde9550869e089', 'sha3-256': 'd4b4dc35397beeff05d247bd4c653b9b65162c747656321b827e7cc1d7f6a625', 'sha3-384': 'dec32ea35cc5b5d805d3d245463251e126d23b226085012f053b9c2207d7a1d74c925204d46518848a76396b515aa0cc', 'sha3-512': '8ca2c3817db6846b808a5367b08b8f9ed963bd308aaf0127a6fc4a23784c01f82948d6222689b761df65991807b5ad904538f756666239d94a8f70f15896bf75'}}
# Identify the dependencies
analyser.get_dependencies()
['libc.so.6']
# Examine the global symbols
analyser.get_global_symbols()
[['libc.so.6', 'GLIBC_2.34', '__libc_start_main'], ['libc.so.6', 'GLIBC_2.2.5', 'printf'], ['libc.so.6', 'GLIBC_2.2.5', '__cxa_finalize']]
# ..and local symbols
analyser.get_local_symbols()
['_ITM_deregisterTMCloneTable', '__gmon_start__', '_ITM_registerTMCloneTable']
# Store data in a file
from bids.output import BIDSOutput
output = BIDSOutput()
output.create_metadata(analyser.get_file_data())
output.create_components(
    analyser.get_dependencies(),
    analyser.get_global_symbols(),
    analyser.get_callgraph(),
    local=analyser.get_local_symbols(),
)
output.generate_output(<<Filename>>)
```

To add data to a dataset, put all the files to be added to the index in a directory and call index_files with the name of the directory.

```python
from bids.index import BIDSIndexer
dataset = BIDSIndexer()
# Assume analysed files are in a directory
dataset.index_files(<<Directory>>)
```

An example of how to search the dataset:

```python
from bids.index import BIDSIndexer
dataset = BIDSIndexer()
# Optionally load data into the dataset
dataset.import_data(<<Filename>>)
# Search dataset
search_results = dataset.search("strcpy")
# Examine the top results
print (search_results[0])
{'file_path': '/tmp/bids/grub-ntldr-img.json', 'score': 1.2741155624389648, 'content': '{\n  "metadata": {\n    "docFormat": "BIDS",\n    "specVersion": "1.0",\n    "id": "a0e508d6-9f1f-49ee-8bd6-39ebc6bc76dc",\n    "version": 1,\n    "timestamp": "2025-02-04T21:51:25Z",\n    "tool": "bids_generator:0.1.0",\n    "binary": {\n      "class": "ELF64",\n      "architecture": "x86_64",\n      "bits": 64,\n      "os": "linux",\n      "filename": "/usr/lib/grub/i386-pc/grub-ntldr-img",\n      "version": "2.2.40",\n      "filesize": 35408,\n      "filedate": "Tue Jun 13 14:25:11 2023",\n      "checksum": {\n        "algorithm": "SHA256",\n        "value": "6bcb9781c412a822031f94a2470d6d420e9fa643e7ee8e921bc491d008aa2c19"\n      }\n    }\n  },\n  "components": {\n    "dynamiclibrary": [\n      {\n        "name": "libc.so.6",\n        "location": "/usr/lib32/libc.so.6",\n        "version": "2.38"\n      }\n    ],\n    "globalsymbol": [\n      "__cxa_finalize",\n      "__errno_location",\n      "__fprintf_chk",\n      "__libc_start_main",\n      "__memcpy_chk",\n      "__sprintf_chk",\n      "__stack_chk_fail",\n      "__strcpy_chk",\n      "close",\n      "fflush",\n      "fgetc",\n      "fwrite",\n      "lseek64",\n      "memcmp",\n      "open64",\n      "perror",\n      "read",\n      "stderr",\n      "stdin",\n      "strchr",\n      "strcmp",\n      "strcpy",\n      "strlen",\n      "strncmp",\n      "strtol",\n      "strtoul",\n      "write"\n    ],\n    "localsymbols": [\n      "_ITM_deregisterTMCloneTable",\n      "_ITM_registerTMCloneTable",\n      "__gmon_start__"\n    ]\n  },\n  "callgraph": [],\n  "relationships": {\n    "libc.so.6": [\n      "__libc_start_main",\n      "__errno_location",\n      "strncmp",\n      "strcpy",\n      "write",\n      "strlen",\n      "__stack_chk_fail",\n      "strchr",\n      "fgetc",\n      "close",\n      "read",\n      "memcmp",\n      "strcmp",\n      "__memcpy_chk",\n      "strtol",\n      "fflush",\n      "__strcpy_chk",\n      "open64",\n      "perror",\n      "strtoul",\n      "fwrite",\n      "lseek64",\n      "__fprintf_chk",\n      "__sprintf_chk",\n      "__cxa_finalize",\n      "stdin",\n      "stderr"\n    ]\n  }\n}\n'}
print (search_results[1])
{'file_path': '/tmp/bids/gencnval.json', 'score': 1.2453277111053467, 'content': '{\n  "metadata": {\n    "docFormat": "BIDS",\n    "specVersion": "1.0",\n    "id": "5424250f-8732-4ea4-ae14-8f7bad435cf5",\n    "version": 1,\n    "timestamp": "2025-02-04T21:52:00Z",\n    "tool": "bids_generator:0.1.0",\n    "binary": {\n      "class": "ELF64",\n      "architecture": "x86_64",\n      "bits": 64,\n      "os": "linux",\n      "filename": "/usr/bin/gencnval",\n      "version": "0.98",\n      "filesize": 27200,\n      "filedate": "Mon Jul  1 18:52:08 2024",\n      "checksum": {\n        "algorithm": "SHA256",\n        "value": "e4f41bdecbaebcf56317d2f7748ab1b9973103ce03e3ea0942231d0f03ffe98a"\n      }\n    }\n  },\n  "components": {\n    "dynamiclibrary": [\n      {\n        "name": "libicutu.so.72",\n        "location": "/usr/lib/x86_64-linux-gnu/libicutu.so.72.1"\n      },\n      {\n        "name": "libicuuc.so.72",\n        "location": "/usr/lib/x86_64-linux-gnu/libicuuc.so.72.1"\n      },\n      {\n        "name": "libc.so.6",\n        "location": "/usr/lib32/libc.so.6",\n        "version": "2.38"\n      }\n    ],\n    "globalsymbol": [\n      "__ctype_b_loc",\n      "__cxa_finalize",\n      "__fprintf_chk",\n      "__libc_start_main",\n      "__printf_chk",\n      "__stack_chk_fail",\n      "__strcpy_chk",\n      "exit",\n      "memcpy",\n      "memset",\n      "puts",\n      "qsort",\n      "stderr",\n      "strchr",\n      "strcmp",\n      "strcpy",\n      "strlen",\n      "strtok"\n    ],\n    "localsymbols": [\n      "T_FileStream_close",\n      "T_FileStream_open",\n      "T_FileStream_readLine",\n      "_ITM_deregisterTMCloneTable",\n      "_ITM_registerTMCloneTable",\n      "__gmon_start__",\n      "u_errorName_72",\n      "u_getDataDirectory_72",\n      "u_parseArgs",\n      "ucnv_compareNames_72",\n      "ucnv_io_stripASCIIForCompare_72",\n      "udata_create",\n      "udata_finish",\n      "udata_write16",\n      "udata_write32",\n      "udata_writeBlock",\n      "udata_writeString",\n      "uprv_free_72",\n      "uprv_isInvariantString_72",\n      "uprv_malloc_72",\n      "uprv_realloc_72",\n      "uprv_strnicmp_72"\n    ]\n  },\n  "callgraph": [],\n  "relationships": {\n    "libc.so.6": [\n      "__printf_chk",\n      "strchr",\n      "strlen",\n      "memset",\n      "__libc_start_main",\n      "memcpy",\n      "__strcpy_chk",\n      "strcpy",\n      "__ctype_b_loc",\n      "__stack_chk_fail",\n      "exit",\n      "strcmp",\n      "puts",\n      "strtok",\n      "__fprintf_chk",\n      "qsort",\n      "__cxa_finalize",\n      "stderr"\n    ]\n  }\n}\n'}
# Look at the contents of result
print (search_results[1]["content"])
{
  "metadata": {
    "docFormat": "BIDS",
    "specVersion": "1.0",
    "id": "5424250f-8732-4ea4-ae14-8f7bad435cf5",
    "version": 1,
    "timestamp": "2025-02-04T21:52:00Z",
    "tool": "bids_generator:0.1.0",
    "binary": {
      "class": "ELF64",
      "architecture": "x86_64",
      "bits": 64,
      "os": "linux",
      "filename": "/usr/bin/gencnval",
      "version": "0.98",
      "filesize": 27200,
      "filedate": "Mon Jul  1 18:52:08 2024",
      "checksum": {
        "algorithm": "SHA256",
        "value": "e4f41bdecbaebcf56317d2f7748ab1b9973103ce03e3ea0942231d0f03ffe98a"
      }
    }
  },
  "components": {
    "dynamiclibrary": [
      {
        "name": "libicutu.so.72",
        "location": "/usr/lib/x86_64-linux-gnu/libicutu.so.72.1"
      },
      {
        "name": "libicuuc.so.72",
        "location": "/usr/lib/x86_64-linux-gnu/libicuuc.so.72.1"
      },
      {
        "name": "libc.so.6",
        "location": "/usr/lib32/libc.so.6",
        "version": "2.38"
      }
    ],
    "globalsymbol": [
      "__ctype_b_loc",
      "__cxa_finalize",
      "__fprintf_chk",
      "__libc_start_main",
      "__printf_chk",
      "__stack_chk_fail",
      "__strcpy_chk",
      "exit",
      "memcpy",
      "memset",
      "puts",
      "qsort",
      "stderr",
      "strchr",
      "strcmp",
      "strcpy",
      "strlen",
      "strtok"
    ],
    "localsymbols": [
      "T_FileStream_close",
      "T_FileStream_open",
      "T_FileStream_readLine",
      "_ITM_deregisterTMCloneTable",
      "_ITM_registerTMCloneTable",
      "__gmon_start__",
      "u_errorName_72",
      "u_getDataDirectory_72",
      "u_parseArgs",
      "ucnv_compareNames_72",
      "ucnv_io_stripASCIIForCompare_72",
      "udata_create",
      "udata_finish",
      "udata_write16",
      "udata_write32",
      "udata_writeBlock",
      "udata_writeString",
      "uprv_free_72",
      "uprv_isInvariantString_72",
      "uprv_malloc_72",
      "uprv_realloc_72",
      "uprv_strnicmp_72"
    ]
  },
  "callgraph": [],
  "relationships": {
    "libc.so.6": [
      "__printf_chk",
      "strchr",
      "strlen",
      "memset",
      "__libc_start_main",
      "memcpy",
      "__strcpy_chk",
      "strcpy",
      "__ctype_b_loc",
      "__stack_chk_fail",
      "exit",
      "strcmp",
      "puts",
      "strtok",
      "__fprintf_chk",
      "qsort",
      "__cxa_finalize",
      "stderr"
    ]
  }
}
```

## License

Licensed under the Apache 2.0 License.

## Limitations

The tools have the following limitations:

- Stripped binaries will result in a limited amount of data

- Callgraph processing is not implemented

- BIDS does not attempt to detect or identify anything that is intentionaly obfuscated, malicious or hidden in an ELF binary.

## Feedback and Contributions

This project is sponsored by NLNET https://nlnet.nl/project/BIDS/.
