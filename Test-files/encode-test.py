import base64

def ToBase64(file, txt):
    with open(file, 'rb') as fileObj:
        video = fileObj.read()
        base64_data = base64.b64encode(video)
        fout = open(txt, 'w')
        fout.write(base64_data.decode())
        fout.close()


def ToFile(txt, file):
    with open(txt, 'r') as fileObj:
        base64_data = fileObj.read()
        ori_video = base64.b64decode(base64_data)
        fout = open(file, 'wb')
        fout.write(ori_video)
        fout.close()


ToBase64("./visitor_1.mov", 'visitor_1.txt')  # 文件转换为base64
