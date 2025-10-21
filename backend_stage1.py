from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
import hashlib
import os
import re

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


# DATABASE MODEL
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




# Add this NEW function after analyze_string() and before routes
def parse_natural_language_query(query):
    """
    Parse natural language query into filters
    Returns: dict of filters or raises ValueError if unparseable
    """
    filters = {}
    query_lower = query.lower().strip()

    # Pattern 1: Check for palindrome keywords
    if 'palindrome' in query_lower or 'palindromic' in query_lower:
        filters['is_palindrome'] = True

    # Pattern 2: Check for "single word" or "one word"
    if 'single word' in query_lower or 'one word' in query_lower:
        filters['word_count'] = 1
    elif 'two word' in query_lower:
        filters['word_count'] = 2
    elif 'three word' in query_lower:
        filters['word_count'] = 3

    # Pattern 3: Check for word count with numbers
    word_count_match = re.search(r'(\d+)\s+words?', query_lower)
    if word_count_match:
        filters['word_count'] = int(word_count_match.group(1))

    # Pattern 4: Check for "longer than X" or "more than X characters"
    longer_match = re.search(r'longer than (\d+)', query_lower)
    if longer_match:
        filters['min_length'] = int(longer_match.group(1)) + 1

    more_than_match = re.search(r'more than (\d+) characters?', query_lower)
    if more_than_match:
        filters['min_length'] = int(more_than_match.group(1)) + 1

    # Pattern 5: Check for "shorter than X" or "less than X characters"
    shorter_match = re.search(r'shorter than (\d+)', query_lower)
    if shorter_match:
        filters['max_length'] = int(shorter_match.group(1)) - 1

    less_than_match = re.search(r'less than (\d+) characters?', query_lower)
    if less_than_match:
        filters['max_length'] = int(less_than_match.group(1)) - 1

    # Pattern 6: Check for "at least X characters"
    at_least_match = re.search(r'at least (\d+) characters?', query_lower)
    if at_least_match:
        filters['min_length'] = int(at_least_match.group(1))

    # Pattern 7: Check for "containing letter X" or "with letter X"
    letter_patterns = [
        r'containing (?:the )?letter ([a-z])',
        r'with (?:the )?letter ([a-z])',
        r'that contains? ([a-z])',
        r'including (?:the )?letter ([a-z])'
    ]

    for pattern in letter_patterns:
        letter_match = re.search(pattern, query_lower)
        if letter_match:
            filters['contains_character'] = letter_match.group(1)
            break

    # Pattern 8: Special case for "first vowel" = 'a'
    if 'first vowel' in query_lower:
        filters['contains_character'] = 'a'

    # Pattern 9: Check for specific vowels
    vowel_match = re.search(r'vowel ([aeiou])', query_lower)
    if vowel_match:
        filters['contains_character'] = vowel_match.group(1)

    # Pattern 10: Check for length range "between X and Y"
    between_match = re.search(r'between (\d+) and (\d+)', query_lower)
    if between_match:
        filters['min_length'] = int(between_match.group(1))
        filters['max_length'] = int(between_match.group(2))

    # Pattern 11: Check for exact length "exactly X characters"
    exact_match = re.search(r'exactly (\d+) characters?', query_lower)
    if exact_match:
        length = int(exact_match.group(1))
        filters['min_length'] = length
        filters['max_length'] = length

    # If no filters were extracted, the query is unparseable
    if not filters:
        raise ValueError("Unable to parse natural language query")

    return filters

# ==================== ROUTES ====================

@app.route('/strings', methods=['POST'])
def create_string():
    """POST /strings - Create/Analyze String"""
    try:
        # Get JSON data from request
        data = request.get_json()

        # Validate request body exists
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        # Validate 'value' field exists
        if 'value' not in data:
            return jsonify({'error': 'Missing "value" field'}), 400

        value = data['value']

        # Validate 'value' is a string
        if not isinstance(value, str):
            return jsonify({'error': 'Invalid data type for "value" (must be string)'}), 422

        # Check if string already exists
        sha256_hash = compute_sha256(value)
        existing = AnalyzedString.query.filter_by(sha256_hash=sha256_hash).first()

        if existing:
            return jsonify({'error': 'String already exists in the system'}), 409

        # Analyze the string
        properties = analyze_string(value)

        # Create new database entry
        new_string = AnalyzedString(
            id=properties['sha256_hash'],
            value=value,
            length=properties['length'],
            is_palindrome=properties['is_palindrome'],
            unique_characters=properties['unique_characters'],
            word_count=properties['word_count'],
            sha256_hash=properties['sha256_hash'],
            character_frequency_map=properties['character_frequency_map']
        )

        # Save to database
        db.session.add(new_string)
        db.session.commit()

        # Return response
        return jsonify(new_string.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/strings/<path:string_value>', methods=['GET'])
def get_string(string_value):
    """GET /strings/{string_value} - Get Specific String"""
    try:
        # Find string in database by value
        analyzed_string = AnalyzedString.query.filter_by(value=string_value).first()

        if not analyzed_string:
            return jsonify({'error': 'String does not exist in the system'}), 404

        return jsonify(analyzed_string.to_dict()), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/strings', methods=['GET'])
def get_all_strings():
    """GET /strings - Get All Strings with Filtering"""
    try:
        # Start with base query
        query = AnalyzedString.query

        # Collect applied filters
        filters_applied = {}

        # Filter by is_palindrome
        is_palindrome_param = request.args.get('is_palindrome')
        if is_palindrome_param is not None:
            if is_palindrome_param.lower() == 'true':
                query = query.filter_by(is_palindrome=True)
                filters_applied['is_palindrome'] = True
            elif is_palindrome_param.lower() == 'false':
                query = query.filter_by(is_palindrome=False)
                filters_applied['is_palindrome'] = False
            else:
                return jsonify({'error': 'Invalid value for is_palindrome (must be true or false)'}), 400

        # Filter by min_length
        min_length = request.args.get('min_length')
        if min_length is not None:
            try:
                min_length = int(min_length)
                query = query.filter(AnalyzedString.length >= min_length)
                filters_applied['min_length'] = min_length
            except ValueError:
                return jsonify({'error': 'Invalid value for min_length (must be integer)'}), 400

        # Filter by max_length
        max_length = request.args.get('max_length')
        if max_length is not None:
            try:
                max_length = int(max_length)
                query = query.filter(AnalyzedString.length <= max_length)
                filters_applied['max_length'] = max_length
            except ValueError:
                return jsonify({'error': 'Invalid value for max_length (must be integer)'}), 400

        # Filter by word_count
        word_count = request.args.get('word_count')
        if word_count is not None:
            try:
                word_count = int(word_count)
                query = query.filter_by(word_count=word_count)
                filters_applied['word_count'] = word_count
            except ValueError:
                return jsonify({'error': 'Invalid value for word_count (must be integer)'}), 400

        # Filter by contains_character
        contains_character = request.args.get('contains_character')
        if contains_character is not None:
            if len(contains_character) != 1:
                return jsonify({'error': 'contains_character must be a single character'}), 400
            # Filter strings that contain the character
            query = query.filter(AnalyzedString.value.contains(contains_character))
            filters_applied['contains_character'] = contains_character

        # Execute query
        results = query.all()

        # Format response
        response = {
            'data': [string.to_dict() for string in results],
            'count': len(results),
            'filters_applied': filters_applied
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/strings/filter-by-natural-language', methods=['GET'])
def natural_language_filter():
    """GET /strings/filter-by-natural-language - Natural Language Filtering"""
    try:
        # Get the query parameter
        query = request.args.get('query')

        if not query:
            return jsonify({'error': 'Missing "query" parameter'}), 400

        # Parse the natural language query
        try:
            parsed_filters = parse_natural_language_query(query)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        # Check for conflicting filters
        if 'min_length' in parsed_filters and 'max_length' in parsed_filters:
            if parsed_filters['min_length'] > parsed_filters['max_length']:
                return jsonify({
                    'error': 'Query parsed but resulted in conflicting filters',
                    'details': f"min_length ({parsed_filters['min_length']}) > max_length ({parsed_filters['max_length']})"
                }), 422

        # Start with base query
        db_query = AnalyzedString.query

        # Apply filters
        if 'is_palindrome' in parsed_filters:
            db_query = db_query.filter_by(is_palindrome=parsed_filters['is_palindrome'])

        if 'word_count' in parsed_filters:
            db_query = db_query.filter_by(word_count=parsed_filters['word_count'])

        if 'min_length' in parsed_filters:
            db_query = db_query.filter(AnalyzedString.length >= parsed_filters['min_length'])

        if 'max_length' in parsed_filters:
            db_query = db_query.filter(AnalyzedString.length <= parsed_filters['max_length'])

        if 'contains_character' in parsed_filters:
            db_query = db_query.filter(AnalyzedString.value.contains(parsed_filters['contains_character']))

        # Execute query
        results = db_query.all()

        # Format response
        response = {
            'data': [string.to_dict() for string in results],
            'count': len(results),
            'interpreted_query': {
                'original': query,
                'parsed_filters': parsed_filters
            }
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/strings/<path:string_value>', methods=['DELETE'])
def delete_string(string_value):
    """DELETE /strings/{string_value}"""
    try:
        # Find string in database
        analyzed_string = AnalyzedString.query.filter_by(value=string_value).first()

        if not analyzed_string:
            return jsonify({'error': 'String does not exist in the system'}), 404

        # Delete from database
        db.session.delete(analyzed_string)
        db.session.commit()

        return '', 204

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==================== INITIALIZATION ====================
with app.app_context():
    db.create_all()

# ==================== RUN APP ====================
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
