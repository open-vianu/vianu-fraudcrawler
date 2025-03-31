from fraudcrawler import FraudCrawlerClient, Language, Location, Deepness

_N_HEAD = 10

def main():
    # Setup the client
    client = FraudCrawlerClient()

    # Setup the search
    search_term = "sildenafil"
    language = Language(name="German")
    location = Location(name="Switzerland")
    deepness = Deepness(num_results=50)
    context = "This organization is interested in medical products and drugs."

    # # Optional: Add tern ENRICHEMENT
    # from fraudcrawler import Enrichment
    # deepness.enrichment = Enrichment(
    #     additional_terms=5,
    #     additional_urls_per_term=10
    # )

    # # Optional: Add MARKETPLACES and EXCLUDED_URLS
    # from fraudcrawler import Host
    # marketplaces = [
    #     Host(name="International", domains="zavamed.com,apomeds.com"),
    #     Host(name="National", domains="netdoktor.ch, nobelpharma.ch")
    # ]
    # excluded_urls = [
    #     Host(name="Compendium", domains="compendium.ch")
    # ]

    # Run the search
    client.run(
        search_term=search_term,
        language=language,
        location=location,
        deepness=deepness,
        context=context,
        # marketplaces=marketplaces,
        # excluded_urls=excluded_urls,
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
    print(f'Number of relevant products: {len(df[df["is_relevant"] == 1])}')
    print()
    print(f"First {_N_HEAD} products are:")
    print(df.head(n=_N_HEAD))
    print()


if __name__ == "__main__":
    main()
