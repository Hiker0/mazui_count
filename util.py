# -*- coding:utf-8 -*-
import pandas as pd

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
