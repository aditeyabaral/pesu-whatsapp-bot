import os
import praw
import logging
import datetime
from dotenv import load_dotenv
from prawcore.exceptions import RequestException

load_dotenv()
reddit = praw.Reddit(
    client_id=os.environ['REDDIT_PERSONAL_USE_TOKEN'],
    client_secret=os.environ['REDDIT_SECRET_TOKEN'],
    user_agent=os.environ['REDDIT_USER_AGENT']
)


def get_reddit_posts(subreddit='PESU'):
    data = list()
    try:
        subreddit = reddit.subreddit(subreddit)
        for post in subreddit.new(limit=10):
            if post.over_18:
                continue
            post_data = dict()
            post_data["title"] = post.title
            post_data["content"] = post.selftext
            post_data["url"] = f"https://reddit.com{post.permalink}"
            post_data["create_time"] = datetime.datetime.fromtimestamp(
                post.created_utc)
            post_data["author"] = post.author.name
            post_data["images"] = list()
            if "media_metadata" in post.__dict__:
                image_details = post.media_metadata
                if image_details:
                    for key in image_details:
                        if image_details[key]['e'] == "Image":
                            post_data["images"].append(
                                image_details[key]['p'][-1]['u'])
            elif "preview" in post.__dict__:
                if post.preview["images"]:
                    for i in post.preview["images"]:
                        post_data["images"].append(i["resolutions"][-1]["url"])
            data.append(post_data)

    except RequestException as error:
        logging.error(f"Request Exception while fetching from Reddit: {error}")
        return get_reddit_posts(subreddit)
    return data
