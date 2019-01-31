import json

from django.core import serializers
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.db import connection
import datetime
from .models import *


def index(request):
    if request.method == 'GET':
        all_company = Company.objects.all()
        context = {'title': 'index', 'all_company': all_company}
        return render(request, 'dj_1/index.html', context)


def historical(request, ticker, api=False):
    ticker_obj = Company.objects.get(company_name=ticker)
    ticker_historical = Historical.objects.filter(company_name=ticker_obj)
    context = {'ticker': ticker,
               'ticker_historical': ticker_historical,
               'date_from': '2018-01-11', 'date_to': '2018-01-08'}

    if api:
        context_api = serializers.serialize('json', ticker_historical, indent=4)
        return HttpResponse(context_api, content_type='application/json')
    return render(request, 'dj_1/historical.html', context)


def insider(request, ticker, api=False):
    ticker_obj = Company.objects.get(company_name=ticker)
    ticker_insider = InsiderTrades.objects.filter(company_name=ticker_obj)
    context = {'ticker': ticker, 'ticker_insider': ticker_insider}
    if api:
        context_api = serializers.serialize('json', ticker_insider, indent=4)
        return HttpResponse(context_api, content_type='application/json')
    return render(request, 'dj_1/insider.html', context)


def insider_name(request, ticker, insider_name, api=False):
    ticker_obj = Company.objects.get(company_name=ticker)
    insider_obj = Insider.objects.get(name=insider_name)
    insider_data = InsiderTrades.objects.filter(company_name=ticker_obj).filter(insider=insider_obj.id)
    context = {'ticker': ticker, 'insider_data': insider_data, 'insider_name': insider_name}

    if api:
        context_api = serializers.serialize('json', insider_data, indent=4)
        return HttpResponse(context_api, content_type='application/json')

    return render(request, 'dj_1/insider_data.html', context)


def analytics(request, ticker, api=False):
    if request.method == 'GET':
        request_dict = request.GET
        if request_dict['date_from'] and request_dict['date_to']:
            ticker_obj = Company.objects.get(company_name=ticker)
            date_from_obj = Historical.objects.filter(company_name=ticker_obj).get(date=request_dict['date_from'])
            date_to_obj = Historical.objects.filter(company_name=ticker_obj).get(date=request_dict['date_to'])
            decision = dict(open=round(date_to_obj.open - date_from_obj.open, 2),
                            high=round(date_to_obj.high - date_from_obj.high, 2),
                            low=round(date_to_obj.low - date_from_obj.low, 2),
                            close=round(date_to_obj.close - date_from_obj.close, 2),
                            volume=round(date_to_obj.volume - date_from_obj.volume, 2))

            context = {'ticker': ticker,
                       'date_from': date_from_obj,
                       'date_to': date_to_obj,
                       'decision': decision,
                       'api_date_from': request_dict['date_from'],
                       'api_date_to': request_dict['date_to'],
                       }
            if api:
                dump = json.dumps(decision, indent=4)
                return HttpResponse(dump, content_type='application/json')

            return render(request, 'dj_1/analytics.html', context)


def delta(request, ticker, api=False):
    ticker_obj = Company.objects.get(company_name=ticker).id

    if request.method == 'GET':
        request_dict = request.GET
        try:
            if int(request_dict['value']) and request_dict['type'] in ['open', 'high', 'low', 'close']:
                s = (" SELECT MAX( select1.date ), date2 {up} FROM ("
                     " SELECT t1.date, t1.{type}, "
                     " MIN(t2.date) as date2 "
                     " FROM dj_1_historical t1 "
                     " INNER JOIN dj_1_historical t2 "
                     " ON (t2.{type} >= t1.{type} + {value} ) "
                     " AND t1.date < t2.date "
                     " AND t1.company_name_id = t2.company_name_id "
                     " WHERE t1.company_alias_id = {ticker_id} "
                     " GROUP BY t1.id "
                     " ORDER BY t1.date ) select1 "
                     " GROUP BY date2 "
                     " UNION "
                     " SELECT MAX( select2.date ), date2{down}FROM ( "
                     " SELECT t1.date, t1.{type}, "
                     " MIN(t2.date) as date2 "
                     " FROM dj_1_historical t1 "
                     " INNER JOIN dj_1_historical t2 "
                     " ON (t2.{type} <= t1.{type} - {value} ) "
                     " AND t1.date < t2.date "
                     " AND t1.company_name_id = t2.company_name_id "
                     " WHERE t1.company_alias_id = {ticker_id} "
                     " GROUP BY t1.id "
                     " ORDER BY t1.date ) select2 "
                     " GROUP BY date2 "
                     " ORDER BY date2; ".format(ticker_id=ticker_obj,
                                                value=request_dict['value'],
                                                type=request_dict['type'],
                                                up=", 'UP' direction ",
                                                down=", 'DOWN' as direction ")
                     )
        except ValueError:
            raise Http404
            # pass
        else:
            cursor = connection.cursor()
            cursor.execute(s)
            row = cursor.fetchall()
            context = {'ticker': ticker, 'row': row, 'type': request_dict['type'], 'value': request_dict['value']}

            if api:
                times_list = []
                for record in row:
                    start = record[0]
                    finish = record[1]
                    answer = {'start': start.strftime('%m/%d/%Y'), 'finish': finish.strftime('%m/%d/%Y'),
                              'status': record[2]}
                    times_list.append(answer)

                return HttpResponse(json.dumps(times_list), content_type='application/json')

            return render(request, 'dj_1/delta.html', context)
