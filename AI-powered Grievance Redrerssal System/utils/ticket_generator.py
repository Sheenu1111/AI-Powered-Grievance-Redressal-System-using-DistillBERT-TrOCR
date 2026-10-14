from datetime import datetime
import random
import string

class TicketGenerator:
    """Generate unique ticket IDs for complaints"""
    
    @staticmethod
    def generate_ticket_id():
        """
        Generate unique ticket ID
        Format: GR2026-YYYYMMDD-XXXXXX (where X is random alphanumeric)
        
        Returns:
            Unique ticket ID string
        """
        # Current date
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Random 6-character alphanumeric string
        random_str = ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        
        ticket_id = f"GR2026-{date_str}-{random_str}"
        
        return ticket_id
    
    @staticmethod
    def validate_ticket_id(ticket_id):
        """
        Validate ticket ID format
        
        Args:
            ticket_id: Ticket ID to validate
            
        Returns:
            Boolean indicating validity
        """
        if not ticket_id:
            return False
        
        # Check format: GR2026-YYYYMMDD-XXXXXX
        parts = ticket_id.split('-')
        
        if len(parts) != 3:
            return False
        
        if parts[0] != 'GR2026':
            return False
        
        if len(parts[1]) != 8 or not parts[1].isdigit():
            return False
        
        if len(parts[2]) != 6 or not parts[2].isalnum():
            return False
        
        return True
