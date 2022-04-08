import os
import re
import pytz
import base64
import logging
from pathlib import Path
from dotenv import load_dotenv
from twilio.rest import Client
from urllib.parse import parse_qs
from requests.utils import requote_uri
from flask import Flask, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler

from db import *
from reddit import *
from instagram import *
from pesu_academy import *

logging.basicConfig(
    level=logging.INFO,
    filemode='w',
    filename='app.log',
    format='%(asctime)s - %(filename)s - %(lineno)d %(levelname)s - %(message)s'
)

load_dotenv()
app = Flask(__name__)
IST = pytz.timezone('Asia/Kolkata')
HOST_NAME = os.environ['HOST_NAME']
PORT = os.environ['PORT']
APP_TOKEN = os.environ['APP_TOKEN']
ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_NUMBER = os.environ['TWILIO_NUMBER']
TWILIO_JOIN_CODE = os.environ['TWILIO_JOIN_CODE']
PESU_ACADEMY_SRN = os.environ['PESU_ACADEMY_SRN']
PESU_ACADEMY_PASSWORD = os.environ['PESU_ACADEMY_PASSWORD']


def send_message(to, body, media=None):
    try:
        body_chunks = [body[i:i+1566] for i in range(0, len(body), 1566)]
        num_chunks = len(body_chunks)

        # Send first chunk with media if any
        if media is None:
            message = twilio_client.messages.create(
                to=f'whatsapp:{to}',
                from_=f"whatsapp:{TWILIO_NUMBER}",
                body=body_chunks[0]
            )
        else:
            message = twilio_client.messages.create(
                to=f'whatsapp:{to}',
                from_=f"whatsapp:{TWILIO_NUMBER}",
                body=body_chunks[0],
                media_url=requote_uri(media)
            )
        time.sleep(1)

        # Send remaining chunks without media
        for i in range(1, num_chunks):
            message = twilio_client.messages.create(
                to=f'whatsapp:{to}',
                from_=f"whatsapp:{TWILIO_NUMBER}",
                body=body_chunks[i]
            )
            time.sleep(1)
    except Exception as e:
        logging.error(f"Error sending message to {to}: {e}")


@app.route("/")
def index():
    url = requote_uri(f'https://wa.me/{TWILIO_NUMBER}?text={TWILIO_JOIN_CODE}')
    return f"Visit {url} and send the messsage to join the channel!", 200


@app.route("/file/<filename>")
def serve(filename):
    # change this to POST and add a token to fetch. Or use params
    return send_from_directory('../', filename, as_attachment=True), 200


@app.route("/upload", methods=['POST'])
def upload():
    token = request.get_json().get('token', None)
    if token != APP_TOKEN:
        return 'Invalid token', 403
    file = request.files['file']
    file.save(os.path.join('../', file.filename))
    return 'OK', 200


@app.route("/receive", methods=['POST'])
def receive():
    data = parse_qs(request.get_data().decode())
    logging.info(data)
    content = data['Body'][0].strip()
    from_number = f"+{data['WaId'][0]}"

    if content == 'subscribe':
        if not check_subscriber_exists(from_number):
            add_subscriber(from_number)
            send_message(
                from_number, "You have successfully subscribed to the channel!")
        else:
            send_message(
                from_number, "You are already a member of the channel!")
    elif content == 'unsubscribe':
        if check_subscriber_exists(from_number):
            remove_subscriber(from_number)
            send_message(from_number, "You have successfully unsubscribed from the channel!")
        else:
            send_message(from_number, "You are not a member of the channel!")
    return 'OK', 200


@app.route("/send", methods=['POST'])
def send():
    data = request.get_json()
    to = data.get('to', None)
    body = data.get('body', None)
    media = data.get('media', None)
    token = data.get('token', None)
    if token != APP_TOKEN:
        return 'Invalid token', 403
    if to is None or body is None:
        return 'Invalid request', 400
    send_message(to, body, media)
    return 'OK', 200


def get_latest_reddit_posts():
    logging.info("Fetching latest Reddit posts")
    posts = get_reddit_posts()
    for post in posts:
        post_time = post["create_time"]
        current_time = datetime.datetime.utcnow()
        time_difference = current_time - post_time
        if time_difference.seconds <= 3600 and time_difference.days == 0:
            content = f"Latest Reddit Post on r/PESU | *{post['title']}*\n{post['author']}\n\n{post['content']}\n\n{post['url']}"
            media_url = post['images'][0] if post['images'] else None
            for number in get_all_subscribers():
                send_message(number, content, media_url)


def get_latest_instagram_posts():
    logging.info("Fetching latest Instagram posts")
    posts = get_instagram_posts()
    current_time = datetime.datetime.now(IST)
    for post in posts:
        post_time = post["time"]
        time_difference = current_time - post_time
        if time_difference.days == 0 and time_difference.seconds <= 600:
            content = f"Latest Instagram Post by @{post['username']}\n\n{post['caption']}\n\n{post['url']}"
            if post['video_url'] is not None:
                media_url = post['video_url']
                for number in get_all_subscribers():
                    send_message(number, content, media_url)
                    send_message(number, content)
            else:
                if post['img_url'] is not None:
                    media_url = post['img_url']
                else:
                    media_url = post['url']
                for number in get_all_subscribers():
                    send_message(number, content, media_url)


def get_latest_pesu_announcements():
    global ALL_ANNOUNCEMENTS_MADE
    global TODAY_ANNOUNCEMENTS_MADE

    logging.info("Fetching announcements from PESU Academy")
    all_announcements = get_pesu_announcements(
        PESU_ACADEMY_SRN, PESU_ACADEMY_PASSWORD)
    new_announcement_count = 0
    for a in all_announcements:
        if a not in ALL_ANNOUNCEMENTS_MADE:
            ALL_ANNOUNCEMENTS_MADE.append(a)
            new_announcement_count += 1

    logging.info(f"New announcements found: {new_announcement_count}")
    ALL_ANNOUNCEMENTS_MADE.sort(key=lambda x: x["date"], reverse=True)
    current_date = datetime.datetime.now().date()
    for announcement in all_announcements:
        if announcement["date"] == current_date:
            if announcement not in TODAY_ANNOUNCEMENTS_MADE:
                img_filename = None
                if announcement["img"] != None:
                    img_base64 = announcement["img"].strip()[22:]
                    img_data = base64.b64decode(img_base64)
                    announcement_title = announcement["header"]
                    formatted_announcement_title = re.sub(
                        r'[^\w\s]', '-', announcement_title)
                    img_filename = f"announcement-img-{formatted_announcement_title}.png"
                    with open(img_filename, 'wb') as f:
                        f.write(img_data)
                    img_filename = f"{HOST_NAME}:{PORT}/file/" + \
                        img_filename if img_filename else None

                attachment_files = list()
                announcement_urls = list()
                if announcement["attachments"]:
                    for fname in announcement["attachments"]:
                        fname = Path(fname).name
                        if fname in os.listdir():
                            attachment_files.append(fname)
                        else:
                            logging.error(
                                f"Could not find attachment: {fname}")
                            if fname.startswith("http"):
                                announcement_urls.append(fname)

                content = f"*{announcement['header']}*\n_{announcement['date']}_\n\n{announcement['body']}"
                if announcement_urls:
                    content += "\n\n" + "\n".join(announcement_urls)

                for number in get_all_subscribers():
                    send_message(number, content, img_filename)
                    for fname in attachment_files:
                        fname = f"{HOST_NAME}:{PORT}/file/" + fname
                        send_message(number, fname, fname)

                TODAY_ANNOUNCEMENTS_MADE.append(announcement)


if __name__ == "__main__":
    twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)
    ALL_ANNOUNCEMENTS_MADE = list()
    TODAY_ANNOUNCEMENTS_MADE = list()

    scheduler = BackgroundScheduler()
    scheduler.add_job(get_latest_reddit_posts, 'interval', minutes=60)
    scheduler.add_job(get_latest_instagram_posts, 'interval', minutes=10)
    scheduler.add_job(get_latest_pesu_announcements, 'interval', seconds=60)
    scheduler.start()
    app.run(host='0.0.0.0', port=PORT, debug=True, use_reloader=False)
