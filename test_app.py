#!/usr/bin/env python3
"""
Simple test script for The Reef Chat application
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_basic_imports():
    """Test if all required modules can be imported"""
    try:
        from flask import Flask
        print("✅ Flask import successful")
        
        import chromadb
        print("✅ ChromaDB import successful")
        
        from utils.document_processor import DocumentProcessor
        print("✅ DocumentProcessor import successful")
        
        # Test document processor
        doc_processor = DocumentProcessor()
        supported_files = doc_processor.SUPPORTED_EXTENSIONS
        print(f"✅ Supported file types: {supported_files}")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_flask_app():
    """Test basic Flask app functionality"""
    try:
        from app import app
        
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                
            # Test main page
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Main page loading")
            else:
                print(f"❌ Main page failed: {response.status_code}")
                
        return True
    except Exception as e:
        print(f"❌ Flask app error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing The Reef Chat Application")
    print("=" * 40)
    
    # Check if OpenAI API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your_openai_api_key_here':
        print("⚠️  Warning: OPENAI_API_KEY not set - chat functionality will not work")
        print("   Please set your OpenAI API key in .env file")
    else:
        print("✅ OpenAI API key is configured")
    
    print()
    
    # Run tests
    import_success = test_basic_imports()
    print()
    
    if import_success:
        flask_success = test_flask_app()
    else:
        print("❌ Skipping Flask tests due to import failures")
        flask_success = False
    
    print()
    print("=" * 40)
    
    if import_success and flask_success:
        print("🎉 All tests passed! The application is ready to run.")
        print("💡 To start the app: python app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        
    return import_success and flask_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)