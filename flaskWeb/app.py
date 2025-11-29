import os
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image, ExifTags

# --- Configuration ---
# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 照片上传目录，存储在 static 文件夹下
UPLOAD_FOLDER_NAME = 'photos'
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', UPLOAD_FOLDER_NAME)
# 元数据文件路径，用于代替数据库
METADATA_FILE = os.path.join(BASE_DIR, 'metadata.json')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# 定义未知的地点常量（小写）
UNKNOWN_LOCATION_LOWER = '未知地点'.lower()

# 初始化 Flask 应用
app = Flask(__name__) 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 确保上传目录和元数据文件存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(METADATA_FILE):
    # 如果元数据文件不存在，创建一个空的列表
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

# --- EXIF Extraction Helper ---

def get_exif_datetime(filepath):
    """
    尝试从照片文件中提取拍摄时间 (DateTimeOriginal)。
    返回格式: YYYY-MM-DDTHH:MM (兼容 datetime-local input) 或 None
    """
    print(f"[DEBUG] 尝试从文件: {os.path.basename(filepath)} 提取 EXIF...")
    try:
        img = Image.open(filepath)
        exif_data = img._getexif()
        
        if exif_data is None:
            print("[DEBUG] EXIF 提取失败: 文件不包含 EXIF 数据。")
            return None

        # 找到 EXIF 标签的对应名称
        exif = {
            ExifTags.TAGS[k]: v
            for k, v in exif_data.items()
            if k in ExifTags.TAGS
        }
        
        # 查找原始拍摄时间 (DateTimeOriginal) 或数字化时间
        datetime_original = exif.get('DateTimeOriginal') or exif.get('DateTimeDigitized')
        
        if datetime_original:
            print(f"[DEBUG] 原始 EXIF 时间字符串: {datetime_original}")
            # EXIF时间格式通常是 "YYYY:MM:DD HH:MM:SS"
            try:
                dt = datetime.strptime(datetime_original, '%Y:%m:%d %H:%M:%S')
                # 转换为前端需要的 "YYYY-MM-DDTHH:MM" 格式
                formatted_time = dt.strftime('%Y-%m-%dT%H:%M')
                print(f"[DEBUG] EXIF 提取成功，格式化时间: {formatted_time}")
                return formatted_time
            except ValueError:
                print("[DEBUG] EXIF 提取失败: 时间格式不匹配 (预期: YYYY:MM:DD HH:MM:SS)。")
                return None
        else:
            print("[DEBUG] EXIF 提取失败: 找不到 'DateTimeOriginal' 或 'DateTimeDigitized' 标签。")


    except Exception as e:
        print(f"[ERROR] 读取 EXIF 数据时发生异常: {e}")
        return None

    return None

# --- Helper Functions for Metadata Management ---

def load_metadata():
    """从 JSON 文件加载所有照片元数据"""
    if not os.path.exists(METADATA_FILE):
        return []
    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 确保时间戳是整数，方便排序和比较
            for item in data:
                if 'timestamp' not in item:
                    try:
                        # 尝试从 time 字段解析时间戳
                        dt = datetime.strptime(item.get('time', '2000-01-01T00:00'), '%Y-%m-%dT%H:%M')
                        item['timestamp'] = int(dt.timestamp())
                    except:
                        item['timestamp'] = 0 # 无法解析的日期使用0
            return data
    except (json.JSONDecodeError, IOError):
        # 如果文件为空或损坏，返回空列表并尝试修复
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return []

def save_metadata(metadata):
    """将照片元数据保存到 JSON 文件"""
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)

def allowed_file(filename):
    """检查文件扩展名是否合法"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Routes ---

@app.route('/')
def index():
    """主页：照片上传、查询和展示界面"""
    # Flask 将在默认的 'templates/' 文件夹中查找 'index.html'
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理照片上传请求"""
    if 'photo' not in request.files:
        return '未选择文件', 400
    
    file = request.files['photo']
    capture_time_form = request.form.get('capture_time') # 用户输入的表单时间
    location_form = request.form.get('location') # 用户输入的表单地点

    if file.filename == '':
        return '未选择文件', 400

    if file and allowed_file(file.filename):
        # 确保文件名安全
        filename = secure_filename(file.filename)
        # 为防止重名，加上时间戳前缀
        unique_filename = f"{int(time.time())}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        try:
            # 1. 保存文件
            file.save(filepath)

            # 2. 尝试提取 EXIF 时间
            exif_time = get_exif_datetime(filepath)
            
            # 3. 确定最终的拍摄时间和地点
            # 优先级: EXIF时间 > 用户输入时间 > 当前时间
            if exif_time:
                final_capture_time = exif_time
                print("[DEBUG] 采用 EXIF 提取的时间。")
            elif capture_time_form:
                final_capture_time = capture_time_form
                print("[DEBUG] 采用用户手动输入的时间。")
            else:
                # 如果都没有，使用上传时的当前时间
                final_capture_time = datetime.now().strftime('%Y-%m-%dT%H:%M')
                print("[DEBUG] 采用当前上传时间。")

            # 优先级: 用户输入地点 > 默认值 (如果未输入，则设为“未知地点”)
            final_location = location_form if location_form else '未知地点'
            print(f"[DEBUG] 最终地点: {final_location}")

            # 4. 解析时间并计算时间戳
            dt = datetime.strptime(final_capture_time, '%Y-%m-%dT%H:%M')
            timestamp = int(dt.timestamp())

            # 5. 更新元数据
            metadata = load_metadata()
            new_entry = {
                'filename': unique_filename,
                'time': final_capture_time,
                'location': final_location,
                # 使用 url_for 来构建正确的静态文件 URL
                'path': url_for('static', filename=f'{UPLOAD_FOLDER_NAME}/{unique_filename}'),
                'timestamp': timestamp
            }
            metadata.append(new_entry)
            save_metadata(metadata)

            return redirect(url_for('index'))
        except Exception as e:
            # 如果是 Pillow 库加载失败，这里会报错。
            return f'文件上传或保存元数据失败: {str(e)}。请检查 Pillow 库是否安装。', 500
    
    return '文件类型不允许', 400

@app.route('/api/photos', methods=['GET'])
def get_photos():
    """
    照片查询 API，根据时间和地点进行过滤和排序。
    查询参数:
    - location: 地点关键词 (string)
    - start_time: 开始时间 (ISO datetime string, e.g., 2023-10-26T00:00)
    - end_time: 结束时间 (ISO datetime string)
    - sort_order: 排序方式 ('asc' 顺序/默认, 'desc' 倒序)
    
    新增逻辑: 如果查询关键词非精确匹配 '未知地点'，则排除所有地点为 '未知地点' 的照片。
    """
    metadata = load_metadata()
    
    # 1. 过滤
    location_filter = request.args.get('location', '').strip().lower()
    start_time_str = request.args.get('start_time')
    end_time_str = request.args.get('end_time')

    filtered_photos = metadata
    
    # 按地点过滤 (新增精确排除逻辑)
    if location_filter:
        final_filtered_photos = []
        for p in filtered_photos:
            photo_location_lower = p.get('location', '').lower()

            # Rule 1: 如果照片地点是 '未知地点'，只有在查询关键词精确匹配时才包含它
            if photo_location_lower == UNKNOWN_LOCATION_LOWER:
                if location_filter == UNKNOWN_LOCATION_LOWER:
                    final_filtered_photos.append(p)
            # Rule 2: 如果照片地点不是 '未知地点'，使用原有的包含匹配逻辑
            elif location_filter in photo_location_lower:
                final_filtered_photos.append(p)
                
        filtered_photos = final_filtered_photos
        
    # 按时间范围过滤
    if start_time_str or end_time_str:
        start_ts = None
        end_ts = None
        
        try:
            if start_time_str:
                # 假设 start_time 总是从当天的 00:00:00 开始
                start_dt = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
                start_ts = int(start_dt.timestamp())
            if end_time_str:
                # 假设 end_time 总是到当天的 23:59:59 结束 (虽然此处只需要精确到分钟)
                end_dt = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
                end_ts = int(end_dt.timestamp())
        except ValueError:
            # 如果时间格式不正确，记录错误但跳过时间过滤
            print("Warning: Invalid date format received for time filtering.")
            pass 

        if start_ts is not None or end_ts is not None:
            final_filtered_photos = []
            for photo in filtered_photos:
                ts = photo.get('timestamp')
                if ts is None:
                    continue
                
                # 检查时间范围
                is_after_start = start_ts is None or ts >= start_ts
                is_before_end = end_ts is None or ts <= end_ts
                
                if is_after_start and is_before_end:
                    final_filtered_photos.append(photo)
            filtered_photos = final_filtered_photos

    # 2. 排序
    sort_order = request.args.get('sort_order', 'asc') # 默认顺序
    
    # 始终按照时间戳进行排序
    reverse_sort = (sort_order == 'desc')
    
    # 使用时间戳进行排序
    # 确保每个元素都有一个 timestamp 键，以防 load_metadata 失败
    filtered_photos.sort(key=lambda x: x.get('timestamp', 0), reverse=reverse_sort)

    # 3. 返回结果 (移除时间戳，因为前端不需要)
    return jsonify([{k: v for k, v in p.items() if k != 'timestamp'} for p in filtered_photos])

if __name__ == '__main__':
    # 打印标准路径信息，帮助用户确认文件结构
    print("-" * 60)
    print("--- 启动 Flask Web 服务器 ---")
    print(f"项目根目录: {BASE_DIR}")
    print(f"静态照片目录: {UPLOAD_FOLDER}")
    print("------------------------------------------------------------")
    app.run(debug=True)