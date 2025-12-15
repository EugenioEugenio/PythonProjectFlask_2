from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class AnalysisResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    mean_value = db.Column(db.Float)
    median_value = db.Column(db.Float)
    correlation = db.Column(db.Float) # Пример: корреляция между двумя столбцами
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'mean_value': self.mean_value,
            'median_value': self.median_value,
            'correlation': self.correlation,
            'timestamp': self.timestamp.isoformat()
        }

# После создания приложения Flask, в app.py нужно будет вызвать db.init_app(app)
# и создать таблицы: with app.app_context(): db.create_all()
