from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from flask_cors import CORS
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'money-tracker-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@db/money_tracker?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 启用 CORS
CORS(app)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 请求验证中间件
@app.before_request
def validate_request():
    # 只对API请求进行验证
    if request.path.startswith('/') and request.method in ['POST', 'PUT', 'PATCH']:
        # 检查Content-Type
        if not request.is_json and request.path not in ['/health', '/']:
            logger.warning(f"非JSON请求: {request.path} from {request.remote_addr}")
            return jsonify({'message': '请求格式错误，需要JSON格式'}), 400
        
        # 检查请求大小
        if request.content_length and request.content_length > 1024 * 1024:  # 1MB限制
            logger.warning(f"请求过大: {request.content_length} bytes from {request.remote_addr}")
            return jsonify({'message': '请求数据过大'}), 413

db = SQLAlchemy(app)

# 数据库模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    records = db.relationship('Record', backref='user', lazy=True)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# JWT验证装饰器
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
            
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.filter_by(id=data['id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
        
    return decorated

# 健康检查端点
@app.route('/health', methods=['GET'])
def health_check():
    try:
        # 测试数据库连接
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'healthy', 'message': 'Backend is running', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'message': 'Backend is running', 'database': 'disconnected', 'error': str(e)}), 500

# 添加根路径测试
@app.route('/', methods=['GET'])
def root():
    return jsonify({'message': 'Flask backend is running', 'endpoints': ['/health', '/register', '/login', '/records', '/record', '/record/<id> (DELETE)']})

# API路由
@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # 检查数据库连接
        db.session.execute(text('SELECT 1'))
        
        data = request.get_json()
        print(f"注册请求数据: {data}")  # 调试信息
        
        if not data:
            print("未收到JSON数据")
            return jsonify({'message': '请求数据格式错误'}), 400
            
        if not data.get('username') or not data.get('password'):
            print("用户名或密码为空")
            return jsonify({'message': '用户名和密码不能为空'}), 400
        
        username = data.get('username').strip()
        password = data.get('password')
        
        print(f"处理用户注册: {username}")
        
        # 验证用户名长度
        if len(username) > 50:
            return jsonify({'message': '用户名长度不能超过50个字符'}), 400
        
        # 检查用户是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"用户名 {username} 已存在")
            return jsonify({'message': '用户名已存在'}), 400
        
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        print(f"用户 {username} 注册成功")  # 调试信息
        return jsonify({'message': '注册成功！'})
        
    except Exception as e:
        db.session.rollback()
        print(f"注册错误详情: {type(e).__name__}: {str(e)}")  # 更详细的错误信息
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'注册失败: {str(e)}'}), 500

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # 检查数据库连接
        db.session.execute(text('SELECT 1'))
        
        auth = request.get_json()
        print(f"登录请求数据: {auth}")
        
        if not auth:
            return jsonify({'message': '请求数据格式错误'}), 400
            
        if not auth.get('username') or not auth.get('password'):
            return jsonify({'message': '用户名和密码不能为空'}), 400
        
        username = auth.get('username').strip()
        password = auth.get('password')
        
        print(f"用户登录尝试: {username}")
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"用户 {username} 不存在")
            return jsonify({'message': '用户名或密码错误'}), 401
            
        if not check_password_hash(user.password, password):
            print(f"用户 {username} 密码错误")
            return jsonify({'message': '用户名或密码错误'}), 401
        
        token = jwt.encode({'id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm='HS256')
        print(f"用户 {username} 登录成功")
        return jsonify({'token': token})
        
    except Exception as e:
        print(f"登录错误详情: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'登录失败: {str(e)}'}), 500

@app.route('/records', methods=['GET'])
@token_required
def get_records(current_user):
    try:
        print(f"获取用户 {current_user.id} 的记录")
        records = Record.query.filter_by(user_id=current_user.id).all()
        output = []
        for record in records:
            record_data = {
                'id': record.id,
                'amount': record.amount,
                'category': record.category,
                'description': record.description or '',
                'date': record.date.isoformat() if record.date else None
            }
            output.append(record_data)
        print(f"返回 {len(output)} 条记录")
        return jsonify({'records': output})
    except Exception as e:
        print(f"获取记录错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'获取记录失败: {str(e)}'}), 500

@app.route('/record', methods=['POST'])
@token_required
def add_record(current_user):
    try:
        data = request.get_json()
        print(f"添加记录数据: {data}")
        
        if not data:
            return jsonify({'message': '请求数据格式错误'}), 400
        
        amount = data.get('amount')
        category = data.get('category')
        description = data.get('description', '')
        
        if amount is None or not category:
            return jsonify({'message': '金额和类别不能为空'}), 400
        
        new_record = Record(
            amount=float(amount),
            category=category,
            description=description,
            user_id=current_user.id
        )
        db.session.add(new_record)
        db.session.commit()
        print(f"用户 {current_user.id} 添加记录成功")
        return jsonify({'message': '记录添加成功！'})
    except Exception as e:
        db.session.rollback()
        print(f"添加记录错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'添加记录失败: {str(e)}'}), 500

@app.route('/record/<int:record_id>', methods=['DELETE'])
@token_required
def delete_record(current_user, record_id):
    try:
        print(f"用户 {current_user.id} 尝试删除记录 {record_id}")
        
        # 查找记录，确保只能删除自己的记录
        record = Record.query.filter_by(id=record_id, user_id=current_user.id).first()
        
        if not record:
            print(f"记录 {record_id} 不存在或不属于用户 {current_user.id}")
            return jsonify({'message': '记录不存在或无权限删除'}), 404
        
        db.session.delete(record)
        db.session.commit()
        print(f"用户 {current_user.id} 成功删除记录 {record_id}")
        return jsonify({'message': '记录删除成功！'})
        
    except Exception as e:
        db.session.rollback()
        print(f"删除记录错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'删除记录失败: {str(e)}'}), 500

def init_db():
    """初始化数据库"""
    import time
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            with app.app_context():
                db.create_all()
                print("数据库初始化成功")
                break
        except Exception as e:
            retry_count += 1
            print(f"数据库连接失败，重试 {retry_count}/{max_retries}: {e}")
            time.sleep(2)
    
    if retry_count >= max_retries:
        print("数据库连接失败，退出程序")
        exit(1)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)