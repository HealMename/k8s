import json

from django.http import HttpResponse, HttpRequest
from django.utils.deprecation import MiddlewareMixin
import logging as log

from libs.utils import ajax, Struct, auth_token

write_list = ['/']



class CoreMiddle(MiddlewareMixin):

    def process_request(self, request):
        try:
            return self._process_request(request)
        except Exception as e:
            log.error(e)

    @staticmethod
    def cross_domain(request, response=None):
        """
        添加跨域头
        """
        origin = request.META.get('HTTP_ORIGIN', '*')
        if request.method == 'OPTIONS' and not response:
            response = HttpResponse()
        if not response:
            return
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Methods'] = 'GET,POST'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Headers'] = 'x-requested-with,content-type,HTTP_TOKEN,Token,App-Type,platform'
        response['Access-Control-Max-Age'] = '1728000'
        # response['X-Frame-Options'] = 'allow-from *'
        return response

    def _process_request(self, request):
        try:
            # REQUEST过期, 使用QUERY代替
            query = request.GET.copy()
            query.update(request.POST)
            # 把body参数合并到QUERY
            try:
                if request.body:
                    body = json.loads(request.body)
                    query.update(body)
            except Exception as e:
                pass
            r = self.cross_domain(request)

            request.QUERY = query
            token = request.QUERY.get('token') or request.META.get('HTTP_TOKEN') or request.COOKIES.get('sessionid')
            request.user_info = {}
            if token:
                request.user_info = auth_token.decode_token(token)
                if request.user_info:
                    request._newtoken = token
            if r:
                return r

        except Exception as e:
            log.error(e)

    def process_response(self, request, response):
        try:
            # 更新token
            if getattr(request, '_newtoken', None):
                auth_token.login_response(response, request._newtoken)
            # 添加跨域头
            self.cross_domain(request, response)
            return response
        except Exception as e:
            log.error(e)
