import requests
import sqlite3
import time
import sys
import traceback

BASE = 'http://127.0.0.1:8000'
DB_PATH = 'backend/auth.db'

results = []

def log(name, endpoint, status):
    results.append((name, endpoint, status))
    print(f"[{status}] {name} ({endpoint})")


def wait_for_server(timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(BASE + '/')
            if r.status_code == 200:
                print('Server is up')
                return True
        except Exception:
            pass
        time.sleep(0.5)
    print('Server did not become ready')
    return False


def db_exec(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    cur.close()
    conn.close()


def db_query(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def cleanup_emails(emails):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for e in emails:
        cur.execute('DELETE FROM users WHERE email = ?', (e,))
    conn.commit()
    cur.close()
    conn.close()


try:
    if not wait_for_server(15):
        log('server_ready','/', 'FAIL')
        sys.exit(2)
    else:
        log('server_ready','/', 'PASS')

    # Prepare unique emails
    ts = int(time.time())
    email = f'test_email_{ts}@example.com'
    pwd = 'TestPass123'
    google_email = f'test_google_{ts}@example.com'
    guest_email = f'test_guest_{ts}@example.com'

    # Ensure no leftover
    cleanup_emails([email, google_email, guest_email])

    # 1) Signup
    r = requests.post(BASE + '/signup', json={
        'name': 'Tester', 'email': email, 'password': pwd
    })
    if r.status_code == 200:
        log('signup', '/signup', 'PASS')
    else:
        log('signup', '/signup', 'FAIL')
        print(r.status_code, r.text)
        raise SystemExit(1)

    # 2) Retrieve verification token from DB
    row = db_query('SELECT verification_token FROM users WHERE email = ?', (email,))
    if row and row[0]:
        vtoken = row[0]
        log('retrieved_verification_token', 'db', 'PASS')
    else:
        log('retrieved_verification_token', 'db', 'FAIL')
        raise SystemExit(1)

    # 3) Verify email
    r = requests.get(BASE + f'/verify/{vtoken}')
    if r.status_code == 200:
        log('verify_email', f'/verify/{vtoken}', 'PASS')
    else:
        log('verify_email', f'/verify/{vtoken}', 'FAIL')
        print(r.status_code, r.text)
        raise SystemExit(1)

    # 4) Login
    r = requests.post(BASE + '/login', json={'email': email, 'password': pwd})
    if r.status_code == 200:
        token = r.json().get('access_token')
        log('login', '/login', 'PASS')
    else:
        log('login', '/login', 'FAIL')
        print(r.status_code, r.text)
        raise SystemExit(1)

    # 5) Me endpoint
    headers = {'Authorization': 'Bearer ' + token}
    r = requests.get(BASE + '/me', headers=headers)
    if r.status_code == 200 and r.json().get('email') == email:
        log('me', '/me', 'PASS')
    else:
        log('me', '/me', 'FAIL')
        print(r.status_code, r.text)
        raise SystemExit(1)

    # 6) Forgot password
    r = requests.post(BASE + '/forgot-password', json={'email': email})
    if r.status_code == 200:
        log('forgot_password_request', '/forgot-password', 'PASS')
    else:
        log('forgot_password_request', '/forgot-password', 'FAIL')
        print(r.status_code, r.text)
        raise SystemExit(1)

    # 7) Get reset token from DB
    row = db_query('SELECT reset_token FROM users WHERE email = ?', (email,))
    if row and row[0]:
        rtoken = row[0]
        log('retrieved_reset_token', 'db', 'PASS')
    else:
        log('retrieved_reset_token', 'db', 'FAIL')
        raise SystemExit(1)

    # 8) Reset password
    new_pwd = 'NewPass123'
    r = requests.post(BASE + f'/reset-password/{rtoken}', json={'password': new_pwd})
    if r.status_code == 200:
        log('reset_password', f'/reset-password/{rtoken}', 'PASS')
    else:
        log('reset_password', f'/reset-password/{rtoken}', 'FAIL')
        print(r.status_code, r.text)
        raise SystemExit(1)

    # 9) Login with new password
    r = requests.post(BASE + '/login', json={'email': email, 'password': new_pwd})
    if r.status_code == 200:
        token = r.json().get('access_token')
        log('login_after_reset', '/login', 'PASS')
    else:
        log('login_after_reset', '/login', 'FAIL')
        print(r.status_code, r.text)
        raise SystemExit(1)

    # 10) Google signup
    g_id = f'google_{ts}'
    r = requests.post(BASE + '/google-signup', json={
        'name': 'GTester', 'email': google_email, 'google_id': g_id, 'token': 'mock'
    })
    if r.status_code == 200:
        gtoken = r.json().get('access_token')
        log('google_signup', '/google-signup', 'PASS')
    else:
        log('google_signup', '/google-signup', 'FAIL')
        print(r.status_code, r.text)
        raise SystemExit(1)

    # 11) Google login
    r = requests.post(BASE + '/google-login', json={'google_id': g_id, 'token': 'mock'})
    if r.status_code == 200:
        log('google_login', '/google-login', 'PASS')
    else:
        log('google_login', '/google-login', 'FAIL')
        print(r.status_code, r.text)
        raise SystemExit(1)

    # 12) Guest signup
    r = requests.post(BASE + '/guest-signup', json={'name': 'Guest', 'email': guest_email})
    if r.status_code == 200:
        log('guest_signup', '/guest-signup', 'PASS')
    else:
        log('guest_signup', '/guest-signup', 'FAIL')
        print(r.status_code, r.text)
        raise SystemExit(1)

    # All tests passed
    print('\nTEST SUMMARY:')
    for t in results:
        print(t)
    print('\nALL TESTS PASSED')
    sys.exit(0)

except SystemExit as e:
    print('\nTESTS FAILED OR STOPPED')
    for t in results:
        print(t)
    sys.exit(getattr(e, 'code', 1))

except Exception as e:
    traceback.print_exc()
    print('\nUNEXPECTED ERROR - TESTS FAILED')
    for t in results:
        print(t)
    sys.exit(1)
