from pathlib import Path

# Generic settings
LOG_FMT = "%(asctime)s | %(name)s | %(funcName)s | %(levelname)s | %(message)s"
LOG_LVL = "DEBUG"
DATE_FMT = "%Y-%m-%d %H:%M:%S"
MAX_RETRIES = 3
RETRY_DELAY = 2
ROOT_DIR = Path(__file__).parents[2]

# Enrichment settings
ENRICHMENT_ADDITIONAL_TERMS = 3
ENRICHMENT_ADDITIONAL_URLS_PER_TERM = 10
ENRICHMENT_UPPER_LIMIT = 10

# Zyte settings
ZYTE_PROBABILITY_THRESHOLD = 0.1

# Processor settings
PROCESSOR_MODEL = "gpt-4o"

# Async settings
N_SERP_WKRS = 10
N_ZYTE_WKRS = 10
N_PROC_WKRS = 10
