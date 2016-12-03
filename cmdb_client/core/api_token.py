import hashlib,time

def get_token(username,token_id):
    '''生成token字符串'''
    timestamp = int(time.time())
    md5_format_str = '%s\n%s\n%s' % (username,timestamp,token_id)
    obj = hashlib.md5()
    obj.update(bytes(md5_format_str,encoding='utf-8'))
    return obj.hexdigest()[10:17],timestamp

if __name__ == '__main__':
    print(get_token('alex','test'))