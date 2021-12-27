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
#       This way, it is able to conveniently interact with the back-end database.
# ******************************
import argparse
import csv
import inspect
import os
import pycountry
import random
import string
import sys
from datetime import datetime
from sqlalchemy.exc import IntegrityError

# allow import of modules from parent directory
cur_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(cur_dir)
sys.path.insert(0, parent_dir)
from app import create_app, db
from app.models import User, Post


# constants
PASSWORD_LENGTH = 16
EMAIL_DOMAIN = 'microblog.xyz'
DEFAULT_DATETIME = datetime(1970, 1, 1)
_BATCH_SIZE = 100


# parse command line arguments
def parse_arguments():
    # print help message if parsing fails.
    #    Credit: Steven Bethard (https://groups.google.com/g/argparse-users/c/LazV_tEQvQw?pli=1)
    class DefaultHelpParser(argparse.ArgumentParser):
        def error(self, message):
            sys.stderr.write('error: %s\n' % message)
            self.print_help()
            sys.exit(2)

    parser = DefaultHelpParser(description="""
    Import Twitter posts into Microblog database.
    Currently only supports the COVID-19 dataset from https://www.trackmyhashtag.com/data/COVID-19.zip
    """)
    parser.add_argument('filename', type=str,
                        help='CSV file to be imported')
    parser.add_argument('-m', '--max-tweets', type=int, default=0,  # import all lines by default
                        help='maximum number of tweets to be imported')
    return parser.parse_args()


def _print_progress(stats):
    """
    Print import progress.
       Customise this function if a more user-friendly output is required.
    """
    print(stats)


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
    user.email = "{}@{}".format(user.username, EMAIL_DOMAIN)
    user.about_me = tweet['User Bio'][0:140]
    # generate a random password
    password_chars = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(password_chars) for i in range(PASSWORD_LENGTH))
    user.password_hash = user.set_password(password)
    # prepare post record
    post = Post()
    post.id = int(tweet['Tweet Id'].strip('"'))
    post.body = tweet['Tweet Content'][0:140]
    post.user_id = user.id
    try:
        post.timestamp = datetime.strptime(tweet['Tweet Posted Time (UTC)'], '%d %b %Y %H:%M:%S')
    except Exception:  # unexpected error when parsing datetime
        post.timestamp = DEFAULT_DATETIME  # set default timestamp if parsing fails
    language = pycountry.languages.get(name=tweet['Tweet Language'])
    if language and hasattr(language, 'alpha_2'):  # try to get the two-digit language code
        post.language = language.alpha_2
    return user, post


def import_csv(filename, max_import_count=0):
    """
    Main function that coordinates the overall data import process.
    """
    # statistics dictionary. the sum of posts* and users* should always be the same as tweet_cnt
    stats = {'posts_ok': 0, 'posts_dup': 0, 'posts_err': 0,
             'users_ok': 0, 'users_dup': 0, 'users_err': 0, 'users_skipped': 0,
             'tweet_cnt': 0,
             }
    # process the input file
    with open(filename, 'r') as csvfile:
        for line_no, row in enumerate(csv.DictReader(csvfile)):
            # flags to remember insert success
            user_ok = False
            post_ok = False
            # construct user and post objects from tweet dictionary
            try:
                user, post = _parse_covid_tweet(row)
            except Exception as e:
                stats['users_err'] += 1
                stats['posts_err'] += 1
                _log_line_error(line_no, e)
                continue  # failed to parse line, try the next record
            # attempt to insert user
            try:
                db.session.add(user)
                user_ok = True  # flag to remember whether user insert was successful
            except IntegrityError:  # record already exists
                stats['users_dup'] += 1
            except Exception as e:  # unexpected error
                stats['users_err'] += 1
                _log_line_error(line_no, e)
            # attempt to insert post
            try:
                db.session.add(post)
                db.session.commit()
                post_ok = True
                stats['posts_ok'] += 1
                stats['users_ok'] += 1 if user_ok else 0
            except IntegrityError:  # record already exists
                stats['posts_dup'] += 1
            except Exception as e:  # unexpected error
                stats['posts_err'] += 1
                _log_line_error(line_no, e)
            # roll back in case post insert failed
            if not post_ok:
                db.session.rollback()
                stats['users_skipped'] += 1 if user_ok else 0
            # total number of lines processed
            stats['tweet_cnt'] += 1
            # max count reached. finish.
            if 0 < max_import_count <= stats['posts_ok']:
                _print_progress(stats)
                break
            # print progress after each batch
            if stats['tweet_cnt'] % _BATCH_SIZE == 0:
                _print_progress(stats)


if __name__ == '__main__':
    args = parse_arguments()
    # set up flask app
    app = create_app()
    app_context = app.app_context()
    app_context.push()
    # for testing purposes only
    import_csv(filename=args.filename, max_import_count=args.max_tweets)
    # tear down flask app
    db.session.remove()
    app_context.pop()
