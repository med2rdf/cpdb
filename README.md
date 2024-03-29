# ConsensusPathDB to JSON-LD

## 1. Introduction

This program converts TSV files from the ConsensusPathDB (CPDB) into JSON-LD formatted JSON Lines.

## 2. Directory Structure

```plaintext
.
┣ data/                      # Default data path
┣ src/
┃  ┣ column_mapper/
┃  ┃  ┣ human.json           # Definition file for mapping human TSV headers to IRIs
┃  ┃  ┣ mouse.json           # Definition file for mapping mouse TSV headers to IRIs
┃  ┃  ┗ yeast.json           # Definition file for mapping yeast TSV headers to IRIs
┃  ┣ cpdb2jsonld.py          # Python program for CPDB conversion
┃  ┣ settings.py             # Configuration file for the conversion program
┃  ┣ taxonomy.json           # Definition file for mapping taxonomy names to taxonomy IDs
┃  ┣ urls.txt                # List of URLs for CPDB TSV files
┃  ┗ context.jsonld          # File defining the JSON-LD context
┣ Dockerfile                 # Definition file for the Docker image
┣ build_tsv2jsonld_cpdb.sh   # Script to build the Docker image
┣ run_tsv2jsonld_cpdb.sh     # Script to execute the conversion program
┣ pyproject.toml
┣ poetry.lock
┗ README.md
```

## 3. Environment

Execution within a Docker container is recommended.

- Python 3.11
  - PyLD
  - Typer
  - Loguru
  - Rich

## 4. Building the Docker Image (First Time Only)

Execute the script to build the Docker image.

```bash
bash build_tsv2jsonld_cpdb.sh
```

Once the build completes without errors, proceed to executing the program.

## 5. Execution of the Conversion Program

Execute the script to run the conversion program.

Two types of conversion scripts are available:

- `run_flow_tsv2jsonld_cpdb.sh`     # Executes the entire flow from file download to conversion based on the URL definition file
- `run_tsv2jsonld_cpdb.sh`          # Passes the path of the manually downloaded DB TSV file as an argument for conversion

### 5.1. run_flow_tsv2jsonld_cpdb.sh

```bash
bash run_flow_tsv2jsonld_cpdb.sh [options...]
```

#### 5.1.1. Arguments

##### 5.1.1.1. `[options...]`

Optional arguments.

**`--hide-progress`**

If specified, hides the progress bar that indicates the conversion progress.

**`--jsonld-output`**

If specified, after converting from TSV to .jsonl, this option generates .jsonld files based on the .jsonl file.

The .jsonld files are split and output in the `<output_file_basename>_jsonld` folder created at the same directory level as the file specified for the .jsonl output.

The size of each .jsonld file is determined by the `JSONLD_MAX_FILE_SIZE` in `src/settings.py`.

### 5.2. run_tsv2jsonld_cpdb.sh

```bash
bash run_tsv2jsonld_cpdb.sh <input_file> <output_file> [options...]
```

Example execution:

```bash
bash run_tsv2jsonld_cpdb.sh data/ConsensusPathDB_human_PPI output/cpdb_converted.jsonl
```

#### 5.2.1. Arguments

##### 5.2.1.1. `<input_file>`

Specifies the path to the ConsensusPathDB TSV file to be input.

##### 5.2.1.2. `<output_file>`

Specifies the path to the output JSON Lines file.

##### 5.2.1.3. `[options...]`

Optional arguments.

**`--taxonomy <taxonomy_name>`**

Specifies the taxonomy. If this option is not included, the taxonomy name contained in the file name will be used.

**`--hide-progress`**

If specified, hides the progress bar that indicates the conversion progress.

**`--jsonld-output`**

After converting to JSON Lines, this generates JSON-LD formatted JSON files from the output .jsonl file.

The .jsonld files are split and output in the `<output_file_basename>_jsonld` folder created at the same directory level as the file specified for the .jsonl output.

The size of each .jsonld file is determined by the `JSONLD_MAX_FILE_SIZE` in `src/settings.py`.

### 5.3. Program Configuration

Configure the conversion program using `src/settings.py`, `src/column_mapper/*.json`, `src/context.jsonld`, `src/taxonomy.json`, and `src/urls.txt`.

#### 5.3.1. `settings.py`

Below is a list of settings in settings.py with their default values.

| Setting Name | Default Value | Description |
| --- | --- | --- |
| `src_dir` | `os.path.dirname(__file__)` | Path to the src directory |
| `DEBUG` | `False` | Enable/disable debug mode |
| `URL_LIST_FILE_PATH` | `os.path.join(src_dir, "urls.txt")` | Path to the file storing the URL list |
| `OUTPUT_DIR` | `os.path.join(src_dir, "output/")` | Path to the directory where output files are saved |
| `COLUMN_MAPPER_DIR` | `os.path.join(src_dir, "column_mapper/")` | Path to the directory storing column mappers |
| `HEADER_ROW_NUMBER` | `2` | Which line contains the header |
| `HEADER_ROW_PREFIX` | `"#  "` | Prefix for the header row |
| `CONTEXT_LOCAL_FILE_PATH` | `os.path.join(src_dir, "context.jsonld")` | Path to the local context file |
| `CONTEXT_FILE_URI` | `"http://example.com/context.jsonld"` | URI for the context file |
| `INFO_LOG_FILE_PATH` | `os.path.join(src_dir, "info.log")` | Path to the log file |
| `ERROR_LOG_FILE_PATH` | `os.path.join(src_dir, "error.log")` | Path to the error log file |
| `NODE_ID_COLUMN` | `"uniprot_entry"` | Column name used as node ID |
| `NODE_ID_PREFIX` | `"cpdb:"` | Prefix for the node ID |
| `NODE_TYPE` | `"m2r:MacromolecularComplex"` | Type of the node |
| `DATA_SOURCE_PREFIX` | `"http://identifiers.org/"` | Prefix for data sources |
| `REFERENCE_PREFIX` | `"pmid:"` | Prefix for references |
| `PARTICIPANTS` | `[ "uniprot_entry", "uniprot_id", ]` | List of participants |
| `TAXONOMY_FILE_PATH` | `os.path.join(src_dir, "taxonomy.json")` | Path to the taxonomy definition file |
| `JSONLD_MAX_FILE_SIZE` | `3 * 1024 * 1024` | Maximum size of a JSON-LD file (in bytes) |

#### 5.3.2. `src/column_mapper/*.json`

If the column headers in the ConsensusPathDB TSV file are changed, modifications to these definitions are necessary.

#### 5.3.3. `context.jsonld`

This is the definition file for the context used when converting to JSON-LD.

#### 5.3.4. `src/taxonomy.json`

This definition file is for translating taxonomy names to taxonomy IDs.

#### 5.3.5. `src/urls.txt`

This lists the URLs for the CPDB TSV files to be converted.
