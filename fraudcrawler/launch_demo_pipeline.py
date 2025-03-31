from fraudcrawler import FraudCrawlerClient, Location, Deepness


def main():
    # Setup the client
    client = FraudCrawlerClient()

    # Setup the search
    search_term = "sildenafil"
    location = Location(name="Switzerland")
    deepness = Deepness(num_results=50)
    context = "This organization is interested in medical products and drugs."

    # # Optional: Add tern ENRICHEMENT
    # from fraudcrawler import Enrichment, Language
    # deepness.enrichement = Enrichment(
    #     language = Language(name="German")
    #     additional_terms=5,
    #     additional_urls_per_term=5
    # )
    #

    # # Optional: Add MARKETPLACES and EXCLUDED_URLS
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
        location=location,
        deepness=deepness,
        context=context,
        # marketplaces=marketplaces,
        # excluded_urls=excluded_urls
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
    print(f"Number of products: {len(df)}\n")
    print(df.head(n=10))
    print()


if __name__ == "__main__":
    main()
