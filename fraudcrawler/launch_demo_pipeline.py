from fraudcrawler import FraudCrawlerClient, Language, Location, Deepness
from fraudcrawler.settings import PROMPTS

_N_HEAD = 10

def main():
    # Setup the client
    client = FraudCrawlerClient()

    # Setup the search
    search_term = "Kühlschrank"
    language = Language(name="German")
    location = Location(name="Switzerland")
    deepness = Deepness(num_results=200)

    # Optional: Add tern ENRICHEMENT
    from fraudcrawler import Enrichment
    deepness.enrichment = Enrichment(
        additional_terms=10,
        additional_urls_per_term=20
    )

    # # Optional: Add MARKETPLACES and EXCLUDED_URLS
    from fraudcrawler import Host
    # marketplaces = [
    #     Host(name="International", domains="zavamed.com,apomeds.com"),
    #     Host(name="National", domains="netdoktor.ch, nobelpharma.ch")
    # ]
    excluded_urls = [
        Host(name="Digitec", domains="digitec.ch"),
        Host(name="Brack", domains="brack.ch")
    ]

    # Execute the pipeline
    client.execute(
        search_term=search_term,
        language=language,
        location=location,
        deepness=deepness,
        prompts=PROMPTS,
        # marketplaces=marketplaces,
        excluded_urls=excluded_urls,
    )

    # Show results
    print()
    title = "Available results"
    print(title)
    print("=" * len(title))
    client.print_available_results()
    print()
    title = f'Results for "{search_term.upper()}"'
    print(title)
    print("=" * len(title))
    df = client.load_results()
    print(f"Number of products found: {len(df)}")
    print()
    print(f"First {_N_HEAD} products are:")
    print(df.head(n=_N_HEAD))
    print()


if __name__ == "__main__":
    main()
