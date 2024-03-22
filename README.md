# ConsensusPathDB to JSON-LD

## Folder Structure

```plaintext
.
├── src/
│   ├── cpdb2jsonld.py          # Python program for converting ConsensusPathDB
│   ├── settings.py             # Configuration file for the conversion program
│   ├── column_mapping.json     # File to map TSV headers to IRI
│   └── context.jsonld          # File defining the JSON-LD context
├── Dockerfile                  # Definition file for Docker image
├── build_tsv2jsonld_cpdb.sh    # Script to build the Docker image
├── run_tsv2jsonld_cpdb.sh      # Script to run the conversion program
├── pyproject.toml
├── poetry.lock
└── README.md
```

## Environment

It is recommended to run this program within a Docker container for consistency across different computing environments.

- Python 3.11
  - PyLD (for processing JSON-LD)
  - tqdm (for progress bars)

## Building the Docker Image (First Time Only)

To build the Docker image, execute the provided script.

```bash
bash build_tsv2jsonld_cpdb.sh
```

Proceed to running the program once the build completes without errors.

## Running the Conversion Program

Execute the program using the following script.

```bash
bash run_tsv2jsonld_cpdb.sh <input_file> <output_file> [options...]
```

Example:

```bash
bash run_tsv2jsonld_cpdb.sh data/ConsensusPathDB_human_PPI output/cpdb_converted.jsonl
```

### About the Arguments

#### `<input_file>`

Specify the path to the ConsensusPathDB TSV file you wish to convert.

#### `<output_file>`

Specify the path where the JSON Lines file will be output.

#### `[options...]`

Optional arguments can be included.

**`--jsonld`**

After converting to JSON Lines, this option generates a JSON format JSON-LD file from the produced .jsonl file. The .jsonld files are split and saved in a folder named `<output_file_basename>_jsonld` at the same hierarchical level as the specified output file. Each .jsonld file's size adheres to `JSONLD_MAX_FILE_SIZE` defined in `src/settings.py`.

### Program Configuration

The conversion program can be configured via `src/settings.py`, `src/column_mapping.json`, and `src/context.jsonld`.

#### `settings.py`

Below is a list of configuration items and their default values in `settings.py`.

| Setting                      | Default Value                                             | Description                                                                   |
|------------------------------|-----------------------------------------------------------|-------------------------------------------------------------------------------|
| `src_dir`                    | `os.path.dirname(__file__)`                               | Path to the `src` directory.                                                  |
| `DEBUG`                      | `False`                                                   | Toggle debug mode on/off.                                                     |
| `HEADER_ROW_NUMBER`          | `2`                                                       | Row number where the header is located.                                       |
| `HEADER_ROW_PREFIX`          | `"#  "`                                                   | Prefix for header rows.                                                       |
| `CONTEXT_LOCAL_FILE_PATH`    | `os.path.join(src_dir, "context.jsonld")`                 | Path to the local context file. Defaults to `src/context.jsonld`.             |
| `CONTEXT_FILE_URI`           | `"http://example.com/context.jsonld"`                     | URI for the context file. This URI is inserted into the JSON Lines context.   |
| `COLUMN_MAPPING_FILE_PATH`   | `os.path.join(src_dir, "column_mapping.json")`            | Path to the column mapping file. Defaults to `src/column_mapping.json`.       |
| `ERROR_LOG_FILE_PATH`        | `os.path.join(src_dir, "error.log")`                      | Path to the error log file. Defaults to `src/error.log`.                      |
| `LOG_FORMAT`                 | `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"`  | Log output format.                                                            |
| `NODE_ID_PREFIX`             | `"cpdb:"`                                                 | Prefix for node IDs. Update needed if context definition changes.             |
| `NODE_TYPE`                  | `"bp3:MolecularInteraction"`                              | Type of node.                                                                 |
| `DATA_SOURCE_PREFIX`         | `"http://identifiers.org/"`                               | Prefix for data source URIs.                                                  |
| `EVIDENCE_PREFIX`            | `"pubmed:"`                                               | Prefix for evidence.                                                          |
| `PARTICIPANTS`               | Array of participant attributes                           | List of attributes for participants.                                          |
| `LITERAL_PARTICIPANTS`       | `["genename"]`                                            | Attributes of participants referenced in a literal form.                     |
| `UNIPROT_ENTRY_COLUMN`       | `"uniprot_entry"`                                         | Column name that refers to UniProt entry.                                     |
| `JSONLD_MAX_FILE_SIZE`       | `3 * 1024 * 1024` (bytes)                                 | Maximum size for a JSON-LD file.                                              |

#### `column_mapping.json`

If there are updates to the ConsensusPathDB TSV file column headers, adjustments will be necessary here.

#### `context.jsonld`

This defines the context used when performing the JSON-LD transformation.
