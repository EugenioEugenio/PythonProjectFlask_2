import os
import pandas as pd
from flask import Flask, request, jsonify, abort
from werkzeug.utils import secure_filename
from config import Config
from database import db, AnalysisResult
import numpy as np

from psycopg2.extensions import register_adapter, AsIs

def adapt_numpy_float(numpy_float):
    return AsIs(numpy_float)

register_adapter(np.float32, adapt_numpy_float)
register_adapter(np.float64, adapt_numpy_float)

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Убедитесь, что папка для загрузки существует
if not os.path.exists(Config.UPLOAD_FOLDER):
    os.makedirs(Config.UPLOAD_FOLDER)

# Создание таблиц БД при первом запуске (можно вынести в отдельный скрипт миграций)
with app.app_context():
    db.create_all()

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def analyze_data(filepath):
    """Загрузка и анализ данных с помощью Pandas."""
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filepath.endswith('.xlsx') or filepath.endswith('.xls'):
            df = pd.read_excel(filepath)
        else:
            return None

        # Пример анализа:
        # Предполагаем, что в файле есть столбцы 'A' и 'B'
        if 'A' in df.columns and 'B' in df.columns:
            mean_val = df['A'].mean()
            median_val = df['A'].median()
            correlation = df['A'].corr(df['B'])
            return mean_val, median_val, correlation
        else:
            # Или просто анализ одного столбца
            if not df.empty and len(df.columns) > 0:
                col = df.columns[0]
                mean_val = df[col].mean()
                median_val = df[col].median()
                correlation = None  # Невозможно вычислить корреляцию для одного столбца
                return mean_val, median_val, correlation
            return None

    except Exception as e:
        app.logger.error(f"Error during data analysis: {e}")
        return None


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Анализ данных
        analysis_results = analyze_data(filepath)

        if analysis_results:
            mean_val, median_val, correlation = analysis_results
            # Сохранение результатов в БД
            result_entry = AnalysisResult(
                filename=filename,
                mean_value=mean_val,
                median_value=median_val,
                correlation=correlation
            )
            db.session.add(result_entry)
            db.session.commit()
            return jsonify({"message": "File uploaded and analyzed successfully", "result_id": result_entry.id}), 201
        else:
            return jsonify({"error": "Could not analyze data. Check file content (e.g., column names A and B)."}), 422
    else:
        return jsonify({"error": "File type not allowed"}), 400


@app.route('/statistics/<int:result_id>', methods=['GET'])
def get_statistics(result_id):
    result = AnalysisResult.query.get(result_id)
    if result:
        return jsonify(result.to_dict()), 200
    else:
        abort(404, description="Analysis result not found")


@app.route('/statistics', methods=['GET'])
def list_statistics():
    results = AnalysisResult.query.all()
    return jsonify([result.to_dict() for result in results]), 200

@app.route('/delete/<int:result_id>', methods=['GET'])
def get_items(result_id):
    result = AnalysisResult.query.get_or_404(result_id) # Найти запись по ID, 404 если нет
    if result:
       try:
          db.session.delete(result)
          db.session.commit()
          return jsonify({'message': f'Item {result_id} deleted successfully'}), 200
       except Exception as e:
          db.session.rollback() # Откат в случае ошибки
          return jsonify({'error': str(e)}), 500









if __name__ == '__main__':
    app.run(debug=True)
