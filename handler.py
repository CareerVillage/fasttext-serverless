import json
import logging
import subprocess
import re
import sys
import unicodedata

from HTMLParser import HTMLParser


# Input text must be pre-processed for fastText to use
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_html_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

punctuation_table = dict.fromkeys(i for i in xrange(sys.maxunicode)
                      if unicodedata.category(unichr(i)).startswith('P'))

def preprocess_text(input):
    s = input
    s = strip_html_tags(s)
    s = s.lower()
    s = s.translate(punctuation_table) # Remove punctuation
    return s

# Find existing hashtags so we do not recomment them again
def find_hashtags(text):
    HASHTAG_REGEXP = r'\B(#[\w-]{3,})\b(?![#\-\w])'
    return re.findall(HASHTAG_REGEXP, text)


# API endpoint returns recommendations and existing hashtags
def endpoint(event, context):
    data = json.loads(event['body'])
    if 'text' not in data:
        logging.error("Validation Failed")
        raise Exception("Couldn't read any provided text.")
        return

    raw_text = data['text']
    clean_text = preprocess_text(raw_text)

    p = subprocess.Popen(
        ['./fasttext', 'predict-prob', 'trained_models/model_standard.bin', '-', '5'],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE
        )

    stdout_recommendations = p.communicate(input=clean_text)

    body = {
        "hashtags_recommended": str(stdout_recommendations),
        "hashtags_already_used": str(" ".join(find_hashtags(raw_text)))
    }

    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin" : "*", # Required for CORS support to work
            "Access-Control-Allow-Credentials" : "true"
        },
        "body": json.dumps(body)
    }

    return response
