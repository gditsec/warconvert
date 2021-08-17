import base64

res = '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'

res = base64.decodestring(res.encode('utf-8'))
p = res.find('\r\n\r\n'.encode('utf-8'))
# print()
res = res[p + 4:]
with open('test.png', 'wb') as img:
    img.write(res)