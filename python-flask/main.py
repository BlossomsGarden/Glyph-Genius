# https://blog.csdn.net/shifengboy/article/details/114274271
import base64
import os
import urllib.request
import numpy as np
from flask import Flask, request, json
from flask import jsonify
import cv2 as cv
from datetime import datetime


app = Flask(__name__)


# lihaolong@10.60.150.93:20056，开放端口: 7860，screen: webui-sd1
RenderLink1="http://202.120.188.3:21789"
# lihaolong@10.60.150.93:20056，开放端口: 7862，screen: webui-sd2
RenderLink2="http://202.120.188.3:21789"
# lihaolong@10.60.150.93:20056，开放端口: 7863，screen: webui-sd3
RenderLink3="http://202.120.188.3:21789"
# lihaolong@10.60.150.93:20056，开放端口: 7864，screen: webui-sd4
RenderLink4="http://202.120.188.3:21789"
# lihaolong@10.60.150.93:20056，开放端口: 7865，screen: webui-sd5
RenderLink5="http://202.120.188.3:21789"
# dch@10.60.150.93:222，开放端口:公网代理202.120.188.3:21789，screen: webui
RenderLink6="http://202.120.188.3:21789"



@app.route('/hello')  # 这里不能为空
def hello_world():
    return 'Hello World!'

def ostu(img0, thresh1=0):
    gray = cv.cvtColor(img0, cv.COLOR_BGR2GRAY)  # 灰度化
    box = cv.boxFilter(gray, -1, (3, 3), normalize=True)  # 去噪
    _, binarized = cv.threshold(box, thresh1, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)  # 二值化
    return binarized

# 将上传待识别的图片切割成正方形
def splitSquare(img):
    height, width, channels = img.shape
    side = min(height, width)
    x = (width - side) // 2
    y = (height - side) // 2
    cropped = img[y:y + side, x:x + side]
    resized = cv.resize(cropped, (256, 256), interpolation=cv.INTER_AREA)
    return resized

SAVE_PATH='/root/SITP/'
# SAVE_PATH='./'
# 将生成的图片留个记录吧
def saveRenderImages(before_render, before_transparent, after_transparent):
    # 获取当前日期和时间
    now = datetime.now()
    date_folder = now.strftime("%Y-%m-%d")
    time_folder = now.strftime("%H-%M-%S")
    # 构建文件夹路径
    folder_path = os.path.join(SAVE_PATH, date_folder, time_folder)
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        # 创建新的文件夹
        os.makedirs(folder_path)
        print(f"Created a new folder: {folder_path}")
    print("文件夹路径",folder_path)

    # 在以时间命名的文件夹中分别写入传入的三张图像
    img_name = now.strftime("before_render.png")
    img_path = os.path.join(folder_path, img_name)
    cv.imwrite(img_path, before_render)
    img_name = now.strftime("before_transparent.png")
    img_path = os.path.join(folder_path, img_name)
    cv.imwrite(img_path, before_transparent)
    img_name = now.strftime("after_transparent.png")
    img_path = os.path.join(folder_path, img_name)
    cv.imwrite(img_path, after_transparent)
    print("Save Three Images OK")


def http_post(url,data):
    res = urllib.request.urlopen(url, data)
    return res.read().decode('utf-8')

# 解决跨域问题
from flask_cors import CORS
CORS(app, resources=r'/*', origins='*', allow_headers='Content-Type')


def ostu(img0, thresh1=0):
    gray = cv.cvtColor(img0, cv.COLOR_BGR2GRAY)  # 灰度化
    box = cv.boxFilter(gray, -1, (3, 3), normalize=True)  # 去噪
    _, binarized = cv.threshold(box, thresh1, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)  # 二值化
    return binarized


@app.route('/meaning', methods=['POST'])
def getMeaning():
    data = request.get_data()
    jsondata = json.loads(data)
    url = jsondata["url"]

    params = {"if": "gb", "char": jsondata["word"].encode('utf-8')}

    result = {
        "success": True,
        "meaning": None
    }
    # sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')  # 改变标准输出的默认编码
    try:

        response = requests.get(url, params=params)
        response.close()
        print(response.url)

        response.raise_for_status()  # 检查是否成功获取页面
        print("soup")
        # 使用 BeautifulSoup 解析页面内容

        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.content, 'html.parser', from_encoding="utf-8")
        all_table = soup.find_all('table')
        dst_table = ""
        for t in all_table:
            classes = t.get('class')
            if classes and classes[0] == 'info':
                dst_table = t

        all_tr = dst_table.find_all('tr')
        print(len(all_tr))
        for tr in all_tr:
            all_th = tr.find_all('th')
            all_td = tr.find_all('td')
            print(all_th[0].get_text())
            if (all_th[0].get_text().strip() == "英文翻譯:"):
                result["meaning"] = all_td[0].get_text().strip()
                break

    except requests.exceptions.HTTPError as http_err:
        # 如果发生 HTTP 错误，会进入这个异常处理块
        print(f'HTTP 错误：{http_err}')

    except Exception as e:
        print("Exception")
        # 处理异常，例如页面不存在或无法访问

        # 但是测试时发现meaning这个接口会出现调用次数过多而禁止访问的情况
        # 这种情况下只有meaning接口有问题，但依然报错“网络问题”导致整个项目无法进入下一阶段
        # 感觉这样设置不是很合理，因此这里将抛出错误后的success也置为True了，返回为“测试含义”
        result = {
            "success": True,
            "message": str(e),
            "meaning": "测试含义"
        }

    print(result)
    return jsonify(result)


UPLOAD_PATH='/var/www/html/images'
# UPLOAD_PATH='./images'
@app.route('/upload', methods=['POST'])
def upload_pic():
    data = request.get_data()  # 接收json数据
    jsondata = json.loads(data)  # json数据解析
    base64_data = jsondata["data"]
    parts = base64_data.split(',')
    img_type = parts[0].split(':')[1].split(';')[0].rsplit('/', 1)[1]  # 图片类型，如"png"
    img_data = parts[1]  # base64编码本体
    img_data = base64.b64decode(img_data)

    nparr = np.frombuffer(img_data, np.uint8)
    img = cv.imdecode(nparr, cv.IMREAD_COLOR)
    img_name='MuseumCanvas.'+img_type
    cv.imwrite(os.path.join(UPLOAD_PATH, img_name) , img)	    # 保存输入的图片

    respose = {
        'urls': "http://139.196.197.42:81/images/{}".format(img_name),
    }
    return jsonify(respose)


@app.route('/recognize',methods=['POST'])
def get_demo():
    data = request.get_data()  # 接收json数据
    jsondata = json.loads(data)  # json数据解析

    #####################################################
    base64_data = jsondata["data"]
    parts = base64_data.split(',')
    img_type = parts[0].split(':')[1].split(';')[0].rsplit('/', 1)[1]   # 图片类型，如"png"
    img_data = parts[1]    # base64编码本体
    img_data = base64.b64decode(img_data)

    nparr = np.frombuffer(img_data, np.uint8)
    img = cv.imdecode(nparr, cv.IMREAD_UNCHANGED)
    img=splitSquare(img)
    cv.imwrite('resize_image.' + img_type, img)  # 保存输入的图片

    ####################
    # 笑死我来
    # 你识别模型是只能识别test.jpg
    # 你得先将图片转码为 JPG 格式
    # 才能正常识别
    ####################
    # 将img转为jpg格式的图像数据
    _, img_encoded = cv.imencode('.jpg', img)
    # 将jpg格式的图像数据编码为base64字符串
    jpg_base64_code = base64.b64encode(img_encoded).decode('utf-8')
    # 将base64字符串添加到data URI中
    base64_data = "data:image/jpeg;base64," + jpg_base64_code

    jsondata["data"]= base64_data
    print(jsondata)
    #######################################################

    # 使用urlencode将字典参数序列化成字符串
    data_string = urllib.parse.urlencode(jsondata)
    # 将序列化后的字符串转换成二进制数据，因为post请求携带的是二进制参数
    last_data = bytes(data_string, encoding='utf-8')
    print("准备向服务器发送请求",last_data)
    # 向服务器发送请求
    res_url=''
    unicode=0
    ch=''
    code=0
    try:
        res = http_post("http://202.120.188.3:21789/api/recognize", last_data)
        jsondata = json.loads(res)
        print("获得结果", jsondata)
        res_url = jsondata['url']
        unicode=jsondata['unicode']
        # 将后缀由png改为jpg、端口号为81
        res_url = 'http://139.196.197.42:81'+res_url[21:-4] + '.jpg'
        ch=jsondata['character']
        code=200

    except urllib.error.HTTPError as e:
        print("HTTPERROR",e)
        code = e.code

    except urllib.error.URLError as e:
        print("URLERROR",e)
        error_code = None
        code=error_code

    respose = {
        'url': res_url,
        'code': code,
        'unicode': unicode,
        'ch':ch
    }

    return jsonify(respose)


# 咱就是说，咱也不知道为啥这里用requests就好了
# 咱也是打工，参考链接：https://stackoverflow.com/questions/26949542/http-error-422-unprocessable-entity-when-calling-api-from-python-but-curl-wo
import requests

# 这是最古老的接口了，因为原先只有一个接口，这里留个档算了
# @app.route('/render',methods=['POST'])
def get_render():
    data = request.get_json()
    base64_data = data.get('base64', 'default')
    prompt_item = data.get('prompt', 'flower')   # 你不提供我就画花儿
    negative_prompt=data.get('negative_prompt', "blurry, watermark, text, signature, frame, cg render, lights")
    batch_size = data.get('batch_size', 1)
    n_iter=data.get('n_iter', 2)

    ###################################################
    parts = base64_data.split(',')
    # base64编码本体
    img_data = parts[1]
    # 将base64编码的字符串解码为字节数据
    image_data = base64.b64decode(img_data)
    # 将字节数据转为NumPy数组
    nparr = np.frombuffer(image_data, np.uint8)
    # 解码NumPy数组为OpenCV图像格式
    img = cv.imdecode(nparr, cv.IMREAD_UNCHANGED)
    width,height,_=img.shape
    # print(width,height)

    # 记录渲染前的图片
    before_render=img

    image = cv.imencode('.png', img)[1]
    imageBase64 = str(base64.b64encode(image))[2:-1]     # 转回base64
    parts = base64_data.split(',')
    head = parts[0]
    base64_data = head + ','+imageBase64
    ####################################################

    # 发送渲染请求
    API_URL="http://202.120.188.3:21789/sdapi/v1/img2img"
    HEADERS = {
        "Content-Type": "application/json"
    }
    DATA = {
        "init_images": [base64_data],
        "sampler_name":"DPM++ 2S a Karras",
         "denoising_strength": 0.98,
         "image_cfg_scale": 0,
         "mask_blur": 4,
         "inpainting_fill": 0,
         "inpaint_full_res": True,
         "prompt": "a photograph of [" + prompt_item + "] against a white background, 30mm, 1080p full HD, 4k, sharp focus.",
         "negative_prompt": negative_prompt,
         "seed": -1,
         "subseed": -1,
         "subseed_strength": 0,
         "seed_resize_from_h": -1,
         "seed_resize_from_w": -1,
         "batch_size": batch_size,
         "n_iter": n_iter,
         "steps": 18,
         "cfg_scale": 9,
         "width": 768,
         "height": 768
    }
    print("渲染标签prompt：",DATA["prompt"])
    json_data = json.dumps(DATA).encode('utf8')
    response = requests.post(url=API_URL, headers=HEADERS, data=json_data)
    res=json.loads(response.text)

    parts = base64_data.split(',')
    head = parts[0]
    res_img_base64 = head + ',' + res["images"][0]
    ########################################################

    # 再将结果转为cv img格式，以下将进行透明处理
    parts = res_img_base64.split(',')
    img_type = parts[0].split(':')[1].split(';')[0].rsplit('/', 1)[1]  # 图片类型，如"png"
    img_data = parts[1]  # base64编码本体
    img_data = base64.b64decode(img_data)
    # 转为numpy格式数组
    nparr = np.frombuffer(img_data, np.uint8)
    # 提取图像的三个通道（红、绿、蓝和 alpha 通道）
    img = cv.imdecode(nparr, cv.IMREAD_COLOR)
    # 记录渲染后透明前的图片
    before_transparent=img
    # 转换为灰度图像
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # 使用阈值技术来创建二值图像
    threshold_value = 200
    ret, threshold = cv.threshold(gray, threshold_value, 255, cv.THRESH_BINARY_INV)
    # 创建掩模mask，将接近白色的像素赋为透明色（alpha=0）
    rgba = cv.cvtColor(img, cv.COLOR_BGR2RGBA)
    rgba[:, :, 3] = threshold

    # ##########################################
    # 注意这里opencv的RGB是反着的，为了避免最后绿色变蓝色，这里颠倒一下 #
    # ##########################################
    red, green, blue, alpha = cv.split(rgba)
    rgba = cv.merge((blue, green, red, alpha))
    # 记录渲染后透明前的图片
    after_transparent = rgba
    # ##########################################
    # 注意这里opencv的RGB是反着的，为了避免最后绿色变蓝色，这里颠倒一下 #
    # ##########################################

    # 又转为base64
    image = cv.imencode('.png', rgba)[1]
    base64_without_head = str(base64.b64encode(image))[2:-1]  # 转回base64
    response = {
        'base64':head + ',' + base64_without_head,
        'width':512,
        'height':512
    }
    saveRenderImages(before_render, before_transparent, after_transparent)
    return jsonify(response)


@app.route('/render1',methods=['POST'])
def get_render1():
    data = request.get_json()
    print(data)
    base64_data = data.get('base64', 'default')
    prompt_item = data.get('prompt', 'flower')   # 你不提供我就画花儿
    negative_prompt=data.get('negative_prompt', "blurry, watermark, text, signature, frame, cg render, lights")
    batch_size = data.get('batch_size', 1)
    n_iter=data.get('n_iter', 1)

    ###################################################
    print("base64_data",base64_data)
    parts = base64_data.split(',')
    # base64编码本体
    img_data = parts[1]
    # 将base64编码的字符串解码为字节数据
    image_data = base64.b64decode(img_data)
    # 将字节数据转为NumPy数组
    nparr = np.frombuffer(image_data, np.uint8)
    # 解码NumPy数组为OpenCV图像格式
    img = cv.imdecode(nparr, cv.IMREAD_UNCHANGED)
    width,height,_=img.shape
    # print(width,height)

    # 记录渲染前的图片
    before_render=img

    image = cv.imencode('.png', img)[1]
    imageBase64 = str(base64.b64encode(image))[2:-1]     # 转回base64
    parts = base64_data.split(',')
    head = parts[0]
    base64_data = head + ','+imageBase64
    ####################################################

    # 发送渲染请求
    API_URL=RenderLink1+"/sdapi/v1/img2img"
    HEADERS = {
        "Content-Type": "application/json"
    }
    DATA = {
        "init_images": [imageBase64],
        "sampler_name":"DPM++ 2S a Karras",
         "denoising_strength": 0.98,
         "image_cfg_scale": 0,
         "mask_blur": 4,
         "inpainting_fill": 0,
         "inpaint_full_res": True,
         "prompt": "a photograph of [" + prompt_item + "] against a white background, 30mm, 1080p full HD, 4K, sharp focus.",
         "negative_prompt": negative_prompt,
         "seed": -1,
         "subseed": -1,
         "subseed_strength": 0,
         "seed_resize_from_h": -1,
         "seed_resize_from_w": -1,
         "batch_size": batch_size,
         "n_iter": n_iter,
         "steps": 16,
         "cfg_scale": 9,
         "width": 512,
         "height": 512,
        "styles": [
            "8K 3D"
        ],
    }
    print("渲染标签prompt：",DATA["prompt"])
    json_data = json.dumps(DATA).encode('utf8')
    response = requests.post(url=API_URL, headers=HEADERS, data=json_data)
    res=json.loads(response.text)

    parts = base64_data.split(',')
    head = parts[0]
    res_img_base64 = head + ',' + res["images"][0]
    ########################################################

    # 再将结果转为cv img格式，以下将进行透明处理
    parts = res_img_base64.split(',')
    img_type = parts[0].split(':')[1].split(';')[0].rsplit('/', 1)[1]  # 图片类型，如"png"
    img_data = parts[1]  # base64编码本体
    img_data = base64.b64decode(img_data)
    # 转为numpy格式数组
    nparr = np.frombuffer(img_data, np.uint8)
    # 提取图像的三个通道（红、绿、蓝和 alpha 通道）
    img = cv.imdecode(nparr, cv.IMREAD_COLOR)
    # 记录渲染后透明前的图片
    before_transparent=img
    # 转换为灰度图像
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # 使用阈值技术来创建二值图像
    threshold_value = 200
    ret, threshold = cv.threshold(gray, threshold_value, 255, cv.THRESH_BINARY_INV)
    # 创建掩模mask，将接近白色的像素赋为透明色（alpha=0）
    rgba = cv.cvtColor(img, cv.COLOR_BGR2RGBA)
    rgba[:, :, 3] = threshold

    # ##########################################
    # 注意这里opencv的RGB是反着的，为了避免最后绿色变蓝色，这里颠倒一下 #
    # ##########################################
    red, green, blue, alpha = cv.split(rgba)
    rgba = cv.merge((blue, green, red, alpha))
    # 记录渲染后透明前的图片
    after_transparent = rgba
    # ##########################################
    # 注意这里opencv的RGB是反着的，为了避免最后绿色变蓝色，这里颠倒一下 #
    # ##########################################

    # 又转为base64
    image = cv.imencode('.png', rgba)[1]
    base64_without_head = str(base64.b64encode(image))[2:-1]  # 转回base64
    response = {
        'base64':head + ',' + base64_without_head,
        'width':512,
        'height':512
    }
    saveRenderImages(before_render, before_transparent, after_transparent)
    return jsonify(response)

@app.route('/render2',methods=['POST'])
def get_render2():
    data = request.get_json()
    base64_data = data.get('base64', 'default')
    prompt_item = data.get('prompt', 'flower')   # 你不提供我就画花儿
    negative_prompt=data.get('negative_prompt', "blurry, watermark, text, signature, frame, cg render, lights")
    batch_size = data.get('batch_size', 1)
    n_iter=data.get('n_iter', 1)

    ###################################################
    parts = base64_data.split(',')
    # base64编码本体
    img_data = parts[1]
    # 将base64编码的字符串解码为字节数据
    image_data = base64.b64decode(img_data)
    # 将字节数据转为NumPy数组
    nparr = np.frombuffer(image_data, np.uint8)
    # 解码NumPy数组为OpenCV图像格式
    img = cv.imdecode(nparr, cv.IMREAD_UNCHANGED)
    width,height,_=img.shape
    # print(width,height)

    # 记录渲染前的图片
    before_render=img

    image = cv.imencode('.png', img)[1]
    imageBase64 = str(base64.b64encode(image))[2:-1]     # 转回base64
    parts = base64_data.split(',')
    head = parts[0]
    base64_data = head + ','+imageBase64
    ####################################################

    # 发送渲染请求
    API_URL=RenderLink2+"/sdapi/v1/img2img"
    HEADERS = {
        "Content-Type": "application/json"
    }
    DATA = {
        "init_images": [imageBase64],
        "sampler_name":"DPM++ 2S a Karras",
         "denoising_strength": 0.98,
         "image_cfg_scale": 0,
         "mask_blur": 4,
         "inpainting_fill": 0,
         "inpaint_full_res": True,
         "prompt": "a photograph of [" + prompt_item + "] against a white background, 30mm, 1080p full HD, 4K, sharp focus.",
         "negative_prompt": negative_prompt,
         "seed": -1,
         "subseed": -1,
         "subseed_strength": 0,
         "seed_resize_from_h": -1,
         "seed_resize_from_w": -1,
         "batch_size": batch_size,
         "n_iter": n_iter,
         "steps": 16,
         "cfg_scale": 9,
         "width": 512,
         "height": 512,
        "styles": [
            "8K 3D"
        ],
    }
    print("渲染标签prompt：",DATA["prompt"])
    json_data = json.dumps(DATA).encode('utf8')
    response = requests.post(url=API_URL, headers=HEADERS, data=json_data)
    res=json.loads(response.text)

    parts = base64_data.split(',')
    head = parts[0]
    res_img_base64 = head + ',' + res["images"][0]
    ########################################################

    # 再将结果转为cv img格式，以下将进行透明处理
    parts = res_img_base64.split(',')
    img_type = parts[0].split(':')[1].split(';')[0].rsplit('/', 1)[1]  # 图片类型，如"png"
    img_data = parts[1]  # base64编码本体
    img_data = base64.b64decode(img_data)
    # 转为numpy格式数组
    nparr = np.frombuffer(img_data, np.uint8)
    # 提取图像的三个通道（红、绿、蓝和 alpha 通道）
    img = cv.imdecode(nparr, cv.IMREAD_COLOR)
    # 记录渲染后透明前的图片
    before_transparent=img
    # 转换为灰度图像
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # 使用阈值技术来创建二值图像
    threshold_value = 200
    ret, threshold = cv.threshold(gray, threshold_value, 255, cv.THRESH_BINARY_INV)
    # 创建掩模mask，将接近白色的像素赋为透明色（alpha=0）
    rgba = cv.cvtColor(img, cv.COLOR_BGR2RGBA)
    rgba[:, :, 3] = threshold

    # ##########################################
    # 注意这里opencv的RGB是反着的，为了避免最后绿色变蓝色，这里颠倒一下 #
    # ##########################################
    red, green, blue, alpha = cv.split(rgba)
    rgba = cv.merge((blue, green, red, alpha))
    # 记录渲染后透明前的图片
    after_transparent = rgba
    # ##########################################
    # 注意这里opencv的RGB是反着的，为了避免最后绿色变蓝色，这里颠倒一下 #
    # ##########################################

    # 又转为base64
    image = cv.imencode('.png', rgba)[1]
    base64_without_head = str(base64.b64encode(image))[2:-1]  # 转回base64
    response = {
        'base64':head + ',' + base64_without_head,
        'width':512,
        'height':512
    }
    saveRenderImages(before_render, before_transparent, after_transparent)
    return jsonify(response)

@app.route('/render3',methods=['POST'])
def get_render3():
    data = request.get_json()
    base64_data = data.get('base64', 'default')
    prompt_item = data.get('prompt', 'flower')   # 你不提供我就画花儿
    negative_prompt=data.get('negative_prompt', "blurry, watermark, text, signature, frame, cg render, lights")
    batch_size = data.get('batch_size', 1)
    n_iter=data.get('n_iter', 1)

    ###################################################
    parts = base64_data.split(',')
    # base64编码本体
    img_data = parts[1]
    # 将base64编码的字符串解码为字节数据
    image_data = base64.b64decode(img_data)
    # 将字节数据转为NumPy数组
    nparr = np.frombuffer(image_data, np.uint8)
    # 解码NumPy数组为OpenCV图像格式
    img = cv.imdecode(nparr, cv.IMREAD_UNCHANGED)
    width,height,_=img.shape
    # print(width,height)

    # 记录渲染前的图片
    before_render=img

    image = cv.imencode('.png', img)[1]
    imageBase64 = str(base64.b64encode(image))[2:-1]     # 转回base64
    parts = base64_data.split(',')
    head = parts[0]
    base64_data = head + ','+imageBase64
    ####################################################

    # 发送渲染请求
    API_URL=RenderLink3+"/sdapi/v1/img2img"
    HEADERS = {
        "Content-Type": "application/json"
    }
    DATA = {
        "init_images": [imageBase64],
        "sampler_name":"DPM++ 2S a Karras",
         "denoising_strength": 0.98,
         "image_cfg_scale": 0,
         "mask_blur": 4,
         "inpainting_fill": 0,
         "inpaint_full_res": True,
         "prompt": "a photograph of [" + prompt_item + "] against a white background, 30mm, 1080p full HD, 4K, sharp focus.",
         "negative_prompt": negative_prompt,
         "seed": -1,
         "subseed": -1,
         "subseed_strength": 0,
         "seed_resize_from_h": -1,
         "seed_resize_from_w": -1,
         "batch_size": batch_size,
         "n_iter": n_iter,
         "steps": 16,
         "cfg_scale": 9,
         "width": 512,
         "height": 512,
        "styles": [
            "8K 3D"
        ],
    }
    print("渲染标签prompt：",DATA["prompt"])
    json_data = json.dumps(DATA).encode('utf8')
    response = requests.post(url=API_URL, headers=HEADERS, data=json_data)
    res=json.loads(response.text)

    parts = base64_data.split(',')
    head = parts[0]
    res_img_base64 = head + ',' + res["images"][0]
    ########################################################

    # 再将结果转为cv img格式，以下将进行透明处理
    parts = res_img_base64.split(',')
    img_type = parts[0].split(':')[1].split(';')[0].rsplit('/', 1)[1]  # 图片类型，如"png"
    img_data = parts[1]  # base64编码本体
    img_data = base64.b64decode(img_data)
    # 转为numpy格式数组
    nparr = np.frombuffer(img_data, np.uint8)
    # 提取图像的三个通道（红、绿、蓝和 alpha 通道）
    img = cv.imdecode(nparr, cv.IMREAD_COLOR)
    # 记录渲染后透明前的图片
    before_transparent=img
    # 转换为灰度图像
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # 使用阈值技术来创建二值图像
    threshold_value = 200
    ret, threshold = cv.threshold(gray, threshold_value, 255, cv.THRESH_BINARY_INV)
    # 创建掩模mask，将接近白色的像素赋为透明色（alpha=0）
    rgba = cv.cvtColor(img, cv.COLOR_BGR2RGBA)
    rgba[:, :, 3] = threshold

    # ##########################################
    # 注意这里opencv的RGB是反着的，为了避免最后绿色变蓝色，这里颠倒一下 #
    # ##########################################
    red, green, blue, alpha = cv.split(rgba)
    rgba = cv.merge((blue, green, red, alpha))
    # 记录渲染后透明前的图片
    after_transparent = rgba
    # ##########################################
    # 注意这里opencv的RGB是反着的，为了避免最后绿色变蓝色，这里颠倒一下 #
    # ##########################################

    # 又转为base64
    image = cv.imencode('.png', rgba)[1]
    base64_without_head = str(base64.b64encode(image))[2:-1]  # 转回base64
    response = {
        'base64':head + ',' + base64_without_head,
        'width':512,
        'height':512
    }
    saveRenderImages(before_render, before_transparent, after_transparent)
    return jsonify(response)

@app.route('/render4',methods=['POST'])
def get_render4():
    data = request.get_json()
    base64_data = data.get('base64', 'default')
    prompt_item = data.get('prompt', 'flower')   # 你不提供我就画花儿
    negative_prompt=data.get('negative_prompt', "blurry, watermark, text, signature, frame, cg render, lights")
    batch_size = data.get('batch_size', 1)
    n_iter=data.get('n_iter', 1)

    ###################################################
    parts = base64_data.split(',')
    # base64编码本体
    img_data = parts[1]
    # 将base64编码的字符串解码为字节数据
    image_data = base64.b64decode(img_data)
    # 将字节数据转为NumPy数组
    nparr = np.frombuffer(image_data, np.uint8)
    # 解码NumPy数组为OpenCV图像格式
    img = cv.imdecode(nparr, cv.IMREAD_UNCHANGED)
    width,height,_=img.shape
    # print(width,height)

    # 记录渲染前的图片
    before_render=img

    image = cv.imencode('.png', img)[1]
    imageBase64 = str(base64.b64encode(image))[2:-1]     # 转回base64
    parts = base64_data.split(',')
    head = parts[0]
    base64_data = head + ','+imageBase64
    ####################################################

    # 发送渲染请求
    API_URL=RenderLink4+"/sdapi/v1/img2img"
    HEADERS = {
        "Content-Type": "application/json"
    }
    DATA = {
        "init_images": [imageBase64],
        "sampler_name":"DPM++ 2S a Karras",
         "denoising_strength": 0.98,
         "image_cfg_scale": 0,
         "mask_blur": 4,
         "inpainting_fill": 0,
         "inpaint_full_res": True,
         "prompt": "a photograph of [" + prompt_item + "] against a white background, 30mm, 1080p full HD, 4K, sharp focus.",
         "negative_prompt": negative_prompt,
         "seed": -1,
         "subseed": -1,
         "subseed_strength": 0,
         "seed_resize_from_h": -1,
         "seed_resize_from_w": -1,
         "batch_size": batch_size,
         "n_iter": n_iter,
         "steps": 16,
         "cfg_scale": 9,
         "width": 512,
         "height": 512,
        "styles": [
            "8K 3D"
        ],
    }
    print("渲染标签prompt：",DATA["prompt"])
    json_data = json.dumps(DATA).encode('utf8')
    response = requests.post(url=API_URL, headers=HEADERS, data=json_data)
    res=json.loads(response.text)

    parts = base64_data.split(',')
    head = parts[0]
    res_img_base64 = head + ',' + res["images"][0]
    ########################################################

    # 再将结果转为cv img格式，以下将进行透明处理
    parts = res_img_base64.split(',')
    img_type = parts[0].split(':')[1].split(';')[0].rsplit('/', 1)[1]  # 图片类型，如"png"
    img_data = parts[1]  # base64编码本体
    img_data = base64.b64decode(img_data)
    # 转为numpy格式数组
    nparr = np.frombuffer(img_data, np.uint8)
    # 提取图像的三个通道（红、绿、蓝和 alpha 通道）
    img = cv.imdecode(nparr, cv.IMREAD_COLOR)
    # 记录渲染后透明前的图片
    before_transparent=img
    # 转换为灰度图像
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # 使用阈值技术来创建二值图像
    threshold_value = 200
    ret, threshold = cv.threshold(gray, threshold_value, 255, cv.THRESH_BINARY_INV)
    # 创建掩模mask，将接近白色的像素赋为透明色（alpha=0）
    rgba = cv.cvtColor(img, cv.COLOR_BGR2RGBA)
    rgba[:, :, 3] = threshold

    # ##########################################
    # 注意这里opencv的RGB是反着的，为了避免最后绿色变蓝色，这里颠倒一下 #
    # ##########################################
    red, green, blue, alpha = cv.split(rgba)
    rgba = cv.merge((blue, green, red, alpha))
    # 记录渲染后透明前的图片
    after_transparent = rgba
    # ##########################################
    # 注意这里opencv的RGB是反着的，为了避免最后绿色变蓝色，这里颠倒一下 #
    # ##########################################

    # 又转为base64
    image = cv.imencode('.png', rgba)[1]
    base64_without_head = str(base64.b64encode(image))[2:-1]  # 转回base64
    response = {
        'base64':head + ',' + base64_without_head,
        'width':512,
        'height':512
    }
    saveRenderImages(before_render, before_transparent, after_transparent)
    return jsonify(response)

@app.route('/render5',methods=['POST'])
def get_render5():
    data = request.get_json()
    base64_data = data.get('base64', 'default')
    prompt_item = data.get('prompt', 'flower')   # 你不提供我就画花儿
    negative_prompt=data.get('negative_prompt', "blurry, watermark, text, signature, frame, cg render, lights")
    batch_size = data.get('batch_size', 1)
    n_iter=data.get('n_iter', 1)

    ###################################################
    parts = base64_data.split(',')
    # base64编码本体
    img_data = parts[1]
    # 将base64编码的字符串解码为字节数据
    image_data = base64.b64decode(img_data)
    # 将字节数据转为NumPy数组
    nparr = np.frombuffer(image_data, np.uint8)
    # 解码NumPy数组为OpenCV图像格式
    img = cv.imdecode(nparr, cv.IMREAD_UNCHANGED)
    width,height,_=img.shape
    # print(width,height)

    # 记录渲染前的图片
    before_render=img

    image = cv.imencode('.png', img)[1]
    imageBase64 = str(base64.b64encode(image))[2:-1]     # 转回base64
    parts = base64_data.split(',')
    head = parts[0]
    base64_data = head + ','+imageBase64
    ####################################################

    # 发送渲染请求
    API_URL=RenderLink5+"/sdapi/v1/img2img"
    HEADERS = {
        "Content-Type": "application/json"
    }
    DATA = {
        "init_images": [imageBase64],
        "sampler_name":"DPM++ 2S a Karras",
         "denoising_strength": 0.98,
         "image_cfg_scale": 0,
         "mask_blur": 4,
         "inpainting_fill": 0,
         "inpaint_full_res": True,
         "prompt": "a photograph of [" + prompt_item + "] against a white background, 30mm, 1080p full HD, 4K, sharp focus.",
         "negative_prompt": negative_prompt,
         "seed": -1,
         "subseed": -1,
         "subseed_strength": 0,
         "seed_resize_from_h": -1,
         "seed_resize_from_w": -1,
         "batch_size": batch_size,
         "n_iter": n_iter,
         "steps": 16,
         "cfg_scale": 9,
         "width": 512,
         "height": 512,
        "styles": [
            "8K 3D"
        ],
    }
    print("渲染标签prompt：",DATA["prompt"])
    json_data = json.dumps(DATA).encode('utf8')
    response = requests.post(url=API_URL, headers=HEADERS, data=json_data)
    res=json.loads(response.text)

    parts = base64_data.split(',')
    head = parts[0]
    res_img_base64 = head + ',' + res["images"][0]
    ########################################################

    # 再将结果转为cv img格式，以下将进行透明处理
    parts = res_img_base64.split(',')
    img_type = parts[0].split(':')[1].split(';')[0].rsplit('/', 1)[1]  # 图片类型，如"png"
    img_data = parts[1]  # base64编码本体
    img_data = base64.b64decode(img_data)
    # 转为numpy格式数组
    nparr = np.frombuffer(img_data, np.uint8)
    # 提取图像的三个通道（红、绿、蓝和 alpha 通道）
    img = cv.imdecode(nparr, cv.IMREAD_COLOR)
    # 记录渲染后透明前的图片
    before_transparent=img
    # 转换为灰度图像
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # 使用阈值技术来创建二值图像
    threshold_value = 200
    ret, threshold = cv.threshold(gray, threshold_value, 255, cv.THRESH_BINARY_INV)
    # 创建掩模mask，将接近白色的像素赋为透明色（alpha=0）
    rgba = cv.cvtColor(img, cv.COLOR_BGR2RGBA)
    rgba[:, :, 3] = threshold

    # ##########################################
    # 注意这里opencv的RGB是反着的，为了避免最后绿色变蓝色，这里颠倒一下 #
    # ##########################################
    red, green, blue, alpha = cv.split(rgba)
    rgba = cv.merge((blue, green, red, alpha))
    # 记录渲染后透明前的图片
    after_transparent = rgba
    # ##########################################
    # 注意这里opencv的RGB是反着的，为了避免最后绿色变蓝色，这里颠倒一下 #
    # ##########################################

    # 又转为base64
    image = cv.imencode('.png', rgba)[1]
    base64_without_head = str(base64.b64encode(image))[2:-1]  # 转回base64
    response = {
        'base64':head + ',' + base64_without_head,
        'width':512,
        'height':512
    }
    saveRenderImages(before_render, before_transparent, after_transparent)
    return jsonify(response)

@app.route('/render6',methods=['POST'])
def get_render6():
    data = request.get_json()
    base64_data = data.get('base64', 'default')
    prompt_item = data.get('prompt', 'flower')   # 你不提供我就画花儿
    negative_prompt=data.get('negative_prompt', "blurry, watermark, text, signature, frame, cg render, lights")
    batch_size = data.get('batch_size', 1)
    n_iter=data.get('n_iter', 1)

    ###################################################
    parts = base64_data.split(',')
    # base64编码本体
    img_data = parts[1]
    # 将base64编码的字符串解码为字节数据
    image_data = base64.b64decode(img_data)
    # 将字节数据转为NumPy数组
    nparr = np.frombuffer(image_data, np.uint8)
    # 解码NumPy数组为OpenCV图像格式
    img = cv.imdecode(nparr, cv.IMREAD_UNCHANGED)
    width,height,_=img.shape
    # print(width,height)

    # 记录渲染前的图片
    before_render=img

    image = cv.imencode('.png', img)[1]
    imageBase64 = str(base64.b64encode(image))[2:-1]     # 转回base64
    parts = base64_data.split(',')
    head = parts[0]
    base64_data = head + ','+imageBase64
    ####################################################

    # 发送渲染请求
    API_URL=RenderLink6+"/sdapi/v1/img2img"
    HEADERS = {
        "Content-Type": "application/json"
    }
    DATA = {
        "init_images": [imageBase64],
        "sampler_name":"DPM++ 2S a Karras",
         "denoising_strength": 0.98,
         "image_cfg_scale": 0,
         "mask_blur": 4,
         "inpainting_fill": 0,
         "inpaint_full_res": True,
         "prompt": "a photograph of [" + prompt_item + "] against a white background, 30mm, 1080p full HD, 4K, sharp focus.",
         "negative_prompt": negative_prompt,
         "seed": -1,
         "subseed": -1,
         "subseed_strength": 0,
         "seed_resize_from_h": -1,
         "seed_resize_from_w": -1,
         "batch_size": batch_size,
         "n_iter": n_iter,
         "steps": 16,
         "cfg_scale": 9,
         "width": 512,
         "height": 512,
        "styles": [
            "8K 3D"
        ],
    }
    print("渲染标签prompt：",DATA["prompt"])
    json_data = json.dumps(DATA).encode('utf8')
    response = requests.post(url=API_URL, headers=HEADERS, data=json_data)
    res=json.loads(response.text)

    parts = base64_data.split(',')
    head = parts[0]
    res_img_base64 = head + ',' + res["images"][0]
    ########################################################

    # 再将结果转为cv img格式，以下将进行透明处理
    parts = res_img_base64.split(',')
    img_type = parts[0].split(':')[1].split(';')[0].rsplit('/', 1)[1]  # 图片类型，如"png"
    img_data = parts[1]  # base64编码本体
    img_data = base64.b64decode(img_data)
    # 转为numpy格式数组
    nparr = np.frombuffer(img_data, np.uint8)
    # 提取图像的三个通道（红、绿、蓝和 alpha 通道）
    img = cv.imdecode(nparr, cv.IMREAD_COLOR)
    # 记录渲染后透明前的图片
    before_transparent=img
    # 转换为灰度图像
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # 使用阈值技术来创建二值图像
    threshold_value = 200
    ret, threshold = cv.threshold(gray, threshold_value, 255, cv.THRESH_BINARY_INV)
    # 创建掩模mask，将接近白色的像素赋为透明色（alpha=0）
    rgba = cv.cvtColor(img, cv.COLOR_BGR2RGBA)
    rgba[:, :, 3] = threshold

    # ##########################################
    # 注意这里opencv的RGB是反着的，为了避免最后绿色变蓝色，这里颠倒一下 #
    # ##########################################
    red, green, blue, alpha = cv.split(rgba)
    rgba = cv.merge((blue, green, red, alpha))
    # 记录渲染后透明前的图片
    after_transparent = rgba
    # ##########################################
    # 注意这里opencv的RGB是反着的，为了避免最后绿色变蓝色，这里颠倒一下 #
    # ##########################################

    # 又转为base64
    image = cv.imencode('.png', rgba)[1]
    base64_without_head = str(base64.b64encode(image))[2:-1]  # 转回base64
    response = {
        'base64':head + ',' + base64_without_head,
        'width':512,
        'height':512
    }
    saveRenderImages(before_render, before_transparent, after_transparent)
    return jsonify(response)

import random
import hashlib
import time

BAIDU_TRANSLATOR_API_URL = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
APP_ID = '20230607001704227'
SECRET_KEY = 'd3Ro7sijeyUU6iF1Sm31'
@app.route('/translate',methods=['POST'])
def cn_to_en():
    # 从 POST 请求中获取要翻译的文字
    data = request.get_data()  # 接收json数据
    jsondata = json.loads(data)  # json数据解析
    text = jsondata["text"]

    # 调用百度翻译 API 进行翻译
    params = {
        'q': text,
        'from': 'zh',
        'to': 'en',
        'appid': APP_ID,
        'salt': random.randint(10000, 99999),
        'sign': '',  # 签名在下面生成
    }

    sign_str = APP_ID + text + str(params['salt']) + SECRET_KEY
    sign = hashlib.md5(sign_str.encode()).hexdigest()
    params['sign'] = sign

    response = requests.get(BAIDU_TRANSLATOR_API_URL, params=params)
    result = response.json()
    time.sleep(1)

    # 如果翻译成功，返回翻译结果
    if 'trans_result' in result:
        return jsonify({'status': 'ok', 'translation': result['trans_result'][0]['dst']})
    # 否则返回错误信息
    else:
        return jsonify({'status': 'error', 'error': result['error_msg']})


if __name__ == '__main__':
    # app.add_url_rule('/', 'hello', hello_world)   # 与@app二选一
    app.run(host='127.0.0.1', port=8080, debug=True)
