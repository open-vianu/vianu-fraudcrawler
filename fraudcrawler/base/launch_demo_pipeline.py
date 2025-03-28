import logging

from fraudcrawler.base.settings import LOG_FMT, LOG_LVL, DATE_FMT
from fraudcrawler import FraudCrawlerClient, Language, Location
from fraudcrawler import Deepness, Enrichment

logging.basicConfig(level=LOG_LVL.upper(), format=LOG_FMT, datefmt=DATE_FMT)
logger = logging.getLogger(__name__)

# Setup the client
client = FraudCrawlerClient()

# Setup the search
search_term = "sildenafil"
language = Language(name="German")
location = Location(name="Switzerland")
deepness = Deepness(num_results=50)
context = "This organization is interested in medical products and drugs."

# # Optional: Add enrichement, marketplaces, and excluded_urls
# deepness.enrichement = Enrichment(
#     additional_terms=5,
#     additional_urls_per_term=5
# )
#
# from fraudcrawler import Host,
# marketplaces = [
#     Host(name="Ricardo", domains="ricardo.ch"),
#     Host(name="Galaxus", domains="digitec.ch, galaxus.ch")
# ]
# excluded_urls = [
#     Host(name="Altibbi", domains="altibbi.com")
# ]

# Run the search
client.run(
    search_term=search_term,
    language=language,
    location=location,
    deepness=deepness,
    context=context,
    # marketplaces=marketplaces,
    # excluded_urls=excluded_urls
)
