import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup

df_main = None
df_img = None
df_desc = None
df_supp = None
tfidf_matrix = None
cosine_similarities = None

def load():
    global df_main
    filename = "Data/steam.csv"
    df_main = pd.read_csv(filename, on_bad_lines="skip", encoding="utf-8")
    print("\n----- df_main -----")
    print(df_main.head(5))
    load_img()
    load_desc()
    load_support()
    return df_main

def load_img():
    global df_img
    filename = "Data/steam_media_data.csv"
    df_img = pd.read_csv(filename, on_bad_lines="skip", encoding="utf-8")
    print("\n----- df_img -----")
    print(df_img.head(5))
    return df_img

def load_desc():
    global df_desc
    filename = "Data/steam_description_data.csv"
    df_desc = pd.read_csv(filename, on_bad_lines="skip", encoding="utf-8")
    print("\n----- df_desc -----")
    print(df_desc.head(5))
    return df_desc

def load_support():
    global df_supp
    filename = "Data/steam_support_info.csv"
    df_supp = pd.read_csv(filename, on_bad_lines="skip", encoding="utf-8")
    print("\n----- df_supp -----")
    print(df_supp.head(5))
    return df_supp

def pre_process():
    global df_main
    df_main["year"] = df_main["release_date"].apply(extract_year)
    df_main["total_ratings"] = df_main.apply(total_ratings, axis=1)
    df_main["score"] = df_main.apply(create_score, axis=1)
    C = df_main["score"].mean()
    m = df_main["total_ratings"].quantile(0.90)

    df_main["weighted_score"] = df_main.apply(weighted_rating, args=(m, C), axis=1)
    df_main[["name", "total_ratings", "score", "weighted_score"]].head(15)

    df_main["steamspy_tags"] = df_main["steamspy_tags"].str.replace(" ", "-")
    df_main["genres"] = df_main["steamspy_tags"].str.replace(";", " ")
    counts = dict()
    for i in df_main.index:
        for g in df_main.loc[i, "genres"].split(" "):
            if g not in counts:
                counts[g] = 1
            else:
                counts[g] = counts[g] + 1
    counts.keys()

    return df_main

def extract_year(date):
    year = date[:4]
    if year.isnumeric():
        return int(year)
    else:
        return np.nan

def total_ratings(record):
    pos_count = record["positive_ratings"]
    neg_count = record["negative_ratings"]
    total_count = pos_count + neg_count
    return total_count

def create_score(row):
    pos_count = row["positive_ratings"]
    neg_count = row["negative_ratings"]
    total_count = pos_count + neg_count
    average = (pos_count / total_count)*10
    return round(average, 2)

def weighted_rating(x, *args):
    m = args[0]
    C = args[1]
    v = x["total_ratings"]
    R = x["score"]
    # Applying IMDB formula
    return round((v/(v+m) * R) + (m/(m+v) * C), 2)

def create_tfidf_vector(df):
    global tfidf_matrix
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(df["genres"])
    return tfidf_matrix

def calculate_cosine(tfidf_matrix):
    global cosine_similarities
    cosine_similarities = linear_kernel(tfidf_matrix, tfidf_matrix)
    return cosine_similarities

def closest_names(df, title):
    scores = list(enumerate(df["name"].apply(matching_score, b=title)))
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
    top_closest_names = [get_title_from_index(df, i[0]) for i in sorted_scores[:20]]
    return top_closest_names

def matching_score(a,b):
    return fuzz.ratio(a.lower(), b.lower())

def get_df_main():
    return df_main

def get_df_img():
    return df_img

def get_df_desc():
    return df_desc

def get_df_supp():
    return df_supp

def get_cosine_similarities():
    return cosine_similarities

def find_closest_title(df, title):
    scores = list(enumerate(df["name"].apply(matching_score, b=title)))
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
    closest_title = get_title_from_index(df, sorted_scores[0][0])
    distance_score = sorted_scores[0][1]
    return closest_title, distance_score

def get_title_from_index(df, index):
    return df[df.index == index]["name"].values[0]

def get_index_from_title(df, title):
    return df[df.name == title].index.values[0]

def get_platform_from_index(df, index):
    return df[df.index == index]["platforms"].values[0]

def get_score_from_index(df, index):
    return df[df.index == index]["weighted_score"].values[0]

def get_app_id_from_index(df, index):
    return df[df.index == index]["appid"].values[0]

def get_img_from_app_id(df, app_id):
    return df[df.steam_appid == app_id]["header_image"].values[0]

def get_desc_from_app_id(df, app_id):
    desc = BeautifulSoup(df[df.steam_appid == app_id]["short_description"].values[0], features="html.parser")
    return desc.get_text()

def get_title_year_from_index(df, index):
    return df[df.index == index]["year"].values[0]

def get_weighted_score_from_index(df, index):
    return df[df.index == index]["weighted_score"].values[0]

def get_total_ratings_from_index(df, index):
    return df[df.index == index]["total_ratings"].values[0]

def get_url_from_app_id(df, app_id):
    url = ''
    if not df[df.steam_appid == app_id].empty:
        url = df[df.steam_appid == app_id]["website"].values[0]
        if url is None or url == '' or isinstance(url, float):
            url = df[df.steam_appid == app_id]["support_url"].values[0]

    if url is None or url == '' or isinstance(url, float):
        url = 'https://store.steampowered.com/'
    return url
