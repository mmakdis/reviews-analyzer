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

nlp_nl = spacy.load("nl_core_news_sm")
nlp_en = spacy.load("en_core_web_sm")

nlp_en.add_pipe(LanguageDetector(), name='language_detector', last=True)
stemmed_to_unstemmed = defaultdict(Counter)


POS_TO_USE = ["NOUN"]


def get_nouns(sentence: str, lang: str) -> str:
    doc = nlp_en(sentence) if lang == "en" else nlp_nl(sentence)
    nouns = [token.pos_ for token in doc]
    indices = [str(doc[i]) for i, x in enumerate(nouns) if x in POS_TO_USE]
    #print(indices)
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


def get_negative(coef: dict) -> list:
    _ = list(sorted_voc_coef.keys())[:2]
    negatives = [key for key in _ if coef[key] < 0]
    return negatives


def get_positive(coef: dict) -> list:
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
app_coef = {}
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
    voc_coef = dict(zip(vectorizer.vocabulary_, linear_regression.coef_))
    sorted_voc_coef = dict(sorted(voc_coef.items(), key=lambda x: x[1]))
    print(f"Positives: {get_positive(sorted_voc_coef)}")
    print(f"Negatives: {get_negative(sorted_voc_coef)}\n")
    # print(linear_regression.predict(x_array))


#cnt_matrix = vectorizer_unstemmed.fit_transform(all_reviews_unstemmed).toarray().transpose()
#vocab_unstemmed = list(vectorizer_unstemmed.vocabulary_.keys())

print(stemmed_to_unstemmed['inlogg'].most_common(1))
