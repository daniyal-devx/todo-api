## Target classification

**Site:** Books to Scrape (books.toscrape.com)

**Why it's okay to scrape:** The site explicitly says "We love being scraped!" 
and displays a banner stating it is a demo site built for practicing web 
scraping. This is a public sandbox made for exactly this purpose.

**Scope:** This scraper only touches the first 3 catalogue pages (60 books 
total). It does not crawl the full site.

**robots.txt check:** Requested https://books.toscrape.com/robots.txt — 
returned 404 Not Found, meaning no robots file exists. This is not 
permission by itself, but combined with the site's own scraping-friendly 
banner, it confirms there is no restriction in place.

**Data collected:** Book title, price, availability, star rating, and 
description — all publicly displayed product info, nothing behind a login.

I will not reuse this code on another site without checking its rules and 
terms first.