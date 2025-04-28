import os
from flask import Flask,session, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
import pickle
import nltk
import logging
import sqlite3

from src.cleaning import process_text
from src.prediction import get_predictions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
Bootstrap(app)

# Download NLTK data
try:
    nltk.download('stopwords', download_dir='/tmp/nltk_data')
    nltk.download('punkt', download_dir='/tmp/nltk_data')
    nltk.data.path.append('/tmp/nltk_data')
    logger.info("NLTK data downloaded successfully")
except Exception as e:
    logger.error(f"Error downloading NLTK data: {str(e)}")

# Load models with error handling
try:
    model_path = os.path.join(os.path.dirname(__file__), "models/lr_final_model.pkl")
    transformer_path = os.path.join(os.path.dirname(__file__), "models/transformer.pkl")
    
    loaded_model = pickle.load(open(model_path, 'rb'))
    loaded_transformer = pickle.load(open(transformer_path, 'rb'))
    logger.info("Models loaded successfully")
except Exception as e:
    logger.error(f"Error loading models: {str(e)}")
    loaded_model = None
    loaded_transformer = None

# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "project.db")

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            return redirect(url_for('about'))
        else:
            error = 'اسم المستخدم أو كلمة السر غير صحيحة'

    return render_template('login.html', error=error)

# Admin login
@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (username, password))
        admin = cursor.fetchone()
        conn.close()

        if admin:
            return redirect(url_for('admin'))
        else:
            error = 'اسم المستخدم أو كلمة السر غير صحيحة'

    return render_template('login.html', error=error)

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Test page
@app.route('/try')
def about():
    return render_template('test.html')

# Admin page
@app.route('/admin')
def admin():
    return render_template('admin.html')

# Payment page
@app.route('/payment')
def pay():
    return render_template('payment.html')

# Prediction route
@app.route('/try', methods=['POST'])
def predict():
    if request.method == 'POST':
        try:
            namequery = request.form['namequery']
            logger.info(f"Processing query: {namequery}")
            
            if not namequery.strip():
                return render_template('error.html', message="الرجاء إدخال نص")
                
            data = [namequery]
            clean_data = process_text(str(data))
            
            if not clean_data:
                return render_template('error.html', message="فشل معالجة النص")
                
            test_features = loaded_transformer.transform([" ".join(clean_data)])
            my_prediction = get_predictions(loaded_model, test_features)
            
            return render_template('test.html', 
                               prediction=my_prediction, 
                               name=namequery)
                               
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return render_template('error.html', 
                               message="حدث خطأ أثناء المعالجة"), 500


@app.route('/payment', methods=['POST'])
def process_subscription():
    if request.method == 'POST':
        try:
            # استلام القيم من النموذج
            full_name = request.form['full_name']
            card_number = request.form['card_number']
            expiry_date = request.form['expiry_date']
            cvv = request.form['cvv']
            phone_number = request.form['phone_number']
            subscription_price = request.form['subscription_price']
            subscription_duration = request.form['subscription_duration']
            
            # التحقق من ملء جميع الحقول
            if not all([full_name, card_number, expiry_date, cvv, phone_number, subscription_price, subscription_duration]):
                return render_template('error.html', message="يجب ملء جميع الحقول")
            
            # الاتصال بقاعدة البيانات
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO subscriptions(full_name, card_number, expiry_date, cvv, phone_number, subscription_price, subscription_duration)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (full_name, card_number, expiry_date, cvv, phone_number, subscription_price, subscription_duration))
            conn.commit()
            conn.close()


            # إعادة التوجيه إلى الصفحة 'about'
            return redirect(url_for('about',subscription_duration=subscription_duration))

        except Exception as e:
            # التعامل مع الأخطاء
            logger.error(f"Subscription processing error: {str(e)}")
            return render_template('error.html', message="حدث خطأ أثناء تسجيل الاشتراك"), 500
        
@app.route('/table_detection')
def table_detection ():
    return render_template('table_detection.html')

@app.route('/table_crowdsource')
def table_crowdsource ():
    return render_template('/Crowdsourced_table.html')

@app.route('/table_user')
def table_user ():
    return render_template('table_user.html')

        
@app.route('/crowd')
def  crowd():
    return render_template('Crowdsourced.html')


@app.route('/crowd', methods=['GET', 'POST'])
def process_report():
    if request.method == 'POST':
        try:
            # استلام القيم من النموذج
            content_type = request.form['contentType']
            justification = request.form['justification']
            
            # معالجة المحتوى حسب النوع
            if content_type == 'image':
                # معالجة تحميل الصورة
                if 'imageInput' not in request.files:
                    return render_template('error.html', message="لم يتم تحميل صورة")
                
                file = request.files['imageInput']
                if file.filename == '':
                    return render_template('error.html', message="لم يتم اختيار صورة")
                
                # حفظ الملف
                upload_folder = 'static/uploads'
                os.makedirs(upload_folder, exist_ok=True)
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                
                content_data = file_path
            else:  # نص
                content_data = request.form.get('textInput', '')
                if not content_data:
                    return render_template('error.html', message="يجب إدخال النص")
            
            # التحقق من ملء جميع الحقول
            if not all([content_type, content_data, justification]):
                return render_template('error.html', message="يجب ملء جميع الحقول")
            
            # الاتصال بقاعدة البيانات
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
           
            # إدخال البيانات
            cursor.execute('''
                INSERT INTO reports(content_type, content_data, justification)
                VALUES (?, ?, ?)
            ''', (content_type, content_data, justification))
            
            conn.commit()
            conn.close()

            flash('تم إرسال التقرير بنجاح!', 'success')
            return redirect(url_for('about'))
            
        except Exception as e:
            return render_template('error.html', message=f"حدث خطأ: {str(e)}")
    
    # إذا كانت الطريقة GET، عرض النموذج
    return render_template('/try')




if __name__ == '__main__':
    app.run(host='0.0.0.0', 
            port=int(os.environ.get('PORT', 5000)), 
            debug=False)