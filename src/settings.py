# Generic settings
LOG_FMT = "%(asctime)s | %(name)s | %(funcName)s | %(levelname)s | %(message)s"
LOG_LVL = "DEBUG"
DATE_FMT = "%Y-%m-%d %H:%M:%S"
RATE_LIMIT_MESSAGE = "rate limit exceeded"

# Pipeline settings
ZYTE_PROBABILITY_THRESHOLD = 0.1
MAX_RETRIES = 3
RETRY_DELAY = 2
ENRICHMENT_ADDITIONAL_TERMS = 3
ENRICHMENT_ADDITIONAL_URLS_PER_TERM = 10
REQUESTS_TIMEOUT = 10

# Async settings
N_SRCH_WKRS = 10
N_ZYTE_WKRS = 10
N_PROC_WKRS = 10

