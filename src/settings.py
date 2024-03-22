import os

src_dir = os.path.dirname(__file__)

DEBUG = False

HEADER_ROW_NUMBER = 2

HEADER_ROW_PREFIX = "#  "

CONTEXT_LOCAL_FILE_PATH = os.path.join(src_dir, "context.jsonld")

CONTEXT_FILE_URI = "http://example.com/context.jsonld"

COLUMN_MAPPING_FILE_PATH = os.path.join(src_dir, "column_mapping.json")

ERROR_LOG_FILE_PATH = os.path.join(src_dir, "error.log")

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

NODE_ID_PREFIX = "cpdb:"

NODE_TYPE = "bp3:MolecularInteraction"

DATA_SOURCE_PREFIX = "http://identifiers.org/"

EVIDENCE_PREFIX = "pubmed:"

PARTICIPANTS = [
    "uniprot_entry",
    "uniprot_id",
    "genename",
    "hgnc_id",
    "entrez_gene",
    "ensembl_gene",
]

LITERAL_PARTICIPANTS = ["genename"]

UNIPROT_ENTRY_COLUMN = "uniprot_entry"

JSONLD_MAX_FILE_SIZE = 3 * 1024 * 1024
