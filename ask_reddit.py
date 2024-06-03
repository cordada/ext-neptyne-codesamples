# License: MIT License
# This sample code shows how to use the reddit API to fetch posts from Ask Reddit.
# We fetch the posts and the comments on the posts, then use the OpenAI API to generate
# a consensus answer to the question asked in the post. We then post the answer to Twitter
# and update a Google Sheet with the answer and send out an email with the answer. The code
# is scheduled to run twice daily.

# You can try this out in the spreadsheet here:
# https://docs.google.com/spreadsheets/d/1YXXBW_B6DeKVJQHGjowf1AJr9s6_yYItPcvDlChf9YM/edit#gid=0


import requests
import neptyne as nt
from openai import OpenAI
from datetime import datetime, timedelta
import praw
from requests_oauthlib import OAuth1

USER_NAME = "DouweOsinga"
USER_AGENT = (f"AnswerBot by /u/{USER_NAME} "
              "https://docs.google.com/spreadsheets/d/1YXXBW_B6DeKVJQHGjowf1AJr9s6_yYItPcvDlChf9YM")


def post_to_twitter(tweet):
    """Make sure to get the consumer_key also known as api key, not the client_id:"""
    url = "https://api.twitter.com/2/tweets"
    auth = OAuth1(nt.get_secret("CONSUMER_KEY"),
                  nt.get_secret("CONSUMER_KEY_SECRET"),
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


def get_reddit_posts(subreddit_name: str, limit: int = 10):
    reddit = praw.Reddit(
        client_id='OWXEgabGO80TYDDMmUJFRA',
        client_secret='f6JUMdyBSHVnnfg0i-ATEzFiW9npYw',
        user_agent=USER_AGENT,
        username=USER_NAME,
    )

    subreddit = reddit.subreddit(subreddit_name)
    posts = subreddit.hot(limit=limit)

    results = []
    for post in posts:
        if post.score >= 3000:
            comments = post.comments.list()
            formatted_date = datetime.utcfromtimestamp(
                post.created_utc).strftime("%Y-%m-%d")
            results.append({
                'title': post.title,
                'url': post.url,
                'score': post.score,
                'date': formatted_date,
                'author': post.author.name,
                'comments': [comment.body for comment in comments if isinstance(comment, praw.models.Comment)]
            })

    return results


def process_post(post):
    asker = post['author']
    discussion = "\n".join(post['comments'])[:3500]
    question = post['title']
    formatted_date = post['date'][:10]
    url = post['url']
    score = post['score']
    prompt = [
        "Given this threaded discussion:\n\n",
        discussion,
        "\n\nFormulate an answer to this question:",
        question,
        "\nfrom ",
        asker]
    prompt += [
        "Try to get to a consensus answer in 60 words. Some questions ask for personal replies, ",
        "how did you spend your summer? Other ask for a general answer like, what is the best way to ",
        "spend a summer. In the first case, return an overview of answers given. In the second case ",
        "return a summary. Formulate the answer as an actual answer to the question that makes sense to ",
        "somebody who doesn't know there was a discussion. Don't use markdown."
    ]
    consensus = call_ai("".join(prompt))
    return formatted_date, url, asker, score, question, consensus


def update_sheet(posts):
    new_rows = []
    rows = {
        row[1]: row
        for row in B5:G
    }
    for post in posts:
        url = post['url']
        if url not in rows:
            new_row = process_post(post)
            new_rows.append(new_row)
            rows[new_row[1]] = new_row
            B5 = sorted(rows.values(), key=lambda row: row[0], reverse=True)
    return new_rows


def generate_tweet(answer, url):
    budget = 280 - 24 - 2
    if len(answer) > budget - 30:
        print(f"Answer too long {len(answer)} reduing to {budget - 30}")
        prompt = f"Summarize this answer to {budget - 20} characters:" + answer
        answer = call_ai(prompt)
        print(f"Now {len(answer)}")

    if len(answer) > budget:
        answer = answer[:budget - 3] + "..."
    tweet = answer + "\n" + url
    return tweet


@nt.daily(hour=1, minute=1, timezone="America/New_York")
@nt.daily(hour=13, minute=1, timezone="America/New_York")
async def keep_updated():
    print("Running...")
    posts = get_reddit_posts("AskReddit", limit=25)
    new_rows = update_sheet(posts)
    paras = []
    for date, url, poster, score, question, answer in new_rows:
        paras.append(f"{poster}: {question}")
        paras.append(answer)
        paras.append(url)
        paras.append('')
    if paras:
        nt.email.send("douwe.osinga@gmail.com", f"{len(new_rows)} New Answers",
                      "\n".join(paras))
    for date, url, poster, score, question, answer in new_rows:
        tweet = generate_tweet(answer, url)
        post_to_twitter(tweet)
    print("Processed", len(new_rows), "rows")
    return new_rows
