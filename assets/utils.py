import time,hashlib,json
from assets import models
from cmdb import settings
from django.shortcuts import render,HttpResponse
from django.core.exceptions import ObjectDoesNotExist

def json_date_handler(obj):
    '''处理时间的工具方法'''
    if hasattr(obj,'isoformat'):
        return obj.strftime('%Y-%m-%d')

def json_datetime_handler(obj):
    '''处理时间的工具方法'''
    if hasattr(obj,'isoformat'):
        return obj.strftime('%Y-%m-%d %H:%M:%S')

def gen_token(username,timestamp,token):
    '''服务端根据客户端请求参数生成token'''
    token_format = '%s\n%s\n%s' % (username,timestamp,token)
    obj = hashlib.md5()
    obj.update(token_format.encode(encoding='utf-8'))# 要把字符串编码，用str.encode()或bytes()都行
    return obj.hexdigest()[10:17]

def token_required(func):
    '''
    token验证装饰器
    客户端提交新资产的时候，需要验证token是否匹配、是否过期
    '''
    def wrapper(*args,**kwargs):
        response = {'errors':[]}
        get_args = args[0].GET
        username = get_args.get('user')
        token_md5_from_client = get_args.get('token')
        timestamp = get_args.get('timestamp')
        if not username or not timestamp or not token_md5_from_client:
            response['errors'].append({'auth_failed':'This API requires toke authentication!'})
            return HttpResponse(json.dumps(response))
        try:
            user_obj = models.UserProfile.objects.get(email=username)
            token_md5_from_server = gen_token(username,timestamp,user_obj.token)
            if token_md5_from_client != token_md5_from_server:
                response['errors'].append({'auth_failed':'Invalid username or token!'})
            else:
                if abs(time.time() - int(timestamp))>settings.TOKEN_TIMEOUT:
                    response['errors'].append({'auth_failed':'Token is expired!'})
                else:
                    '''查找token_md5_from_client最近是否使用过、使用过就过期了，'''
                    pass
                print('\033[41;1m%s --- client: %s\033[0m' % (time.time(),timestamp),time.time()-int(timestamp))
        except ObjectDoesNotExist as e:
            response['errors'].append({'auth_failed':'Invalid username or token!'})
        if response['errors']:
            return HttpResponse(json.dumps(response))
        else:
            return func(*args,**kwargs)
    return wrapper