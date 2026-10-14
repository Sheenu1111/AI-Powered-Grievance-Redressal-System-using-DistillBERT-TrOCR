import sqlite3
import os
from config import DATABASE_PATH

def init_database():
    """Initialize the database with required tables"""
    
    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create complaints table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE NOT NULL,
            complaint_text TEXT NOT NULL,
            original_filename TEXT,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            department TEXT NOT NULL,
            status TEXT DEFAULT 'Submitted',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            admin_notes TEXT
        )
    ''')
    
    # Create departments table for login
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_name TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Add default department accounts (username matches dept name for simplicity)
    # Default password for all: 'dept123'
    default_depts = [
        ('Public Works Department', 'pwd', 'dept123'),
        ('Electrical Department', 'electrical', 'dept123'),
        ('Sanitation Department', 'sanitation', 'dept123'),
        ('Human Resources Department', 'hr', 'dept123'),
        ('Municipal Corporation', 'municipal', 'dept123'),
        ('Police Department', 'police', 'dept123'),
        ('General Administration', 'admin_dept', 'dept123')
    ]
    
    for dept, user, pwd in default_depts:
        cursor.execute('INSERT OR IGNORE INTO departments (dept_name, username, password) VALUES (?, ?, ?)',
                     (dept, user, pwd))
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == '__main__':
    init_database()
