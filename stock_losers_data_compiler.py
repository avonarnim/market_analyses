import requests
import lxml.html as lh
import pandas as pd
from csv import writer
from csv import reader
from pandas_datareader import data
from selenium import webdriver
from config import keys
import json

def get_losers(url):
    webpage = requests.get(url)
    webpage_content = lh.fromstring(webpage.content)
    tr_elements = webpage_content.xpath('//tr')

    # getting table headers
    col = []
    i = 0
    desired_headers = [tr_elements[0][idx] for idx in [0, 2, 4]]
    for cell in desired_headers:
        i += 1
        name = cell.text_content()
        col.append((name,[]))

    col.append(("Day 2 High %", []))
    col.append(("Day 3 High %", []))
    col.append(("Day 4 High %", []))
    col.append(("Day 5 High %", []))
    col.append(("Day 6 High %", []))
    col.append(("Day 7 High %", []))

    for idx in range(1, 12):
        row = tr_elements[idx]
        if len(row) != 10:
            continue

        i = 0
        for cell in [row[idx] for idx in [0, 2, 4]]:
            data = cell.text_content()
            if data != "":
                try:
                    data = float(data)
                except:
                    pass
            col[i][1].append(data)
            i += 1
        for j in range(3, 9):
            col[i][1].append(0)
            i += 1

    dict = {title:column for (title, column) in col}
    df = pd.DataFrame(dict)
    return df

def add_rows_to_document(new_rows, document):

    with open(document, 'r') as reader:
        prev_num_of_rows = len(reader.readlines())
    with open(document, 'a') as file:
        new_rows.to_csv(file, header=True, index=False)
        # has now appended new rows to the document
    return prev_num_of_rows

def track_progress_of_stocks(drive, stopping_point, document):

    with open(document, 'r') as reader, \
        open(document, 'w', newline='') as writer:
        drive.get('https://www.google.com/search?q=google')
        df = pd.read_csv(document)
        row_count = 0
        for idx in range(len(df[1:])):
            if row_count < stopping_point:
                drive.find_element_by_xpath('//*[@id="tsf"]/div[2]/div[1]/div[1]/div/div[1]/input').send_keys(df.loc[idx]['Symbol'] + ' stock').send_keys(Keys.RETURN)
                highest_price = drive.find_element_by_xpath('//*[@id="knowledge-finance-wholepage__entity-summary"]/div/div/g-card-section[2]/div/div/div[1]/table/tbody/tr[2]/td[2]').text
                percentage_change = int(10000*(highest_price - df.loc[idx]['Price (Intraday)']) / highest_price)/100
                i = 0
                while df.loc[idx][i] != "" and i < 10:
                    i += 1
                if i != 10:
                    df.loc[idx][i] = percentage_change
            else:
                break
        df.to_csv(document, header=True, index=False)

    return

if __name__ == '__main__':

    doc_path = keys["csv_path"]
    loser_data = get_losers('https://finance.yahoo.com/losers/')
    num_of_rows_from_before = add_rows_to_document(loser_data, doc_path)
    # driver = webdriver.Chrome(keys["chromedriver_path"])
    # track_progress_of_stocks(driver, num_of_rows_from_before, doc_path)
    # driver.quit()
