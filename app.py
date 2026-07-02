print("=== app.py is being executed ===")
from flask import Flask
import config
from apps.front import bp as front_bp
from exts import db, csrf
from gevent import pywsgi
from flask import Flask, request, jsonify,send_file,render_template
import json
import requests
from flask_cors import CORS
import sys

app = Flask(__name__)
CORS(app)  # 允许跨域请求
app.config.from_object(config)
app.register_blueprint(front_bp)

db.init_app(app)
csrf.init_app(app)

with app.app_context():
    db.create_all()

# --------------------修改部分-------------------：
# 你的大模型配置
api_key = "Bearer VzicVmTUqlgBEpFAozPr:CUFUXgdCCxyLOamZxhsU"
url = "https://spark-api-open.xf-yun.com/v2/chat/completions"

# 管理对话历史
chat_history = []

def get_answer(messages):
    headers = {
        'Authorization': api_key,
        'content-type': "application/json"
    }
    body = {
        "model": "x1",
        "user": "user_id",
        "messages": messages,
        "stream": True,
        "tools": [
            {
                "type": "web_search",
                "web_search": {
                    "enable": True,
                    "search_mode": "deep"
                }
            }
        ]
    }
    
    full_response = ""
    is_first_content = True

    response = requests.post(url=url, json=body, headers=headers, stream=True)
    for chunks in response.iter_lines():
        if chunks and '[DONE]' not in str(chunks):
            data_org = chunks[6:]
            try:
                chunk = json.loads(data_org)
                text = chunk['choices'][0]['delta']
                
                if 'reasoning_content' in text and text['reasoning_content']:
                    print(text['reasoning_content'], end="")
                
                if 'content' in text and text['content']:
                    if is_first_content:
                        print("\n*******************以上为思维链内容，模型回复内容如下********************\n")
                        is_first_content = False
                    print(text['content'], end="")
                    full_response += text['content']
            except json.JSONDecodeError:
                continue
    
    return full_response

def get_text(role, content):
    return {"role": role, "content": content}

def get_length(messages):
    return sum(len(msg["content"]) for msg in messages)

def check_len(messages):
    while get_length(messages) > 11000:
        messages.pop(0)
    return messages

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # 验证请求数据
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        data = request.get_json()
        user_message = data.get('message')
        
        # 初始状态 - 用户尚未输入任何内容
        if not user_message:
            return jsonify({
                "status": "success",
                "response": "Hello, I am an AI assistant focusing on gene sequence analysis. Do you have any questions about gene sequences, DNA, RNA, or related fields?"
            })
        
        # 检查是否为字符串
        if not isinstance(user_message, str):
            return jsonify({"error": "Invalid message format"}), 400
            
        # 调试输出
        print(f"Received message: {user_message}")
        
        # 定义基因相关关键词列表
        gene_keywords = [
            '基因序列', '基因', 'DNA', 'RNA', '基因组', '碱基', '测序',
            '转录', '翻译', '非编码RNA', 'ncRNA', '转录组', '外显子',
            '内含子', '启动子', 'ORF', 'CDS', 'UTR', 'miRNA',
            'siRNA', 'lncRNA', 'circRNA', '甲基化', '突变',
            'SNP', 'Indel', '变异', '表达量', '比对', '组装',
            '注释', 'BLAST', 'FASTA', 'FASTQ', 'NGS', '高通量测序','蛋白质序列', '蛋白质', '氨基酸', '肽链', '残基', '多肽',
    '蛋白结构', '一级结构', '二级结构', '三级结构', '四级结构',
    '结构域', '基序', '折叠', 'α螺旋', 'β折叠', '无规则卷曲',
    '信号肽', '跨膜区', '活性位点', '同源建模', '分子对接',
    '质谱', '蛋白测序', 'Edman降解', '翻译后修饰', '磷酸化',
    '糖基化', '泛素化', '蛋白质组', '蛋白质组学', 'SDS-PAGE',
    'Western blot', 'ELISA', '亲和层析', '结晶', 'X射线衍射',
    'NMR', '冷冻电镜', 'UniProt', 'PDB', 'FASTA', 'BLAST',
    '比对', '注释', '突变', '变异', '表达量', '相互作用'
        ]
        
        # 检查用户输入是否包含基因相关关键词
        contains_gene_keyword = any(
            keyword.lower() in user_message.lower() 
            for keyword in gene_keywords
        )
        
        # 如果不包含基因相关关键词
        if not contains_gene_keyword:
            return jsonify({
                "status": "success",
                "response": "Sorry, please change to another question about gene sequences or related fields ~"
            })
        
        # 调用大模型API获取回答
        messages = [{"role": "user", "content": user_message}]
        ai_response = get_answer(messages)
        
        return jsonify({
            "status": "success",
            "response": ai_response
        })
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return render_template('front/index.html')
# --------------------修改部分结束-----------------------




if __name__ == '__main__':
    app.run(host="127.0.0.1",port=5012,debug=True)
    # server = pywsgi.WSGIServer(('0.0.0.0',5002),app)
    # server.serve_forever()
