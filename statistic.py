# -*- coding:utf-8 -*-
import os
import re
import shutil
import sys
import numpy as np
import argparse
import pandas as pd
import util
import configparser
import xlrd
import openpyxl.workbook

reload(sys)
sys.setdefaultencoding( "utf-8" )

ALLOW_OPTPYE=['全麻（插管）','腰麻','全麻（未插管）','腰硬联合','硬膜外']
SRC2_ALLOW_OPTPYE=['日间眼科局监','2#眼科局监','日间人流','无痛分娩','无痛取卵','门诊人流','胃肠镜']
PACU_ALLOW_OPTPYE=['麻醉门诊','复苏室']

ALLOW_LOCATION=['大手术室','胃肠镜全麻','气管镜','日间','DSA','关节复位','双镜','抢救插管']
DOCTOR_ALIAS = {'刑怡安':'邢怡安','王晓丽':'王晓莉','沈皓':'沈浩','魏巍':'魏薇','刘玉奇':'刘玉齐','张缈':'张渺','董建玉':'董健玉','苏依单':'苏依丹',u'＊':u'*', u'，':u',', u'　':u' '}

DEBUG=1
DUTY_FILE = "duty.ini"
doctors_dict = dict()
menzhen_dict = dict()
zhiban_dict = dict()

days_list=[]

global src1_df, src2_df, pacu_df, doctors_df, month

def read_excel(database):
    print "read excel:"+database
    dframe1 = pd.read_excel(database, sheet_name="Worksheet")
    #print dframe1
    return dframe1

def read_csv(database):
    print "read csv:" + database
    dframe1 = pd.read_csv(database)
    #print dframe1
    return dframe1

def calculate_oneday_percentage(src1_day_df, src2_day_df,pacu_day_df, perc_df):
    global menzhen_dict
    #print perc_df
    weichangjing_num = 0
    src1_day_df = util.dataframe_replace(src1_day_df.copy(),['麻1（主麻）','麻2（副麻）','麻3（接班主麻）','麻4（接班副麻）'],{u'*':u''})

    for index,row in src1_day_df.iterrows():
        date = row['日期']
        op_type = row['麻醉类型']
        op_location = row['请选择手术地点']
        main_doctor = row['麻1（主麻）']
        assistant_doctor = row['麻2（副麻）']
        succession_main = row['麻3（接班主麻）']
        succession_assistant = row['麻4（接班副麻）']

        if util.isWeiChangJing(op_location):
            weichangjing_num = weichangjing_num +1
            docs = util.getChineseString(main_doctor)
            #menzhen = menzhen_dict[date]
            if pd.notnull(assistant_doctor):
                docs.extend(util.getChineseString(assistant_doctor))

            if pd.notnull(succession_main):
                docs.extend(util.getChineseString( succession_main))

            if pd.notnull(succession_assistant):
                docs.extend(util.getChineseString(succession_assistant))

            for doc in docs:
                num = 1.0/len(docs)
                if doctors_dict[doc] == 3:
                    #perc_df.loc[doc, '全(主)'] = perc_df.loc[doc, '全(主)'] + num
                    perc_df.loc[doc, '全(副)'] = perc_df.loc[doc, '全(副)'] + num
                else:
                    perc_df.loc[doc, '全(主)'] = perc_df.loc[doc, '全(主)'] + num
                    perc_df.loc[doc, '全(副)'] = perc_df.loc[doc, '全(副)'] + num

        else:
            if op_type == '全麻（插管）':
                if pd.notnull(main_doctor):
                    perc_df.loc[main_doctor,'全(主)'] = perc_df.loc[main_doctor,'全(主)'] + 1
                if pd.notnull(assistant_doctor):
                    perc_df.loc[assistant_doctor,'全(副)'] = perc_df.loc[assistant_doctor,'全(副)'] + 1
            elif op_type == '全麻（未插管）':
                if pd.notnull(main_doctor):
                    perc_df.loc[main_doctor,'静(主)'] = perc_df.loc[main_doctor,'静(主)'] + 1
                if pd.notnull(assistant_doctor):
                    perc_df.loc[assistant_doctor,'静(副)'] = perc_df.loc[assistant_doctor,'静(副)'] + 1
            elif op_type == '腰麻' or op_type == '腰硬联合' or op_type =='硬膜外':
                if pd.notnull(main_doctor):
                    perc_df.loc[main_doctor,'硬(主)'] = perc_df.loc[main_doctor,'硬(主)'] + 1
                if pd.notnull(assistant_doctor):
                    perc_df.loc[assistant_doctor,'硬(副)'] = perc_df.loc[assistant_doctor,'硬(副)'] + 1
            else:

                if pd.notnull(op_type):
                    print "意外的手术类型:" + op_type
                else:
                    print "手术类型为空"

    #perc_df.to_csv(u"123.csv")
    for index, row in src2_day_df.iterrows():
        op_type = row['请选择类型']
        op_num = row['总例数']
        pair_num = row['全套例数']
        if pd.isna(op_num):
            op_num = 1
        doc1 = row['麻1']
        doc2 = row['麻2']
        doc3 = row['麻3']
        doc4 = row['麻4']
        doc5 = row['麻5']

        if op_type == '日间眼科局监' or op_type =='2#眼科局监':
            docs = util.getChineseString(doc1)
            if len(docs)==1:
                perc_df.loc[docs[0],'眼科监护']=perc_df.loc[docs[0],'眼科监护'] + op_num
            elif len(docs)>1:
                for doc in  docs:
                    perc_df.loc[doc, '眼科监护'] = perc_df.loc[doc, '眼科监护'] + op_num*1.0/len(docs)
            else:
                print '麻１　为空'
        elif op_type == '日间人流':
            if pd.notnull(doc1):
                perc_df.loc[doc1, '静(主)'] = perc_df.loc[doc1, '静(主)'] + op_num
            if pd.notnull(doc2):
                perc_df.loc[doc2, '静(副)'] = perc_df.loc[doc2, '静(副)'] + op_num
        elif op_type == '无痛分娩':
            docs = []
            docs.extend(util.getChineseString( doc1))
            if pd.notnull(doc2):
                docs.extend(util.getChineseString( doc2))
            for doc in docs:
                perc_df.loc[doc, '无痛分娩'] = perc_df.loc[doc, '无痛分娩'] + op_num*1.0/len(docs)
        elif op_type == '无痛取卵':
            if pd.notnull(doc1):
                perc_df.loc[doc1,'无痛取卵']=perc_df.loc[doc1,'无痛取卵'] + op_num
            else:
                print '麻１　为空'

        elif op_type == '门诊人流':
            if pd.notnull(doc1):
                perc_df.loc[doc1,'门诊人流']=perc_df.loc[doc1,'眼科监护'] + op_num
            else:
                print '麻１　为空'
        elif op_type == '胃肠镜':
            op_num = op_num - pair_num*2
            menzhen = menzhen_dict[date]

            docs = []
            docs.extend(util.getChineseString( doc1))
            if pd.notnull(doc2):
                docs.extend(util.getChineseString( doc2))
            if pd.notnull(doc3):
                docs.extend(util.getChineseString( doc3))
            if pd.notnull(doc4):
                docs.extend(util.getChineseString( doc4))

            num = op_num*1.0 / len(docs)
            num_par = pair_num*1.0/ len(docs)
            for doc in docs:
                if doctors_dict[doc] == 3 and menzhen != 'None':
                    perc_df.loc[doc, '胃肠镜（单）'] = perc_df.loc[doc, '胃肠镜（单）'] + num*0.3
                    perc_df.loc[doc, '胃肠镜（套）'] = perc_df.loc[doc, '胃肠镜（套）'] + num_par*0.3
                    perc_df.loc[menzhen, '胃肠镜（单）'] = perc_df.loc[menzhen, '胃肠镜（单）'] + num * 0.7
                    perc_df.loc[menzhen, '胃肠镜（套）'] = perc_df.loc[menzhen, '胃肠镜（套）'] + num_par * 0.7
                else:
                    perc_df.loc[doc, '胃肠镜（单）'] = perc_df.loc[doc, '胃肠镜（单）'] + num
                    perc_df.loc[doc, '胃肠镜（套）'] = perc_df.loc[doc, '胃肠镜（套）'] + num_par
            print ""
        else:
           print '未知的手术类型:' + op_type

    for index, row in perc_df.iterrows():
        quan_zhu=row['全(主)']*216*0.7
        quan_fu = row['全(副)']*216*0.3
        ying_zhu = row['硬(主)']*60*0.7
        ying_fu = row['硬(副)']*60*0.3
        jing_zhu = row['静(主)']*80*0.7
        jing_fu = row['静(副)']*80*0.3
        wcj_dan = row['胃肠镜（单）'] * 40
        wcj_tao = row['胃肠镜（套）']*50
        renliu = row['门诊人流'] * 80
        quluan = row['无痛取卵']*40
        fenmian = row['无痛分娩'] * 230
        jianhu = row['眼科监护']*19.6
        total = quan_zhu+ quan_fu + ying_zhu + ying_fu + jing_zhu + jing_fu+ wcj_dan + wcj_tao +renliu + quluan+ fenmian+jianhu
        if doctors_dict[index] != 4:
            perc_df.loc[index,'津贴'] = total
    return perc_df

def calculate_percentage():
    global src1_df, src2_df, pacu_df

    #day_df = src1_df[src1_df[u"日期"] == days_list[0]]
    #calculate_oneday_percentage(day_df)
    writer = pd.ExcelWriter('提成.xlsx')

    docs = []
    ids = []
    types = []
    for index, row in doctors_df.iterrows():
        docs.append(unicode(row["name"], "utf-8"))
        ids.append(index)
        types.append(row["doctor_type"])

    num = len(docs)
    huizong_df = pd.DataFrame({'名字': docs},columns=['名字'])

    for day in days_list:
        datestr = day.day

        src1_day_df = src1_df[src1_df["日期"]==day]
        src2_day_df = src2_df[src2_df['时间'] == day]
        pacu_day_df = pacu_df[pacu_df['时间'] == day]
        mydict = {'名字': docs,
                  '全(主)': np.zeros(num),
                  '全(副)': np.zeros(num), '硬(主)': np.zeros(num),
                  '硬(副)': np.zeros(num), '静(主)': np.zeros(num),
                  '静(副)': np.zeros(num), '胃肠镜（单）': np.zeros(num),
                  '胃肠镜（套）': np.zeros(num), '门诊人流': np.zeros(num),
                  '无痛取卵': np.zeros(num), '无痛分娩': np.zeros(num),
                  '眼科监护': np.zeros(num),'津贴': np.zeros(num)}

        columns = ['名字', '全(主)', '全(副)', '硬(主)',
                   '硬(副)', '静(主)',
                   '静(副)', '胃肠镜（单）','胃肠镜（套）',
                   '门诊人流', '无痛取卵',
                   '无痛分娩', '眼科监护',
                   '津贴']

        perc_df = pd.DataFrame(mydict, columns=columns)

        perc_df = perc_df.set_index('名字')
        perc_df.reindex(docs)

        day_result = calculate_oneday_percentage(src1_day_df, src2_day_df, pacu_day_df, perc_df)
        sheet = str(day.day) #str(day).split()[0]

        jintie = day_result['津贴']
        huizong_df[datestr]=jintie.tolist()
        day_result.to_excel(writer, sheet)

    huizong_df.set_index('名字')
    mid = huizong_df.sum( axis=1)
    huizong_df.insert(1, '月总计', mid)
    huizong_df.to_excel(writer, u'月汇总')
    writer.save()

    print "提成计算完成：　提成.xlsx"
    return

def src1_check():
    '''检查大帐单一'''
    global src1_df,zhiban_dict
    success = 1
    print "检查大帐单一 ..."

    for index, row in src1_df.iterrows():

        series = row['数据唯一编号']
        date = row['日期']
        op_type = row['麻醉类型']
        op_location = row['请选择手术地点']
        main_doctor = row['麻1（主麻）']
        op_time_filed = row['手术时间']
        op_name = row['术式']

        total_doc = []
        if pd.notnull(main_doctor):
            li = util.getChineseString( main_doctor)

            total_doc.extend(li)
            if len(li) > 1 and (not util.isWeiChangJing(op_location)):
                success = 0
                print series, "不正确的麻醉人数", op_location

        assistant_doctor = row['麻2（副麻）']
        if pd.notnull(assistant_doctor):
            #assistant_doctor=assistant_doctor.replace('*', '')
            total_doc.append(assistant_doctor.replace('*',''))
        succession_main = row['麻3（接班主麻）']
        if pd.notnull(succession_main):
            #succession_main = succession_main.replace('*', '')
            total_doc.append(succession_main.replace('*',''))
        succession_assistant = row['麻4（接班副麻）']
        if pd.notnull(succession_assistant):
            #succession_assistant = succession_assistant.replace('*', '')
            total_doc.append( succession_assistant.replace('*',''))
        has_succession = row['是否接班']

        #空行
        if  pd.isnull(date):
            continue
        #手术地点
        if op_location not in ALLOW_LOCATION:
            success = 0
            print series,"不知道的手术地点",op_location
        elif op_location == 'DSA' and op_type != '全麻（插管）':
            success = 0
            print series, "DSA", op_type
        #麻醉类型检查
        if pd.notnull(op_type) and (op_type not in ALLOW_OPTPYE):
            success = 0
            print series,"不知道的麻醉类型：", op_type

        if util.list_dubble_item(total_doc):
            success = 0
            print series, "重复的麻醉医生", total_doc

        for doc in total_doc:
            if doc not in doctors_dict.keys():
                success = 0
                print series, "不识别的麻醉医生：", doc

        if  pd.notnull(op_type) and (not util.isWeiChangJing(op_location)) and pd.notnull(assistant_doctor):
            main_d = main_doctor.replace('*','')
            assistant_d= assistant_doctor.replace('*','')

            if op_name=='肝移植' or op_location.upper() == 'DSA' :
                if doctors_dict[main_d] != 1:
                    print series, op_name,"主麻副麻登记错误：", main_doctor, assistant_doctor
            elif doctors_dict[main_d] == 1  and doctors_dict[assistant_d] == 0:
                if (main_doctor.find('*') < 0)and (assistant_doctor.find('*') < 0):
                    print series,"主麻副麻登记错误：",main_doctor, assistant_doctor


        if has_succession == '是':

            if pd.isnull(succession_main) and pd.isnull(succession_assistant):
                success = 0
                print series, "接班主麻副麻登记错误：", main_doctor, assistant_doctor

        elif has_succession == '否':
            if(pd.notnull(succession_main) or pd.notnull(succession_assistant)):
                success = 0
                print series, "接班主麻副麻登记错误：", main_doctor, assistant_doctor
        else:
            if (not util.isWeiChangJing(op_location)) and op_location != '抢救插管':
                print series, "没有登记是否接班：", main_doctor, assistant_doctor


        if pd.isnull(op_time_filed):
            if op_location != '抢救插管':
                print series, "没有登记手术时间"
        else:
            op_time = int(op_time_filed)
            if op_time <= 0:
                print series, "手术时间登记错误"

    if success:
        print "电子大帐１检查通过"
    return success


def src2_check():
    global src2_df
    success = 1

    print "检查大帐单二 ..."

    for index, row in src2_df.iterrows():
        op_type = row['请选择类型']
        series = row['数据唯一编号']
        # 麻醉类型检查
        if pd.notnull(op_type) and (op_type not in SRC2_ALLOW_OPTPYE):
            success = 0
            print series,"不知道的麻醉类型：", op_type

        #检查医生
        doctors = []
        if pd.notnull(row['麻1']):
            doctor1 = unicode.strip(row['麻1'])
            doctors.extend(util.getChineseString(doctor1))
        else:
            print series+"缺少麻一"

        if pd.notnull(row['麻2']):
            doctor2 = unicode.strip(row['麻2'])
            doctors.extend(util.getChineseString(doctor2))

        if pd.notnull(row['麻3']):
            doctor3 = unicode.strip(row['麻3'])
            doctors.extend(util.getChineseString(doctor3))

        if pd.notnull(row['麻4']):
            doctor4 = unicode.strip(row['麻4'])
            doctors.extend(util.getChineseString(doctor4))

        if pd.notnull(row['麻5']):
            doctor5 = unicode.strip(row['麻5'])
            doctors.extend(util.getChineseString(doctor5))

        for doc in doctors:
            if doc not in doctors_dict.keys():
                success = 0
                print series,"不识别的麻醉医生：", doc

    if success:
        print "电子大帐二检查通过"
    return success


def pacu_check():
    global pacu_df
    success = 1

    print "检查门诊和ＰＡＣＵ..."

    for index, row in pacu_df.iterrows():
        date = row['时间']
        op_type=row['请选择类型']
        doctor = row['复苏人员（出诊人员）']

        # 麻醉类型检查
        if pd.notnull(op_type) and (op_type not in PACU_ALLOW_OPTPYE):
            success = 0
            print "不知道的麻醉类型：", op_type

        # 检查医生
        if doctor not in doctors_dict.keys():
            success = 0
            print "不识别的麻醉医生：", doctor

    if success:
        print "ＰＡＣＵ检查通过"

    return success

def menzhen_check():
    global  menzhen_dict
    need_menzhen_days=[]
    for index, row in src1_df.iterrows():
        date = row['日期']
        op_location = row['请选择手术地点']

        if util.isWeiChangJing(op_location):
            if date not in need_menzhen_days:
                need_menzhen_days.append(date)
    for index, row in src2_df.iterrows():
        date = row['时间']
        op_type = row['请选择类型']
        if op_type == '胃肠镜':
            if date not in need_menzhen_days:
                need_menzhen_days.append(date)

    keys = menzhen_dict.keys()
    success = 1
    for day in need_menzhen_days:
        if day not in keys:
            week = day.weekday()
            if week < 5:
                success = 0
                menzhen_dict[day]='None'
                print day, "星期%d没有值班医生"%(week)
    if success:
        print "门诊值班检查通过"

    return success

def database_check():
    print '－－－－－输入信息检查－－－－－－－'
    res1 = src1_check()
    res2 = src2_check()
    res3 = pacu_check()
    res4 = menzhen_check()

    if res1 == 0 or res2==0 or res3==0 or res4 == 0:
        return 0
    else:
        return 1

#预处理
def pre_handler():
    global src1_df, src2_df, pacu_df

    print "－－－－预处理－－－－－－"
    print "处理大帐一"

    src1_df = util.dataframe_drop_null(src1_df, '日期')
    src1_df = util.dataframe_replace(src1_df,['麻1（主麻）','麻2（副麻）','麻3（接班主麻）','麻4（接班副麻）'],DOCTOR_ALIAS)

    src2_df = util.dataframe_drop_null(src2_df, '时间')
    src2_df = util.dataframe_replace(src2_df, ['麻1', '麻2', '麻3', '麻4','麻5'], DOCTOR_ALIAS)

    pacu_df = util.dataframe_drop_null(pacu_df, '时间')
    pacu_df = util.dataframe_replace(pacu_df, ['复苏人员（出诊人员）'], DOCTOR_ALIAS)


    #src1_df = util.dataframe_replace(src1_df,['麻1（主麻）','麻2（副麻）','麻3（接班主麻）','麻4（接班副麻）'],{'*':''})
    src2_df = util.dataframe_replace(src2_df, ['麻1', '麻2', '麻3', '麻4','麻5'], {'*':''})
    pacu_df = util.dataframe_replace(pacu_df, ['复苏人员（出诊人员）'], {'*':''})

    return



#获取值班信息
def getZhibanInfo():
    global zhiban_dict
    print '－－－－－获取值班信息－－－'
    for day in days_list:
        last_dt = day - pd.Timedelta("1 days")
        src1_day_df = src1_df[src1_df["日期"] == day]
        src2_day_df = src2_df[src2_df['时间'] == day]
        doctorlist = []
        doctors = []

        if zhiban_dict.has_key(last_dt):
            last_doctors = zhiban_dict[last_dt]
        else:
            last_doctors=[]

        for index, row in src1_day_df.iterrows():
            main_doctor = row['麻1（主麻）']
            assistant_doctor = row['麻2（副麻）']
            succession_main = row['麻3（接班主麻）']
            succession_assistant = row['麻4（接班副麻）']
            if pd.notnull(main_doctor):
                doctors.extend(util.getChineseString(main_doctor))

            if pd.notnull(assistant_doctor):
                doctors.extend(util.getChineseString(assistant_doctor))

            if pd.notnull(succession_main):
                doctors.extend(util.getChineseString(succession_main))

            if pd.notnull(succession_assistant):
                doctors.extend(util.getChineseString(succession_assistant))


        for index, row in src2_day_df.iterrows():
            doctor1 = row['麻1']
            doctor2 = row['麻2']
            doctor3 = row['麻3']
            doctor4 = row['麻4']
            doctor5 = row['麻5']

            if pd.notnull(doctor1):
                doctors.extend(util.getChineseString(doctor1))
            if pd.notnull(doctor2):
                doctors.extend(util.getChineseString(doctor2))
            if pd.notnull(doctor3):
                doctors.extend(util.getChineseString(doctor3))
            if pd.notnull(doctor4):
                doctors.extend(util.getChineseString(doctor4))
            if pd.notnull(doctor5):
                doctors.extend(util.getChineseString(doctor5))

        str=''
        for doc in doctors:
            if ('*' in doc):
                d = doc.replace('*','')
                if d not in doctorlist and d not in last_doctors:
                    doctorlist.append(d)
                    str= d+' '+str
        print day, str
        zhiban_dict[day] = doctorlist

def getMenzhenInfo():
    global menzhen_dict

    print '－－－－－获取门诊值班信息－－－'
    for index, row in pacu_df.iterrows():
        date = row['时间']
        doctor = row['复苏人员（出诊人员）']
        type = row['请选择类型']
        if type == '麻醉门诊' and (date not in menzhen_dict.keys()):
            menzhen_dict[date]=doctor
            print date, doctor


def main(src1,src2,pacu,doctors_list):
    global src1_df, src2_df,pacu_df,doctors_df
    global days_list

    src1_df = read_excel(src1)
    src2_df = read_excel(src2)
    pacu_df = read_excel(pacu)
    doctors_df = read_csv(doctors_list)

    #读取医生类型
    doctors_df = doctors_df.set_index("NO.")
    for index,row in doctors_df.iterrows():
        name = unicode(row["name"], "utf-8")
        name = name.strip()
        doctors_dict[name]=row["doctor_type"]

    #统计日期
    for index,row in src1_df.iterrows():

        date = row['日期']
        if (pd.notnull(date)):
            if date.month != month:
                src1_df= src1_df.drop(index)
                continue
            if (not days_list.__contains__(date)):
                days_list.append(date)

    for index,row in src2_df.iterrows():
        date = row['时间']
        if (pd.notnull(date)):
            if date.month != month:
                src2_df= src2_df.drop(index)
                continue
            if (not days_list.__contains__(date)):
                days_list.append(date)

    for index,row in pacu_df.iterrows():
        date = row['时间']
        if (pd.notnull(date)):
            if date.month != month:
                pacu_df= pacu_df.drop(index)
                continue
            if (not days_list.__contains__(date)):
                days_list.append(date)


    pre_handler()
    getZhibanInfo()
    getMenzhenInfo()
    duty_config = configparser.ConfigParser();
    duty_config.add_section(u"门诊")
    duty_config.add_section(u"值班")
    ret = database_check()
    for date in days_list:
        if date in menzhen_dict.keys():
            value = menzhen_dict[date]
            duty_config.set(u"门诊",date.strftime("%Y-%m-%d"),value=value)
        if date in zhiban_dict:
            d_list = zhiban_dict[date]
            duty_config.set(u"值班", date.strftime("%Y-%m-%d"), value=','.join(d_list))

    duty_config.write(open(DUTY_FILE,"w"))
    print "\n----------------------------------------------"
    if ret != 1:
        print "检查到错误, 请更正信息。。"
    print "请确认值班信息是否真确，可修改‘ｄuty.ini’改正错误"
    print"输入　N 退出，　Y 继续．．"
    while 1:
        command = raw_input('>>')
        if command == 'y' or command == 'Y':
            break
        elif command == 'n' or command == 'N':
            exit()

    days_list = sorted(days_list)
    duty_config.clear()
    menzhen_dict.clear()
    zhiban_dict.clear()
    duty_config.read(DUTY_FILE)
    for date in days_list:
        day= date.strftime("%Y-%m-%d")
        value = duty_config.get(u'门诊',day,fallback=None)
        if value != None:
            menzhen_dict[date]= value
        else:
            menzhen_dict[date] = None
        docs = duty_config.get(u'值班',day,fallback=None)
        if docs != None:
            d_list = docs.split(',')
            zhiban_dict[date] = d_list

    calculate_percentage()
    return

if __name__ == '__main__':

    conf = configparser.ConfigParser()
    conf.read("config.ini")


    src1 = conf.get("path","src1")
    src2 = conf.get("path","src2")
    pacu = conf.get("path","pacu")
    doctors_list = conf.get("path","doctors_list")

    month =  conf.getint("config","month")

    subsidies = "科室补贴(新新).xls"
    percentage = "2018.手术提成+(1).xls"
    parser = argparse.ArgumentParser()
    parser.add_argument("--src1", help="电子大帐一")
    parser.add_argument("--src2", help="电子大帐二")
    parser.add_argument("--pacu", help="PACU与麻醉门诊登记")
    parser.add_argument("--doctors", help="医生列表")
    parser.add_argument("--subsidies", help="科室补贴")
    parser.add_argument("--percentage", help="手术提成")

    args = parser.parse_args()

    if args.src1 and (os.path.exists(args.src1)):
        src1=args.src1
    elif not DEBUG:
        print "找不到电子大帐一"
        exit()

    if args.src2 and (os.path.exists(args.src2)):
        src2=args.src2
    elif not DEBUG:
        print "找不到电子大帐二"
        exit()

    if args.pacu and (os.path.exists(args.pacu)):
        pacu=args.pacu
    elif not DEBUG:
        print "找不到麻醉门诊登记"
        exit()

    if args.doctors and (os.path.exists(args.doctors)):
        doctors_list=args.doctors
    elif not DEBUG:
        print "找不到医生列表"
        exit()

    print "电子大帐一:%s"%(src1)
    print "电子大帐二:%s"%(src2)
    print "麻醉门诊登记:%s"%(pacu)  
    print "医生列表:%s"%(doctors_list)


    main(src1,src2,pacu,doctors_list)