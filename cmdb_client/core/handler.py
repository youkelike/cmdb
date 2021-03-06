from core import info_collection,api_token
from conf import settings
import urllib,sys,os,json,datetime,urllib.parse,urllib.request


class ArgvHandler(object):
    def __init__(self,argv_list):
        self.argvs = argv_list
        self.parse_argv()

    def parse_argv(self):
        if len(self.argvs)>1:
            if hasattr(self,self.argvs[1]):
                func = getattr(self,self.argvs[1])
                func()
            else:
                self.help_msg()
        else:
            self.help_msg()

    def help_msg(self):
        '''
        由于资产数据更新并不频繁，建议使用系统的crontab，每天执行一次collect_data就行
        '''
        msg = '''
        collect_data
        run_forever
        get_asset_id
        report_asset
        '''
        print(msg)

    def collect_data(self):
        obj = info_collection.InfoCollection()
        asset_data = obj.collect()
        print(asset_data)

    def run_forever(self):
        '''不需要'''
        pass

    def __attach_token(self,url_str):
        '''给请求URL加上token参数'''
        user = settings.Params['auth']['user']
        token_id = settings.Params['auth']['token']
        md5_token,timestamp = api_token.get_token(user,token_id)
        url_arg_str = 'user=%s&timestamp=%s&token=%s' % (user,timestamp,md5_token)
        if '?' in url_str:
            new_url = '%s&%s' % (url_str,url_arg_str)
        else:
            new_url = '%s?%s' %(url_str,url_arg_str)
        return new_url

    def __submit_data(self,action_type,data,method):
        '''
        构建http请求发送数据到服务器
        :param action_type:
        :param data: 字典形式的参数
        :param method: 小写的get/post
        '''
        if action_type in settings.Params['urls']:
            #没有在配置中写端口号，就默认是80
            if type(settings.Params['port']) is int:
                url = 'http://%s:%s%s' % (settings.Params['server'],settings.Params['port'],settings.Params['urls'][action_type])
            else:
                url = 'http://%s%s' % (settings.Params['server'],settings.Params['urls'][action_type])
            url = self.__attach_token(url)
            print('Connecting [%s]...' % url)
            if method == 'get':
                try:
                    data_encode = urllib.parse.urlencode(data)
                    req = urllib.request.Request(url,data_encode)
                    res = urllib.request.urlopen(req,timeout=settings.Params['request_timeout']).read()
                    print('-->server response:', res)
                    return res
                except urllib.error.HTTPError as e:
                    sys.exit('\033[31;1m%s\033[0m' % e)
            elif method == 'post':
                try:
                    data_encode = urllib.parse.urlencode(data)
                    req = urllib.request.Request(url=url,
                                                data=data_encode.encode(encoding='utf-8', errors='ignore'),
                                                method='POST')
                    req.add_header('Content-Type','application/x-www-form-urlencoded')
                    res = urllib.request.urlopen(req, timeout=settings.Params['request_timeout']).read()
                    # print(res)
                    # res = json.loads(str(res))
                    print('\033[31;1m[%s]:[%s]\033[0m response:\n%s' % (method,url,res))
                    return res
                except Exception as e:
                    sys.exit('\033[31;1m%s\033[0m' % e)
        else:
            raise KeyError

    def load_asset_id(self):
        '''从本地文件中取出资产id'''
        asset_id_file = settings.Params['asset_id']
        has_asset_id = False
        if os.path.isfile(asset_id_file):
            asset_id = open(asset_id_file).read().strip()
            if asset_id.isdigit():
                return asset_id
            else:
                has_asset_id = False
        else:
            has_asset_id = False

    def __update_asset_id(self,new_asset_id):
        asset_id_file = settings.Params['asset_id']
        print(asset_id_file)
        f = open(asset_id_file,'w')
        f.write(str(new_asset_id))
        f.close()

    def report_asset(self):
        '''
        如果本地已经记录了asset_id，直接请求/asset/report/，如果服务器未找到匹配的记录就返回错误，找到了就更新
        如果本地没有asset_id，就请求/asset/report/asset_with_no_asset_id/，结果可能是提交新资产待审核或者返回丢失的asset_id，或者提示数据不合法
        '''
        obj = info_collection.InfoCollection()
        asset_data = obj.collect()
        asset_id = self.load_asset_id()
        if asset_id:#本地已经记录了资产id，说明资产信息已经有记录
            asset_data['asset_id'] = asset_id
            post_url = 'asset_report'
        else:#说明是第一次提交资产信息,或者asset_id丢失了
            #必须要加上这个字段，才能在服务端通过数据合法验证
            asset_data['asset_id'] = None
            post_url = 'asset_report_with_no_id'
        data = {'asset_data':json.dumps(asset_data)}
        response = self.__submit_data(post_url,data,method='post')
        # 返回的json字节串需要解码后才能反序列化
        response = response.decode('utf-8')
        response = json.loads(response)
        # asset_id丢失，返回的对象里会包含asset_id，存储到本地文件
        if 'asset_id' in response:
            self.__update_asset_id(response['asset_id'])
        # 提交结果记录日志
        self.log_record(response)

    def log_record(self,log,action_type=None):
        '''
        自定义的日志记录
        '''
        f = open(settings.Params['log_file'],'a')
        if log is str:
            pass
        if type(log) is dict:
            if 'info' in log:
                for msg in log['info']:
                    log_format = '%s\tINFO\t%s\n' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),msg)
                    f.write(log_format)
            if 'error' in log:
                for msg in log['error']:
                    log_format = '%s\tERROR\t%s\n' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),msg)
                    f.write(log_format)
            if 'warning' in log:
                for msg in log['warning']:
                    log_format = '%s\tWARNING\t%s\n' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),msg)
                    f.write(log_format)
        f.close()
