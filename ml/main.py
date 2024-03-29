# -*- coding: utf-8 -*-

from collections import defaultdict, Counter
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from pprint import pprint
import spacy
from math import sqrt
from nltk.stem.snowball import SnowballStemmer
import matplotlib.pyplot as plt
from matplotlib import gridspec
import numpy as np
import re
from wordcloud import WordCloud
from PIL import Image
import random
from palettable.colorbrewer.qualitative import Dark2_8
from nltk.corpus import stopwords
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
parser.add_argument('-s', '--filter-stopwords', choices=('yes', 'no'),
                    default='yes',
                    help='Filter stopwords from the sentences or not? Usage: -s yes')
parser.add_argument('-g', '--generate-plots', action="store_true",
                    help='Use this to generate plots.')

parsed = parser.parse_args()

nlp_nl = spacy.load("nl_core_news_sm")
nlp_en = spacy.load("en_core_web_sm")

nlp_en.add_pipe(LanguageDetector(), name='language_detector', last=True)
stemmed_to_unstemmed = defaultdict(Counter)

POS_TO_USE = ["NOUN"].extend(parsed.pos_to_use) if \
    parsed.pos_to_use is not None else ["NOUN"]
FILTER_STOPWORDS = False if parsed.filter_stopwords == "no" else True
GENERATE_PLOTS = parsed.generate_plots
SIZE = (12, 8)
REPLACE_NO_SPACE = re.compile("[.;:!\'?,\"()\[\]]")
REPLACE_WITH_SPACE = re.compile("(<br\s*/><br\s*/>)|(\-)|(\/)")


class Plotting(object):
    """
    A class for handling the plots.
    Will be put in a different script.
    """

    def __init__(self, path: str = "output.json"):
        """
        Read the output.json file.
        :param path:
        """
        with open(path, encoding="utf-8") as f:
            self.data = json.load(f)

    def plot(self):
        for app, date in self.data.items():
            ratings = []
            months = []
            for month in date:
                ratings.append(sum([review["rating"] for review in date[month]]) / len(date[month]))
                months.append(month)

            x = np.array([n for n in range(len(months))])
            y = np.array(ratings)
            plt.autoscale(enable=True, axis="x", tight=False)
            plt.xticks(x, months)
            plt.title(app, fontsize=22)
            plt.autoscale(enable=True, axis="both", tight=False)
            plt.plot(x, y, "ro")
            plt.show()
            #plt.savefig(f"plots/{app}.png")

    def color_func(self, word, font_size, position, orientation, random_state=None, **kwargs):
        return tuple(Dark2_8.colors[random.randint(0, 7)])

    def show_wordcloud(self, data="Test", title=None, font_path="./Fonts/AmaticSC-Bold.ttf", icon="flag.png"):
        icon_path = "./icons/" + icon
        icon = Image.open(icon_path)
        mask = Image.new("RGB", icon.size, (255, 255, 255))
        mask.paste(icon, icon)
        mask = np.array(mask)
        for app, date in self.data.items():
            reviews = []
            for month in date:
                reviews = [review["comment"] for review in date[month]]
            wordcloud = WordCloud(
                font_path=font_path,
                background_color='white',
                mask=mask,
                max_words=2000,
                max_font_size=40,
                scale=3,
                random_state=42)

            wordcloud.generate_from_text((" ").join(reviews))
            wordcloud.recolor(color_func=self.color_func, random_state=3)
            wordcloud.to_file(f"wordclouds/{app}.png")


class NLP(object):
    """
    The NLP class to handle all NLP-related stuff.
    """

    def __init__(self):
        """
        Only thing that the constructor does is make 2 objects.
        `datedata` and `_app_coef`. `datedata` is the sorted (gonna-be) data
        that will get used by the methods. And `_app_coef` is this type of
        data:

        ```
        "voc_coef": {
                "positives": [
                    "naughty",
                    "work"
                ],
                "negatives": [
                    "grt",
                    "button"
                ]
            }
        ```
        For every app.
        """
        self.datedata = {}
        self._app_coef = {}

    def get_nouns(self, sentence: str, lang: str) -> str:
        """
        This method uses spaCy to get specific POS from sentences.
        Example: only get the nouns and the verbs. It uses POS_TO_USE-
        Which is a global variable that depends on the argument --pos-to-use.
        returns: str

        Parameters
        ----------
        sentence : str
            The sentence to use.

        lang     : str
            The language to use. If the language is not "en", then it's assumed
            that the lanuage is Dutch. Nothing else.
        """
        # Remove stop words. Yes.
        sentence = " ".join([word for word in sentence.split() if word not in
                             stopwords.words("english" if lang == "en" else "dutch")
                             ]) if FILTER_STOPWORDS else sentence
        doc = nlp_en(sentence) if lang == "en" else nlp_nl(sentence)
        nouns = [token.pos_ for token in doc]
        indices = [str(doc[i]) for i, x in enumerate(nouns) if x in POS_TO_USE]
        stemmer = SnowballStemmer(language="english" if lang == "en" else "dutch")
        # Count how many times token maps to stemmed token
        for token in indices:
            stemmed_to_unstemmed[stemmer.stem(token).lower()][token.lower()] += 1

        return " ".join([stemmer.stem(token) for token in indices])

    def difference_in_months(self, start: datetime, end: datetime) -> int:
        """
        Gets the difference between two datetimes, if in months, then return
        the difference in months.
        returns: int

        Parameters
        ----------
        start : datetime
            The start datetime.

        end   : datetime
            The end datetime.
        """
        if start.year == end.year:
            months = end.month - start.month
        else:
            months = (12 - start.month) + (end.month)

        return months

    def get_negatives(self, coef: dict) -> list:
        """
        Gets the last two (most) negative words from the provided dictionary.
        Well, technically they're at the beginning, hence the [:2].
        Only if they're < 0.
        returns: list

        Parameters
        ----------
        coef : dict
            The dict to use to get the negatives from.
        """
        _ = list(coef.keys())[:2]
        negatives = [key for key in _ if coef[key] < 0]
        return negatives

    def get_positives(self, coef: dict) -> list:
        """
        Gets the last two (most) positive words from the provided dictionary.
        Only if they're > 0.
        returns: list

        Parameters
        ----------
        coef : dict
            The dict to use to get the positives from.
        """
        _ = list(coef.keys())[-2:]
        positives = [key for key in _ if coef[key] > 0]
        return positives

    def dummy_dict(self) -> dict:
        """
        Returns a dictionary that looks like this:
        ```
        {
            "positives": [],
            "negatives": []
        }
        ```
        This is useful for less coding on the backend side.
        Cool, I know.
        """
        _dict = {"positives": [], "negatives": []}
        return _dict

    def fix_data(self) -> dict:
        """
        The data that we begin with is not very good for this type work.
        So this method first fixes it.
        """
        # Load the JSON data from the file.
        with open("../data/review.json") as f:
            data = json.load(f)

        orgdata = {}
        # Fix and organize the data, to ease out work.
        for review in data:
            app_id = review["app"]["$oid"]
            orgdata.setdefault(app_id, [])
            orgdata[app_id].append(review)
            self.datedata.setdefault(app_id, {})

        return orgdata

    def preprocess_data(self, time=None):
        """
        Sort the data, by months. For an example:
        For every month, add the values that have a timestamp in that month,
        to its current m-y (ex: Sep 19) key. This method first needs to use
        fix_data() in order to work.
        """
        orgdata = self.fix_data()
        for app in orgdata:
            sorted_app: dict = sorted(orgdata[app], key=lambda k: k['timestamp']['$date'])
            old_date = None
            for date in sorted_app:
                del date["app"]
                date["comment"] = REPLACE_NO_SPACE.sub("",
                                                       date["comment"].lower())
                date["comment"] = REPLACE_WITH_SPACE.sub(" ", date["comment"])
                temp_date = datetime.utcfromtimestamp(date["timestamp"]["$date"] / 1000)
                if old_date is None:
                    old_date = temp_date
                    self.datedata[app][old_date.strftime("%b-%y")] = [date]
                    continue
                difference = self.difference_in_months(old_date, temp_date)
                if difference < 1:
                    self.datedata[app][old_date.strftime("%b-%y")].append(date)
                else:
                    old_date = temp_date
                    self.datedata[app][old_date.strftime("%b-%y")] = [date]

    def write_output(self, path="output.json"):
        """
        Write the output of the datedata object (the sorted months) into a file
        named "output.json".

        Parameters
        ----------
        path : str
            Provide a path (default `output.json`).
        """
        with open(path, "w", encoding='utf-8') as file:
            json.dump(self.datedata, file, ensure_ascii=False, indent=4)

    def train(self, min_df=0.05):
        """
        Train a simple linear regression algorithm based on the data
        that was previously sorted. Needs some serious clean up, lol.

        Parameters
        ----------
        min_df : int
            CountVectorizer's min_df (default `0.05`).
        """
        vectorizer = CountVectorizer(ngram_range=(1, 1), min_df=min_df, binary=True)
        tfidf_vectorizer = TfidfVectorizer()
        all_reviews = []
        self._app_coef = {}
        for app in self.datedata:
            reviews, ratings, reviews_normal = [], [], []
            for date in self.datedata[app]:
                for review in self.datedata[app][date]:
                    doc = nlp_en(review["comment"])
                    lang = doc._.language["language"]
                    nouns_only_stemmed = self.get_nouns(review["comment"], lang)
                    reviews.append(nouns_only_stemmed)
                    reviews_normal.append(review["comment"])
                    ratings.append(review["rating"])

            all_reviews.extend(reviews)

            x_array = vectorizer.fit_transform(reviews)
            x_tfidf = tfidf_vectorizer.fit_transform(reviews)
            x_tfidf_dict = dict(x_tfidf.todok().items())
            #counter = {}
            averages = {}
            for key, value in x_tfidf_dict.items():
                #counter.setdefault(key[0], 0)
                #counter[key[0]] += 1
                averages.setdefault(key[0], [])
                averages[key[0]].append(value)

            highest_average = 0
            highest_sentence = ""
            #print(averages)
            for key, value in averages.items():
                if len(value) < 4:
                    continue
                sentence = reviews_normal[key]
                average = sum(value) / len(value)

                if average > highest_average:
                    highest_average = average
                    highest_sentence = sentence

            highest_sentence = '. '.join(map(lambda s: s.strip().capitalize(),
                                             highest_sentence.split('.')))
            highest_sentence += '.' if highest_sentence[0] != '.' else ''
            print(f"Sentence: {highest_sentence}, avg: {highest_average}")
            lr = LinearRegression()
            lr.fit(x_array, ratings)
            voc_coef = dict(zip(vectorizer.get_feature_names(), lr.coef_))
            sorted_voc_coef = dict(sorted(voc_coef.items(), key=lambda x: x[1]))
            self._app_coef[app] = {"positives": self.get_positives(sorted_voc_coef),
                                   "negatives": self.get_negatives(sorted_voc_coef),
                                   "helpful": highest_sentence}

            # print(linear_regression.predict(x_array))

    def write_to_apps(self):
        """
        Writes the data needed for the website to `apps.json`, e.g.

        ```
        "voc_coef": {
                "positives": [
                    "naughty",
                    "work"
                ],
                "negatives": [
                    "grt",
                    "button"
                ]
            }
        ```

        Gets added to the app with that data.
        """
        app_coef = {}
        for app in self._app_coef:
            positives = [stemmed_to_unstemmed[positive].most_common(1)[0][0] for
                         positive in self._app_coef[app]["positives"] if positive is not None]
            negatives = [stemmed_to_unstemmed[negative].most_common(1)[0][0] for
                         negative in self._app_coef[app]["negatives"] if negative is not None]
            helpful = self._app_coef[app]["helpful"]

            app_coef[app] = {"coef": {"positives": positives,
                                      "negatives": negatives},
                             "helpful": helpful}

        with open('../data/apps.json', 'r+', encoding='utf-8') as f:
            data = json.load(f)
            for key in data:
                app_id = key["_id"]["$oid"]
                key["voc_coef"] = app_coef[app_id]["coef"] if app_id in \
                    app_coef else self.dummy_dict()
                key["helpful"] = app_coef[app_id]["helpful"] if app_id in \
                    app_coef else None
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.truncate()


nlp = NLP()
nlp.preprocess_data()
nlp.train()
nlp.write_to_apps()


#plot = Plotting()
#plot.show_wordcloud()
#plot.plot()
