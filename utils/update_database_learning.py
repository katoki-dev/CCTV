"""
CASS - Simple Database Creator for Self-Learning Tables
Run this after starting the app once to create the new tables
"""
import sqlite3
import os

# Path to database
db_path = 'database.db'

# SQL for creating new tables
SQL_STATEMENTS = [
    # VerificationLog table
    """
    CREATE TABLE IF NOT EXISTS verification_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        detection_log_id INTEGER NOT NULL,
        verification_source VARCHAR(20) NOT NULL,
        user_id INTEGER,
        verification_result VARCHAR(20) NOT NULL,
        corrected_label VARCHAR(50),
        confidence_rating FLOAT,
        vlm_model_used VARCHAR(50),
        vlm_response TEXT,
        notes TEXT,
        image_path VARCHAR(500),
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        processed BOOLEAN DEFAULT 0,
        sampled_randomly BOOLEAN DEFAULT 0,
        FOREIGN KEY (detection_log_id) REFERENCES detection_logs(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """,
    
    # Indexes for verification_logs
    """
    CREATE INDEX IF NOT EXISTS idx_verification_source_timestamp 
    ON verification_logs(verification_source, timestamp)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_verification_result 
    ON verification_logs(verification_result, processed)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_verification_detection 
    ON verification_logs(detection_log_id)
    """,
    
    # ModelPerformance table
    """
    CREATE TABLE IF NOT EXISTS model_performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name VARCHAR(50) NOT NULL,
        date DATE NOT NULL,
        total_detections INTEGER DEFAULT 0,
        verified_detections INTEGER DEFAULT 0,
        true_positives INTEGER DEFAULT 0,
        false_positives INTEGER DEFAULT 0,
        avg_confidence FLOAT,
        threshold_used FLOAT,
        accuracy_rate FLOAT,
        f1_score FLOAT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(model_name, date)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_model_date 
    ON model_performance(model_name, date)
    """,
    
    # TrainingQueue table
    """
    CREATE TABLE IF NOT EXISTS training_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name VARCHAR(50) NOT NULL,
        priority VARCHAR(10) DEFAULT 'MEDIUM',
        verified_sample_count INTEGER DEFAULT 0,
        status VARCHAR(20) DEFAULT 'PENDING',
        scheduled_time DATETIME,
        started_at DATETIME,
        completed_at DATETIME,
        old_model_path VARCHAR(500),
        new_model_path VARCHAR(500),
        performance_improvement FLOAT,
        error_message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_status_scheduled 
    ON training_queue(status, scheduled_time)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_training_model 
    ON training_queue(model_name)
    """,
    
    # ModelVersion table
    """
    CREATE TABLE IF NOT EXISTS model_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name VARCHAR(50) NOT NULL,
        version_number INTEGER NOT NULL,
        model_path VARCHAR(500) NOT NULL,
        deployed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        performance_metrics TEXT,
        trained_on_samples INTEGER,
        is_active BOOLEAN DEFAULT 0,
        rollback_available BOOLEAN DEFAULT 1,
        notes TEXT,
        UNIQUE(model_name, version_number)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_model_version 
    ON model_versions(model_name, version_number)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_model_active 
    ON model_versions(model_name, is_active)
    """
]

def create_tables():
    """Create all self-learning tables"""
    print("=" * 70)
    print("CASS Self-Learning System - Database Table Creation")
    print("=" * 70)
    
    if not os.path.exists(db_path):
        print(f"\n⚠ Database not found at {db_path}")
        print("Please run the CASS app at least once to create the database.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\nCreating tables...")
        for i, sql in enumerate(SQL_STATEMENTS, 1):
            cursor.execute(sql)
            print(f"  [{i}/{len(SQL_STATEMENTS)}] Executed")
        
        conn.commit()
        
        # Verify tables
        print("\nVerifying tables...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required = ['verification_logs', 'model_performance', 'training_queue', 'model_versions']
        for table in required:
            if table in tables:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} - MISSING!")
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("✓ Database tables created successfully!")
        print("=" * 70)
        print("\nNew tables:")
        print("  • verification_logs  - VLM and user feedback")
        print("  • model_performance  - Model accuracy tracking")
        print("  • training_queue     - Retraining job queue")
        print("  • model_versions     - Model version control")
        print("\nYou can now enable self-learning features in the CASS system.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error creating tables: {str(e)}")
        return False

if __name__ == '__main__':
    import sys
    success = create_tables()
    sys.exit(0 if success else 1)
