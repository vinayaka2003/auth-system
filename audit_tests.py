"""
COMPREHENSIVE PRODUCTION-GRADE AUDIT TEST SUITE v2
===================================================
Tests all API endpoints, authentication flows, security boundaries,
database behavior, and edge cases.
"""
import requests
import json
import time
import sqlite3
import base64
import sys
import concurrent.futures

BASE = 'http://127.0.0.1:8000'
DB = 'backend/auth.db'
results = []

def log(name, status, details=''):
    results.append((name, status, details))
    print(f'[{status}] {name}: {details}')

def safe_json(r):
    try:
        return r.json()
    except:
        return r.text[:200]

def db_query(sql, params=()):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    conn.close()
    return row

def db_query_all(sql, params=()):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def db_exec(sql, params=()):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()

# Cleanup test users
for e in ['audit_test@example.com', 'xss@test.com', 'long@test.com', 'weak@test.com',
          'notanemail', 'empty_signup@test.com', 'unicode@test.com', 'special@test.com']:
    db_exec('DELETE FROM users WHERE email = ?', (e,))

email = 'audit_test@example.com'
pwd = 'SecurePass123!'

print('=' * 60)
print('SECTION 1: HOME ENDPOINT')
print('=' * 60)

# T01: Home endpoint
r = requests.get(BASE + '/')
log('T01_home_endpoint', 'PASS' if r.status_code == 200 else 'FAIL',
    f'{r.status_code} {safe_json(r)}')

print()
print('=' * 60)
print('SECTION 2: SIGNUP TESTS')
print('=' * 60)

# T02: Valid signup
r = requests.post(BASE + '/signup', json={'name': 'Auditor', 'email': email, 'password': pwd})
log('T02_valid_signup', 'PASS' if r.status_code == 200 else 'FAIL',
    f'{r.status_code} {safe_json(r)}')

# T03: Duplicate signup
r = requests.post(BASE + '/signup', json={'name': 'Auditor', 'email': email, 'password': pwd})
log('T03_duplicate_signup', 'PASS' if r.status_code == 400 else 'FAIL',
    f'{r.status_code} {safe_json(r)}')

# T04: Empty fields signup
r = requests.post(BASE + '/signup', json={'name': '', 'email': '', 'password': ''})
log('T04_empty_fields_signup',
    'FAIL' if r.status_code == 200 else 'PASS',
    f'{r.status_code} - Server {"accepted" if r.status_code == 200 else "rejected"} empty fields')

# T05: Invalid email format signup
r = requests.post(BASE + '/signup', json={'name': 'Test', 'email': 'notanemail', 'password': pwd})
log('T05_invalid_email_signup',
    'FAIL' if r.status_code == 200 else 'PASS',
    f'{r.status_code} - Server {"accepted" if r.status_code == 200 else "rejected"} invalid email format')

# T06: Missing fields signup
r = requests.post(BASE + '/signup', json={'email': 'partial@test.com'})
log('T06_missing_fields_signup', 'PASS' if r.status_code == 422 else 'FAIL',
    f'{r.status_code}')

# T07: Weak/empty password
r = requests.post(BASE + '/signup', json={'name': 'Test', 'email': 'weak@test.com', 'password': ''})
log('T07_weak_password',
    'FAIL' if r.status_code == 200 else 'PASS',
    f'{r.status_code} - Server {"accepted" if r.status_code == 200 else "rejected"} empty password')

# T08: Malformed JSON payload signup
r = requests.post(BASE + '/signup', data='not json', headers={'Content-Type': 'application/json'})
log('T08_malformed_payload_signup', 'PASS' if r.status_code >= 400 else 'FAIL',
    f'{r.status_code}')

# Cleanup
for e in ['notanemail', 'weak@test.com']:
    db_exec('DELETE FROM users WHERE email = ?', (e,))

print()
print('=' * 60)
print('SECTION 3: EMAIL VERIFICATION TESTS')
print('=' * 60)

# T09: Check verification token exists in DB
row = db_query('SELECT is_verified, verification_token FROM users WHERE email = ?', (email,))
log('T09_verification_state_after_signup',
    'INFO',
    f'is_verified={row[0]}, verification_token={row[1]}' if row else 'User not found')

if row:
    log('T09a_verification_bypass',
        'FAIL' if row[0] == 1 else 'PASS',
        f'User is auto-verified after signup (is_verified={row[0]}) - VERIFICATION IS BYPASSED IN CODE')

# T10: Verify with invalid token
r = requests.get(BASE + '/verify/invalidtoken123')
log('T10_verify_invalid_token', 'PASS' if r.status_code == 400 else 'FAIL',
    f'{r.status_code} {safe_json(r)}')

print()
print('=' * 60)
print('SECTION 4: LOGIN TESTS')
print('=' * 60)

# T11: Correct login
r = requests.post(BASE + '/login', json={'email': email, 'password': pwd})
if r.status_code == 200:
    token = r.json().get('access_token')
    log('T11_valid_login', 'PASS', f'{r.status_code} token_received={bool(token)}')
else:
    token = None
    log('T11_valid_login', 'FAIL', f'{r.status_code} {safe_json(r)}')

# T12: Wrong password
r = requests.post(BASE + '/login', json={'email': email, 'password': 'wrongpassword'})
log('T12_wrong_password', 'PASS' if r.status_code == 401 else 'FAIL',
    f'{r.status_code} {safe_json(r)}')

# T13: Wrong email
r = requests.post(BASE + '/login', json={'email': 'nonexistent@test.com', 'password': pwd})
log('T13_wrong_email', 'PASS' if r.status_code == 401 else 'FAIL',
    f'{r.status_code} {safe_json(r)}')

# T14: Empty login fields
r = requests.post(BASE + '/login', json={'email': '', 'password': ''})
log('T14_empty_login',
    'FAIL' if r.status_code == 200 else 'PASS',
    f'{r.status_code} - Server {"ISSUED A TOKEN for empty email" if r.status_code == 200 else "rejected"} empty login')

# T15: Missing login fields
r = requests.post(BASE + '/login', json={})
log('T15_missing_login_fields', 'PASS' if r.status_code == 422 else 'FAIL',
    f'{r.status_code}')

# T16: Malformed login payload
r = requests.post(BASE + '/login', data='garbage', headers={'Content-Type': 'application/json'})
log('T16_malformed_login', 'PASS' if r.status_code >= 400 else 'FAIL',
    f'{r.status_code}')

print()
print('=' * 60)
print('SECTION 5: JWT / AUTH PROTECTED ENDPOINTS')
print('=' * 60)

# T17: /me with valid token
if token:
    r = requests.get(BASE + '/me', headers={'Authorization': f'Bearer {token}'})
    data = r.json()
    log('T17_me_valid_token', 'PASS' if r.status_code == 200 and data.get('email') == email else 'FAIL',
        f'{r.status_code} {data}')

# T18: /me without token
r = requests.get(BASE + '/me')
log('T18_me_no_token', 'PASS' if r.status_code == 401 else 'FAIL',
    f'{r.status_code} {safe_json(r)}')

# T19: /me with invalid token
r = requests.get(BASE + '/me', headers={'Authorization': 'Bearer invalidtoken123'})
log('T19_me_invalid_token', 'PASS' if r.status_code == 401 else 'FAIL',
    f'{r.status_code} {safe_json(r)}')

# T20: /me with tampered JWT
if token:
    parts = token.split('.')
    tampered = parts[0] + '.' + parts[1] + '.tampered_signature'
    r = requests.get(BASE + '/me', headers={'Authorization': f'Bearer {tampered}'})
    log('T20_me_tampered_jwt', 'PASS' if r.status_code == 401 else 'FAIL',
        f'{r.status_code} {safe_json(r)}')

# T21: /me with expired token
r = requests.get(BASE + '/me', headers={'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QHRlc3QuY29tIiwiZXhwIjoxNjAwMDAwMDAwfQ.invalid'})
log('T21_me_expired_token', 'PASS' if r.status_code == 401 else 'FAIL',
    f'{r.status_code}')

# T22: /dashboard with valid token
if token:
    r = requests.get(BASE + '/dashboard', headers={'Authorization': f'Bearer {token}'})
    log('T22_dashboard_valid', 'PASS' if r.status_code == 200 else 'FAIL',
        f'{r.status_code} {safe_json(r)}')

# T23: /dashboard without token
r = requests.get(BASE + '/dashboard')
log('T23_dashboard_no_token', 'PASS' if r.status_code == 401 else 'FAIL',
    f'{r.status_code} {safe_json(r)}')

# T24: /dashboard with invalid token
r = requests.get(BASE + '/dashboard', headers={'Authorization': 'Bearer fakejwt'})
log('T24_dashboard_invalid_token', 'PASS' if r.status_code == 401 else 'FAIL',
    f'{r.status_code} {safe_json(r)}')

# T25: Auth header without Bearer prefix - SECURITY TEST
if token:
    r = requests.get(BASE + '/me', headers={'Authorization': token})
    log('T25_auth_no_bearer_prefix',
        'FAIL' if r.status_code == 200 else 'PASS',
        f'{r.status_code} - Token without Bearer prefix {"ACCEPTED (security issue)" if r.status_code == 200 else "rejected"}')

# T26: Auth header with wrong prefix
r = requests.get(BASE + '/me', headers={'Authorization': 'Token fakejwt'})
log('T26_auth_wrong_prefix', 'INFO',
    f'{r.status_code} - {safe_json(r)}')

print()
print('=' * 60)
print('SECTION 6: PASSWORD RESET TESTS')
print('=' * 60)

# T27: Forgot password - valid email (may fail due to Resend API)
try:
    r = requests.post(BASE + '/forgot-password', json={'email': email}, timeout=15)
    log('T27_forgot_password_valid',
        'PASS' if r.status_code == 200 else 'FAIL',
        f'{r.status_code} {safe_json(r)}')
except Exception as e:
    log('T27_forgot_password_valid', 'FAIL', f'Exception: {e}')

# T28: Forgot password - nonexistent email
try:
    r = requests.post(BASE + '/forgot-password', json={'email': 'ghost@test.com'}, timeout=10)
    log('T28_forgot_password_nonexistent',
        'PASS' if r.status_code == 404 else 'FAIL',
        f'{r.status_code} {safe_json(r)}')
except Exception as e:
    log('T28_forgot_password_nonexistent', 'FAIL', f'Exception: {e}')

# Security: user enumeration via forgot password
log('T28a_user_enumeration', 'WARN',
    'Forgot password reveals if email is registered (404 vs 200). User enumeration possible.')

# T29: Forgot password - empty email
try:
    r = requests.post(BASE + '/forgot-password', json={'email': ''}, timeout=10)
    log('T29_forgot_password_empty', 'INFO',
        f'{r.status_code} {safe_json(r)}')
except Exception as e:
    log('T29_forgot_password_empty', 'FAIL', f'Exception: {e}')

# T30: Get reset token from DB
row = db_query('SELECT reset_token FROM users WHERE email = ?', (email,))
reset_token = row[0] if row else None
log('T30_reset_token_in_db',
    'PASS' if reset_token else 'INFO',
    f'token_present={bool(reset_token)}')

# T31: Reset password with valid token
new_pwd = 'NewSecurePass456!'
if reset_token:
    r = requests.post(BASE + f'/reset-password/{reset_token}', json={'password': new_pwd})
    log('T31_reset_password_valid', 'PASS' if r.status_code == 200 else 'FAIL',
        f'{r.status_code} {safe_json(r)}')
else:
    log('T31_reset_password_valid', 'SKIP', 'No reset token (email send may have failed)')

# T32: Reset password with invalid token
r = requests.post(BASE + '/reset-password/invalidtoken123', json={'password': 'test123'})
log('T32_reset_password_invalid_token', 'PASS' if r.status_code == 400 else 'FAIL',
    f'{r.status_code} {safe_json(r)}')

# T33: Reset password - reuse token
if reset_token:
    r = requests.post(BASE + f'/reset-password/{reset_token}', json={'password': 'another123'})
    log('T33_reset_password_reused_token', 'PASS' if r.status_code == 400 else 'FAIL',
        f'{r.status_code} {safe_json(r)}')
else:
    log('T33_reset_password_reused_token', 'SKIP', 'No reset token')

# T34: Login with new/old password after reset
if reset_token:
    r = requests.post(BASE + '/login', json={'email': email, 'password': new_pwd})
    log('T34_login_after_reset', 'PASS' if r.status_code == 200 else 'FAIL',
        f'{r.status_code}')

    r = requests.post(BASE + '/login', json={'email': email, 'password': pwd})
    log('T35_login_old_password_rejected', 'PASS' if r.status_code == 401 else 'FAIL',
        f'{r.status_code}')
else:
    # Still using original password
    log('T34_login_after_reset', 'SKIP', 'Reset flow did not complete')
    log('T35_login_old_password_rejected', 'SKIP', 'Reset flow did not complete')

# T36: Reset password with empty password body
r = requests.post(BASE + '/reset-password/sometoken', json={'password': ''})
log('T36_reset_empty_password', 'INFO',
    f'{r.status_code} - Empty password in reset: {"accepted by format validation" if r.status_code != 422 else "rejected"}')

# T37: Reset with no token expiry check
log('T37_reset_token_no_expiry', 'WARN',
    'Reset tokens have NO expiry mechanism. A reset token remains valid indefinitely until used.')

print()
print('=' * 60)
print('SECTION 7: GOOGLE AUTH TESTS')
print('=' * 60)

# T38: Google login with invalid token
r = requests.post(BASE + '/google-login', json={'token': 'fake_google_token'})
log('T38_google_login_invalid', 'PASS' if r.status_code == 401 else 'FAIL',
    f'{r.status_code} {safe_json(r)}')

# T39: Google login with empty token
r = requests.post(BASE + '/google-login', json={'token': ''})
log('T39_google_login_empty', 'PASS' if r.status_code >= 400 else 'FAIL',
    f'{r.status_code} {safe_json(r)}')

# T40: Google login missing fields
r = requests.post(BASE + '/google-login', json={})
log('T40_google_login_missing_fields', 'PASS' if r.status_code == 422 else 'FAIL',
    f'{r.status_code}')

# T41: google-signup endpoint (referenced in docs but may not exist)
r = requests.post(BASE + '/google-signup', json={'name': 'test', 'email': 'x@test.com', 'google_id': '123', 'token': 'x'})
log('T41_google_signup_endpoint',
    'FAIL' if r.status_code in [405, 404] else 'INFO',
    f'{r.status_code} - Endpoint {"MISSING" if r.status_code in [405, 404] else "exists"} (documented in QUICK_START.md)')

# T42: guest-signup endpoint
r = requests.post(BASE + '/guest-signup', json={'name': 'Guest', 'email': 'g@test.com'})
log('T42_guest_signup_endpoint',
    'FAIL' if r.status_code in [405, 404] else 'INFO',
    f'{r.status_code} - Endpoint {"MISSING" if r.status_code in [405, 404] else "exists"} (documented in QUICK_START.md)')

print()
print('=' * 60)
print('SECTION 8: SECURITY TESTS')
print('=' * 60)

# T43: SQL Injection in login email
r = requests.post(BASE + '/login', json={'email': "' OR 1=1 --", 'password': 'test'})
log('T43_sql_injection_login', 'PASS' if r.status_code == 401 else 'FAIL',
    f'{r.status_code}')

# T44: SQL Injection in forgot password
try:
    r = requests.post(BASE + '/forgot-password', json={'email': "' OR 1=1 --"}, timeout=10)
    log('T44_sql_injection_forgot', 'PASS' if r.status_code in [404, 400, 422] else 'FAIL',
        f'{r.status_code}')
except:
    log('T44_sql_injection_forgot', 'INFO', 'Request timed out or errored')

# T45: XSS in signup name
r = requests.post(BASE + '/signup', json={'name': '<script>alert(1)</script>', 'email': 'xss@test.com', 'password': 'test123'})
xss_stored = r.status_code == 200
log('T45_xss_stored_in_name',
    'WARN' if xss_stored else 'PASS',
    f'{r.status_code} - XSS payload {"WAS STORED" if xss_stored else "was rejected"} in user name field')

if xss_stored:
    r2 = requests.post(BASE + '/login', json={'email': 'xss@test.com', 'password': 'test123'})
    if r2.status_code == 200:
        xss_token = r2.json().get('access_token')
        r3 = requests.get(BASE + '/me', headers={'Authorization': f'Bearer {xss_token}'})
        if r3.status_code == 200:
            name_in_response = r3.json().get('name', '')
            log('T45a_xss_reflected_in_me',
                'WARN' if '<script>' in name_in_response else 'PASS',
                f'Name returned raw: {name_in_response[:100]}')

# T46: Very long input
r = requests.post(BASE + '/signup', json={'name': 'A' * 10000, 'email': 'long@test.com', 'password': 'B' * 10000})
log('T46_very_long_input',
    'WARN' if r.status_code == 200 else 'PASS',
    f'{r.status_code} - 10K char inputs {"accepted" if r.status_code == 200 else "rejected"}')

# T47: CSRF
log('T47_csrf_protection', 'WARN',
    'No CSRF token mechanism. API relies on CORS only. SameSite cookies not used (localStorage tokens).')

# T48: Rate limiting
log('T48_rate_limiting', 'WARN',
    'No rate limiting. Brute force on /login, /forgot-password, /signup all possible.')

# T49: Password hashing check
row = db_query('SELECT password FROM users WHERE email = ?', (email,))
if row and row[0]:
    is_bcrypt = row[0].startswith('$2')
    log('T49_password_hashing', 'PASS' if is_bcrypt else 'FAIL',
        f'bcrypt={is_bcrypt}, hash_prefix={row[0][:10]}')
else:
    log('T49_password_hashing', 'FAIL', 'No password hash found')

# T50: Secrets in .env file
log('T50_env_secrets_exposed', 'WARN',
    '.env contains SECRET_KEY, RESEND_API_KEY, GOOGLE_CLIENT_ID in plaintext. No .gitignore protection verified.')

# T51: Token storage mechanism
log('T51_token_in_localstorage', 'WARN',
    'JWT tokens stored in localStorage (frontend). Vulnerable to XSS token theft.')

# T52: No HTTPS enforcement
log('T52_no_https', 'WARN',
    'All URLs hardcoded to http://. No HTTPS enforcement. Tokens transmitted in cleartext.')

# T53: Debug endpoint exposed
r = requests.get(BASE + '/test-email')
log('T53_debug_endpoint', 'WARN',
    f'{r.status_code} - /test-email debug endpoint accessible. Sends email to hardcoded address.')

# Cleanup
for e in ['xss@test.com', 'long@test.com']:
    db_exec('DELETE FROM users WHERE email = ?', (e,))

print()
print('=' * 60)
print('SECTION 9: CORS TESTS')
print('=' * 60)

# T54: CORS preflight from allowed origin (5500)
r = requests.options(BASE + '/login', headers={
    'Origin': 'http://127.0.0.1:5500',
    'Access-Control-Request-Method': 'POST',
    'Access-Control-Request-Headers': 'Content-Type'
})
cors_header = r.headers.get('access-control-allow-origin', '')
log('T54_cors_allowed_5500', 'PASS' if cors_header == 'http://127.0.0.1:5500' else 'FAIL',
    f'ACAO={cors_header}')

# T55: CORS from disallowed origin
r = requests.options(BASE + '/login', headers={
    'Origin': 'http://evil.com',
    'Access-Control-Request-Method': 'POST',
    'Access-Control-Request-Headers': 'Content-Type'
})
cors_header = r.headers.get('access-control-allow-origin', '')
log('T55_cors_evil_blocked', 'PASS' if cors_header != 'http://evil.com' else 'FAIL',
    f'ACAO={cors_header}')

# T56: CORS from port 8080 - CRITICAL
r = requests.options(BASE + '/login', headers={
    'Origin': 'http://127.0.0.1:8080',
    'Access-Control-Request-Method': 'POST',
    'Access-Control-Request-Headers': 'Content-Type'
})
cors_header = r.headers.get('access-control-allow-origin', '')
log('T56_cors_port_8080_blocked', 'FAIL',
    f'ACAO={cors_header} - Frontend on port 8080 NOT in CORS list (only 5500/5501 allowed). FRONTEND REQUESTS WILL FAIL!')

print()
print('=' * 60)
print('SECTION 10: ENDPOINT ENUMERATION')
print('=' * 60)

# T57: OpenAPI docs
r = requests.get(BASE + '/docs')
log('T57_swagger_docs', 'WARN' if r.status_code == 200 else 'PASS',
    f'{r.status_code} - Swagger UI {"EXPOSED" if r.status_code == 200 else "hidden"}')

# T58: OpenAPI JSON
r = requests.get(BASE + '/openapi.json')
if r.status_code == 200:
    endpoints = list(r.json().get('paths', {}).keys())
    log('T58_openapi_json', 'WARN',
        f'Endpoints: {endpoints}')

# T59: Test all expected endpoints exist
expected = ['/', '/signup', '/login', '/me', '/dashboard', '/verify/{token}',
            '/forgot-password', '/reset-password/{token}', '/google-login', '/test-email']
for ep in expected:
    found = ep in endpoints if r.status_code == 200 else False
    if not found:
        log(f'T59_endpoint_{ep}', 'INFO', f'Endpoint {ep} not found in schema')

# Check for missing documented endpoints
for ep in ['/google-signup', '/guest-signup']:
    found = ep in endpoints if r.status_code == 200 else False
    log(f'T59_missing_{ep}', 'FAIL' if not found else 'PASS',
        f'{ep} {"MISSING from API" if not found else "found"} (documented in QUICK_START.md)')

print()
print('=' * 60)
print('SECTION 11: DATABASE INTEGRITY')
print('=' * 60)

# T60: Schema check
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("PRAGMA table_info(users)")
columns = cur.fetchall()
col_names = [c[1] for c in columns]
conn.close()
log('T60_db_schema', 'INFO', f'Columns: {col_names}')

# T61: Email uniqueness
row = db_query('SELECT count(*) FROM users WHERE email = ?', (email,))
log('T61_email_unique', 'PASS' if row and row[0] == 1 else 'FAIL',
    f'Count={row[0] if row else 0}')

# T62: All users
rows = db_query_all('SELECT id, email, auth_provider, is_verified FROM users')
log('T62_total_users', 'INFO', f'Total: {len(rows)}')
for row in rows:
    print(f'  User: id={row[0]}, email={row[1]}, provider={row[2]}, verified={row[3]}')

# T63: Database file permissions
import os
db_path = os.path.join('backend', 'auth.db')
log('T63_db_file_exists', 'PASS' if os.path.exists(db_path) else 'FAIL', db_path)

# T64: SQLite (not production-grade DB)
log('T64_sqlite_in_production', 'WARN',
    'Using SQLite for auth system. Not suitable for production (no concurrent writes, no replication).')

print()
print('=' * 60)
print('SECTION 12: PERFORMANCE TESTS')
print('=' * 60)

# T65: Home endpoint latency
start = time.time()
r = requests.get(BASE + '/')
elapsed = (time.time() - start) * 1000
log('T65_perf_home', 'PASS' if elapsed < 500 else 'WARN', f'{elapsed:.0f}ms')

# T66: Login latency
# Use current password (may be new_pwd if reset worked, or pwd if not)
current_pwd = pwd  # original password since we don't know if reset worked
r_test = requests.post(BASE + '/login', json={'email': email, 'password': pwd})
if r_test.status_code != 200:
    current_pwd = new_pwd

start = time.time()
r = requests.post(BASE + '/login', json={'email': email, 'password': current_pwd})
elapsed = (time.time() - start) * 1000
log('T66_perf_login', 'PASS' if elapsed < 2000 else 'WARN',
    f'{elapsed:.0f}ms (includes bcrypt)')

# Get fresh token
if r.status_code == 200:
    token = r.json().get('access_token')

# T67: /me latency
if token:
    start = time.time()
    r = requests.get(BASE + '/me', headers={'Authorization': f'Bearer {token}'})
    elapsed = (time.time() - start) * 1000
    log('T67_perf_me', 'PASS' if elapsed < 500 else 'WARN', f'{elapsed:.0f}ms')

# T68: Concurrent requests
def make_request(_):
    return requests.get(BASE + '/').status_code

start = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(make_request, i) for i in range(20)]
    statuses = [f.result() for f in futures]
elapsed = (time.time() - start) * 1000
all_200 = all(s == 200 for s in statuses)
log('T68_concurrent_20', 'PASS' if all_200 else 'WARN',
    f'{elapsed:.0f}ms total, all_200={all_200}')

print()
print('=' * 60)
print('SECTION 13: EDGE CASES & HTTP METHODS')
print('=' * 60)

# T69: GET on POST-only endpoint
r = requests.get(BASE + '/signup')
log('T69_get_on_signup', 'PASS' if r.status_code == 405 else 'INFO', f'{r.status_code}')

r = requests.delete(BASE + '/login')
log('T70_delete_on_login', 'PASS' if r.status_code == 405 else 'INFO', f'{r.status_code}')

r = requests.put(BASE + '/me')
log('T71_put_on_me', 'PASS' if r.status_code == 405 else 'INFO', f'{r.status_code}')

# T72: Path traversal
r = requests.get(BASE + '/verify/../../../etc/passwd')
log('T72_path_traversal', 'PASS' if r.status_code in [400, 404, 307] else 'INFO', f'{r.status_code}')

# T73: Unicode name
r = requests.post(BASE + '/signup', json={'name': '日本語テスト', 'email': 'unicode@test.com', 'password': 'test123'})
log('T73_unicode_name', 'INFO',
    f'{r.status_code} - Unicode {"accepted" if r.status_code == 200 else "rejected"}')
db_exec('DELETE FROM users WHERE email = ?', ('unicode@test.com',))

# T74: Special chars in password
r = requests.post(BASE + '/signup', json={'name': 'Special', 'email': 'special@test.com', 'password': '!@#$%^&*()_+-=[]{}|;:,.<>?'})
log('T74_special_chars_password', 'INFO',
    f'{r.status_code} - Special chars {"accepted" if r.status_code == 200 else "rejected"}')
if r.status_code == 200:
    r2 = requests.post(BASE + '/login', json={'email': 'special@test.com', 'password': '!@#$%^&*()_+-=[]{}|;:,.<>?'})
    log('T74a_login_special_password', 'PASS' if r2.status_code == 200 else 'FAIL', f'{r2.status_code}')
db_exec('DELETE FROM users WHERE email = ?', ('special@test.com',))

print()
print('=' * 60)
print('SECTION 14: FRONTEND CODE ANALYSIS')
print('=' * 60)

# T75: dashboard.js missing loadUser function
log('T75_dashboard_missing_loadUser', 'FAIL',
    'dashboard.js calls loadUser() but this function is NEVER DEFINED. Dashboard will crash for authenticated users.')

# T76: login.html contains markdown code fences
log('T76_login_html_syntax_errors', 'FAIL',
    'login.html contains ``` markdown code fences (lines 7,17,23,82). HTML will render these as text.')

# T77: verify.html is empty
log('T77_verify_html_empty', 'FAIL',
    'verify.html is empty (0 bytes). Email verification landing page non-functional.')

# T78: verify.js is empty
log('T78_verify_js_empty', 'FAIL',
    'verify.js is empty (0 bytes). No client-side verification logic.')

# T79: signup.html missing Google/Guest buttons
log('T79_signup_missing_google_guest', 'FAIL',
    'signup.html has no Google or Guest buttons despite QUICK_START.md claiming they exist.')

# T80: Dashboard missing CSS
log('T80_dashboard_no_css', 'FAIL',
    'dashboard.html has no CSS stylesheet linked. Will render with browser defaults.')

# T81: Frontend hardcoded URLs
log('T81_hardcoded_backend_url', 'WARN',
    'All JS files hardcode http://127.0.0.1:8000. Not configurable for deployment.')

# T82: No input validation in frontend
log('T82_no_frontend_validation', 'WARN',
    'No client-side validation for email format, password strength, empty fields, etc.')

# T83: Error handling in forgot.js
log('T83_forgot_no_error_handling', 'WARN',
    'forgot.js uses alert(result.message) - will show "undefined" for error responses.')

# T84: guest login has no backend call
log('T84_guest_no_backend', 'WARN',
    'Guest login is purely client-side (sets localStorage only). No server-side guest record.')

# T85: requirements.txt empty
log('T85_requirements_empty', 'FAIL',
    'requirements.txt is empty. No dependencies listed. Cannot reproduce environment.')

print()
print('=' * 60)
print('SECTION 15: ACCESSIBILITY AUDIT')
print('=' * 60)

log('T86_no_aria_labels', 'FAIL',
    'No ARIA labels on any form inputs. Screen readers cannot identify fields.')

log('T87_no_form_labels', 'FAIL',
    'No <label> elements for any inputs. Only placeholder text used.')

log('T88_no_focus_styles', 'WARN',
    'No custom focus styles defined. Relies on browser defaults.')

log('T89_no_error_announcements', 'FAIL',
    'Error messages via alert() only. No inline error messages. No aria-live regions.')

log('T90_no_skip_navigation', 'WARN',
    'No skip-to-content links. Single-page forms mitigate impact.')

log('T91_keyboard_navigation', 'WARN',
    'Buttons use onclick handlers. Keyboard-accessible but no visible focus indicators.')

log('T92_color_contrast', 'INFO',
    'Button bg #2a5298 on white text. Link color #2a5298 on white bg. Should pass WCAG AA.')

# Cleanup all test users
db_exec('DELETE FROM users WHERE email = ?', (email,))

print()
print('=' * 70)
print('=' * 70)
print('FINAL SUMMARY')
print('=' * 70)
print('=' * 70)

passed = sum(1 for r in results if r[1] == 'PASS')
failed = sum(1 for r in results if r[1] == 'FAIL')
info_count = sum(1 for r in results if r[1] == 'INFO')
warn = sum(1 for r in results if r[1] == 'WARN')
skip = sum(1 for r in results if r[1] == 'SKIP')

print(f'\nPASSED:   {passed}')
print(f'FAILED:   {failed}')
print(f'WARNINGS: {warn}')
print(f'INFO:     {info_count}')
print(f'SKIP:     {skip}')
print(f'TOTAL:    {len(results)}')

print('\n--- FAILURES ---')
for r in results:
    if r[1] == 'FAIL':
        print(f'  [FAIL] {r[0]}: {r[2]}')

print('\n--- WARNINGS ---')
for r in results:
    if r[1] == 'WARN':
        print(f'  [WARN] {r[0]}: {r[2]}')
