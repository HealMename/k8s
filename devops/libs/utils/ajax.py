# coding: utf-8
import json as simplejson
from json.encoder import JSONEncoder
import datetime
from django.http import HttpResponse
"""ajax工具类"""


class XJSONEncoder(JSONEncoder):
    """
    JSON扩展: 支持datetime和date类型
    """

    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(o, datetime.date):
            return o.strftime('%Y-%m-%d')
        else:
            return JSONEncoder.default(self, o)


class SimpleAjaxException(Exception):
    pass


def ajax_data(response_code, data=None, error=None, next=None, message=None):
    """if the response_code is true, then the data is set in 'data',
    if the response_code is false, then the data is set in 'error'
    """
    r = dict(response='ok', data=data, error='', next='', message='')
    if response_code is True or response_code.lower() in ('ok', 'yes', 'true'):
        r['response'] = 'ok'
    else:
        r['response'] = 'fail'
    if data is not None:
        r['data'] = data
    if error:
        r['error'] = error
    if next:
        r['next'] = next
    if message:
        r['message'] = message
    return r


def ajax_ok_data(data='', next=None, message=None):
    return ajax_data('ok', data=data, next=next, message=message)


def ajax_fail_data(error='', data=None, next=None, message=None):
    return ajax_data('fail', data=data, error=error, next=next, message=message)


def json_response(data):
    r = HttpResponse(simplejson.dumps(data, cls=XJSONEncoder))
    r['Content-Type'] = 'application/json'
    return r


def ajax_ok(data='', next=None, message=None):
    """
    功能说明： ajax请求正常返回接口
    :param data: 数据
    :param next: 下一步
    :param message: 返回信息
    :return:
    """
    return json_response(ajax_ok_data(data, next, message))


def ajax_fail(error='', data=None, next=None, message=None):
    """
    功能说明： ajax请求出错接口
    :param error: 错误信息
    :param data: 数据
    :param next: 下一布
    :param message: 返回信息
    :return:
    """
    return json_response(ajax_fail_data(error, data, next, message))


def jsonp_response(callback, data):
    data = simplejson.dumps(data, cls=XJSONEncoder, encoding='utf-8')
    data = "%s(%s)" % (callback, data)
    r = HttpResponse(data)
    r['Content-Type'] = 'application/javascript'
    return r


def jsonp_ok(request, data='', next=None, message=None):
    """
    return a success response
    """
    body = ajax_ok_data(data, next, message)

    callback = request.GET.get('callback')
    if callback:
        return jsonp_response(callback, body)
    else:
        return json_response(body)


def jsonp_fail(request, error='', data=None, next=None, message=None):
    """
    return an error response
    """
    body = ajax_fail_data(error, data, next, message)
    callback = request.GET.get('callback')
    if callback:
        return jsonp_response(callback, body)
    else:
        r = json_response(body)
        # r.status_code = 400
        return r







