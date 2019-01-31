from lxml import html
import requests
import re
import json
from datetime import datetime


class Utils:

    def read_from_tickers(self):
        with open('tickers.txt', 'r') as f_handler:
            symbol_list = []
            for line in f_handler:
                symbol_list.append(line.rstrip())
            return symbol_list

    def url_gen(self):
        all_symbols = self.read_from_tickers()
        for symbol in all_symbols:
            yield dict(
                symbol_name=symbol,
                type='historical',
                url=f'https://www.nasdaq.com/symbol/{symbol.lower()}/historical'
                )

            for i in range(1, 11):
                yield dict(
                    symbol_name=symbol,
                    type='insider-trades',
                    url=f'https://www.nasdaq.com/symbol/{symbol.lower()}/insider-trades?page={i}'
                )

    def parser(self, url_gen):
        if url_gen['type'] == 'insider-trades':
            return self.insider_trades(url_gen)
        if url_gen['type'] == 'historical':
            return self.historical(url_gen)
        else:
            print('error')

    @staticmethod
    def format_data(date_value):
        if len(date_value) < 10:
            return datetime.today().strftime('%Y-%m-%d')
        else:
            date_list = date_value.split('/')
            return '{YYYY}-{MM}-{DD}'.format(YYYY=date_list[2], MM=date_list[0], DD=date_list[1])

    def historical(self, url_gen):

        page = requests.get(url_gen['url'])
        tree = html.fromstring(page.content)

        page_table = list(tree.xpath(".//div[@id='quotes_content_left_pnlAJAX']/table/tbody/tr/td/text()"))

        table_info = (''.join(page_table))

        info_list = (re.findall(r'\s+(\S+)\s', re.sub('[,]', '', table_info)))
        info_dict = []
        while len(info_list):
            info_dict.append(dict(
                date=self.format_data(info_list[0]),
                open=info_list[1],
                high=info_list[2],
                low=info_list[3],
                close=info_list[4],
                volume=info_list[5]
            ))
            del info_list[:6]

            symbol_dict = dict(company=dict(short_name=url_gen['symbol_name'].lower()),
                               type='historical',
                               info=info_dict
                               )

        return json.dumps(symbol_dict, sort_keys=True, indent=4)

    def insider_trades(self, url_gen):

            page = requests.get(url_gen['url'])
            tree = html.fromstring(page.content)

            xpath_selection = list(tree.xpath(".//*[@class='genTable']/table/tr/td//text()"))
            info_dict = []
            while len(xpath_selection):
                if len(xpath_selection) < 8 or xpath_selection[7].isupper():
                    xpath_selection.insert(6, 0)
                temp_list = xpath_selection[:8]
                del xpath_selection[:8]

                info_dict.append(dict(
                    insider_name=temp_list[0],
                    relation=temp_list[1],
                    last_date=self.format_data(temp_list[2]),
                    trans_type=temp_list[3],
                    owner_type=temp_list[4],
                    shares_traded=re.sub('[,]', '', temp_list[5]),
                    last_price=temp_list[6],
                    shares_held=re.sub('[,]', '', temp_list[7])
                ))
            symbol_dict = dict(company=dict(short_name=url_gen['symbol_name'].lower()),
                               type='insider-trades',
                               info=info_dict
                               )

            return json.dumps(symbol_dict, sort_keys=True, indent=4)


if __name__ == '__main__':
    i = Utils()

    pass
