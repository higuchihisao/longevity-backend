#!/usr/bin/env python
"""
Setup script for longevity_backend
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Longevity Backend...")
    
    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Check if virtual environment exists
    if not Path("venv").exists():
        print("📦 Creating virtual environment...")
        if not run_command("python -m venv venv", "Creating virtual environment"):
            sys.exit(1)
    
    # Activate virtual environment and install requirements
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/MacOS
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    # Install requirements
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing requirements"):
        sys.exit(1)
    
    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        print("📝 Creating .env file...")
        with open(".env", "w") as f:
            f.write("""# Django Settings
SECRET_KEY=django-insecure-change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DB_NAME=longevity_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
""")
        print("✅ .env file created")
    
    # Run migrations
    if not run_command(f"{python_cmd} manage.py makemigrations", "Creating migrations"):
        sys.exit(1)
    
    if not run_command(f"{python_cmd} manage.py migrate", "Running migrations"):
        sys.exit(1)
    
    # Create superuser (optional)
    print("\n👤 Do you want to create a superuser? (y/n): ", end="")
    create_superuser = input().lower().strip()
    if create_superuser in ['y', 'yes']:
        run_command(f"{python_cmd} manage.py createsuperuser", "Creating superuser")
    
    # Seed data (optional)
    print("\n🌱 Do you want to seed the database with sample data? (y/n): ", end="")
    seed_data = input().lower().strip()
    if seed_data in ['y', 'yes']:
        run_command(f"{python_cmd} manage.py seed_data", "Seeding database")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Make sure PostgreSQL is running")
    print("2. Update .env file with your database credentials")
    print("3. Run: python manage.py runserver")
    print("4. Visit: http://localhost:8000/admin/")

if __name__ == "__main__":
    main()

