"""
Chatbot Utils - Helper functions for the Flask chatbot application
"""

import os
from typing import List, Dict
from datetime import datetime

def load_beach_info() -> Dict[str, str]:
    """
    Load information about Pantai Sulamadaha
    
    Returns:
        Dictionary containing beach information
    """
    beach_info = {
        "name": "Pantai Sulamadaha",
        "location": "Indonesia",
        "description": "Pantai indah dengan ombak yang menawan dan fasilitas wisata lengkap",
        "founded": "Unknown",
        "rating": "4.8/5"
    }
    return beach_info

def format_timestamp(dt: datetime) -> str:
    """
    Format datetime to readable string
    
    Args:
        dt: datetime object
        
    Returns:
        Formatted timestamp string
    """
    return dt.strftime("%H:%M:%S")

def validate_api_key() -> bool:
    """
    Validate if Google API key is configured
    
    Returns:
        True if API key exists, False otherwise
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    return bool(api_key and api_key != "your-google-api-key-here")

class ConversationManager:
    """Manage conversation history"""
    
    def __init__(self):
        self.conversations = {}
    
    def create_session(self, session_id: str) -> None:
        """Create new conversation session"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add message to conversation"""
        if session_id not in self.conversations:
            self.create_session(session_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.conversations[session_id].append(message)
    
    def get_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for session"""
        return self.conversations.get(session_id, [])
    
    def clear_history(self, session_id: str) -> None:
        """Clear conversation history"""
        if session_id in self.conversations:
            self.conversations[session_id] = []
    
    def get_session_count(self, session_id: str) -> int:
        """Get message count for session"""
        return len(self.conversations.get(session_id, []))

if __name__ == "__main__":
    # Test the utilities
    print("🏖️ Pantai Sulamadaha Chatbot Utils")
    print("-" * 40)
    
    info = load_beach_info()
    print(f"Beach: {info['name']}")
    print(f"Location: {info['location']}")
    print(f"Rating: {info['rating']}")
    
    print("\n✅ API Key Status:", "Configured" if validate_api_key() else "⚠️ Not configured")
    
    # Test ConversationManager
    manager = ConversationManager()
    session_id = "test_session"
    
    manager.add_message(session_id, "user", "Test message")
    manager.add_message(session_id, "assistant", "Test response")
    
    print(f"\n📝 Test Conversation ({session_id}):")
    for msg in manager.get_history(session_id):
        print(f"  {msg['role']}: {msg['content']}")
