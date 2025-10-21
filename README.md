# String Analyzer API

A RESTful API service that analyzes strings and stores their computed properties built with Flask.

## Features

For each analyzed string, the API computes and stores:

| Property | Description |
|----------|-------------|
| **length** | Number of characters in the string |
| **is_palindrome** | Whether the string reads the same forwards & backwards (case-insensitive) |
| **unique_characters** | Count of distinct characters |
| **word_count** | Number of words (split by whitespace) |
| **sha256_hash** | SHA-256 hash of the string (used as unique ID) |
| **character_frequency_map** | Dictionary mapping each character → its count |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/strings` | Analyze and store a new string |
| `GET` | `/strings/{string_value}` | Retrieve one analyzed string |
| `GET` | `/strings` | Retrieve all analyzed strings (with filters) |
| `GET` | `/strings/filter-by-natural-language` | Filter using plain-English queries |
| `DELETE` | `/strings/{string_value}` | Delete a string record |

---

## Natural Language Filtering

Use simple English queries like:

| Example Query | Interpreted Filters |
|---------------|---------------------|
| `all single word palindromic strings` | `word_count=1`, `is_palindrome=true` |
| `strings longer than 10 characters` | `min_length=11` |
| `strings containing the letter z` | `contains_character=z` |

---

## Tech Stack

- **Language:** Python 3.14
- **Framework:** Flask
- **Database:** SQLite (Development) / PostgreSQL (Production)
- **Libraries:** Flask-SQLAlchemy, Flask-CORS
- **Deployment:** Railway / Heroku / AWS

---

##  How to Run Locally

### 1️⃣ Clone the repo
```bash
git clone https://github.com/DonIyin/HNG_backend_stage1.git
cd HNG_backend_stage1
```

### 2️⃣ Create a virtual environment
```bash
python -m venv venv

# Activate it
venv\Scripts\activate       # on Windows
source venv/bin/activate    # on Mac/Linux
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Set up environment variables
Create a `.env` file:
```env
DATABASE_URL=sqlite:///strings.db
PORT=5000
```

### 5️⃣ Run the server
```bash
python backend_stage1.py
```

Your API is now live at: **http://localhost:5000**

---

## 🧪 Example Requests

### Create a String
```bash
curl -X POST http://localhost:5000/strings \
  -H "Content-Type: application/json" \
  -d '{"value": "racecar"}'
```

### Get Specific String
```bash
curl http://localhost:5000/strings/racecar
```

### Filter Palindromes
```bash
curl "http://localhost:5000/strings?is_palindrome=true"
```

### Natural Language Query
```bash
curl "http://localhost:5000/strings/filter-by-natural-language?query=single%20word%20palindromic%20strings"
```


## 📋 Example Response

**POST /strings**
```json
{
  "id": "e00f9ef51a95f6e854862eed28dc0f1a68f154d9f75ddd841ab00de6ede9209b",
  "value": "racecar",
  "properties": {
    "length": 7,
    "is_palindrome": true,
    "unique_characters": 4,
    "word_count": 1,
    "sha256_hash": "e00f9ef51a95f6e854862eed28dc0f1a68f154d9f75ddd841ab00de6ede9209b",
    "character_frequency_map": {
      "r": 2,
      "a": 2,
      "c": 2,
      "e": 1
    }
  },
  "created_at": "2025-10-21T20:26:45.807826Z"
}
```

---

## 🚨 Error Responses

| Code | Meaning | Example |
|------|---------|---------|
| `400` | Bad Request | Invalid request body or query params |
| `404` | Not Found | String doesn't exist |
| `409` | Conflict | String already exists |
| `422` | Unprocessable Entity | Invalid data type for `value` |

---  
