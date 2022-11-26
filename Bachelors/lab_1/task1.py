#%%
from tqdm import tqdm
import pandas as pd
import pdb
import requests
import bs4
import json

#%%
def parse_html(html):
    return bs4.BeautifulSoup(html, "html.parser")


def get_page(link):
    return requests.get(link)


def scrape_movies():
    # determinam numarul total de submisii
    html = get_page("https://www.imdb.com/chart/top/").content
    soup = parse_html(html)

    # vom salva in acest dictionar datele despre titlul filmului si link
    # ne va ajuta ulterior sa construim un tabel (dataframe) folosind pandas
    d = {
        "movie": [],
        "url_movie": [],
    }

    lines = soup.select("table.chart tbody tr")

    for line in lines:
        # selectam celulele de pe aceasta linie
        cells = [cell for cell in line.select("td")]

        # extragem link-ul pentru film
        url_movie = cells[1].select_one("a")["href"]
        
        d["movie"].append(cells[1].text)
        d["url_movie"].append(url_movie)

    return pd.DataFrame(d)


df_movies = scrape_movies()
links = []
for link in df_movies["url_movie"]:
    links.append("https://www.imdb.com" + link + "reviews")
#print(links)

# %%
def scrape_reviews(links):
    d = {}
    for link in links:     
        html = get_page(link).content
        soup = parse_html(html)
        
        title = soup.find("a", itemprop="url").contents[0]
        d[title] = []

        key = soup.find("div", {"class": "load-more-data"})["data-key"]
        more_data_link = f'{link}/_ajax?ref_=undefined&paginationKey={key}'   
        html = get_page(more_data_link).content
        soup = parse_html(html)

        reviews = soup.find_all("div", {"class": "review-container"})
        for review in reviews:
            review_title = review.find("a", {"class": "title"}).get_text()
            review_text = review.find("div", {"class": "text show-more__control"}).get_text()
            review_raiting = review.find("span", {"class": "rating-other-user-rating"})
            if review_raiting:
                review_raiting = review_raiting.get_text().strip("\n")
            review_date = review.find("span", {"class": "review-date"}).get_text()
            reviewer = review.find("span", {"class": "display-name-link"}).get_text()

            review_dict = {
                "title": review_title,
                "content": review_text,
                "raiting": review_raiting,
                "date": review_date,
                "author": reviewer
            }
            d[title].append(review_dict)
            # for testing efficiency
            break
        break

    return d

all_reviews = scrape_reviews(links)
f = open("reviews.json", "w")
json.dump(all_reviews, f)
f.close()