from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LinearRegression
import numpy as np
import spacy
import json

nlp = spacy.load("nl_core_news_sm")


# Load the JSON data from the file.
with open("../data/review.json") as f:
    data = json.load(f)

orgdata = {}

# Fix and organize the data, to ease out work.
for review in data:
    app_id = review["app"]["$oid"]
    orgdata.setdefault(app_id, [])
    orgdata[app_id].append(review)

vectorizer = CountVectorizer()
for app in orgdata:
    reviews, ratings = [], []
    for review in orgdata[app]:
        reviews.append(review["comment"])
        ratings.append(review["rating"])
    x_array = vectorizer.fit_transform(reviews)
    linear_regression = LinearRegression().fit(x_array, ratings)
    voc_coef = dict(zip(vectorizer.vocabulary_, linear_regression.coef_))
    
    print(dict(sorted(voc_coef.items(), key=lambda x: x[1])))
    # print(linear_regression.predict(x_array))