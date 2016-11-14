import os,sys,platform

if platform.system() == 'Windows':
    BASE_DIR = '\\'.join(os.path.abspath(os.path.dirname(__file__)).split('\\')[:-1])
    print(BASE_DIR)
else:
    BASE_DIR = '/'.join(os.path.abspath(os.path.dirname(__file__)).split('/')[:-1])
sys.path.append(BASE_DIR)

from cmdb_client.core import handler

if __name__ == '__main__':
    handler.ArgvHandler(sys.argv)