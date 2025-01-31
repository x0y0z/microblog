#!/usr/bin/env python
# ******************************
# File: tweet_importer.py
# Author: Mario Schranz
#
# Description
# -----------
# Script to import Twitter posts (i.e. tweets) into a back-end database
#    and create a user account for each author.
#
# Note: This script is designed to be run from a flask shell.
#       This way, it is able to use database-mapped objects.
# ******************************
import argparse
import csv
import hashlib
import inspect
import os
import re
import pycountry
import random
import string
import sys
from datetime import datetime
from sqlalchemy.exc import IntegrityError

# allow import of modules from parent directory
cur_file = inspect.getfile(inspect.currentframe())
cur_dir = os.path.dirname(os.path.abspath(cur_file))
parent_dir = os.path.dirname(cur_dir)
sys.path.insert(0, parent_dir)
from app import create_app, db
from app.models import User, Post


# constants
PSW_LEN = 16
EMAIL_DOMAIN = 'microblog.xyz'
DFLT_TS = datetime(1970, 1, 1)
OBFUSCATE_USERNAME = True
_BATCH_SIZE = 100
# regexp for emojis (source: https://stackoverflow.com/a/58356570)
_EMOJI = re.compile("["
                    u"\U0001F600-\U0001F64F"  # emoticons
                    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                    u"\U0001F680-\U0001F6FF"  # transport & map symbols
                    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                    u"\U00002500-\U00002BEF"  # chinese char
                    u"\U00002702-\U000027B0"
                    u"\U00002702-\U000027B0"
                    u"\U000024C2-\U0001F251"
                    u"\U0001f926-\U0001f937"
                    u"\U00010000-\U0010ffff"
                    u"\u2640-\u2642"
                    u"\u2600-\u2B55"
                    u"\u200d"
                    u"\u23cf"
                    u"\u23e9"
                    u"\u231a"
                    u"\ufe0f"  # dingbats
                    u"\u3030"
                    "]+", re.UNICODE)


# parse command line arguments
def parse_arguments():
    # print help message if parsing fails (Credit: Steven Bethard)
    #   https://groups.google.com/g/argparse-users/c/LazV_tEQvQw?pli=1
    class DefaultHelpParser(argparse.ArgumentParser):
        def error(self, message):
            sys.stderr.write('error: %s\n' % message)
            self.print_help()
            sys.exit(2)

    p = DefaultHelpParser(description="""
    Import Twitter posts into Microblog database.
      Supported dataset: https://www.trackmyhashtag.com/data/COVID-19.zip
    """)
    p.add_argument('filename', type=str,
                   help="CSV file to be imported")
    p.add_argument('-m', '--max-posts', type=int,
                   default=0,  # import all lines by default
                   help="maximum number of posts to be imported" +
                        ", defaults to 0 (unlimited)")
    p.add_argument('-o', '--offset', type=int, default=1,
                   help="line offset within CSV file to start import at" +
                        ", defaults to 1")
    args = p.parse_args()
    if args.max_posts < 0:
        p.error("maximum number of posts must be at least 0")
    if args.max_posts < 1:
        p.error("line offset must be at least 1")
    return args


def _print_progress(stats):
    """
    Print import progress. Customise this function if required.
    """
    print("{}:{}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), stats))


def _log_line_error(line_number, payload):
    """
    Log an import error for a specific line.
    """
    print("Error on line {}: {}".format(line_number, payload))


def _parse_covid_tweet(tweet):
    """
    Parse a tweet from the COVID-19 dataset from
       https://www.trackmyhashtag.com/data/COVID-19.zip
    """
    # prepare user record
    user = User()
    user.id = int(tweet["User Id"].strip('"'))
    user.username = tweet['Screen Name'].lower()
    if OBFUSCATE_USERNAME:  # optionally hash the username using SHA224
        user_hash = hashlib.sha224(user.username.encode('utf-8'))
        user.username = user_hash.hexdigest()
    user.email = "{}@{}".format(user.username, EMAIL_DOMAIN)
    user.about_me = re.sub(_EMOJI, '', tweet['User Bio'])[0:140]
    # generate a random password
    psw_chars = string.ascii_letters + string.digits + string.punctuation
    psw = ''.join(random.choice(psw_chars) for _ in range(PSW_LEN))
    user.password_hash = user.set_password(psw)
    # prepare post record
    post = Post()
    post.id = int(tweet['Tweet Id'].strip('"'))
    post.body = re.sub(_EMOJI, '', tweet['Tweet Content'])[0:140]
    post.user_id = user.id
    try:
        post.timestamp = datetime.strptime(tweet['Tweet Posted Time (UTC)'],
                                           '%d %b %Y %H:%M:%S')
    except Exception:  # unexpected error when parsing datetime
        post.timestamp = DFLT_TS  # default timestamp if parsing fails
    language = pycountry.languages.get(name=tweet['Tweet Language'])
    if language and hasattr(language, 'alpha_2'):  # get two-digit lang code
        post.language = language.alpha_2
    return user, post


def import_csv(filename, max_import_count=0, offset=0):
    """
    Main function that coordinates the overall data import process.
    """
    # ensure parameters are larger or equal than zero
    max_count = max(0, max_import_count)
    start_line = max(1, offset)
    print("Importing up to {} posts from {}, starting at offset {}".
          format("UNLIMITED" if max_count <= 0 else max_count,
                 filename, start_line))
    # statistics: sum of posts* and users* should match tweet_cnt
    stats = {'line_no': 0, 'tweet_cnt': 0,
             'post_ok': 0, 'post_dup': 0, 'post_err': 0,
             'user_ok': 0, 'user_dup': 0, 'user_err': 0, 'user_posterr': 0,
             }
    # process the input file
    with open(filename, 'r') as csv_file:
        for line_no, row in enumerate(csv.DictReader(csv_file)):
            if line_no <= start_line-1:
                continue  # skip the first n lines
            # flags to remember insert success
            user_ok = False
            post_ok = False
            # construct user and post objects from tweet dictionary
            try:
                user, post = _parse_covid_tweet(row)
            except Exception as e:
                stats['user_err'] += 1
                stats['post_err'] += 1
                _log_line_error(line_no, e)
                continue  # failed to parse line, try the next record
            # attempt to insert user
            try:
                db.session.add(user)
                db.session.commit()
                user_ok = True  # remember user insert success
            except IntegrityError:  # record already exists
                stats['user_dup'] += 1
            except Exception as e:  # unexpected error
                stats['user_err'] += 1
                _log_line_error(line_no, e)
            # roll back in case user insert failed
            if not user_ok:
                db.session.rollback()
            # attempt to insert post
            try:
                db.session.add(post)
                db.session.commit()
                post_ok = True  # remember post insert success
                stats['post_ok'] += 1
                stats['user_ok'] += 1 if user_ok else 0
            except IntegrityError:  # record already exists
                stats['post_dup'] += 1
            except Exception as e:  # unexpected error
                stats['post_err'] += 1
                _log_line_error(line_no, e)
            # roll back in case post insert failed
            if not post_ok:
                db.session.rollback()
                stats['user_posterr'] += 1 if user_ok else 0
            # total number of lines processed
            stats['tweet_cnt'] += 1
            # max count reached. finish.
            if 0 < max_count <= stats['post_ok']:
                stats['line_no'] = line_no
                _print_progress(stats)
                break
            # print progress after each batch
            if stats['tweet_cnt'] % _BATCH_SIZE == 0:
                stats['line_no'] = line_no
                _print_progress(stats)


if __name__ == '__main__':
    param = parse_arguments()
    # set up flask app
    app = create_app()
    app_context = app.app_context()
    app_context.push()
    # perform the actual import
    import_csv(filename=param.filename, max_import_count=param.max_posts,
               offset=param.offset)
    # tear down flask app
    db.session.remove()
    app_context.pop()
