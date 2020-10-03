import datetime
from multiprocessing import Process
from os import mkdir
from time import sleep
from urllib.request import urlopen

import pandas as pd
from lxml import etree


class FuncProcess(Process):

    def __init__(self, x_):
        Process.__init__(self)
        self.x__ = x_
        Process.name = x_

    def run(self):

        c = CompanyOnYahoo(self.x__, 86400, 'MAX')

        try:
            tree = c.setup_lxml()

            # get csv`s

            data_ = c.three_days_before_change(c.get_csv())
            news = c.get_news(tree)

            # save csv`s

            if len(news) > 0:
                c.save_csv(data_, news)
            else:
                raise Exception(f"W: {c.name} does not exist in the list of finance.yahoo.com")

        except Exception as e:
            print(e)


class CompanyOnYahoo:

    def __init__(self, name, tick_period, days):

        # Day = 86400 on Yahoo

        self.period = tick_period
        self.period_str = days

        # oldest_date_key

        self.key1 = self.get_oldest_date_key(self.period_str)

        # current_day_key

        self.key2, _ = self.get_current_date_key()

        # name of company

        self.name = name

        # url of company

        self.url = f'https://finance.yahoo.com/quote/{name}/news?p={name}'
        # url csv download

        self.csv_url = f'https://query1.finance.yahoo.com/v7/finance/download/' \
                       f'{name}?' \
                       f'period1={self.key1}' \
                       f'&period2={self.key2}&' \
                       f'interval=1d&' \
                       f'events=history '

    # create link with url

    def setup_lxml(self):

        response = urlopen(self.url)
        htmlparser = etree.HTMLParser()
        _tree_ = etree.parse(response, htmlparser)
        return _tree_

    # return today key

    def get_current_date_key(self):
        d0 = datetime.date(1970, 1, 1)
        d_current = datetime.date.today()
        return (d_current - d0).days * self.period, d_current

    # generate oldest key

    def get_oldest_date_key(self, days):
        _, current_date = self.get_current_date_key()
        if days == 'MAX':
            period1 = 0
        else:
            period1 = self.key2 - int(days) * self.period
        return period1

    # csv-reader ( Pandas )

    def get_csv(self):
        return pd.read_csv(self.csv_url)

    # change the initial data, add the 3day_before_change column,
    # which is the ratio of the values
    # of closed deals with a period of 3 days

    @staticmethod
    def three_days_before_change(data):
        data.reset_index()
        data['Date'] = pd.to_datetime(data['Date'])
        i = 0
        j = 0
        while i < len(data):
            while j < len(data):
                if (data.loc[j, 'Date'] - data.loc[i, 'Date']).days == 3:
                    data.loc[j, '3days_before_change'] = data.loc[j, 'Close'] / data.loc[i, 'Close']
                j += 1
            i += 1
            j = i + 1
        return data

    # save .csv tables in './CSV/<CompanyName>.csv'

    def save_csv(self, data, data_news):
        try:
            data.to_csv(f'./CSV/{self.name}.csv')
            data_news.to_csv(f'./CSV/{self.name}' + '_latest_news.csv')
        except FileNotFoundError:
            print(f'W:No such file or directory: `./CSV/{self.name}.csv`')
            mkdir('./CSV')
            self.save_csv(data, data_news)

    # get latest news in 'Summary' block

    @staticmethod
    def get_news(tree_):
        csv_news = []
        headers = tree_.xpath(
            '//html/body/div[1]/div/div/div[1]/div/div[3]/div[1]/div/div[5]/div/div/div/ul/'
            'li[*]/div/div/div[*]/h3/a/text()')
        descriptions = tree_.xpath(
            '//html/body/div[1]/div/div/div[1]/div/div[3]/div[1]/div/div[5]/div/div/div/ul/'
            'li[*]/div/div/div[*]/p/text()')
        hrefs = tree_.xpath(
            '//html/body/div[1]/div/div/div[1]/div/div[3]/div[1]/div/div[5]/div/div/div/ul/'
            'li[*]/div/div/div[*]/h3/a/@href')

        if headers:
            csv_news = pd.DataFrame({
                'Headers': headers,
                'Description': descriptions,
                'Link': hrefs,
            })
            csv_news['Link'] = 'https://finance.yahoo.com' + csv_news['Link']
        elif descriptions:
            csv_news = pd.DataFrame.empty
        return csv_news


if __name__ == "__main__":

    # setup list of companies
    try:

        with open('./input.txt', 'r') as f:
            pass

    except FileNotFoundError:

        print('Enter list of companies split by ",":')
        with open('./input.txt', 'tw') as f:
            f.writelines(input())

    finally:
        with open('./input.txt', 'r') as f:
            dictionary = f.readline().replace(' ', '').split(',')
            print(dictionary)
    load_bar = '..'
    for x in dictionary:
        process = FuncProcess(x)
        process.start()
    while process.is_alive():
        print(f'Loading{load_bar}')
        load_bar += '.'
        sleep(3)
    print('Finished! Check .csv in ./CSV/')
