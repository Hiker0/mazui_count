# -*- coding:utf-8 -*-
import pandas as pd
import re
def dataframe_replace(df, clumns,  remap):
    for index, row in df.iterrows():
        for clumn in clumns:
            keys = remap.keys()
            value = row[clumn]
            if pd.notnull(value):
                changed = 0
                for key in keys:
                    changed = 1
                    if key in value:
                        value=value.replace(key, remap[key])
                if changed:
                    df.loc[index, clumn]=value
    return df

def dataframe_drop_null(df, clumn):
    for index, row in df.iterrows():
        if pd.isnull(row[clumn]):
            df = df.drop(index)

    return df

'''有重复返回１，没有返回０ '''
def list_dubble_item(list):
    if len(list) != len(set(list)):
        return 1
    else:
        return 0

def getButie(op_time):
    if op_time <= 60:
        butie = 0
    elif op_time <= 180:
        butie = op_time-60
    else:
        butie = (op_time-180)*2+120

    return butie

def getChineseString(test):
    # return re.split('[ ,]', test)
    return re.findall(ur"[\u4e00-\u9fa5]+", test)

def isWeiChangJing(location):
    if location == '胃肠镜全麻' or location == '气管镜':
        return 1
    else:
        return 0


