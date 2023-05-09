import json
import time
import datetime

from libs.utils import Struct


def argument(self, **kw):
    args = Struct()
    error = None
    for k, typ in kw.items():
        if not isinstance(typ, Schema):
            raise TypeError()
        v = self.get(k)
        try:
            typ.key = k
            args[k] = typ.validate(v)
        except Exception as e:
            error = str(e)
    return args, error


class ValidateException(Exception):
    def __init__(self, err=""):
        self.err = err
        Exception.__init__(self, err)


class Schema(object):
    """
    使用方法
    >>> def data_validate(request):
    >>>     args, e = request.QUERY.argument(
    >>>            name=Schema(type=str, required=True, error="姓名不能为空"),
    >>>            age=Schema(type=int, required=True, filter=lambda x: x > 0, error="年龄信息错误"),
    >>>            image=Schema(type=[str], default=""),
    >>>            data=Schema(type=[{"qid": int, "aid": [str]}])
    >>>    )
    """
    def __init__(self, typ, required=False, default=None, f=None, error=None, key=None):
        self.type = typ
        self.default = default
        self.required = required
        self.filter = f
        self._error = error
        self.key = key

    def error(self):
        return self._error if self._error else f"args: '{self.key}' Error"

    def _iterable_parse(self, val, typ=None):
        """可迭代格式验证"""
        val = json.loads(val) if isinstance(val, str) else val
        if not isinstance(val, (list, tuple, set, frozenset)):
            raise ValidateException(self.error())
        self._required(val)
        data = []
        _typ = self.type if not typ else typ
        for i in _typ:
            for v in val:
                v = self._validate_method(v, i)
                data.append(v)
        return data or val

    def _type_parse(self, val, typ=None):
        """可转换格式验证"""
        _typ = self.type if not typ else typ
        if val == "true":
            return True
        elif val == "false":
            return False
        return _typ(val)

    def _dict_parse(self, val, typ=None):
        """dict格式验证"""
        e = self.error()
        val = json.loads(val) if isinstance(val, str) else val
        if not isinstance(val, dict):
            raise ValidateException(self.error())
        self._required(val)
        _typ = self.type if not typ else typ
        keys = _typ.keys()
        data = Struct()
        for i in keys:
            if i not in val.keys():
                raise ValidateException("%s中缺少key: %s" % (self.key, i) if not e else e)

        for k, v in val.items():
            t = _typ.get(k)
            if not t:
                data[k] = v
                continue
            data[k] = self._validate_method(v, t)
        return data or Struct(val)

    def _callable(self, data):
        """可调用方式验证"""
        if not callable(self.filter):
            raise ValidateException("%s 不支持调用" % self.key)
        if not self.filter(data):
            raise ValidateException("参数%s:不合法" % self.key)
        return data

    @staticmethod
    def _date(date, _):
        t = time.strptime(date, "%Y-%m-%d")
        v = datetime.datetime(*t[:3])
        return v

    def _validate_method(self, val, typ):
        med = {
            TYPE: self._type_parse,
            ITERABLE: self._iterable_parse,
            DICT: self._dict_parse,
            DATE: self._date,
        }.get(_priority(typ))
        return med(val, typ)

    def _required(self, val):
        if not val:
            if not self.required:
                return self.default if self.default else type_default_value(self.type)
            else:
                raise ValidateException(self.error())

    def validate(self, val):
        if val is None or not val:
            if not self.required:
                return self.default if self.default else type_default_value(self.type)
            else:
                raise ValidateException(self.error())
        data = self._validate_method(val, self.type)
        if self.filter:
            data = self._callable(data)
        return data


def _callable_str(callable_):
    if hasattr(callable_, '__name__'):
        return callable_.__name__
    return str(callable_)


RE, DATE, TIMESTAMP, CALLABLE, TYPE, DICT, ITERABLE = range(7)


def _priority(s):
    """Return priority for a given object."""
    if type(s) in (list, tuple, set, frozenset):
        return ITERABLE
    if type(s) is dict:
        return DICT
    if issubclass(type(s), type):
        return TYPE
    if callable(s):
        return CALLABLE
    if isinstance(s, str):
        if s == "date":
            return DATE
        return RE


def type_default_value(t):
    """返回基本类型默认值, 没有识别的类型返回None"""
    if type(t) in (list, tuple, set, frozenset):
        return []
    if type(t) is dict:
        return {}
    return {str: "", int: 0}.get(t)

