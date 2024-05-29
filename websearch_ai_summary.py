# License: MIT License
# This sample code shows how to use the Bing Web Search API to search
# the web for a query and summarize the results using the OpenAI API.
# The code defines a function web_search that takes a query and
# returns a list of search results. The function summarize_results
# takes the query, titles, and snippets of the search results and
# uses the OpenAI API to generate a 100-word summary of the results.

# You can try this out in the spreadsheet here:
# https://docs.google.com/spreadsheets/d/1nn0Ybnpr062Tf3oUebxEmTjymkeZ2mapT1SBZwtm6DQ/edit#gid=0



import requests
import neptyne as nt
from openai import OpenAI

BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"


def web_search(q):
    params = {"q": q, "count": 10, "mkt": "en-US"}
    response = requests.get(BING_ENDPOINT, params=params)
    response.raise_for_status()
    return [
        [rec.get('url'), rec.get('name'), rec.get('snippet')]
        for rec in response.json()['webPages']['value']
    ]


def summarize_results(query, titles, snippets):
    results = [
        title + ":" + snippet
        for title, snippet in zip(titles, snippets)
        if title and snippet
    ]
    if not results:
        return ""

    prompt = (
        "Formulate a 100 word answer to this question\n"
        + query
        + "\n"
        + "Based on these web search results (titles and snippets):\n"
        + "\n".join(results)
    )
    # No key needed; Neptyne provides one:
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "assistant",
                "content": prompt,
            },
        ],
    )
    return completion.choices[0].message.content
