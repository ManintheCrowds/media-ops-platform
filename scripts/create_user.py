"""Create initial admin user."""
from app.database import SessionLocal
from app.models import User
from app.auth.oauth2 import get_password_hash

db = SessionLocal()
try:
    user = db.query(User).filter(User.username == 'admin').first()
    if not user:
        new_user = User(
            username='admin',
            email='admin@example.com',
            hashed_password=get_password_hash('SecurePassword123!'),
            is_admin=True,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        print(f"✅ User 'admin' created successfully (ID: {new_user.id})")
    else:
        print(f"ℹ️  User 'admin' already exists (ID: {user.id})")
finally:
    db.close()

