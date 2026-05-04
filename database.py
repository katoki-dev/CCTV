"""
CEMSS - Campus Event management and Surveillance System
Database Initialization
"""
from models import (db, User, Camera, Permission, DetectionLog, Alert, RestrictedZone,
                    SeverityRule, AlertRule, AnalyticsCache, PermissionRequest)
from config import DATABASE_URI, BASE_DIR
from datetime import time


def init_database(app):
    """Initialize the database and create tables"""
    with app.app_context():
        db.create_all()
        create_default_admin()
        migrate_existing_users()
        create_default_rules()
        print("✓ Database initialized successfully")
        print("✓ Phase 1 tables ready (SeverityRule, AlertRule, AnalyticsCache)")
        print("✓ RestrictedZone table ready for zone-based alerts")


def create_default_admin():
    """Create default admin user if it doesn't exist"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@cemss.local',
            is_admin=True,
            is_approved=True  # Admin is pre-approved
        )
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print("✓ Default admin user created (username: admin, password: admin)")
        print("  WARNING: Change the default password in production!")
    else:
        # Ensure existing admin is approved (migration)
        if not admin.is_approved:
            admin.is_approved = True
            db.session.commit()
            print("✓ Existing admin user approved")
        print("✓ Admin user already exists")


def migrate_existing_users():
    """Approve all existing users (migration for is_approved field)"""
    unapproved_users = User.query.filter_by(is_approved=False).all()
    if unapproved_users:
        # Approve existing users (they were created before approval system)
        for user in unapproved_users:
            if user.username != 'admin':  # Skip admin, already handled
                user.is_approved = True
        db.session.commit()
        print(f"✓ Approved {len(unapproved_users)} existing users")


def create_default_rules():
    """Create default severity and alert rules for Phase 1"""
    # Check if rules already exist
    if SeverityRule.query.count() == 0:
        # Default severity rules
        default_severity_rules = [
            SeverityRule(
                name="Fall Detection - Critical",
                model_name="fall",
                severity_score=9,
                is_active=True
            ),
            SeverityRule(
                name="Person at Night - High",
                model_name="person",
                time_window_start=time(22, 0),  # 10 PM
                time_window_end=time(6, 0),  # 6 AM
                severity_score=7,
                is_active=True
            ),
            SeverityRule(
                name="Phone Detection - Medium",
                model_name="phone",
                severity_score=5,
                is_active=True
            ),
            SeverityRule(
                name="Person in Restricted Zone - High",
                model_name="person",
                # zone_id will be set when zones are created
                severity_score=8,
                is_active=True
            )
        ]
        
        for rule in default_severity_rules:
            db.session.add(rule)
        
        db.session.commit()
        print(f"✓ Created {len(default_severity_rules)} default severity rules")
    
    # Check if alert rules exist
    if AlertRule.query.count() == 0:
        # Default alert rules
        default_alert_rules = [
            AlertRule(
                name="Critical Alerts Only",
                min_severity=9,
                cooldown_seconds=30,
                is_active=False  # Disabled by default
            ),
            AlertRule(
                name="High Priority Alerts",
                min_severity=7,
                cooldown_seconds=60,
                is_active=True  # Enabled by default
            ),
            AlertRule(
                name="All Detections",
                min_severity=1,
                cooldown_seconds=60,
                is_active=False  # Disabled by default
            )
        ]
        
        for rule in default_alert_rules:
            db.session.add(rule)
        
        db.session.commit()
        print(f"✓ Created {len(default_alert_rules)} default alert rules")


if __name__ == '__main__':
    """Run standalone database initialization"""
    from flask import Flask
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    init_database(app)
    
    with app.app_context():
        user_count = User.query.count()
        camera_count = Camera.query.count()
        zone_count = RestrictedZone.query.count()
        rule_count = SeverityRule.query.count() + AlertRule.query.count()
        
        print(f"\nDatabase Status:")
        print(f"  Users: {user_count}")
        print(f"  Cameras: {camera_count}")
        print(f"  Restricted Zones: {zone_count}")
        print(f"  Rules: {rule_count}")
        print(f"\nDefault credentials:")
        print(f"  Username: admin")
        print(f"  Password: admin")
