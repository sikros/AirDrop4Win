from flask import Flask,request
import os
import logging
import socket
import sys
import qrcode
import numpy as np
import uuid
import json
import base64
from hashlib import md5
from random import randint
import ctypes
from ctypes.wintypes import MAX_PATH
import os.path  
import win32clipboard as w    
import win32con,win32api,win32gui
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def get_clip():#读取剪切板  
    w.OpenClipboard()  
    d = w.GetClipboardData(win32con.CF_TEXT)  
    w.CloseClipboard()  
    return d.decode('GBK')

def set_clip(aString):
    w.OpenClipboard()  
    w.EmptyClipboard()  
    w.SetClipboardText(aString)  
    w.CloseClipboard()  

def get_key(uuidstring):
    hashkey = md5(uuidstring.encode('utf8')).hexdigest()
    return str(hashkey)

def port_is_used(port,ip='127.0.0.1'):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        s.connect(ip,port)
        s.shutdown(2)
        return True
    except:
        return False

def load_config(reconfig=False):
    if reconfig:
        os.remove('config.json')
    try:
        with open('config.json') as f:
            config= json.loads(f.read())
            ip=config['ip']
            port=config['port']
            uuidstring = config['uuid']
            key = md5(uuidstring.encode('utf8')).hexdigest()
    except:
        try: 
            s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) 
            s.connect(('8.8.8.8',80)) 
            ip = s.getsockname()[0] 
        finally: 
            s.close() 
        port=randint(5000,8000)
        while port_is_used(port,ip):
            port=randint(5000,8000)
        uuidstring = str(uuid.uuid1())
        key = md5(uuidstring.encode('utf8')).hexdigest()
        jsondata={'ip':ip,'port':port,'uuid':uuidstring}
        with open(r'config.json',mode='w+') as f:
            f.write(json.dumps(jsondata))
    finally:
        return(ip,port,key)

def get_qrcode(ip,port):
    qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1
    )
    qr.add_data(str(ip)+':'+str(port))
    qr.make(fit=True)
    img = qr.make_image()
    img2 = np.array(img.convert('L'))
    d = {255: '■', 0: '  '}
    rows, cols = img2.shape
    for i in range(rows):        
        for j in range(cols):
            print(d[img2[i, j]], end='')
        print('')

app = Flask(__name__)
@app.route('/hello',methods=['POST'])
def hello():
    name=request.form["name"]
    print("新设备连接:", name)
    return key

@app.route('/pushclip',methods=['POST'])
def pushclip():
    remote_key=request.form["key"]
    if str(key) not in str(remote_key):
        return 'fail'
    context=request.form["context"]
    set_clip(context)
    print("收到新的剪贴板推送:",context)
    return 'success'

@app.route('/pullclip',methods=['POST'])
def pullclip():
    remote_key=request.form["key"]
    if str(key) not in str(remote_key):
        return 'fail'
    context=get_clip()
    print("剪贴板已推送给手机:",context)
    return context


@app.route('/drop',methods=['POST'])
def drop():
    remote_key=request.form["key"]
    if str(key) not in str(remote_key):
        return 'fail'
    dll = ctypes.windll.shell32
    buf = ctypes.create_unicode_buffer(MAX_PATH + 1)
    if dll.SHGetSpecialFolderPathW(None, buf, 0x0005, False):
        path = str(buf.value)+'\\AirDrop\\'
    else:
        path = 'AirDrop\\'
    file = request.files['file']
    filename = fname = file.filename
    aq=0
    while os.path.exists(path+filename):
        aq += 1
        filename=str(aq)+"_"+fname
    if not os.path.exists(path):
        os.mkdir(path)
    file.save(path+filename)  
    os.startfile(path+filename)
    print("接收到新的文件:", path+filename)
    return 'success'


if __name__ == '__main__':
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    global key
    (ip,port,key)=load_config()
    try:
        print('AirDrop服务启动成功:请使用快捷指令连接')
        print('手机端程序请在微信小程序<捷径沙盒>中搜索AirDrop下载')
        print('输入IP地址：'+str(ip)+':'+str(port)+' 或扫描下面的二维码建立连接')
        get_qrcode(ip,port)
        app.run(host=ip,debug=False, port=port)
    except:
        (ip,port,key)=load_config(True)
        print('\033[22;37;41m\t')
        print('AirDrop服务启动成功，您的网络环境发生变更，请重新连接快捷指令')
        print('手机端程序请在微信小程序<捷径沙盒>中搜索AirDrop下载')
        print('输入IP地址：'+str(ip)+':'+str(port)+' 或扫描下面的二维码建立连接')
        print('\033[0m')
        get_qrcode(ip,port)
        app.run(host=ip,debug=False, port=port)