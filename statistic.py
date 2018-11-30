# -*- coding:utf-8 -*-
import os
import re
import shutil
import sys
import numpy as np
import argparse
import pandas as pd

reload(sys)
sys.setdefaultencoding( "utf-8" )

ALLOW_OPTPYE=[u'全麻（插管）',u'腰麻',u'全麻（未插管）',u'腰硬联合',u'硬膜外']
SRC2_ALLOW_OPTPYE=[u'日间眼科局监',u'2#眼科局监',u'日间人流',u'无痛分娩',u'无痛取卵',u'门诊人流',u'胃肠镜']
PACU_ALLOW_OPTPYE=[u'麻醉门诊',u'复苏室']

ALLOW_LOCATION=[u'大手术室',u'胃肠镜全麻',u'气管镜',u'日间',u'DSA',u'关节复位',u'双镜',u'抢救插管']
DOCTOR_ALIAS = {u'刑怡安':u'邢怡安',u'＊':u'', u'*':'',u',':u'，'}


DEBUG=1
doctors_dict = dict()
menzhen_dict = dict()
zhiban_dict = dict()

days_list=list()
global src1_df, src2_df, pacu_df, doctors_df

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
    #print perc_df
    weichangjing_num = 0
    for index,row in src1_day_df.iterrows():
        date = row[u'日期']
        op_type = row[u'麻醉类型']
        op_location = row[u'请选择手术地点']
        main_doctor = row[u'麻1（主麻）']
        assistant_doctor = row[u'麻2（副麻）']
        succession_main = row[u'麻3（接班主麻）']
        succession_assistant = row[u'麻4（接班副麻）']

        if op_location == u'胃肠镜全麻':
            weichangjing_num = weichangjing_num +1
            docs = re.split(u'[ ，]', main_doctor)
            menzhen = menzhen_dict[date]
            if pd.notnull(assistant_doctor):
                docs.append(assistant_doctor)

            if pd.notnull(succession_main):
                docs.append(succession_main)

            if pd.notnull(succession_assistant):
                docs.append(succession_assistant)

            for doc in docs:
                num = 1.0/len(docs)
                if doctors_dict[doc] == 3:
                    #perc_df.loc[doc, u'全(主)'] = perc_df.loc[doc, u'全(主)'] + num
                    perc_df.loc[doc, u'全(副)'] = perc_df.loc[doc, u'全(副)'] + num
                else:
                    perc_df.loc[doc, u'全(主)'] = perc_df.loc[doc, u'全(主)'] + num
                    perc_df.loc[doc, u'全(副)'] = perc_df.loc[doc, u'全(副)'] + num

        else:
            if op_type == u'全麻（插管）':
                if pd.notnull(main_doctor):
                    perc_df.loc[main_doctor,u'全(主)'] = perc_df.loc[main_doctor,u'全(主)'] + 1
                if pd.notnull(assistant_doctor):
                    perc_df.loc[assistant_doctor,u'全(副)'] = perc_df.loc[assistant_doctor,u'全(副)'] + 1
            elif op_type == u'全麻（未插管）':
                if pd.notnull(main_doctor):
                    perc_df.loc[main_doctor,u'静(主)'] = perc_df.loc[main_doctor,u'静(主)'] + 1
                if pd.notnull(assistant_doctor):
                    perc_df.loc[assistant_doctor,u'静(副)'] = perc_df.loc[assistant_doctor,u'静(副)'] + 1
            elif op_type == u'腰麻' or op_type == u'腰硬联合' or op_type ==u'硬膜外':
                if pd.notnull(main_doctor):
                    perc_df.loc[main_doctor,u'硬(主)'] = perc_df.loc[main_doctor,u'硬(主)'] + 1
                if pd.notnull(assistant_doctor):
                    perc_df.loc[assistant_doctor,u'硬(副)'] = perc_df.loc[assistant_doctor,u'硬(副)'] + 1
            else:

                if pd.notnull(op_type):
                    print "意外的手术类型:" + op_type
                else:
                    print "手术类型为空"

    #perc_df.to_csv(u"123.csv")
    for index, row in src2_day_df.iterrows():
        op_type = row[u'请选择类型']
        op_num = row[u'总例数']
        pair_num = row[u'全套例数']
        if pd.isna(op_num):
            op_num = 1
        doc1 = row[u'麻1']
        doc2 = row[u'麻2']
        doc3 = row[u'麻3']
        doc4 = row[u'麻4']
        doc5 = row[u'麻5']

        if op_type == u'日间眼科局监' or op_type ==u'2#眼科局监':
            if pd.notnull(doc1):
                perc_df.loc[doc1,u'眼科监护']=perc_df.loc[doc1,u'眼科监护'] + op_num
            else:
                print '麻１　为空'
        elif op_type == u'日间人流':
            if pd.notnull(doc1):
                perc_df.loc[doc1, u'静(主)'] = perc_df.loc[doc1, u'静(主)'] + op_num
            if pd.notnull(doc2):
                perc_df.loc[doc2, u'静(副)'] = perc_df.loc[doc2, u'静(副)'] + op_num
        elif op_type == u'无痛分娩':
            docs = []
            docs.extend(re.split(u'[ ，]', doc1))
            if pd.notnull(doc2):
                docs.extend(re.split(u'[ ，]', doc2))
            for doc in docs:
                perc_df.loc[doc, u'无痛分娩'] = perc_df.loc[doc, u'无痛分娩'] + op_num*1.0/len(docs)
        elif op_type == u'无痛取卵':
            if pd.notnull(doc1):
                perc_df.loc[doc1,u'无痛取卵']=perc_df.loc[doc1,u'无痛取卵'] + op_num
            else:
                print '麻１　为空'

        elif op_type == u'门诊人流':
            if pd.notnull(doc1):
                perc_df.loc[doc1,u'门诊人流']=perc_df.loc[doc1,u'眼科监护'] + op_num
            else:
                print '麻１　为空'
        elif op_type == u'胃肠镜':
            op_num = op_num - pair_num*2
            menzhen = menzhen_dict[date]

            docs = []
            docs.extend(re.split(u'[ ，]', doc1))
            if pd.notnull(doc2):
                docs.extend(re.split(u'[ ，]', doc2))
            if pd.notnull(doc3):
                docs.extend(re.split(u'[ ，]', doc3))
            if pd.notnull(doc4):
                docs.extend(re.split(u'[ ，]', doc4))

            num = op_num*1.0 / len(docs)
            num_par = pair_num*1.0/ len(docs)
            for doc in docs:
                if doctors_dict[doc] == 3:
                    perc_df.loc[doc, u'胃肠镜（单）'] = perc_df.loc[doc, u'胃肠镜（单）'] + num*0.3
                    perc_df.loc[doc, u'胃肠镜（套）'] = perc_df.loc[doc, u'胃肠镜（套）'] + num_par*0.3
                    perc_df.loc[menzhen, u'胃肠镜（单）'] = perc_df.loc[menzhen, u'胃肠镜（单）'] + num * 0.7
                    perc_df.loc[menzhen, u'胃肠镜（套）'] = perc_df.loc[menzhen, u'胃肠镜（套）'] + num_par * 0.7
                else:
                    perc_df.loc[doc, u'胃肠镜（单）'] = perc_df.loc[doc, u'胃肠镜（单）'] + num
                    perc_df.loc[doc, u'胃肠镜（套）'] = perc_df.loc[doc, u'胃肠镜（套）'] + num_par
            print ""
        else:
           print '未知的手术类型:' + op_type

    for index, row in perc_df.iterrows():
        quan_zhu=row[u'全(主)']*216*0.7
        quan_fu = row[u'全(副)']*216*0.3
        ying_zhu = row[u'硬(主)']*60*0.7
        ying_fu = row[u'硬(副)']*60*0.3
        jing_zhu = row[u'静(主)']*80*0.7
        jing_fu = row[u'静(副)']*80*0.3
        wcj_dan = row[u'胃肠镜（单）'] * 40
        wcj_tao = row[u'胃肠镜（套）']*50
        renliu = row[u'门诊人流'] * 80
        quluan = row[u'无痛取卵']*40
        fenmian = row[u'无痛分娩'] * 230
        jianhu = row[u'眼科监护']*19.6
        total = quan_zhu+ quan_fu + ying_zhu + ying_fu + jing_zhu + jing_fu+ wcj_dan + wcj_tao +renliu + quluan+ fenmian+jianhu
        if doctors_dict[index] != 4:
            perc_df.loc[index,u'津贴'] = total
    return perc_df

def calculate_percentage():
    global src1_df, src2_df, pacu_df

    #day_df = src1_df[src1_df[u"日期"] == days_list[0]]
    #calculate_oneday_percentage(day_df)
    writer = pd.ExcelWriter(u'提成.xlsx')

    docs = []
    ids = []
    types = []
    for index, row in doctors_df.iterrows():
        docs.append(unicode(row["name"], "utf-8"))
        ids.append(index)
        types.append(row["doctor_type"])

    num = len(docs)
    huizong_df = pd.DataFrame({u'名字': docs, u'日均':np.zeros(num)})

    for day in days_list:
        src1_day_df = src1_df[src1_df[u"日期"]==day]
        src2_day_df = src2_df[src2_df[u'时间'] == day]
        pacu_day_df = pacu_df[pacu_df[u'时间'] == day]
        mydict = {u'名字': docs,
                  u'医生类型': types, u'全(主)': np.zeros(num),
                  u'全(副)': np.zeros(num), u'硬(主)': np.zeros(num),
                  u'硬(副)': np.zeros(num), u'静(主)': np.zeros(num),
                  u'静(副)': np.zeros(num), u'胃肠镜（单）': np.zeros(num),
                  u'胃肠镜（套）': np.zeros(num), u'门诊人流': np.zeros(num),
                  u'无痛取卵': np.zeros(num), u'无痛分娩': np.zeros(num),
                  u'眼科监护': np.zeros(num),u'津贴': np.zeros(num)}

        columns = [u'名字', u'医生类型', u'全(主)', u'全(副)', u'硬(主)',
                   u'硬(副)', u'静(主)',
                   u'静(副)', u'胃肠镜（单）',u'胃肠镜（套）',
                   u'门诊人流', u'无痛取卵',
                   u'无痛分娩', u'眼科监护',
                   u'津贴']

        perc_df = pd.DataFrame(mydict, columns=columns)

        perc_df = perc_df.set_index(u'名字')
        perc_df.reindex(docs)

        day_result = calculate_oneday_percentage(src1_day_df, src2_day_df, pacu_day_df, perc_df)
        sheet = str(day).split()[0]
        day_result.to_excel(writer, sheet)
        


    writer.save()

    print "提成计算完成：　提成.xlsx"
    return

def src1_check():
    '''检查大帐单一'''
    global src1_df
    success = 1
    print "检查大帐单一 ..."

    for index, row in src1_df.iterrows():

        series = row[u'数据唯一编号']
        date = row[u'日期']
        op_type = row[u'麻醉类型']
        op_location = row[u'请选择手术地点']
        main_doctor = row[u'麻1（主麻）']
        assistant_doctor = row[u'麻2（副麻）']
        succession_main = row[u'麻3（接班主麻）']
        succession_assistant = row[u'麻4（接班副麻）']

        #空行
        if  pd.isnull(date):
            continue
        #手术地点
        if op_location not in ALLOW_LOCATION:
            success = 0
            print series,"不知道的手术地点",op_location
        #麻醉类型检查
        if pd.notnull(op_type) and (op_type not in ALLOW_OPTPYE):
            success = 0
            print series,"不知道的麻醉类型：", op_type

        #主麻醉医生检查
        if pd.notnull(main_doctor) and (main_doctor not in doctors_dict.keys()):
            if op_location == u'胃肠镜全麻':
                docs = re.split(u'[ ，]', main_doctor)
                for doc in docs:
                    if doc not in doctors_dict.keys():
                        success = 0
                        print series,"不识别的麻醉医生：", doc
            elif op_location == u'抢救插管':
                docs = re.split(u'[ ，]', main_doctor)
                for doc in docs:
                    if doc not in doctors_dict.keys():
                        success = 0
                        print series, "不识别的麻醉医生：", doc
            else:
                success = 0
                print series,"不识别的麻醉医生：", main_doctor
            # 副麻醉医生检查
        if pd.notnull(assistant_doctor) and (assistant_doctor not in doctors_dict.keys()):
            success = 0
            print series,"不识别的麻醉医生：", assistant_doctor
            #副麻醉医生检查
        if pd.notnull(succession_main) and (succession_main not in doctors_dict.keys()):
            success = 0
            print series,"不识别的麻醉医生：", succession_main

        # 副麻醉医生检查
        if pd.notnull(succession_assistant) and (succession_assistant not in doctors_dict.keys()):
            success = 0
            print series,"不识别的麻醉医生：", succession_assistant

        if  pd.notnull(op_type) and (op_location != u'胃肠镜全麻'):
            if doctors_dict[main_doctor] == 1 and pd.notnull(assistant_doctor) and doctors_dict[assistant_doctor] == 0:
                success = 0
                print series,"主麻副麻登记错误：",main_doctor, assistant_doctor

    if success:
        print "电子大帐１检查通过"
    return success


def src2_check():
    global src2_df
    success = 1

    print "检查大帐单二 ..."

    for index, row in src2_df.iterrows():
        op_type = row[u'请选择类型']
        series = row[u'数据唯一编号']
        # 麻醉类型检查
        if pd.notnull(op_type) and (op_type not in SRC2_ALLOW_OPTPYE):
            success = 0
            print series,"不知道的麻醉类型：", op_type

        #检查医生
        doctors = []
        if pd.notnull(row[u'麻1']):
            doctor1 = unicode.strip(row[u'麻1'])
            doctors.extend(re.split(u'[ ，]', doctor1))
        else:
            print series+"缺少麻一"

        if pd.notnull(row[u'麻2']):
            doctor1 = unicode.strip(row[u'麻2'])
            doctors.extend(re.split(u'[ ，]', doctor1))

        if pd.notnull(row[u'麻3']):
            doctor1 = unicode.strip(row[u'麻3'])
            doctors.extend(re.split(u'[ ，]', doctor1))

        if pd.notnull(row[u'麻4']):
            doctor1 = unicode.strip(row[u'麻4'])
            doctors.extend(re.split(u'[ ，]', doctor1))

        if pd.notnull(row[u'麻5']):
            doctor1 = unicode.strip(row[u'麻5'])
            doctors.extend(re.split(u'[ ，]', doctor1))

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
        date = row[u'时间']
        op_type=row[u'请选择类型']
        doctor = row[u'复苏人员（出诊人员）']

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

    need_menzhen_days=[]
    for index, row in src1_df.iterrows():
        date = row[u'日期']
        op_location = row[u'请选择手术地点']

        if op_location == u'胃肠镜全麻':
            if date not in need_menzhen_days:
                need_menzhen_days.append(date)
    for index, row in src2_df.iterrows():
        date = row[u'时间']
        op_type = row[u'请选择类型']
        if op_type == u'胃肠镜':
            if date not in need_menzhen_days:
                need_menzhen_days.append(date)

    keys = menzhen_dict.keys()
    success = 1
    for day in need_menzhen_days:
        if day not in keys:
            date = pd.to_datetime(day)
            week = date.weekday()
            if week < 5:
                success = 0
                print date, "星期%d没有值班医生"%(week+1)
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
        print "数据检查未通过"
        exit()
    return

#预处理
def pre_handler():
    global src1_df, src2_df, pacu_df

    print "－－－－预处理－－－－－－"
    print "处理大帐一"
    for index, row in src1_df.iterrows():
        date = row[u'日期']
        main_doctor = row[u'麻1（主麻）']
        assistant_doctor = row[u'麻2（副麻）']
        succession_main = row[u'麻3（接班主麻）']
        succession_assistant = row[u'麻4（接班副麻）']

        # 空行
        if pd.isnull(date):
            src1_df = src1_df.drop([index])
            continue

        if isinstance(main_doctor,unicode):
            changed = 0
            for re in DOCTOR_ALIAS.keys():
                if re in main_doctor:
                    changed = 1
                    main_doctor = main_doctor.replace(re,DOCTOR_ALIAS[re])
            if changed:
                #print row[u'麻1（主麻）']+' -> ' + main_doctor
                src1_df.loc[index,u'麻1（主麻）'] = main_doctor

        if isinstance(assistant_doctor,unicode):
            changed = 0
            for re in DOCTOR_ALIAS.keys():
                if re in assistant_doctor:
                    changed = 1
                    assistant_doctor = assistant_doctor.replace(re,DOCTOR_ALIAS[re])
            if changed:
                #print row[u'麻2（副麻）']+' -> ' + assistant_doctor
                src1_df.loc[index,u'麻2（副麻）'] = assistant_doctor

        if isinstance(succession_main,unicode):
            changed = 0
            for re in DOCTOR_ALIAS.keys():
                if re in succession_main:
                    changed = 1
                    succession_main = succession_main.replace(re,DOCTOR_ALIAS[re])
            if changed:
                src1_df.loc[index,u'麻3（接班主麻）'] = succession_main

        if isinstance(succession_assistant,unicode):
            changed = 0
            for re in DOCTOR_ALIAS.keys():
                if re in succession_assistant:
                    changed = 1
                    succession_assistant = succession_assistant.replace(re,DOCTOR_ALIAS[re])
            if changed:
                src1_df.loc[index,u'麻4（接班副麻）'] = succession_assistant

    print "处理大帐二"
    for index, row in src2_df.iterrows():
        date = row[u'时间']
        doctor1 = row[u'麻1']
        doctor2 = row[u'麻2']
        doctor3 = row[u'麻3']
        doctor4 = row[u'麻4']
        doctor5 = row[u'麻5']

        # 空行
        if pd.isnull(date):
            src2_df = src2_df.drop([index])
            continue

        if isinstance(doctor1, unicode):
            changed = 0
            for re in DOCTOR_ALIAS.keys():
                if re in doctor1:
                    changed = 1
                    doctor1 = doctor1.replace(re, DOCTOR_ALIAS[re])
            if changed:
                src2_df.loc[index, u'麻1'] = doctor1

        if isinstance(doctor2, unicode):
            changed = 0
            for re in DOCTOR_ALIAS.keys():
                if re in doctor2:
                    changed = 1
                    doctor2 = doctor2.replace(re, DOCTOR_ALIAS[re])
            if changed:
                src2_df.loc[index, u'麻2'] = doctor2

        if isinstance(doctor3, unicode):
            changed = 0
            for re in DOCTOR_ALIAS.keys():
                if re in doctor3:
                    changed = 1
                    doctor3 = doctor3.replace(re, DOCTOR_ALIAS[re])
            if changed:
                src2_df.loc[index, u'麻3'] = doctor3

        if isinstance(doctor4, unicode):
            changed = 0
            for re in DOCTOR_ALIAS.keys():
                if re in doctor4:
                    changed = 1
                    doctor4 = doctor4.replace(re, DOCTOR_ALIAS[re])
            if changed:
                src2_df.loc[index, u'麻4'] = doctor4
        if isinstance(doctor5, unicode):
            changed = 0
            for re in DOCTOR_ALIAS.keys():
                if re in doctor5:
                    changed = 1
                    doctor5 = doctor5.replace(re, DOCTOR_ALIAS[re])
            if changed:
                src2_df.loc[index, u'麻5'] = doctor5

    print "处理ＰＡＣＵ"
    for index, row in pacu_df.iterrows():
        date = row[u'时间']
        doctor1 = row[u'复苏人员（出诊人员）']

        # 空行
        if pd.isnull(date):
            pacu_df = pacu_df.drop([index])
            continue

        if isinstance(doctor1, unicode):
            changed = 0
            for re in DOCTOR_ALIAS.keys():
                if re in doctor1:
                    changed = 1
                    doctor1 = doctor1.replace(re, DOCTOR_ALIAS[re])
            if changed:
                pacu_df.loc[index, u'复苏人员（出诊人员）'] = doctor1
    return


#获取值班信息
def getDutyInfo():
    global menzhen_dict
    print '－－－－－获取门诊值班信息－－－'
    for index, row in pacu_df.iterrows():
        date = row[u'时间']
        doctor = row[u'复苏人员（出诊人员）']
        type = row[u'请选择类型']
        if type == u'麻醉门诊' and (date not in menzhen_dict.keys()):
            menzhen_dict[date]=doctor
            print date, doctor


def main(src1,src2,pacu,doctors_list):
    global src1_df, src2_df,pacu_df,doctors_df

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
        date = row[u'日期']
        if (not days_list.__contains__(date)) and (pd.notnull(date)):
            days_list.append(date)

    for index,row in src2_df.iterrows():
        date = row[u'时间']
        if (not days_list.__contains__(date)) and (pd.notnull(date)):
            days_list.append(date)

    for index,row in pacu_df.iterrows():
        date = row[u'时间']
        if (not days_list.__contains__(date)) and (pd.notnull(date)):
            days_list.append(date)

    pre_handler()
    getDutyInfo()
    database_check()
    calculate_percentage()
    return

if __name__ == '__main__':

    src1 = "11月麻醉电子大账（一）_20181123225156.xlsx"
    src2 = "11月麻醉电子大账（二)_20181123224256.xlsx"
    pacu = "11月PACU与麻醉门诊登记_20181123224239.xlsx"
    doctors_list = "doctor_list.csv"

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