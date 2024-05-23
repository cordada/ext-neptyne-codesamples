# License: MIT License
# This sample code shows how to use the Y Combinator API to fetch all recent posts from the
# Ask HN section of Hacker News. We fetch the posts and their discussions recursively and
# then use the OpenAI API to generate a consensus answer to the question asked in the post.
# We then post the answer to Twitter and update a Google Sheet with the answer and send out
# an email with the answer. The code is scheduled to run daily.

# You can try this out in the spreadsheet here:
# https://docs.google.com/spreadsheets/d/1T7p-KGDB1RmdgFtil0fmk4bYP8Xu3CYH7_o8g9UyaZI/edit#gid=0


import requests
import neptyne as nt
from openai import OpenAI
from datetime import datetime, timedelta
import aiohttp
import asyncio
from requests_oauthlib import OAuth1


def post_to_twitter(tweet):
    """Make sure to get the consumer_key and not the api_key:"""
    url = "https://api.twitter.com/2/tweets"
    auth = OAuth1(nt.get_secret("CONSUMER_KEY"),
                  nt.get_secret("CONSUMER_SECRET"),
                  nt.get_secret("ACCESS_TOKEN"),
                  nt.get_secret("ACCESS_TOKEN_SECRET"))
    payload = {"text": tweet}
    return requests.post(
        auth=auth, url=url, json=payload, headers={"Content-Type": "application/json"}
    )


def call_ai(prompt):
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


async def fetch_json(session, url):
    async with session.get(url) as response:
        return await response.json()


async def post_discussion(session, story_id):
    url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
    response = await fetch_json(session, url)
    result = {
        'author': response.get('by'),
        'text': response.get('text'),
        'children': []
    }
    if 'kids' in response:
        tasks = [post_discussion(session, kid_id) for kid_id in response['kids']]
        result['children'] = await asyncio.gather(*tasks)
    return result


async def fetch_ask_hn_posts(session, before_date=None):
    url = 'https://hn.algolia.com/api/v1/search_by_date?tags=ask_hn&numericFilters=points>40'
    if before_date:
        timestamp = int(datetime.strptime(before_date, '%Y-%m-%d').timestamp())
        url += f',created_at_i<{timestamp}'
    response = await fetch_json(session, url)
    return response['hits']


async def fetch_and_process_ask_hn_posts(before_date=None):
    async with aiohttp.ClientSession() as session:
        ask_hn_posts = await fetch_ask_hn_posts(session, before_date)
        tasks = [
            post_discussion(session, post['objectID']) for post in ask_hn_posts
        ]
        discussions = await asyncio.gather(*tasks)
        results = [
            {
                **post,
                'children': discussion['children']
            }
            for post, discussion in zip(ask_hn_posts, discussions)
        ]
    return [res for res in results if res['title'].startswith('Ask HN:')]


def flatten_children(elem, indent=-1):
    if indent == -1:
        res = []
    else:
        if elem['author'] is None:
            return []
        res = [indent * '\t' + elem['author'] + ':' + elem['text'].replace('\n', ' ')]
    for child in elem['children']:
        res += flatten_children(child, indent + 1)
    return res


def process_post(post):
    answers = flatten_children(post)
    asker = post['author']
    discussion = "\n".join(answers)[:2500]
    question = post['title'][len('ask hn:'):].strip()
    story_text = post.get('story_text')
    created_at = post['created_at'][:10]
    url = f"https://news.ycombinator.com/item?id={post['story_id']}"
    prompt = [
        "Given this threaded discussion:\n\n",
        discussion,
        "\n\nFormulate an answer to this question:",
        question,
        "\nfrom ",
        asker]
    if story_text:
        prompt += [
            '\nwith this background from the author:',
            story_text,
            ".\n"]
    prompt += [
        "Try to get to a consensus answer in 60 words. Some questions ask for personal replies, ",
        "how did you spend your summer? Other ask for a general answer like, what is the best way to ",
        "spend a summer. In the first case, return an overview of answers given. In the second case ",
        "return a summary. Formulate the answer as an actual answer to the question that makes sense to ",
        "somebody who doesn't know there was a discussion. Don't use markdown."
    ]
    consensus = call_ai("".join(prompt))
    return created_at, url, asker, question, consensus


def update_sheet(posts):
    new_rows = []
    rows = {
        row[1]: row
        for row in B5:F
    }
    for post in posts:
        url = f"https://news.ycombinator.com/item?id={post['story_id']}"
        if url not in rows:
            new_row = process_post(post)
            new_rows.append(new_row)
            rows[new_row[1]] = new_row
            B5 = sorted(rows.values(), key=lambda row: row[0], reverse=True)
    return new_rows


def generate_tweet(question, answer, url):
    if len(question) > 40:
        question = call_ai("Summarize this question to 35 characters: " + question)
    budget = 280 - 24 - len(question) - 2
    if len(answer) > budget - 30:
        print(f"Answer too long {len(answer)} reduing to {budget - 30}")
        prompt = f"Summarize this answer to {budget - 20} characters:" + answer
        answer = call_ai(prompt)
        print(f"Now {len(answer)}")

    if len(answer) > budget:
        answer = answer[:budget - 3] + "..."
    tweet = question + "\n" + answer + "\n" + url
    return tweet


@nt.daily(hour=17, minute=30, timezone="America/New_York")
async def keep_updated():
    posts = await fetch_and_process_ask_hn_posts()
    new_rows = update_sheet(posts)
    paras = []
    for date, url, poster, question, answer in new_rows:
        paras.append(f"{poster}: {question}")
        paras.append(answer)
        paras.append(url)
        paras.append('')
    if paras:
        nt.email.send("douwe.osinga@gmail.com", f"{len(new_rows)} New Answers",
                      "\n".join(paras))
    for date, url, poster, question, answer in new_rows:
        tweet = generate_tweet(question, answer, url)
        post_to_twitter(tweet)
    return new_rows
