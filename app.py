import os
from flask import Flask, request, render_template
from flask_bootstrap import Bootstrap
import pickle
import nltk
import logging
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
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
            
            return render_template('results.html', 
                               prediction=my_prediction, 
                               name=namequery)
                               
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return render_template('error.html', 
                               message="حدث خطأ أثناء المعالجة"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', 
            port=int(os.environ.get('PORT', 5000)), 
            debug=False)
