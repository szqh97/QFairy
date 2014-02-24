QFairy
======

download qvod movie 

install
=======
1. 下载https://pypi.python.org/packages/source/s/setuptools/setuptools-2.2.tar.gz 解压后，执行 python setup.py install 安装setuptools
2. 执行 easy_install.py web.py 安装 web.py

在Windows下安装时会报

Traceback (most recent call last):
  File "C:\Python27\lib\runpy.py", line 162, in _run_module_as_main
    "__main__", fname, loader, pkg_name)
  File "C:\Python27\lib\runpy.py", line 72, in _run_code
    exec code in run_globals
  File "C:\Python27\lib\SimpleHTTPServer.py", line 27, in <module>
    class SimpleHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  File "C:\Python27\lib\SimpleHTTPServer.py", line 208, in SimpleHTTPRequestHand
ler
    mimetypes.init() # try to read system mime.types
  File "C:\Python27\lib\mimetypes.py", line 359, in init
    db.read_windows_registry()
  File "C:\Python27\lib\mimetypes.py", line 259, in read_windows_registry
    for subkeyname in enum_types(hkcr):
  File "C:\Python27\lib\mimetypes.py", line 250, in enum_types
    ctype = ctype.encode(default_encoding) # omit in 3.x!
UnicodeDecodeError: 'ascii' codec can't decode byte 0xd7 in position 9: ordinal
not in range(128)
    
解决方法：
  修改 %SYSTME%\Python27\Lib\mimetypes.py文件,在import 后加入
if sys.getdefaultencoding() != 'gbk':
    reload(sys)
    sys.setdefaultencoding('gbk')
