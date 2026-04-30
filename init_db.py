import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    # We import the factory function 'create_app' and the database object 'db'
    from app import create_app, db
    
    # We execute the function to create the actual app instance
    app = create_app()
    
    print("✅ Successfully initialized app via create_app()")
except Exception as e:
    print(f"❌ Error during initialization: {e}")
    sys.exit(1)

def init_db():
    # We must use the app context to connect to the database
    with app.app_context():
        print(f"🔌 Connecting to Aiven MySQL...")
        try:
            # Create all tables defined in your models
            db.create_all()
            print("\n" + "="*30)
            print("🚀 SUCCESS! DATABASE IS LIVE")
            print("="*30)
            print("Your tables are now created on Aiven.")
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            print("\nMake sure your .env has the right password and ca.pem is in this folder.")

if __name__ == '__main__':
    init_db()