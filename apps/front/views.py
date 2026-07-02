# -*- coding: utf-8 -*-
import os
import uuid
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor

from flask import (
    Blueprint, redirect, url_for, render_template,
    request, jsonify, make_response, send_file
)

from .models import SampleModel, CacheModel
from .forms import SampleForm, RetrieveForm
from exts import db, csrf

from tools.main import OneForAll
import config


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger("front.views")


bp = Blueprint("front", __name__)
executor = ThreadPoolExecutor(10)


# ========== 异步任务异常回调（避免静默吞异常） ==========
def _task_done_callback(future):
    exc = future.exception()
    if exc is not None:
        logger.error(f"后台预测任务异常: {exc}", exc_info=exc)


# ========== 工具方法 ==========
def get_uuid():
    return str(uuid.uuid1())


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


def parse_result(uuid_str):
    """解析结果 CSV 的前 100 行供前端展示"""
    result_data = []
    result_file = os.path.join(config.PREDICTION_RESULT_PATH, uuid_str + '.csv')
    try:
        if not os.path.isfile(result_file):
            return False
        with open(result_file, 'r', encoding='utf-8') as f:
            lines = [i.strip() for i in f.readlines()]
        count = 0
        for line in lines[1:]:
            if count >= 100:
                break
            count += 1
            parts = line.split(",")
            if len(parts) != 4:
                continue
            result_data.append(parts)
        return result_data
    except Exception as e:
        logger.error(f"parse_result error: {e}")
        return False


def _sample_set_done(uuid_str):
    """把数据库里的 state 置为 1"""
    sample = SampleModel.query.filter_by(sample_name=uuid_str).first()
    if sample and sample.state == 0:
        sample.state = 1
        db.session.commit()


# ===================== 页面路由 =====================
@bp.route('/')
def index():
    return render_template('front/new_home.html')


@bp.route('/batch')
def batch():
    return render_template('front/batch.html')


@bp.route('/download')
def download():
    return render_template('front/download.html')


@bp.route('/help')
def help():
    return render_template('front/help.html')


@bp.route('/about')
def about():
    return render_template('front/about.html')


@bp.route('/detail/<uuid_str>')
def detail(uuid_str):
    done_file = os.path.join(config.PREDICTION_RESULT_PATH, uuid_str + "_done.csv")
    if os.path.isfile(done_file):
        _sample_set_done(uuid_str)

    context = {
        'sample': SampleModel.query.filter_by(sample_name=uuid_str).first(),
        'results': parse_result(uuid_str)
    }
    return render_template('front/detail.html', **context)


@bp.route('/detail/download/<uuid_str>')
def detail_download(uuid_str):
    sample = SampleModel.query.filter_by(sample_name=uuid_str).first()
    csv_path = os.path.join(config.PREDICTION_RESULT_PATH, uuid_str + ".csv")

    if sample and sample.state == 1 and os.path.isfile(csv_path):
        response = make_response(send_file(csv_path, as_attachment=True))
        response.headers["Content-Disposition"] = \
            "attachment; filename={};".format(uuid_str + ".csv")
        return response
    return jsonify({'code': 400, 'msg': "The task does not exist or has expired."})


# ===================== API：状态查询（新增，给前端轮询用） =====================
@csrf.exempt
@bp.route('/api/status/<uuid_str>')
def api_status(uuid_str):
    """返回任务当前状态：0 处理中 / 1 已完成 / -1 失败"""
    done_file = os.path.join(config.PREDICTION_RESULT_PATH, uuid_str + "_done.csv")
    err_file  = os.path.join(config.PREDICTION_RESULT_PATH, uuid_str + "_error.log")

    if os.path.isfile(done_file):
        _sample_set_done(uuid_str)
        if os.path.isfile(err_file):
            return jsonify({'code': 200, 'state': -1, 'msg': 'prediction error'})
        return jsonify({'code': 200, 'state': 1})
    return jsonify({'code': 200, 'state': 0})


# ===================== API：文本提交（旧接口，保留） =====================
@csrf.exempt
@bp.route('/api/predict', methods=['POST'])
def predict():
    form = SampleForm(request.form)
    if not form.validate():
        return jsonify({'code': 400, 'msg': form.get_error()})

    sample_name = get_uuid()
    sample_content = form.content.data

    sample_hash = hash(sample_content)
    cache = CacheModel.query.filter_by(hash=sample_hash).first()
    if cache:
        return jsonify({'code': 200, 'data': cache.sample_name})

    try:
        with open(os.path.join(config.SAMPLE_PATH_OLD, sample_name + ".fasta"),
                  'w', encoding='utf-8') as f:
            f.write(sample_content)
    except Exception as e:
        logger.error(f"Save sample failed: {e}")
        return jsonify({'code': 400, 'msg': "Problems with data storage."})

    # 异步 + 异常回调
    future = executor.submit(OneForAll(sample_name).run)
    future.add_done_callback(_task_done_callback)

    db.session.add(SampleModel(
        sample_name=sample_name,
        sample_path=os.path.join(config.SAMPLE_PATH_OLD, sample_name + ".fasta"),
        reverse_state=0
    ))
    db.session.add(CacheModel(hash=sample_hash, sample_name=sample_name))
    db.session.commit()
    return jsonify({'code': 200, 'data': sample_name})


# ===================== API：物种特异性预测 =====================
@csrf.exempt
@bp.route('/api/file_predict', methods=['POST'])
def file_predict():
    return _handle_predict_request(mode='species')


# ===================== API：通用预测 =====================
@csrf.exempt
@bp.route('/api/uploadMamba', methods=['POST'])
def upload_mamba():
    return _handle_predict_request(mode='general')


def _handle_predict_request(mode='species'):
    """
    统一处理两种预测接口
    支持：文件上传 (type=1) / 序列粘贴 (type=0)
    """
    sample_name = get_uuid()
    submit_type = request.form.get('type', '1')
    species = request.form.get('species', '')

    sample_content = None
    sample_str = None

    # ---------- 取数据 ----------
    if submit_type == '1':
        if 'file' not in request.files:
            return jsonify({'code': 400, 'msg': 'No file uploaded'})
        file = request.files['file']
        if not file or not allowed_file(file.filename):
            return jsonify({'code': 400,
                            'msg': "The file is wrong or the extension is not allowed (.fasta)."})
        sample_content = file.read()
        try:
            sample_str = sample_content.decode('utf-8')
        except UnicodeDecodeError:
            sample_str = sample_content.decode('latin-1')
    else:
        seq = request.form.get('seq', '')
        if not seq or not seq.strip():
            return jsonify({'code': 400, 'msg': 'No sequence provided'})
        sample_str = seq.strip()
        sample_content = sample_str.encode('utf-8')

    # ---------- 缓存 ----------
    sample_hash = hash(sample_str)
    cache = CacheModel.query.filter_by(hash=sample_hash).first()
    if cache:
        return jsonify({'code': 200, 'data': cache.sample_name})

    # ---------- 落盘 ----------
    os.makedirs(config.SAMPLE_PATH_OLD, exist_ok=True)
    sample_path = os.path.join(config.SAMPLE_PATH_OLD, sample_name + ".fasta")
    try:
        with open(sample_path, 'wb') as f:
            f.write(sample_content)
    except Exception as e:
        logger.error(f"Save file failed: {e}")
        return jsonify({'code': 400, 'msg': "Problems with data storage."})

    # ---------- 异步提交（带异常回调） ----------
    try:
        future = executor.submit(OneForAll(sample_name, species=species).run)
        future.add_done_callback(_task_done_callback)
        logger.info(f"[{sample_name}] task submitted, mode={mode}, species={species}")
    except Exception as e:
        logger.error(f"Submit task failed: {e}\n{traceback.format_exc()}")
        return jsonify({'code': 400, 'msg': f'Submit task failed: {e}'})

    # ---------- 入库 ----------
    db.session.add(SampleModel(
        sample_name=sample_name,
        sample_path=sample_path,
        reverse_state=0
    ))
    db.session.add(CacheModel(hash=sample_hash, sample_name=sample_name))
    db.session.commit()

    return jsonify({'code': 200, 'data': sample_name})


# ===================== API：检索任务 =====================
@csrf.exempt
@bp.route('/api/retrieve', methods=['POST'])
def retrieve():
    form = RetrieveForm(request.form)
    if form.validate():
        return jsonify({'code': 200, 'id': form.uuid.data})
    return jsonify({'code': 400, 'msg': form.get_error()})


# ===================== API：手动更新 state（兼容旧接口） =====================
@bp.route('/api/update/<uuid_str>')
def sample_update(uuid_str):
    sample = SampleModel.query.filter_by(sample_name=uuid_str).first()
    if sample:
        sample.state = 1
        db.session.commit()
        return jsonify({'code': 200, 'msg': "success"})
    return jsonify({'code': 400})