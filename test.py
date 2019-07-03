# -*- coding:utf-8 -*-
import re

test = u"陈力 ,韩光炜, 王晓莉 ,张渺"

print re.findall(ur"[\u4e00-\u9fa5]+",test)#
zz = re.split(r'[ , ]', test)
print zz
