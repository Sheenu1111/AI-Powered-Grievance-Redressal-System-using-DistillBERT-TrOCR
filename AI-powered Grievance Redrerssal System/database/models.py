from database.db_setup import get_db_connection
from datetime import datetime

class ComplaintModel:
    """Model for handling complaint database operations"""
    
    @staticmethod
    def create_complaint(ticket_id, complaint_text, category, priority, 
                        sentiment, department, original_filename=None):
        """Create a new complaint record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO complaints 
            (ticket_id, complaint_text, original_filename, category, priority, 
             sentiment, department, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Submitted')
        ''', (ticket_id, complaint_text, original_filename, category, 
              priority, sentiment, department))
        
        conn.commit()
        conn.close()
        return ticket_id
    
    @staticmethod
    def get_complaint_by_ticket_id(ticket_id):
        """Get complaint by ticket ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM complaints WHERE ticket_id = ?', (ticket_id,))
        complaint = cursor.fetchone()
        
        conn.close()
        return dict(complaint) if complaint else None
    
    @staticmethod
    def get_all_complaints(status=None, department=None):
        """Get all complaints, optionally filtered by status and department"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM complaints'
        params = []
        where_clauses = []
        
        if status:
            where_clauses.append('status = ?')
            params.append(status)
        
        if department:
            where_clauses.append('department = ?')
            params.append(department)
            
        if where_clauses:
            query += ' WHERE ' + ' AND '.join(where_clauses)
            
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, tuple(params))
        complaints = cursor.fetchall()
        conn.close()
        
        return [dict(complaint) for complaint in complaints]
    
    @staticmethod
    def update_complaint_status(ticket_id, new_status, admin_notes=None):
        """Update complaint status"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if new_status == 'Resolved':
            cursor.execute('''
                UPDATE complaints 
                SET status = ?, admin_notes = ?, updated_at = ?, resolved_at = ?
                WHERE ticket_id = ?
            ''', (new_status, admin_notes, datetime.now(), datetime.now(), ticket_id))
        else:
            cursor.execute('''
                UPDATE complaints 
                SET status = ?, admin_notes = ?, updated_at = ?
                WHERE ticket_id = ?
            ''', (new_status, admin_notes, datetime.now(), ticket_id))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_statistics(department=None):
        """Get dashboard statistics, optionally filtered by department"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        where_clause = ""
        params = []
        if department:
            where_clause = " WHERE department = ?"
            params = [department]
        
        # Total complaints
        cursor.execute(f'SELECT COUNT(*) as total FROM complaints{where_clause}', tuple(params))
        total = cursor.fetchone()['total']
        
        # By status
        cursor.execute(f'SELECT status, COUNT(*) as count FROM complaints{where_clause} GROUP BY status', tuple(params))
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # By priority
        cursor.execute(f'SELECT priority, COUNT(*) as count FROM complaints{where_clause} GROUP BY priority', tuple(params))
        priority_counts = {row['priority']: row['count'] for row in cursor.fetchall()}
        
        # By category
        cursor.execute(f'SELECT category, COUNT(*) as count FROM complaints{where_clause} GROUP BY category', tuple(params))
        category_counts = {row['category']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'total': total,
            'by_status': status_counts,
            'by_priority': priority_counts,
            'by_category': category_counts
        }

    @staticmethod
    def get_department_user(username, password):
        """Verify department credentials and return department name"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT dept_name FROM departments WHERE username = ? AND password = ?', 
                     (username, password))
        result = cursor.fetchone()
        conn.close()
        return result['dept_name'] if result else None
