import pandas as pd
import datetime
from urllib.request import urlopen
from lxml import etree


class CompanyOnYahoo:

    def __init__(self, name, tick_period, days):
        # Day = 84000 on Yahoo
        self.period = tick_period
        self.period_str = days
        # first_date_key

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
    def setup_LXML(self, name):

        response = urlopen(self.url)
        htmlparser = etree.HTMLParser()
        tree = etree.parse(response, htmlparser)
        return tree

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

    def three_days_before_change(self, data):
        data_mod = data.set_index('Date')
        data_mod.index = pd.to_datetime(data_mod.index)
        data_mod = data_mod.resample('3d').mean()
        data_mod["3day_before_change"] = 0.0
        data['3day_before_change'] = 0.0
        data_mod.reset_index(inplace=True)
        i = 0
        while i < len(data_mod) - 1:
            data_mod.loc[i, "3day_before_change"] = data_mod.loc[i + 1, 'Close'] / data_mod.loc[i, 'Close']
            i += 1

        result = pd.concat([data, data_mod['3day_before_change']], axis=1)
        return result

    # save .csv tables in './CSV/<CompanyName>.csv'
    def save_csv(self, data, data_mod, data_news):
        data.to_csv(f'./CSV/{self.name}.csv')
        data_mod.to_csv(f'./CSV/{self.name}' + '_with3d.csv')
        data_news.to_csv(f'./CSV/{self.name}' + '_latest_news.csv')
        pass


if __name__ == "__main__":

    # test dictionary
    dictionary = ['PD', 'ZUO', 'PINS', 'ZM', 'PTVL', 'DOCU', 'CLDR', 'RUN']

    #
    for x in dictionary:
        c = CompanyOnYahoo(x, 86400, 'MAX')
        tree_ = c.setup_LXML(c.name)

        # create XPath-expressions for news-block
        headers = tree_.xpath(
            '//html/body/div[1]/div/div/div[1]/div/div[3]/div[1]/div/div[5]/div/div/div/ul/li[*]/div/div/div[*]/h3/a/text()')
        descriptions = tree_.xpath(
            '//html/body/div[1]/div/div/div[1]/div/div[3]/div[1]/div/div[5]/div/div/div/ul/li[*]/div/div/div[*]/p/text()')
        hrefs = tree_.xpath(
            '//html/body/div[1]/div/div/div[1]/div/div[3]/div[1]/div/div[5]/div/div/div/ul/li[*]/div/div/div[*]/h3/a/@href')

        if headers:
            # get latest news
            csv_news = pd.DataFrame({
                'Headers': headers,
                'Description': descriptions,
                'Link': hrefs,
            })

            # save csv`s
            c.save_csv(c.get_csv(),
                       c.three_days_before_change(c.get_csv()),
                       csv_news)

        elif not descriptions:
            print(f"{c.name} does not exist in the list of finance.yahoo.com")
