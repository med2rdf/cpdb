import os

src_dir = os.path.dirname(__file__)

DEBUG = False

DEBUG_LOG_FILE_PATH = os.path.join(src_dir, "debug.log")

URL_LIST_FILE_PATH = os.path.join(src_dir, "urls.txt")

OUTPUT_DIR = os.path.join(src_dir, "output/")

COLUMN_MAPPER_DIR = os.path.join(src_dir, "column_mapper/")

HEADER_ROW_NUMBER = 2

HEADER_ROW_PREFIX = "#  "

CONTEXT_LOCAL_FILE_PATH = os.path.join(src_dir, "context.jsonld")

CONTEXT_FILE_URI = "http://example.com/context.jsonld"

INFO_LOG_FILE_PATH = os.path.join(src_dir, "info.log")

ERROR_LOG_FILE_PATH = os.path.join(src_dir, "error.log")

NODE_ID_COLUMN = "uniprot_entry"

UNIPROT_ENTRY_COLUMN = "uniprot_entry"

UNIPROT_ID_COLUMN = "uniprot_id"

NODE_ID_PREFIX = "cpdb:"

NODE_TYPE = "m2r:MacromolecularComplex"

DATA_SOURCE_PREFIX = "http://identifiers.org/"

REFERENCE_PREFIX = "pmid:"

PARTICIPANTS = [UNIPROT_ID_COLUMN]

TAXONOMY_FILE_PATH = os.path.join(src_dir, "taxonomy.json")

JSONLD_MAX_FILE_SIZE = 3 * 1024 * 1024
