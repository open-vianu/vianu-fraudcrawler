# vianu-fraudcrawler
Intelligent Market Monitoring

The pipeline for monitoring the market has the folling main steps:
1. search for a given term using SerpAPI
2. get product information using ZyteAPI
3. assess relevance of the found products using an OpenAI API

## Installation
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install vianu-fraudcrawler
```

## Usage
### `.env` file
Make sure to create an `.env` file with the necessary API keys and credentials (c.f. `.env.example` file).

### Run demo pipeline
```bash
python -m fraudcrawler.launch_demo_pipeline
```

### Customize the pipeline
Start by initializing the client
```python
from fraudcrawler import FraudCrawlerClient

# Initialize the client
client = FraudCrawlerClient()
```

For setting up the search we need 5 main objects
- `search_term`: The search term for the query.
- `language`: The Language used in SerpAPI ('hl') and for related search terms (within optional enrichement)
- `location`: The SerpAPI location ('gl') used for the query.
- `deepness`: Defines the search depth.
- `context`: The context prompt to use for detecting relevant products

```python
from fraudcrawler import Location, Deepness
# Setup the search
search_term = "sildenafil"
language = Language(name="German")
location = Location(name="Switzerland")
deepness = Deepness(num_results=50)
context = "This organization is interested in medical products and drugs."
```

(Optional) Add search term enrichement. This will find related search terms (in a given language) and search for these as well.
```python
from fraudcrawler import Enrichment
deepness.enrichment = Enrichment(
    additional_terms=5,
    additional_urls_per_term=10
)
```

(Optional) Add marketplaces where we explicitely want to look for (this will focus your search as the :site parameter for a google search)
```python
from fraudcrawler import Host
marketplaces = [
    Host(name="International", domains="zavamed.com,apomeds.com"),
    Host(name="National", domains="netdoktor.ch, nobelpharma.ch"),
]
```

(Optional) Exclude urls (where you don't want to find products)
```python
excluded_urls = [
    Host(name="Compendium", domains="compendium.ch"),
]
```

And finally run the pipeline
```python
# Execute the pipeline
client.execute(
    search_term=search_term,
    location=location,
    deepness=deepness,
    context=context,
    # marketplaces=marketplaces,    # Uncomment this for using marketplaces
    # excluded_urls=excluded_urls   # Uncomment this for using excluded_urls
)
```
This creates a file with name pattern `<search_term>_<datetime[%Y%m%d%H%M%S]>.csv` inside the folder `data/results/`.

Once the pipeline terminated the results can be loaded and examined as follows:
```python
df = client.load_results()
print(df.head(n=10))
```

If the client has been used to run multiple pipelines, an overview of the available results (for a given instance of 
`FraudCrawlerClient`) can be obtained with
```python
client.print_available_results()
```

## Contributing
see `CONTRIBUTING.md`

### Async Setup
The following image provides a schematic representation of the package's async setup.
![Async Setup](https://github.com/open-vianu/vianu-fraudcrawler/raw/master/docs/assets/images/Fraudcrawler_Async_Setup.svg)
