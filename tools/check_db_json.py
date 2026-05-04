from app import app, db
from models import Camera, Permission, User
import json

def check_db_integrity():
    with app.app_context():
        print("Checking Cameras...")
        cameras = Camera.query.all()
        for cam in cameras:
            try:
                if cam.active_models:
                    json.loads(cam.active_models)
            except json.JSONDecodeError as e:
                print(f"ERROR: Camera {cam.id} has invalid active_models: {cam.active_models}")

        print("\nChecking Permissions JSON...")
        permissions = Permission.query.all()
        orphan_perms = []
        for perm in permissions:
            try:
                if perm.allowed_models:
                    json.loads(perm.allowed_models)
            except json.JSONDecodeError as e:
                print(f"ERROR: Permission {perm.id} has invalid allowed_models: {perm.allowed_models}")
            
            # Check relationships (this will trigger a query if not eager loaded)
            if not perm.user:
                print(f"ERROR: Permission {perm.id} references invalid user_id {perm.user_id}")
                orphan_perms.append(perm)
            elif not perm.camera:
                print(f"ERROR: Permission {perm.id} references invalid camera_id {perm.camera_id}")
                orphan_perms.append(perm)

        if orphan_perms:
            print(f"\nFound {len(orphan_perms)} orphan permissions.")
            # Uncomment to fix:
            # for p in orphan_perms:
            #     db.session.delete(p)
            # db.session.commit()
            # print("Deleted orphan permissions.")
        else:
            print("No orphan permissions found.")

        print("\nChecking Users...")
        users = User.query.all()
        print(f"Total Users: {len(users)}")

if __name__ == "__main__":
    check_db_integrity()
