"""
Security audit script for CEMSS
Checks for common security issues
"""
import os
import re
import json
from pathlib import Path

def audit_security():
    """Run security audit"""
    issues = []
    warnings = []
    info = []
    
    # 1. Check for hardcoded secrets
    print("🔍 Scanning for hardcoded secrets...")
    secret_patterns = [
        (r'password\s*=\s*["\'](?!.*{{)[^"\']+["\']', 'Hardcoded password'),
        (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key'),
        (r'secret_key\s*=\s*["\'](?!.*SECRET_KEY)[^"\']+["\']', 'Hardcoded secret key'),
    ]
    
    for py_file in Path('.').rglob('*.py'):
        if 'venv' in str(py_file) or '__pycache__' in str(py_file):
            continue
        
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            for pattern, issue_type in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    warnings.append(f"{issue_type} in {py_file}")
    
    # 2. Check .env file
    print("🔍 Checking .env configuration...")
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
            if 'admin' in env_content and 'password' in env_content.lower():
                warnings.append("Default admin credentials may be in .env")
    else:
        info.append(".env file not found - using environment variables")
    
    # 3. Check for SQL injection vulnerabilities
    print("🔍 Checking for SQL injection risks...")
    sql_patterns = [
        r'execute\([f"\'].*{.*}',
        r'\.query\([f"\'].*{.*}',
    ]
    
    for py_file in Path('.').rglob('*.py'):
        if 'venv' in str(py_file):
            continue
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            for pattern in sql_patterns:
                if re.search(pattern, content):
                    warnings.append(f"Potential SQL injection risk in {py_file}")
    
    # 4. Check Flask debug mode
    print("🔍 Checking Flask configuration...")
    if os.path.exists('app.py'):
        with open('app.py', 'r') as f:
            if 'debug=True' in f.read():
                issues.append("Flask debug mode enabled in app.py - CRITICAL for production")
    
    # 5. Check for exposed sensitive endpoints
    print("🔍 Checking API endpoints...")
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            if 'DEBUG=True' in f.read():
                issues.append("DEBUG=True in .env - should be False in production")
    
    # 6. Check file permissions (Linux/Mac)
    if os.name != 'nt':
        print("🔍 Checking file permissions...")
        sensitive_files = ['.env', 'database.db', 'config.py']
        for file in sensitive_files:
            if os.path.exists(file):
                mode = os.stat(file).st_mode
                if mode & 0o004:  # World readable
                    warnings.append(f"{file} is world-readable")
    
    # 7. Check dependencies for known vulnerabilities
    print("🔍 Checking dependencies...")
    info.append("Run 'pip-audit' or 'safety check' for dependency vulnerabilities")
    
    # Results
    print("\n" + "="*60)
    print("SECURITY AUDIT RESULTS")
    print("="*60)
    
    if issues:
        print(f"\n🔴 CRITICAL ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if info:
        print(f"\nℹ️  INFORMATION ({len(info)}):")
        for i in info:
            print(f"  - {i}")
    
    if not issues and not warnings:
        print("\n✅ No security issues found!")
    
    print("\n" + "="*60)
    
    # Save report
    report = {
        'critical': issues,
        'warnings': warnings,
        'info': info,
        'total_issues': len(issues) + len(warnings)
    }
    
    with open('security_audit_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("📄 Report saved to security_audit_report.json")
    
    return len(issues) == 0

if __name__ == '__main__':
    success = audit_security()
    exit(0 if success else 1)
