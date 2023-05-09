import datetime
import time
import json
import logging
import re
import hashlib
import traceback
from django.conf import settings
from django.http import HttpResponse
log = logging.getLogger(__name__)
from django.template import loader


class Struct(dict):
    """
    - 为字典加上点语法. 例如:
    >>> o = Struct({'a':1})
    >>> o.a
    >>> 1
    >>> o.b
    >>> None
    """

    def __init__(self, *e, **f):
        if e:
            self.update(e[0])
        if f:
            self.update(f)

    def __getattr__(self, name):
        # Pickle is trying to get state from your object, and dict doesn't implement it.
        # Your __getattr__ is being called with "__getstate__" to find that magic method,
        # and returning None instead of raising AttributeError as it should.
        if name.startswith('__'):
            raise AttributeError
        return self.get(name)

    def __setattr__(self, name, val):
        self[name] = val

    def __delattr__(self, name):
        self.pop(name, None)

    def __hash__(self):
        return id(self)

def strxor(s, key):
    """
    功能:异或加密
    返回:一个bytearray类型
    """
    try:
        key = key & 0xff
        a = bytearray(s)
        b = bytearray(len(a))
        for i, c in enumerate(a):
            b[i] = c ^ key
        return b
    except Exception as e:
        logging.error(e)


def check_response(data_dict):
    """
    功能:检测返回数据结果
    :param data_dict:
    :return: 成功返回data_dict的data和True,失败或者错误返回message和False
    """
    # 返回结果的response可能为ok, fail, error
    if data_dict.response == "error" or data_dict.response == "fail":
        return data_dict.data, data_dict.message, False
    else:
        if isinstance(data_dict.data, dict):
            data = Struct(data_dict.data)
        else:
            data = data_dict.data
        return data, data_dict.message, True


def num_to_ch(num):
    """
    功能说明：讲阿拉伯数字转换成中文数字（转换[0, 10000)之间的阿拉伯数字 ）
    ----------------------------------------------------------------------------
    修改人                修改时间                修改原因
    ----------------------------------------------------------------------------
    陈龙                2012.2.9
    """
    num = int(num)
    _MAPPING = ('零', '一', '二', '三', '四', '五', '六', '七', '八', '九',)
    _P0 = ('', '十', '百', '千',)
    _S4 = 10 ** 4

    if _S4 <= num < 0:
        return None
    if num < 10:
        return _MAPPING[num]
    else:
        lst = []
        while num >= 10:
            lst.append(num % 10)
            num = num / 10
        lst.append(num)
        c = len(lst)  # 位数
        result = u''
        for idx, val in enumerate(lst):
            if val != 0:
                result += _P0[idx] + _MAPPING[int(val)]
            if idx < c - 1 and lst[idx + 1] == 0:
                result += '零'
        return result[::-1].replace('一十', '十')

def join(o):
    """
    把数组用逗号连接成字符串

    例如:
    >>> join([1, 2])
    >>> '1,2'
    """
    if isinstance(o, (list, tuple)):
        return ','.join(str(i) for i in o)
    return str(o)

def type_default_value(type):
    """返回基本类型默认值, 没有识别的类型返回None"""
    tab = {str:"", list:[], int:0}
    return tab.get(type)


def trancate_date(ctime, format="%Y-%m-%d %H:%M:%S"):
    """时间戳转字符串"""
    timeArray = time.localtime(ctime)
    otherStyleTime = time.strftime(format, timeArray)
    return otherStyleTime


def casts(self, **kw):
    """
    功能说明：       批量转换url参数类型
    用法:
    >>> request.GET.__class__ = casts
    >>> args = request.GET.casts(keyword=str, page=int, a="(\d+)")
    >>> print args
    >>> {'keyword': '', 'page':0, 'a':''}
    ----------------------------------------------------------------------------
    修改人                修改时间                修改原因
    ----------------------------------------------------------------------------
    王晨光                2016-6-26
    """
    args = Struct()
    for k, typ in kw.items():
        v = self.get(k)
        if isinstance(typ, str):
            if typ == 'json':
                try:
                    v = json.loads(v) if v else {}
                except Exception as e:
                    print (e)
            elif typ == 'datetime':
                if v:
                    t = time.strptime(v, "%Y-%m-%d %H:%M:%S")
                    v = datetime.datetime(*t[:6])
                else:
                    v = None
            else:
                m = re.match(typ, v or '')
                groups = m.groups() if m else ()
                groups = [g for g in groups if g is not None]
                v = groups[0] if groups else ''
        else:
            defv = type_default_value(typ)
            try:
                v = typ(v) if v is not None else defv
            except:
                v = defv
        args[k] = v
    return args


def loads(self):
    """
    功能说明：      解析json格式参数
    用法:
    >>> request.__class__ = loads
    >>> args = request.loads()
    >>> print args
    >>> {}
    解析失败返回空字典
    ----------------------------------------------------------------------------
    修改人                修改时间                修改原因
    ----------------------------------------------------------------------------
    王晨光                2016-10-10
    """
    try:
        o = json.loads(self.body)
    except:
        o = {}
    return Struct(o)


_upload_key = {}


def upload_key():
    global _upload_key
    today = datetime.date.today()
    if not _upload_key or _upload_key["expire_date"] != today:
        now = datetime.datetime.now()
        date_now = now.strftime("%Y%m%d")
        sever_key = settings.UPLOAD_KEY
        m = hashlib.md5()
        m.update(f'{sever_key}{date_now}'.encode('utf-8'))
        key = m.hexdigest()
        _upload_key = dict(
            key=key,
            expire_date=today
        )
        return key
    return _upload_key['key']


def render_template_data(request, template_path, context):
    t = loader.get_template(template_path)
    if hasattr(request, 'user'):
        user = request.user
        context['user'] = user
    context['settings'] = settings
    # context['upload_key'] = upload_key()
    s = t.render(context, request)
    return s


def render_template(request, template_path, context={}):
    s = render_template_data(request, template_path, context)
    return HttpResponse(s)


def safe(path):
    """
    功能说明：       安全修饰器, path: 模板路径
    如果页面报错, 至少给用户返回一个无数据的模板页面
    ----------------------------------------------------------------------------
    修改人                修改时间                修改原因
    ----------------------------------------------------------------------------
    王晨光                2016.5.27
    """
    def _safe(f):
        def wrap(request, *args, **kw):
            try:
                o = f(request, *args, **kw)
                if o is None:
                    o = {}
                if isinstance(o, dict):
                    return render_template(request, path, o)
                else:
                    return o
            except:
                exc = traceback.format_exc()
                log.error(exc)
                r = render_template(request, path, {})
                r.status_code = 500
                return r
        return wrap
    return _safe
