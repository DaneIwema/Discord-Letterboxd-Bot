LETTERBOXD DISCORD BOT
Description

This bot reads Letterboxd RSS feeds for linked users and posts updates in a Discord channel when new movie reviews are published. It keeps track of which reviews have already been seen using a local SQLite database. The goal is to let Discord users automatically share their latest Letterboxd activity with a server.

Setup

Clone or download the repository to your computer.

Make sure Python 3.10 or higher is installed.

Install the required libraries:
pip install discord.py requests

In the script, replace:

TOKEN with your Discord bot token.

CHANNEL_ID with the ID of the Discord channel where reviews should be posted.

Run the bot with:
python bot.py

Usage

Once the bot is running and invited to your server, users can link their Letterboxd accounts by typing:

please addme <letterboxd_username>

Example:
pweese addme johndoe

The bot will:

Fetch the user’s Letterboxd RSS feed.

Store the user’s Discord ID, Letterboxd username, and latest review date in the SQLite database.

Begin automatically checking for new reviews about every 10 minutes.

Post new reviews (title and description) in the designated channel.

Design Overview

The bot is built around three main components:

Discord integration using discord.py

Data persistence with SQLite

RSS parsing with Python’s built-in XML library

The bot uses an asynchronous loop (tasks.loop) to periodically check each user’s RSS feed. It spreads out these checks to avoid hitting Letterboxd’s servers too frequently.

Key Design Trade-offs

Simplicity vs. Scalability:

Using SQLite makes setup simple and keeps all data local, but it limits scalability. For a larger community or a hosted bot, a cloud database or persistent store would be better.

Polling vs. Event-driven Design:

The bot polls RSS feeds on a timed interval because Letterboxd does not provide webhooks or an API. This design is easier to implement but less efficient than an event-driven model.

Reliability vs. Performance:

Each user is checked sequentially with small delays to balance server load and avoid timeouts. This adds slight latency but makes the bot more reliable when checking many users.

Error Handling:

The bot uses simple return codes (404, 408, 500) to handle HTTP or parsing errors. This is easy to maintain but could be expanded with retry logic or logging for production use.

How It Works

When a user runs the "addme" command, the bot verifies the Letterboxd username by fetching their RSS feed.

The bot stores the Discord ID, username, and latest review’s date in the SQLite database.

The background loop checks each user’s RSS feed at a set interval.

If the bot finds a newer review, it updates the database and posts the title and review in the channel.

Limitations

The bot relies on public RSS feeds, so private Letterboxd profiles cannot be tracked.

Review updates are only as current as the polling interval (default: 10 minutes).

It must stay running continuously to detect updates.

Future Improvements

Add better error logging and user feedback.

Allow per-user channel preferences.

Support reactions or comments on posted reviews.

Move to a hosted database for persistence across restarts.
