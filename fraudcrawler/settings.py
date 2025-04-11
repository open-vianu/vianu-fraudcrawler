from pathlib import Path

# Generic settings
LOG_FMT = "%(asctime)s | %(name)s | %(funcName)s | %(levelname)s | %(message)s"
LOG_LVL = "DEBUG"
LOG_DATE_FMT = "%Y-%m-%d %H:%M:%S"
MAX_RETRIES = 3
RETRY_DELAY = 2
ROOT_DIR = Path(__file__).parents[1]

# Serp settings
GOOGLE_LOCATIONS_FILENAME = ROOT_DIR / "fraudcrawler" / "base" / "google-locations.json"
GOOGLE_LANGUAGES_FILENAME = ROOT_DIR / "fraudcrawler" / "base" / "google-languages.json"

# Enrichment settings
ENRICHMENT_DEFAULT_LIMIT = 10

# Zyte settings
ZYTE_DEFALUT_PROBABILITY_THRESHOLD = 0.1

# Processor settings
PROCESSOR_DEFAULT_MODEL = "gpt-4o"
PROCESSOR_DEFAULT_MISSING_FIELDS_RELEVANCE = 1
PROCESSOR_DEFAULT_MISSING_FIELDS_PRODUCT = 1

# Async settings
DEFAULT_N_SERP_WKRS = 10
DEFAULT_N_ZYTE_WKRS = 10
DEFAULT_N_PROC_WKRS = 10

USER_PROMPT_TEMPLATE = "Context: {context}\n\nProduct Details: {name}\n{description}\\n\nIs this label allowed?:"

PROMPTS = [
    {
        "prompt_name": "relevance_classification",
        "context": "This organization is interested in checking the energy efficiency of certain devices.",
        "system_prompt": (
            "You are a helpful and intelligent assistant. Your task is to classify any given product as "
            "either relevant (1) or not relevant (0) to this organization, strictly based on the context "
            "and product details provided. Only respond with the number 1 or 0."
        ),
        "allowed_classes": ["0", "1"],
    },
    {
        "prompt_name": "seriousness_classification",
        "context": "This organization is interested in checking the energy efficiency of certain devices.",
        "system_prompt": (
            "You are an intelligent and discerning assistant. Your task is to classify a given product as either "
            "a serious, legitimate product (1) or junk/not serious (0), based solely on the product information "
            "provided. Respond only with the number 1 or 0."
        ),
        "allowed_classes": ["0", "1"],
    },
    {
        "prompt_name": "energy_label_requirement_classification",
        "context": "This organization is interested in checking the energy efficiency of certain devices.",
        "system_prompt": (
            "You are an intelligent assistant. Under Swiss legislation (EnG 730.0 Energiegesetz, EnEV 730.02 "
            "Energieeffizienzverordnung), certain devices require an energy label. Based on the product details provided, "
            "classify whether the product requires an energy label (1) or does not (0). Respond only with the number 1 or 0."
        ),
        "allowed_classes": ["0", "1"],
    },
    {
        "prompt_name": "energy_label_mention_classification",
        "context": "This organization is interested in checking the energy efficiency of certain devices.",
        "system_prompt": (
            "You are an intelligent assistant. Your task is to check whether the product description or text "
            "explicitly mentions an energy label. Classify as 1 if there is a mention or 0 if there is none. "
            "Respond only with the number 1 or 0."
        ),
        "allowed_classes": ["0", "1"],
    },
    {
        "prompt_name": "allowed_label_classification",
        "context": "This organization is interested in checking the energy efficiency of certain devices.",
        "system_prompt": (
            "You are an intelligent assistant. Your task is to verify the energy efficiency class of a given product. "
            "Classify as 1 if the product has a low-efficiency label (F, G, or worse). "
            "Classify as 0 if the product has an acceptable efficiency label (A, B, C, D, or E), or if no label is mentioned at all. "
            "Respond only with the number 1 or 0."
        ),
        "allowed_classes": ["0", "1"],
    },
]
