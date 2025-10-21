from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
import hashlib
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///strings.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)


# ==================== DATABASE MODEL ====================
class AnalyzedString(db.Model):
    __tablename__ = 'analyzed_strings'

    id = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text, nullable=False, unique=True)
    length = db.Column(db.Integer, nullable=False)
    is_palindrome = db.Column(db.Boolean, nullable=False)
    unique_characters = db.Column(db.Integer, nullable=False)
    word_count = db.Column(db.Integer, nullable=False)
    sha256_hash = db.Column(db.String(64), nullable=False)
    character_frequency_map = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'value': self.value,
            'properties': {
                'length': self.length,
                'is_palindrome': self.is_palindrome,
                'unique_characters': self.unique_characters,
                'word_count': self.word_count,
                'sha256_hash': self.sha256_hash,
                'character_frequency_map': self.character_frequency_map
            },
            'created_at': self.created_at.isoformat() + 'Z'
        }


# ==================== UTILITY FUNCTIONS ====================
def compute_sha256(text):
    """Generate SHA-256 hash of a string"""
    return hashlib.sha256(text.encode()).hexdigest()


def is_palindrome(text):
    """Check if string is palindrome (case-insensitive)"""
    cleaned = text.lower().replace(' ', '')
    return cleaned == cleaned[::-1]


def count_unique_characters(text):
    """Count distinct characters"""
    return len(set(text))


def count_words(text):
    """Count words separated by whitespace"""
    return len(text.split())


def get_character_frequency(text):
    """Generate character frequency map"""
    freq = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    return freq


def analyze_string(value):
    """Analyze string and return all properties"""
    return {
        'length': len(value),
        'is_palindrome': is_palindrome(value),
        'unique_characters': count_unique_characters(value),
        'word_count': count_words(value),
        'sha256_hash': compute_sha256(value),
        'character_frequency_map': get_character_frequency(value)
    }


# ==================== ROUTES ====================

@app.route('/strings', methods=['POST'])
def create_string():
    """POST /strings - Create/Analyze String"""
    # TODO: Implement in Step 2
    return jsonify({"message": "TODO: Implement POST"}), 201


@app.route('/strings/<path:string_value>', methods=['GET'])
def get_string(string_value):
    """GET /strings/{string_value} - Get Specific String"""
    # TODO: Implement in Step 2
    return jsonify({"message": f"TODO: Get {string_value}"}), 200


@app.route('/strings', methods=['GET'])
def get_all_strings():
    """GET /strings - Get All Strings with Filtering"""
    # TODO: Implement in Step 2
    return jsonify({"message": "TODO: Get all with filters"}), 200


@app.route('/strings/filter-by-natural-language', methods=['GET'])
def natural_language_filter():
    """GET /strings/filter-by-natural-language"""
    # TODO: Implement in Step 2
    return jsonify({"message": "TODO: Natural language filter"}), 200


@app.route('/strings/<path:string_value>', methods=['DELETE'])
def delete_string(string_value):
    """DELETE /strings/{string_value}"""
    # TODO: Implement in Step 2
    return '', 204


# ==================== INITIALIZATION ====================
with app.app_context():
    db.create_all()

# ==================== RUN APP ====================
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)