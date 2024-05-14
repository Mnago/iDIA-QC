import os.path
import sqlite3

from applet.logger_utils import logger
from applet.obj.DBEntity import RunInfo, RunData, RunDataF4, RunDataS7, PredInfo

db_dir_path = os.path.join(os.getcwd(), 'db')
if not os.path.exists(db_dir_path):
    os.mkdir(db_dir_path)

db_file_path = os.path.join(db_dir_path, 'diaqc.db')

conn = sqlite3.connect(db_file_path, check_same_thread=False)

RUN_DATA_SELECT_COL = 'seq_id, data_tag, data_val'

F4_RUN_DATA_SELECT_COL = 'seq_id, data_index, data_val'

S7_RUN_DATA_SELECT_COL = 'seq_id, data_tag, pept, data_val'


# 插入一条记录
def add_run_info(run_info: RunInfo):
    sql = 'insert into run_info(inst_id, run_id, run_name, file_name, file_type, is_delete) values (?, ?, ?, ?, ?, ?) '
    try:
        c = conn.cursor()
        c.execute(sql, run_info.get_key_val())
        conn.commit()
    except Exception as e:
        logger.exception('add run info error')


# 保存该批次的全部数据
def add_thiz_data(delete_run_name, save_run_info: [RunInfo], save_run_data_list: [RunData],
                  save_run_data_f4: [RunDataF4], save_run_data_s7: [RunDataS7], pred_info_list: [PredInfo]):
    try:
        logger.info('Start save data to db')
        c = conn.cursor()

        if len(delete_run_name) > 0:
            delete_param = ','.join("'" + d + "'" for d in delete_run_name)
            delete_run_info_sql = 'update run_info set is_delete = 1 where run_name in (' + delete_param + ')'
            c.execute(delete_run_info_sql)

        save_run_info_sql = 'insert into run_info(inst_name, run_prefix, run_id, run_name, file_name, file_type, seq_id, state, last_modify_time, file_size, source, is_delete, gmt_create) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime("now","localtime")) '
        batch_insert_run_info_list = []
        for dd in save_run_info:
            batch_insert_run_info_list.append(dd.get_key_val())
        c.executemany(save_run_info_sql, batch_insert_run_info_list)

        # 插入run data
        save_run_data_sql = 'insert into run_data (seq_id, data_tag, data_val) values (?, ?, ?) '
        batch_insert_run_data_list = []
        for dd in save_run_data_list:
            batch_insert_run_data_list.append(dd.get_key_val())
        c.executemany(save_run_data_sql, batch_insert_run_data_list)

        # 插入 run data f4
        save_run_data_f4_sql = 'insert into run_data_f4 (seq_id, data_index, data_val) values (?, ?, ?) '
        batch_insert_run_data_f4_list = []
        for dd in save_run_data_f4:
            batch_insert_run_data_f4_list.append(dd.get_key_val())
        c.executemany(save_run_data_f4_sql, batch_insert_run_data_f4_list)

        # 插入s7 data
        save_run_data_s7_sql = 'insert into run_data_s7 (seq_id, data_tag, pept, data_val) values (?, ?, ?, ?) '
        batch_insert_run_data_s7_list = []
        for dd in save_run_data_s7:
            batch_insert_run_data_s7_list.append(dd.get_key_val())
        c.executemany(save_run_data_s7_sql, batch_insert_run_data_s7_list)

        save_pred_info_sql = 'insert into pred_result(run_id, seq_id, pred_key, pred_score, pred_label) values (?, ?, ?, ?, ?) '
        batch_insert_run_info_list = []
        for pred_info in pred_info_list:
            batch_insert_run_info_list.append(pred_info.get_key_val())
        c.executemany(save_pred_info_sql, batch_insert_run_info_list)

        conn.commit()
        logger.info('Success save data to db')
        return True
    except Exception as e:
        logger.exception('save run data error')
        return False


def query_run_info_list(run_id_list) -> [RunInfo]:
    result_list = []
    param_str = ','.join("'" + run_id + "'" for run_id in run_id_list)
    sql = 'SELECT inst_name, run_id, run_name, file_name, seq_id, file_type, run_prefix, source from run_info where run_id in (' + param_str + ') and is_delete = 0 order by seq_id asc '
    try:
        c = conn.cursor()
        c.execute(sql)
        results = c.fetchall()
        for row in results:
            run_info = RunInfo()
            run_info.inst_name = row[0]
            run_info.run_id = row[1]
            run_info.run_name = row[2]
            run_info.file_name = row[3]
            run_info.seq_id = row[4]
            run_info.file_type = row[5]
            run_info.run_prefix = row[6]
            run_info.source = row[7]
            result_list.append(run_info)
        return result_list
    except Exception as e:
        logger.exception('query query_run_info_list error')


def query_run_info_param(inst_id, limit_num, run_data_type) -> [RunInfo]:
    result_list = []
    param_list = []
    param_list.append(run_data_type)
    if inst_id is None:
        sql = 'SELECT inst_name, run_id, run_name, file_name, seq_id, id, state, file_type, gmt_create, run_prefix from run_info where source = ? and is_delete = 0 order by id desc '
    else:
        sql = 'SELECT inst_name, run_id, run_name, file_name, seq_id, id, state, file_type, gmt_create, run_prefix from run_info where source = ? and inst_name = ? and  is_delete = 0 order by id desc'
        param_list.append(inst_id)

    if limit_num is not None:
        sql = sql + ' limit ? '
        param_list.append(limit_num)

    try:
        c = conn.cursor()
        c.execute(sql, param_list)
        results = c.fetchall()
        for row in results:
            run_info = RunInfo()
            run_info.inst_name = row[0]
            run_info.run_id = row[1]
            run_info.run_name = row[2]
            run_info.file_name = row[3]
            run_info.seq_id = row[4]
            run_info.id = row[5]
            run_info.state = row[6]
            run_info.file_type = row[7]
            run_info.gmt_create = row[8]
            run_info.run_prefix = row[9]
            result_list.append(run_info)
        return result_list
    except Exception as e:
        logger.exception('query query_run_info_param error')


def query_run_info_all(source=1) -> [RunInfo]:
    result_list = []
    sql = 'SELECT inst_name, run_id, run_name, file_name, seq_id, state, file_type, gmt_create, run_prefix from run_info where source = ? and is_delete = 0 '
    try:
        c = conn.cursor()
        c.execute(sql, (source, ))
        results = c.fetchall()
        for row in results:
            run_info = RunInfo()
            run_info.inst_name = row[0]
            run_info.run_id = row[1]
            run_info.run_name = row[2]
            run_info.file_name = row[3]
            run_info.seq_id = row[4]
            run_info.state = row[5]
            run_info.file_type = row[6]
            run_info.gmt_create = row[7]
            run_info.run_prefix = row[8]
            result_list.append(run_info)
        return result_list
    except Exception as e:
        logger.exception('query query_run_info_all error')
        return []


def query_run_data(seq_id_list) -> [RunData]:
    result_list = []
    param_str = ','.join("'" + seq_id + "'" for seq_id in seq_id_list)
    sql = 'SELECT ' + RUN_DATA_SELECT_COL + ' from run_data where seq_id in (' + param_str + ') order by seq_id asc '
    try:
        c = conn.cursor()
        c.execute(sql)
        results = c.fetchall()
        for row in results:
            run_data = convert_run_data(row)
            result_list.append(run_data)
    except Exception as e:
        logger.exception('query query_run_data error')
    return result_list


def query_one_run_data(seq_id) -> [RunData]:
    result_list = []
    sql = 'SELECT ' + RUN_DATA_SELECT_COL + ' from run_data where seq_id = ? '
    try:
        c = conn.cursor()
        c.execute(sql, [seq_id])
        results = c.fetchall()
        for row in results:
            run_data = convert_run_data(row)
            result_list.append(run_data)
    except Exception as e:
        logger.exception('query query_one_run_data error')
    return result_list


def query_run_f4_data(seq_id_list) -> [RunDataF4]:
    result_list = []
    param_str = ','.join("'" + seq_id + "'" for seq_id in seq_id_list)
    sql = 'SELECT ' + F4_RUN_DATA_SELECT_COL + ' from run_data_f4 where seq_id in (' + param_str + ') order by seq_id asc, data_index asc '
    try:
        c = conn.cursor()
        c.execute(sql)
        results = c.fetchall()
        for row in results:
            run_data = convert_run_f4_data(row)
            result_list.append(run_data)
    except Exception as e:
        logger.exception('query query_run_f4_data error')
    return result_list


def query_one_run_f4_data(seq_id) -> [RunDataF4]:
    result_list = []
    sql = 'SELECT ' + F4_RUN_DATA_SELECT_COL + ' from run_data_f4 where seq_id = ? order by seq_id asc, data_index asc '
    try:
        c = conn.cursor()
        c.execute(sql, [seq_id])
        results = c.fetchall()
        for row in results:
            run_data = convert_run_f4_data(row)
            result_list.append(run_data)
    except Exception as e:
        logger.exception('query query_one_run_f4_data error')
    return result_list


def query_run_s7_data(seq_id_list) -> [RunDataS7]:
    result_list = []
    param_str = ','.join("'" + seq_id + "'" for seq_id in seq_id_list)
    sql = 'SELECT ' + S7_RUN_DATA_SELECT_COL + ' from run_data_s7 where seq_id in (' + param_str + ') order by seq_id asc '
    try:
        c = conn.cursor()
        c.execute(sql)
        results = c.fetchall()
        for row in results:
            run_data = convert_run_s7_data(row)
            result_list.append(run_data)
    except Exception as e:
        logger.exception('query query_run_s7_data error')
    return result_list


def query_one_run_s7_data(seq_id) -> [RunDataS7]:
    result_list = []
    sql = 'SELECT ' + S7_RUN_DATA_SELECT_COL + ' from run_data_s7 where seq_id = ? order by seq_id asc '
    try:
        c = conn.cursor()
        c.execute(sql, [seq_id])
        results = c.fetchall()
        for row in results:
            run_data = convert_run_s7_data(row)
            result_list.append(run_data)
    except Exception as e:
        logger.exception('query run info list error')
    return result_list


def query_all_seq_id():
    sql = 'select seq_id from run_info where is_delete = 0'
    seq_id_list = []
    try:
        c = conn.cursor()
        c.execute(sql)
        results = c.fetchall()
        for row in results:
            seq_id_list.append(row[0])
    except Exception as e:
        logger.exception('query run info list error')
    return seq_id_list


def query_all_pred_info(seq_id_list) -> [PredInfo]:
    pred_info_list = []
    param_str = ','.join("'" + seq_id + "'" for seq_id in seq_id_list)
    sql = 'SELECT run_id, pred_key, pred_score, pred_label, seq_id from pred_result where seq_id in (' + param_str + ')'
    try:
        c = conn.cursor()
        c.execute(sql)
        results = c.fetchall()
        for row in results:
            pred_info = PredInfo()
            pred_info.run_id = row[0]
            pred_info.pred_key = row[1]
            pred_info.pred_score = row[2]
            pred_info.pred_label = row[3]
            pred_info.seq_id = row[4]
            pred_info_list.append(pred_info)
    except Exception as e:
        logger.exception('query_all_pred_info error')
    return pred_info_list


'''
转换 run data
'''


def convert_run_data(row):
    run_data = RunData()
    run_data.seq_id = row[0]
    run_data.data_tag = row[1]
    run_data.data_val = row[2]
    return run_data


'''
转换F4数据
'''


def convert_run_f4_data(row):
    run_data = RunDataF4()
    run_data.seq_id = row[0]
    run_data.data_index = row[1]
    run_data.data_val = row[2]
    return run_data


def convert_run_s7_data(row):
    run_data = RunDataF4()
    run_data.seq_id = row[0]
    run_data.data_tag = row[1]
    run_data.pept = row[2]
    run_data.data_val = row[3]
    return run_data
