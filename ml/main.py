 # -*- coding: utf-8 -*-
from collections import defaultdict, Counter
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LinearRegression
from pprint import pprint
import spacy
from nltk.stem.snowball import SnowballStemmer
from spacy.lookups import Lookups
from spacy_langdetect import LanguageDetector
from datetime import datetime
import json
from tqdm import tqdm
import argparse


parser = argparse.ArgumentParser(description="This script handles the NLP over the user reviews.")

# Optional argument
parser.add_argument('-p', '--pos-to-use', nargs='+',
                help='The types of POS to use. Usage: -p VERB NUM ADP')

parsed = parser.parse_args()

nlp_nl = spacy.load("nl_core_news_sm")
nlp_en = spacy.load("en_core_web_sm")

nlp_en.add_pipe(LanguageDetector(), name='language_detector', last=True)
stemmed_to_unstemmed = defaultdict(Counter)


POS_TO_USE = ["NOUN"]

for _, value in parsed._get_kwargs():
    if _ == "pos_to_use" and value is not None:
        POS_TO_USE.extend(value)


def get_nouns(sentence: str, lang: str) -> str:
    doc = nlp_en(sentence) if lang == "en" else nlp_nl(sentence)
    nouns = [token.pos_ for token in doc]
    indices = [str(doc[i]) for i, x in enumerate(nouns) if x in POS_TO_USE]
    stemmer = SnowballStemmer(language="english" if lang == "en" else "dutch")
    # Count how many times token maps to stemmed token
    for token in indices:
        stemmed_to_unstemmed[stemmer.stem(token).lower()][token.lower()] += 1

    return " ".join([stemmer.stem(token) for token in indices])


def difference_in_months(start: datetime, end: datetime) -> int:
    if start.year == end.year:
        months = end.month - start.month
    else:
        months = (12 - start.month) + (end.month)

    return months


def get_negatives(coef: dict) -> list:
    _ = list(sorted_voc_coef.keys())[:2]
    negatives = [key for key in _ if coef[key] < 0]
    return negatives


def get_positives(coef: dict) -> list:
    _ = list(sorted_voc_coef.keys())[-2:]
    positives = [key for key in _ if coef[key] > 0]
    return positives


# Load the JSON data from the file.
with open("../data/review.json") as f:
    data = json.load(f)

orgdata = {}
datedata = {}

# Fix and organize the data, to ease out work.
for review in data:
    app_id = review["app"]["$oid"]
    orgdata.setdefault(app_id, [])
    orgdata[app_id].append(review)
    datedata.setdefault(app_id, {})

for app in orgdata:
    sorted_app: dict = sorted(orgdata[app], key=lambda k: k['timestamp']['$date'])
    old_date = None
    for date in sorted_app:
        temp_date = datetime.utcfromtimestamp(date["timestamp"]["$date"] / 1000)
        if old_date is None:
            old_date = temp_date
            datedata[app][old_date.strftime("%b-%y")] = [date]
            continue
        difference = difference_in_months(old_date, temp_date)
        if difference < 1:
            datedata[app][old_date.strftime("%b-%y")].append(date)
        else:
            old_date = temp_date
            datedata[app][old_date.strftime("%b-%y")] = [date]

with open("output.json", "w") as file:
    pass
    file.write(json.dumps(datedata))

vectorizer = CountVectorizer(min_df=0.05)
_app_coef = {}
for app in datedata:
    reviews, ratings = [], []
    for date in datedata[app]:
        for review in datedata[app][date]:
            doc = nlp_en(review["comment"])
            lang = doc._.language["language"]
            nouns_only_stemmed = get_nouns(review["comment"], lang)
            reviews.append(nouns_only_stemmed)
            ratings.append(review["rating"])

    x_array = vectorizer.fit_transform(reviews)
    linear_regression = LinearRegression().fit(x_array, ratings)
    voc_coef = dict(zip(vectorizer.get_feature_names(), linear_regression.coef_))
    sorted_voc_coef = dict(sorted(voc_coef.items(), key=lambda x: x[1]))
    _app_coef[app] = {"positives": get_positives(sorted_voc_coef),
                      "negatives": get_negatives(sorted_voc_coef)}
    # print(linear_regression.predict(x_array))


#cnt_matrix = vectorizer_unstemmed.fit_transform(all_reviews_unstemmed).toarray().transpose()
#vocab_unstemmed = list(vectorizer_unstemmed.vocabulary_.keys())

app_coef = {}
for app in _app_coef:
    positives = [stemmed_to_unstemmed[positive].most_common(1)[0][0] for
                 positive in _app_coef[app]["positives"] if positive is not None]
    negatives = [stemmed_to_unstemmed[negative].most_common(1)[0][0] for
                 negative in _app_coef[app]["negatives"] if negative is not None]

    app_coef[app] = {"coef": {"positives": positives, "negatives": negatives}}


# Yes.
def dummy_dict() -> dict:
    _dict = {"positives": [], "negatives": []}
    for key, value in _dict.items():
        value.extend(["![NER]"] * 2)
    return _dict


def is_ok(coef: dict) -> bool:
    for key, value in coef.items():
        if not value:
            return False
    return True

with open('../data/apps.json', 'r+', encoding='utf-8') as f:
    data = json.load(f)
    for key in data:
        app_id = key["_id"]["$oid"]
        key["voc_coef"] = app_coef[app_id]["coef"] if app_id in app_coef else dummy_dict()
    f.seek(0)
    json.dump(data, f, ensure_ascii=False, indent=4)
    f.truncate()
