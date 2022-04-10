# PESU WhatsApp Bot

PESU Academy WhatsApp Bot for the PESsants and PESts of PES University

You can add the bot using [this](https://wa.me/+14155238886?text=join%20sets-ever) link. Once the bot has join, please send `subscribe` to subscribe to notifications.

You can also send `unsubscribe` to unsubscribe yourself from notifications.

Every 72 hours, your subscription will expire. You can renew your subscription by sending `subscribe` again, followed by `join sets-ever`. If you notice that you are not receiving messages, renewing your subscription will resolve the issue.

## What can the bot do?

1. It periodically fetches PESU announcements and notifies you immediately. With a refresh interval of **1 minute**, it proves to be faster than the PESU Academy website!
2. It updates you about Instagram posts made by clubs
3. It follows the r/PESU subreddit

## Setup the WhatsApp Bot

1. The bot uses the Twilio WhatsApp API. Sign up on [Twilio WhatsApp](https://www.twilio.com/whatsapp/) to obtain a phone number, a join code and your client credentials

2. After setting up the API, you need to set the redirect URL for when a message is sent to the bot to a route on the Flask app. This can be done on the Twilio console. Set it to `host_name:port_number/recieve` 

3. Clone the repository
```bash
git clone git@github.com:aditeyabaral/pesu-whatsapp-bot.git
```

4. Create a separate virtual environment and install the dependencies. You can use virtualenv -- simple to setup and use.
```bash
cd pesu-whatsapp-bot
virtualenv bot
source bot/bin/activate
pip3 install -r requirements.txt
```

5. Setup an `.env` file with the following variables

```bash
TWILIO_ACCOUNT_SID=""
TWILIO_AUTH_TOKEN=""
TWILIO_NUMBER=""
TWILIO_JOIN_CODE=""
APP_TOKEN=""
HOST_NAME=""
PORT=""
DATABASE_URL=""
PESU_ACADEMY_SRN=""
PESU_ACADEMY_PASSWORD=""
REDDIT_SECRET_TOKEN=""
REDDIT_PERSONAL_USE_TOKEN=""
REDDIT_USER_AGENT=""
```

6. Run the bot using the following command
```bash
python3 app/app.py
```

## How to contribute to PESU WhatsApp Bot?

We are not looking for new contributions at the moment, since it would defeat the purpose of having a quick and easy way to get the announcements.

However, feel free to open an issue if you have any suggestions.

## Maintainers

Contact any of us for any support.

[Aditeya Baral](https://github.com/aditeyabaral)<br>
[Aronya Baksy](https://github.com/abaksy)