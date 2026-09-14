import uuid
import os
import ssl
import json
import base64
import hashlib
import hmac
import secrets
import html
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, date
from email.message import EmailMessage
from io import BytesIO
import pandas as pd
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build as google_build
    from googleapiclient.http import MediaIoBaseUpload
except ImportError:
    Credentials = None
    google_build = None
    MediaIoBaseUpload = None

DB_FILE = Path('family_data.db')
UPLOAD_DIR = Path('uploads')
UPLOAD_DIR.mkdir(exist_ok=True)
TOTAL_PAGES = 11


S = [

{'p':2,'t':'Ready Reference','k':'ready_reference','type':'fixed','icon':'','rows':[
('Family Doctor',['Name','Office Address','Residence Address','Mobile / Contact Number']),
('Specialist Doctor (if any)',['Name','Office Address','Residence Address','Mobile / Contact Number']),
('Tax Consultant',['Name','Office Address','Residence Address','Mobile / Contact Number']),
('Insurance Agent',['Name','Office Address','Residence Address','Mobile / Contact Number']),
('Stock Broker',['Name','Office Address','Residence Address','Mobile / Contact Number'])]},
{'p':2,'t':'Mobile / Phone (Self)','k':'mobile_phone_self','type':'simple','icon':'','fields':['Mobile / Phone (Self)']},
{'p':2,'t':'Document Details','k':'document_details','type':'fixed','icon':'','rows':[
('Passport',['Number','Expiry Date']),
('Driving License',['Number','Expiry Date']),
('Credit Card / ATM Cards',['Number','Expiry Date']),
('Club Membership / Professional / Others',['Number','Expiry Date']),
('Vehicle Details',['Number','Expiry Date']),
('Income Tax PAN No.',['Number','Expiry Date']),
('Aadhar Card',['Number','Expiry Date'])]},


{'p':3,'t':'Location of Important Documents','k':'important_documents','type':'fixed','icon':'','rows':[
('Personal Will',['Location']),
("Spouse's Will",['Location']),
('Insurance Policies',['Location']),
('Invest. Papers',['Location']),
('Property Records',['Location']),
('Birth Certificate',['Location']),
('Marriage Certificate',['Location']),
('Domicile Certificate',['Location']),
('Important Agreements',['Location']),
('Other Important Papers',['Location'])]},
{'p':3,'t':'Insurance - LIC Policy Details','k':'lic_policy','type':'repeat','icon':'','columns':[
'Name / Nominee',
'Policy No. / Issuing Office',
'Amt. Insured',
'Issue Date / Maturity Date',
'Table & Term',
'Premium',
'Remarks'
],'sub':{
'Name / Nominee':['Nominee -'],
'Policy No. / Issuing Office':['Through Mr.'],
'Issue Date / Maturity Date':['Date of Last Payment','Date of Maturity']
}},


{'p':4,'t':'Medi Claim Policy Details','k':'medi_claim','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name & Type of Policy',
'Policy No. / Previous Policy No.',
'Amt. Insured',
'Issue Date / Maturity Date',
'Premium',
'Remarks'
]},
{'p':4,'t':'Vehicle Insurance Policy Details','k':'vehicle_insurance','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name / Vehicle',
'Policy No. / Issuing Office',
'Amt. Insured',
'Issue Date / Maturity Date',
'Premium',
'Remarks'
],'sub':{
'Name / Vehicle':[
'Model / Make',
'Engine No.',
'Chassis No.',
'Registration No.',
'Year of Mfg.',
'Agent Name',
'Mobile Number'
],
'Issue Date / Maturity Date':['Valid till']
}},
{'p':4,'t':'Fire / Burglary Insurance Details','k':'fire_burglary','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name of Property / Nominee',
'Policy No. / Issuing Office',
'Amt. Insured',
'Risks Covered',
'Issue Date / Maturity Date',
'Premium (Rs.)',
'Remarks'
]},


{'p':5,'t':'Bank Accounts','k':'bank_accounts','type':'repeat','icon':'','columns':[
'Bank Name',
'Branch',
'Type of Account',
'Operating Instructions',
'Nominee/s',
'Specimen Signature'
]},
{'p':5,'t':'Fixed Deposit / Recurring Deposit / Company Deposit','k':'deposits','type':'repeat','icon':'','columns':[
'Bank/ Company & Branch',
'Type of Dep. (FD/RD)',
'FDR No.',
'Date of Dep.',
'Fvg.',
'Amt. (Rs.)',
'Due Date',
'Op. Inst.',
'Nominee/s',
'Specimen Signature',
'Loan/OD availed'
]},


{'p':6,'t':'Shares / Unity / Debentures / Bonds','k':'shares_units','type':'repeat','icon':'','columns':[
'Company',
'No. of Shares',
'Demat A/c No.',
'Demat Bank details',
'Demat Statement location',
'Held singly / Jointly'
]},
{'p':6,'t':'Lockers','k':'lockers','type':'repeat','icon':'','columns':[
'Bank/ Name & Branch',
'Locker No.',
'In the Name of',
'Code',
'Rent (Rs.)',
'Rent Renewal Date',
'Nominee',
'Contents'
]},


{'p':7,'t':'Public Provident Fund (PPF)','k':'ppf','type':'repeat','icon':'','columns':[
'Bank Name & Branch',
'Fvg.',
'PPF A/c No.',
'Maturity Date',
'Nominee/s'
]},
{'p':7,'t':'Pension A/C.','k':'pension','type':'repeat','icon':'','columns':[
'Bank Name & Branch',
'Type of Account & Pension A/c No.',
'Operating Instructions',
'Pension Payment Order No.',
'Nominee/s',
'Due Date for Life Certificate',
'Signature'
]},
{'p':7,'t':'ATM / Debit Card Details','k':'atm_debit','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name',
'SB A/c No. / Bank & Branch',
'ATM / Debit Card No.',
'Issue Date',
'Valid Thru',
'CVV No.',
'Remarks'
],'sensitive':['ATM / Debit Card No.','CVV No.']},
{'p':7,'t':'Credit Card Details','k':'credit_cards','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name',
"Bank's Name",
'ATM / Debit Card No.',
'Valid From',
'Valid Thru',
'CVV No.',
'Remarks / T-Pin'
],'sensitive':['ATM / Debit Card No.','CVV No.','Remarks / T-Pin']},


{'p':8,'t':'PAN Card Details','k':'pan_cards','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name',
"Father's / Husband Name",
'PANCARD No. / Issue Date',
'Contact Details'
]},
{'p':8,'t':'Passport Details','k':'passports','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name',
'Passport No.',
'Issue Date',
'Expiry Date',
'Issuing Authority',
'Previous Passport Details'
]},
{'p':8,'t':'Electricity Details','k':'electricity','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name',
'House Details',
'Meter No.',
'Customer No.',
'Deposit Rs.',
'Remarks'
]},
{'p':8,'t':'Gas Pipe Line Details','k':'gas_pipeline','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name',
'House Details',
'Meter No. / Customer No. / Khata No.',
'Deposit Rs.',
'Remarks'
]},
{'p':8,'t':'Gas Cylinder Agency Service Details','k':'gas_cylinder','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name',
'House Details',
'Customer No.',
'IOC Serial No.',
'Deposit Rs.',
'Remarks'
]},


{'p':9,'t':'Land Line Details','k':'landline','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name',
'House Details',
'Phone No.',
'Customer ID / Account No.',
'Deposit LL / Broad Band / Wi Fi Rs.',
'Remarks'
]},
{'p':9,'t':'Driving License Details','k':'driving_license','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name',
'Driving License No. / Licensing Authority',
'Issue Date / CDOI',
'Valid From',
'Valid Till',
'Remarks / Blood Group'
]},
{'p':9,'t':'Ration Card Details','k':'ration_card','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name',
'Ration Card No. / Issuing Authority',
'Issue Date',
'Remarks'
]},
{'p':9,'t':'Aadhar Card - UID Details','k':'aadhaar','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name',
'Aadhar Card No. / Enrolment No.',
'Issue Date',
'Remarks'
]},


{'p':10,'t':'Election Identity Card - Details','k':'election_id','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name',
"Father's / Husband Name",
'Identity Card No.',
'Issue Date'
]},
{'p':10,'t':'House Property','k':'house_property','type':'repeat','icon':'','columns':[
'Property & Standing in the name of',
'How Acquired (Inherited / Loan) Bank Loan Details. Loan Amt. O/S + Amt.',
'Registration No. / Share Certificate No.',
'Nominee if any',
'Property Card No. & Valid upon',
'House Tax (Rs.)',
'Next Due Date of House Tax',
'Inst. Policy No. / Date & Due',
'Risks / Covered',
'Mortgage Bank & Branch / Place of Docs.'
]},
{'p':10,'t':'House Tax Details','k':'house_tax','type':'repeat','icon':'','columns':[
'Sr. No.',
'Name',
'House Details',
'Census No.',
'Property Identification No.',
'Construction Sq. Mtrs.',
'Remarks'
]},
{'p':10,'t':'Income Tax','k':'income_tax','type':'repeat','icon':'','columns':[
'Permanent Account Number',
'Ward No. & Office address',
'Last Return Filed',
'File No.'
]},


{'p':11,'t':'Will','k':'will','type':'simple','icon':'','fields':[
'My will is executed on',
'Copy of the will is kept at'
]},
{'p':11,'t':'Power of Attorney','k':'power_of_attorney','type':'simple','icon':'','fields':[
'Power of Attorney executed for wife/Son/Others',
'My Power of Attorney is',
'Deed Executed On',
'Details kept in File No.'
]},
{'p':11,'t':'My Debt / Liabilities','k':'debt_liabilities','type':'simple','icon':'','fields':[
'I am guarantor of Mr.',
'Give Complete Details - Guarantee 1',
'Give Complete Details - Guarantee 2',
'I have borrowed from',
'Give Complete Details - Borrowed',
'Other Liabilities'
]},
]


def safe(v):
    out = ''
    for c in str(v).lower():
        out += c if c.isalnum() else '_'
    while '__' in out:
        out = out.replace('__', '_')
    return out.strip('_')


def fields(sec):
    if sec['type'] == 'simple':
        return list(sec['fields'])
    if sec['type'] == 'fixed':
        return list(dict.fromkeys(f for _, fs in sec['rows'] for f in fs))
    result = list(sec['columns'])
    result += [
        f'{parent} :: {child}'
        for parent, children in sec.get('sub', {}).items()
        for child in children
    ]
    return result


PAGE_META = {
    2:("General Information","people"),
    3:("Documents & LIC","document"),
    4:("Insurance Policies","shield"),
    5:("Banking & Deposits","bank"),
    6:("Investments & Lockers","chart"),
    7:("PPF, Pension & Cards","card"),
    8:("IDs & Utilities — Part 1","id"),
    9:("IDs & Utilities — Part 2","phone"),
    10:("Property & Tax","home"),
    11:("Legal & Liabilities","legal")
}


SVG_ICONS = {
    "people":'<svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3"/><path d="M3.5 19c.6-3.2 2.5-5 5.5-5s4.9 1.8 5.5 5"/><circle cx="17" cy="9" r="2.3"/><path d="M15.5 14.2c2.6.2 4.2 1.7 5 4.8"/></svg>',
    "document":'<svg viewBox="0 0 24 24"><path d="M6 3h9l4 4v14H6z"/><path d="M15 3v5h5M9 12h6M9 16h6"/></svg>',
    "shield":'<svg viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 5-3.4 8.1-8 9-4.6-.9-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/></svg>',
    "bank":'<svg viewBox="0 0 24 24"><path d="M3 10h18M5 10v8M9 10v8M15 10v8M19 10v8M3 20h18M12 3l9 5H3z"/></svg>',
    "chart":'<svg viewBox="0 0 24 24"><path d="M4 19V5M4 19h17"/><path d="M7 15l4-4 3 2 6-7"/></svg>',
    "card":'<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M7 15h4"/></svg>',
    "id":'<svg viewBox="0 0 24 24"><rect x="4" y="3" width="16" height="18" rx="2"/><circle cx="12" cy="9" r="2.5"/><path d="M8 16c.8-2 2-3 4-3s3.2 1 4 3"/></svg>',
    "phone":'<svg viewBox="0 0 24 24"><path d="M7 3h3l1.5 4-2 1.5a15 15 0 0 0 6 6L17 12l4 1.5v3c0 2-1.5 3.5-3.5 3.5C10 20 4 14 4 6.5 4 4.5 5 3 7 3z"/></svg>',
    "home":'<svg viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10M9 20v-6h6v6"/></svg>',
    "legal":'<svg viewBox="0 0 24 24"><path d="M12 3v17M7 7h10M5 7l-3 6a3 3 0 0 0 6 0zM19 7l-3 6a3 3 0 0 0 6 0zM8 20h8"/></svg>',
    "bell":'<svg viewBox="0 0 24 24"><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></svg>'
}


def css():
    st.markdown("""
    <style>
    :root { --navy:#0b1730; --navy2:#122342; --ink:#15233b; --muted:#66758c; --line:#e6ebf2; --bg:#f6f8fb; --accent:#2457d6; }
    .stApp { background:var(--bg); color:var(--ink); }
    [data-testid="stSidebar"] { background:linear-gradient(180deg,#09152d 0%,#0d1d3b 100%); }
    [data-testid="stSidebar"] * { color:#edf3ff; }
    [data-testid="stSidebar"] .stRadio label { color:#d9e4f8 !important; }
    .brand { padding:10px 8px 22px; }
    .brand-icon { width:54px;height:54px;border-radius:16px;background:rgba(255,255,255,.10);display:flex;align-items:center;justify-content:center;margin-bottom:14px;border:1px solid rgba(255,255,255,.10); }
    .brand-icon svg { width:31px;height:31px;fill:none;stroke:#fff;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round; }
    .brand-title { font-size:20px;font-weight:750;line-height:1.12;letter-spacing:-.3px; }
    .brand-sub { margin-top:8px;font-size:11px;color:#aebbd2 !important;line-height:1.45; }
    .side-heading { margin:18px 8px 8px;text-transform:uppercase;letter-spacing:1.2px;font-size:10px;color:#8fa2c1 !important;font-weight:700; }
    .topbar { display:flex;align-items:center;justify-content:space-between;gap:18px;margin:2px 0 22px;padding-bottom:18px;border-bottom:1px solid var(--line); }
    .top-title { font-size:30px;font-weight:780;letter-spacing:-1px;line-height:1.1; }
    .top-sub { color:var(--muted);font-size:13px;margin-top:7px; }
    .secure { font-size:11px;color:#49617f;background:#eef3fb;border:1px solid #dbe4f1;padding:8px 12px;border-radius:999px;white-space:nowrap; }
    .top-actions { display:flex;gap:8px;align-items:center;justify-content:flex-end; }
    .welcome { display:flex;align-items:center;gap:18px;background:#fff;border:1px solid var(--line);border-radius:18px;padding:18px 20px;margin-bottom:24px;box-shadow:0 5px 18px rgba(18,35,66,.045); }
    .welcome-art { width:54px;height:54px;flex:0 0 54px;border-radius:15px;background:#edf3ff;display:flex;align-items:center;justify-content:center; }
    .welcome-art svg { width:32px;height:32px;fill:none;stroke:#2457d6;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round; }
    .welcome b { display:block;font-size:15px;margin-bottom:3px; }
    .welcome span { color:var(--muted);font-size:12px; }
    .page-head { display:flex;justify-content:space-between;align-items:flex-end;gap:16px;margin:5px 0 10px; }
    .kicker { color:#5e7190;font-size:10px;font-weight:800;letter-spacing:1.3px;text-transform:uppercase;margin-bottom:4px; }
    .page-title { font-size:25px;font-weight:760;letter-spacing:-.5px; }
    .counter { color:#64748b;font-size:12px;background:#fff;border:1px solid var(--line);padding:7px 11px;border-radius:999px;white-space:nowrap; }
    .section-head { display:flex;align-items:center;gap:12px;background:#fff;border:1px solid var(--line);border-bottom:0;border-radius:16px 16px 0 0;padding:15px 17px 11px;margin-top:22px; }
    .section-icon { width:34px;height:34px;border-radius:10px;background:#edf3ff;display:flex;align-items:center;justify-content:center;flex:0 0 34px; }
    .section-icon svg { width:19px;height:19px;fill:none;stroke:#2457d6;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round; }
    .section-title { font-weight:730;font-size:15px; }
    .section-body { background:#fff;border:1px solid var(--line);border-top:0;border-radius:0 0 16px 16px;padding:4px 17px 18px;box-shadow:0 5px 18px rgba(18,35,66,.035); }
    .subcard { background:#fbfcfe;border:1px solid #e7edf5;border-radius:13px;padding:14px 14px 12px;margin:12px 0;transition:box-shadow .15s ease,transform .15s ease,border-color .15s ease; }
    .subcard:hover { box-shadow:0 7px 20px rgba(18,35,66,.07);border-color:#d9e2ef;transform:translateY(-1px); }
    .subcard-title { font-size:13px;font-weight:720;margin-bottom:10px; }
    .upload { border:1px dashed #cbd6e6;background:#f8faff;border-radius:11px;padding:10px 12px;margin:10px 0 4px; }
    .upload-title { font-size:11px;font-weight:700;color:#324867; }
    .upload-sub { font-size:10px;color:#7a8aa0;margin-top:3px; }
    [data-testid="stFileUploaderDropzoneInstructions"] small { font-size:0 !important; }
    [data-testid="stFileUploaderDropzoneInstructions"] small::after { content:"Limit 1 GB per file · PDF, PNG, JPG, JPEG"; font-size:11px; }
    .saved-title { font-size:12px;font-weight:700;margin:15px 0 7px; }
    .overdue-row { background:#fff7f7;border:1px solid #f1dada;border-radius:9px;padding:8px 10px;margin:5px 0;font-size:11px;color:#7b3333; }
    .bottom-actions { display:flex;gap:10px;margin:22px 0 8px;padding:14px;background:#fff;border:1px solid var(--line);border-radius:15px; }
    .footer { text-align:center;color:#8491a4;font-size:10px;padding:25px 0 12px; }
    div[data-testid="stMetric"] { background:#fff;border:1px solid var(--line);border-radius:13px;padding:12px; }
    .stButton>button { border-radius:9px;font-weight:650; }

    /* Mobile/browser dark-mode fix: keep form controls readable */
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div {
        background:#ffffff !important;
    }
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea {
        background:#ffffff !important;
        color:#15233b !important;
        -webkit-text-fill-color:#15233b !important;
        caret-color:#15233b !important;
    }
    div[data-baseweb="input"] input::placeholder,
    div[data-baseweb="textarea"] textarea::placeholder {
        color:#66758c !important;
        -webkit-text-fill-color:#66758c !important;
        opacity:1 !important;
    }
    [data-testid="stSidebar"] .stButton>button { color:#ffffff !important; background:#122342 !important; border:1px solid rgba(255,255,255,.18) !important; }
    [data-testid="stSidebar"] .stButton>button:hover { color:#ffffff !important; background:#1a3158 !important; border-color:rgba(255,255,255,.28) !important; }
    .auth-shell { max-width:760px;margin:6vh auto 0; }
    .auth-card { text-align:center;background:#fff;border:1px solid var(--line);border-radius:20px;padding:28px 22px 20px;margin-bottom:16px;box-shadow:0 10px 30px rgba(18,35,66,.06); }
    .auth-brand { width:58px;height:58px;margin:0 auto 12px;border-radius:16px;background:#edf3ff;display:flex;align-items:center;justify-content:center; }
    .auth-brand svg { width:34px;height:34px;fill:none;stroke:#2457d6;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round; }
    .auth-title { font-size:24px;font-weight:780;letter-spacing:-.6px; }
    .auth-subtitle { color:var(--muted);font-size:12px;margin-top:5px; }
    </style>
    """, unsafe_allow_html=True)


def house_svg():
    return '<svg viewBox="0 0 24 24"><path d="M3 10.5 12 3l9 7.5"/><path d="M5.5 9.5V21h13V9.5M9 21v-6h6v6"/><path d="M8 11h.01M16 11h.01"/></svg>'


DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
REQUIRE_POSTGRES = os.getenv(
    'REQUIRE_POSTGRES',
    '1' if os.getenv('RAILWAY_ENVIRONMENT_NAME') else '0'
) == '1'

DB_FILE = Path(os.getenv('SQLITE_DB_FILE', 'family_data.db'))
ATTACHMENT_DIR = Path(os.getenv('ATTACHMENT_DIR', 'uploads'))
ATTACHMENT_DIR.mkdir(exist_ok=True)


AUTH_MIN_PASSWORD = 12


def _current_tenant_id():
    tid = st.session_state.get('tenant_id')
    if not tid:
        raise RuntimeError('Your session is not authenticated.')
    return str(tid)


def _hash_password(password, salt=None):
    if not isinstance(password, str) or len(password) < AUTH_MIN_PASSWORD:
        raise ValueError(
            f'Password must be at least {AUTH_MIN_PASSWORD} characters.'
        )

    salt = salt or secrets.token_bytes(16)

    digest = hashlib.scrypt(
        password.encode('utf-8'),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32
    )

    return salt.hex(), digest.hex()


def _verify_password(password, salt_hex, digest_hex):
    try:
        digest = hashlib.scrypt(
            password.encode('utf-8'),
            salt=bytes.fromhex(salt_hex),
            n=2**14,
            r=8,
            p=1,
            dklen=32
        )

        return hmac.compare_digest(
            digest.hex(),
            str(digest_hex)
        )
    except Exception:
        return False


def _normalize_email(email):
    return str(email or '').strip().lower()


def _auth_rate_limited(email):
    rows = _q(
        'SELECT attempted_at FROM auth_attempts '
        'WHERE email=:e ORDER BY attempted_at DESC LIMIT 5',
        {'e': email},
        fetch=True
    )

    if len(rows) < 5:
        return False

    try:
        return (
            datetime.now() -
            datetime.fromisoformat(rows[-1]['attempted_at'])
        ).total_seconds() < 15 * 60
    except Exception:
        return False


def _record_auth_failure(email):
    _q(
        'INSERT INTO auth_attempts(id,email,attempted_at) '
        'VALUES (:id,:e,:t)',
        {
            'id': uuid.uuid4().hex,
            'e': email,
            't': datetime.now().isoformat(timespec='seconds')
        }
    )


def _clear_auth_failures(email):
    _q(
        'DELETE FROM auth_attempts WHERE email=:e',
        {'e': email}
    )


def _authenticate(email, password):
    email = _normalize_email(email)

    if _auth_rate_limited(email):
        return None, (
            'Too many failed attempts. Please wait 15 minutes and try again.'
        )

    row = _q(
        'SELECT id,name,email,password_salt,password_hash '
        'FROM tenants WHERE email=:e LIMIT 1',
        {'e': email},
        fetch=True
    )

    if not row or not _verify_password(
        password,
        row[0]['password_salt'],
        row[0]['password_hash']
    ):
        _record_auth_failure(email)
        return None, 'Invalid email or password.'

    _clear_auth_failures(email)

    return row[0], None


def _create_tenant(name, email, password):
    name = str(name or '').strip()
    email = _normalize_email(email)

    if not name:
        raise ValueError('Family / account name is required.')

    if '@' not in email or '.' not in email.split('@')[-1]:
        raise ValueError('Enter a valid email address.')

    salt, digest = _hash_password(password)
    tid = uuid.uuid4().hex

    try:
        _q(
            'INSERT INTO tenants('
            'id,name,email,password_salt,password_hash,created_at'
            ') VALUES (:id,:n,:e,:s,:h,:t)',
            {
                'id': tid,
                'n': name,
                'e': email,
                's': salt,
                'h': digest,
                't': datetime.now().isoformat(timespec='seconds')
            }
        )
    except Exception as exc:
        if (
            'unique' in str(exc).lower()
            or 'duplicate' in str(exc).lower()
        ):
            raise ValueError(
                'An account with this email already exists.'
            )

        raise

    return tid


def _login(row):
    st.session_state.authenticated = True
    st.session_state.tenant_id = str(row['id'])
    st.session_state.tenant_name = str(row['name'])
    st.session_state.tenant_email = str(row['email'])

    for k in (
        'google_submission_id',
        'google_submission_fingerprint',
        'google_submission_success'
    ):
        st.session_state.pop(k, None)


def _logout():
    for k in list(st.session_state.keys()):
        st.session_state.pop(k, None)

    st.rerun()


def auth_gate():
    if (
        st.session_state.get('authenticated')
        and st.session_state.get('tenant_id')
    ):
        return True

    st.markdown(
        '<div class="auth-shell">'
        '<div class="auth-card">'
        '<div class="auth-brand">' + house_svg() + '</div>'
        '<div class="auth-title">My Family Should Know</div>'
        '<div class="auth-subtitle">Private family information vault</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    if st.session_state.get('show_signup'):
        auth_wrap = st.container()
        with auth_wrap:
            if st.button(
                'Back to sign in',
                key='back_to_signin',
                use_container_width=True
            ):
                st.session_state['show_signup'] = False
                st.rerun()

            st.markdown(
                '<div style="text-align:center;margin:8px 0 18px;">'
                '<div style="font-size:20px;font-weight:750;color:#15233b;">Create new account</div>'
                '<div style="color:#66758c;font-size:12px;margin-top:5px;">'
                'Create a separate private workspace. '
                f'Password must be at least {AUTH_MIN_PASSWORD} characters.'
                '</div></div>',
                unsafe_allow_html=True
            )

            with st.form('signup_form'):
                name = st.text_input('Family / account name')
                email = st.text_input(
                    'Email address',
                    key='signup_email'
                )
                pw = st.text_input(
                    'Password',
                    type='password',
                    key='signup_pw'
                )
                pw2 = st.text_input(
                    'Confirm password',
                    type='password',
                    key='signup_pw2'
                )
                submitted = st.form_submit_button(
                    'Create private account',
                    type='primary',
                    use_container_width=True
                )

            if submitted:
                if pw != pw2:
                    st.error('Passwords do not match.')
                else:
                    try:
                        tid = _create_tenant(name, email, pw)
                        row = _q(
                            'SELECT id,name,email FROM tenants '
                            'WHERE id=:id',
                            {'id': tid},
                            fetch=True
                        )[0]
                        _login(row)
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
    else:
        auth_wrap = st.container()
        with auth_wrap:
            with st.form('login_form'):
                email = st.text_input('Email address')
                password = st.text_input('Password', type='password')
                submitted = st.form_submit_button(
                    'Sign in',
                    type='primary',
                    use_container_width=True
                )

            if submitted:
                row, err = _authenticate(email, password)
                if err:
                    st.error(err)
                else:
                    _login(row)
                    st.rerun()

            st.markdown(
                '<div style="text-align:center;margin:14px 0 8px;'
                'color:#66758c;font-size:12px;">'
                'Don\'t have an account?</div>',
                unsafe_allow_html=True
            )

            if st.button(
                'Create new account',
                use_container_width=True,
                key='switch_to_signup'
            ):
                st.session_state['show_signup'] = True
                st.rerun()

    return False


try:
    from sqlalchemy import create_engine, text
except ImportError:
    create_engine = None
    text = None


@st.cache_resource(show_spinner=False)
def _engine():
    if REQUIRE_POSTGRES and not DATABASE_URL:
        raise RuntimeError(
            'PostgreSQL is required for the deployed multi-tenant '
            'application. Configure DATABASE_URL.'
        )

    if create_engine is None:
        raise RuntimeError(
            'SQLAlchemy is required. Install dependencies from requirements.txt.'
        )

    url = DATABASE_URL or f'sqlite:///{DB_FILE.resolve()}'

    if url.startswith('postgres://'):
        url = 'postgresql+psycopg2://' + url[len('postgres://'):]

    elif url.startswith('postgresql://'):
        url = 'postgresql+psycopg2://' + url[len('postgresql://'):]

    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
        future=True
    )


def _q(sql, params=None, fetch=False, many=False):
    params = params or {}

    with _engine().begin() as conn:
        result = conn.execute(text(sql), params)

        if fetch:
            return [dict(r._mapping) for r in result]

        return result.rowcount


def _placeholder_columns(sec):
    return (
        ['id', 'created_at', 'updated_at',
         'attachment_path', 'attachment_name']
        + (['row_label'] if sec['type'] == 'fixed' else [])
        + fields(sec)
    )


def init_db():
    _q("""CREATE TABLE IF NOT EXISTS tenants (
        id VARCHAR(64) PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_salt TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        created_at VARCHAR(40) NOT NULL
    )""")

    _q("""CREATE TABLE IF NOT EXISTS auth_attempts (
        id VARCHAR(64) PRIMARY KEY,
        email TEXT NOT NULL,
        attempted_at VARCHAR(40) NOT NULL
    )""")

    _q("""CREATE TABLE IF NOT EXISTS records (
        id VARCHAR(64) PRIMARY KEY,
        tenant_id VARCHAR(64) NOT NULL,
        section_key VARCHAR(120) NOT NULL,
        created_at VARCHAR(40) NOT NULL,
        updated_at VARCHAR(40) NOT NULL,
        row_label TEXT DEFAULT '',
        attachment_name TEXT DEFAULT '',
        attachment_path TEXT DEFAULT ''
    )""")

    _q("""CREATE TABLE IF NOT EXISTS record_values (
        record_id VARCHAR(64) NOT NULL,
        tenant_id VARCHAR(64) NOT NULL,
        field_name TEXT NOT NULL,
        field_value TEXT DEFAULT '',
        PRIMARY KEY(record_id, field_name)
    )""")

    if DATABASE_URL:
        _q("""CREATE TABLE IF NOT EXISTS attachments (
            record_id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(64) NOT NULL,
            filename TEXT NOT NULL,
            mime_type TEXT DEFAULT '',
            data BYTEA,
            drive_file_id TEXT DEFAULT '',
            drive_url TEXT DEFAULT '',
            size_bytes BIGINT DEFAULT 0,
            pending_path TEXT DEFAULT '',
            upload_status TEXT DEFAULT 'pending',
            upload_error TEXT DEFAULT ''
        )""")
    else:
        _q("""CREATE TABLE IF NOT EXISTS attachments (
            record_id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(64) NOT NULL,
            filename TEXT NOT NULL,
            mime_type TEXT DEFAULT '',
            data BLOB,
            drive_file_id TEXT DEFAULT '',
            drive_url TEXT DEFAULT '',
            size_bytes INTEGER DEFAULT 0,
            pending_path TEXT DEFAULT '',
            upload_status TEXT DEFAULT 'pending',
            upload_error TEXT DEFAULT ''
        )""")

    _q("""CREATE TABLE IF NOT EXISTS family_contacts (
        id VARCHAR(64) PRIMARY KEY,
        tenant_id VARCHAR(64) NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1,
        created_at VARCHAR(40) NOT NULL
    )""")

    _q("""CREATE TABLE IF NOT EXISTS app_settings (
        tenant_id VARCHAR(64) NOT NULL,
        key VARCHAR(120) NOT NULL,
        value TEXT NOT NULL,
        updated_at VARCHAR(40) NOT NULL,
        PRIMARY KEY(tenant_id,key)
    )""")

    _q("""CREATE TABLE IF NOT EXISTS reminder_log (
        tenant_id VARCHAR(64) NOT NULL,
        section_key TEXT NOT NULL,
        record_id VARCHAR(64) NOT NULL,
        field_name TEXT NOT NULL,
        due_date TEXT NOT NULL,
        days_before INTEGER NOT NULL,
        email TEXT NOT NULL,
        sent_at TEXT NOT NULL,
        PRIMARY KEY(
            tenant_id,
            section_key,
            record_id,
            field_name,
            due_date,
            days_before,
            email
        )
    )""")

    _q("""CREATE TABLE IF NOT EXISTS reminder_attempts (
        id VARCHAR(64) PRIMARY KEY,
        tenant_id VARCHAR(64) NOT NULL,
        section_key TEXT NOT NULL,
        record_id VARCHAR(64) NOT NULL,
        field_name TEXT NOT NULL,
        due_date TEXT NOT NULL,
        days_before INTEGER NOT NULL,
        email TEXT NOT NULL,
        attempted_at TEXT NOT NULL,
        status TEXT NOT NULL,
        error TEXT DEFAULT ''
    )""")

    if DATABASE_URL:
        tenant_tables = _q("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name IN (
                  'records',
                  'record_values',
                  'attachments',
                  'family_contacts',
                  'app_settings',
                  'reminder_log',
                  'reminder_attempts'
              )
              AND column_name = 'tenant_id'
        """, fetch=True)

        existing_tenant_columns = {
            str(r['table_name'])
            for r in tenant_tables
        }

    else:
        existing_tenant_columns = set()

        for table in (
            'records',
            'record_values',
            'attachments',
            'family_contacts',
            'app_settings',
            'reminder_log',
            'reminder_attempts'
        ):
            cols = _q(
                f'PRAGMA table_info({table})',
                fetch=True
            )

            if any(
                str(r.get('name')) == 'tenant_id'
                for r in cols
            ):
                existing_tenant_columns.add(table)

    for table in (
        'records',
        'record_values',
        'attachments',
        'family_contacts',
        'app_settings',
        'reminder_log',
        'reminder_attempts'
    ):
        if table not in existing_tenant_columns:
            _q(
                f'ALTER TABLE {table} '
                f'ADD COLUMN tenant_id VARCHAR(64)'
            )

    if DATABASE_URL:
        attachment_columns = {
            str(r['column_name'])
            for r in _q("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema=current_schema()
                  AND table_name='attachments'
            """, fetch=True)
        }
    else:
        attachment_columns = {
            str(r.get('name'))
            for r in _q(
                'PRAGMA table_info(attachments)',
                fetch=True
            )
        }

    if 'drive_file_id' not in attachment_columns:
        _q(
            "ALTER TABLE attachments "
            "ADD COLUMN drive_file_id TEXT DEFAULT ''"
        )

    if 'drive_url' not in attachment_columns:
        _q(
            "ALTER TABLE attachments "
            "ADD COLUMN drive_url TEXT DEFAULT ''"
        )

    if 'size_bytes' not in attachment_columns:
        _q(
            "ALTER TABLE attachments "
            "ADD COLUMN size_bytes BIGINT DEFAULT 0"
        )

    if 'pending_path' not in attachment_columns:
        _q(
            "ALTER TABLE attachments "
            "ADD COLUMN pending_path TEXT DEFAULT ''"
        )

    if 'upload_status' not in attachment_columns:
        _q(
            "ALTER TABLE attachments "
            "ADD COLUMN upload_status TEXT DEFAULT 'pending'"
        )

    if 'upload_error' not in attachment_columns:
        _q(
            "ALTER TABLE attachments "
            "ADD COLUMN upload_error TEXT DEFAULT ''"
        )

    if DATABASE_URL:
        pk_rows = _q("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name=kcu.constraint_name
             AND tc.table_schema=kcu.table_schema
            WHERE tc.table_name='app_settings'
              AND tc.constraint_type='PRIMARY KEY'
            ORDER BY kcu.ordinal_position
        """, fetch=True)

        pk_cols = [
            str(r['column_name'])
            for r in pk_rows
        ]

        if pk_cols == ['key']:
            legacy_name = (
                'app_settings_legacy_' +
                datetime.now().strftime('%Y%m%d_%H%M%S')
            )

            _q(
                f'ALTER TABLE app_settings '
                f'RENAME TO {legacy_name}'
            )

            _q("""CREATE TABLE app_settings (
                tenant_id VARCHAR(64) NOT NULL,
                key VARCHAR(120) NOT NULL,
                value TEXT NOT NULL,
                updated_at VARCHAR(40) NOT NULL,
                PRIMARY KEY(tenant_id,key)
            )""")

            _q(
                f'INSERT INTO app_settings('
                f'tenant_id,key,value,updated_at'
                f') SELECT tenant_id,key,value,updated_at '
                f'FROM {legacy_name} '
                f'WHERE tenant_id IS NOT NULL'
            )

    else:
        cols = _q(
            'PRAGMA table_info(app_settings)',
            fetch=True
        )

        key_pk = next(
            (
                int(r.get('pk') or 0)
                for r in cols
                if r.get('name') == 'key'
            ),
            0
        )

        tenant_pk = next(
            (
                int(r.get('pk') or 0)
                for r in cols
                if r.get('name') == 'tenant_id'
            ),
            0
        )

        if key_pk and not tenant_pk:
            _q(
                'CREATE TABLE app_settings_migrated ('
                'tenant_id VARCHAR(64) NOT NULL, '
                'key VARCHAR(120) NOT NULL, '
                'value TEXT NOT NULL, '
                'updated_at VARCHAR(40) NOT NULL, '
                'PRIMARY KEY(tenant_id,key))'
            )

            _q(
                'INSERT INTO app_settings_migrated('
                'tenant_id,key,value,updated_at'
                ') SELECT tenant_id,key,value,updated_at '
                'FROM app_settings '
                'WHERE tenant_id IS NOT NULL'
            )

            _q('DROP TABLE app_settings')

            _q(
                'ALTER TABLE app_settings_migrated '
                'RENAME TO app_settings'
            )


def _ensure_tenant_defaults():
    tid = _current_tenant_id()
    now = datetime.now().isoformat(timespec='seconds')

    for k, v in {
        'enabled': '1',
        'email_enabled': '1',
        'overdue_enabled': '1',
        'days_before': '30,15,7,1'
    }.items():
        _q(
            'INSERT INTO app_settings('
            'tenant_id,key,value,updated_at'
            ') VALUES (:tid,:k,:v,:t) '
            'ON CONFLICT(tenant_id,key) DO NOTHING',
            {
                'tid': tid,
                'k': k,
                'v': v,
                't': now
            }
        )


def _attachment_size(attachment):
    if attachment is None:
        return 0

    size = getattr(attachment, 'size', None)

    if isinstance(size, int) and size >= 0:
        return size

    try:
        pos = attachment.tell()
        attachment.seek(0, 2)
        size = attachment.tell()
        attachment.seek(pos)
        return int(size)
    except Exception:
        return 0


def _attachment_sha256(attachment):
    if attachment is None:
        return ''

    try:
        pos = attachment.tell()
        attachment.seek(0)

        digest = hashlib.sha256()

        while True:
            chunk = attachment.read(4 * 1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

        attachment.seek(pos)

        return digest.hexdigest()

    except Exception:
        return ''


def _draft_fingerprint(
    sec,
    vals,
    attachment=None,
    row_label=''
):
    material = {
        'section_key': sec['k'],
        'row_label': row_label or '',
        'values': {
            f: str(vals.get(f, '') or '')
            for f in fields(sec)
        },
        'attachment_name': (
            getattr(attachment, 'name', '')
            if attachment else ''
        ),
        'attachment_mime': (
            getattr(attachment, 'type', '')
            if attachment else ''
        ),
        'attachment_size': _attachment_size(attachment),
        'attachment_sha256': (
            _attachment_sha256(attachment)
            if attachment else ''
        ),
    }

    return hashlib.sha256(
        json.dumps(
            material,
            ensure_ascii=False,
            sort_keys=True,
            separators=(',', ':')
        ).encode('utf-8')
    ).hexdigest()


GOOGLE_DRIVE_FOLDER_ID = os.getenv(
    'GOOGLE_DRIVE_FOLDER_ID',
    os.getenv('DRIVE_FOLDER_ID', '')
).strip()


GOOGLE_DRIVE_OAUTH_CLIENT_JSON = os.getenv(
    'GOOGLE_DRIVE_OAUTH_CLIENT_JSON',
    ''
).strip()

GOOGLE_DRIVE_REFRESH_TOKEN = os.getenv(
    'GOOGLE_DRIVE_REFRESH_TOKEN',
    ''
).strip()

MAX_TOTAL_DOCUMENT_GB = float(
    os.getenv('MAX_TOTAL_DOCUMENT_GB', '50')
)

DRIVE_CHUNK_MB = max(
    8,
    int(os.getenv('DRIVE_UPLOAD_CHUNK_MB', '32'))
)

DRIVE_OAUTH_SCOPES = [
    'https://www.googleapis.com/auth/drive.file'
]


@st.cache_resource(show_spinner=False)
def _drive_service():
    if not GOOGLE_DRIVE_FOLDER_ID:
        raise RuntimeError(
            'GOOGLE_DRIVE_FOLDER_ID is not configured. Run google_drive_oauth_setup.py and set the generated folder ID for the OAuth-authorized Google account.'
        )

    if not GOOGLE_DRIVE_OAUTH_CLIENT_JSON:
        raise RuntimeError(
            'GOOGLE_DRIVE_OAUTH_CLIENT_JSON is not configured.'
        )

    if not GOOGLE_DRIVE_REFRESH_TOKEN:
        raise RuntimeError(
            'GOOGLE_DRIVE_REFRESH_TOKEN is not configured. Complete the one-time Google Drive OAuth setup first.'
        )

    if (
        Credentials is None
        or google_build is None
        or MediaIoBaseUpload is None
    ):
        raise RuntimeError(
            'Google Drive dependencies are missing. Install the packages from requirements.txt.'
        )

    try:
        client_config = json.loads(
            GOOGLE_DRIVE_OAUTH_CLIENT_JSON
        )
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            'GOOGLE_DRIVE_OAUTH_CLIENT_JSON is not valid JSON.'
        ) from exc

    config = (
        client_config.get('web')
        or client_config.get('installed')
        or client_config
    )

    client_id = str(config.get('client_id') or '').strip()
    client_secret = str(config.get('client_secret') or '').strip()

    if not client_id or not client_secret:
        raise RuntimeError(
            'GOOGLE_DRIVE_OAUTH_CLIENT_JSON does not contain a client_id and client_secret.'
        )

    creds = Credentials(
        token=None,
        refresh_token=GOOGLE_DRIVE_REFRESH_TOKEN,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=client_id,
        client_secret=client_secret,
        scopes=DRIVE_OAUTH_SCOPES,
    )

    return google_build(
        'drive',
        'v3',
        credentials=creds,
        cache_discovery=False
    )

def _drive_retry(
    operation,
    label,
    attempts=7
):
    delay = 1.0
    last_exc = None

    for attempt in range(attempts):
        try:
            return operation()

        except Exception as exc:
            last_exc = exc

            status = getattr(
                exc,
                'status_code',
                None
            )

            resp = getattr(
                exc,
                'resp',
                None
            )

            if status is None and resp is not None:
                status = getattr(
                    resp,
                    'status',
                    None
                )

            message = str(exc).lower()

            retryable = (
                status in {429, 500, 502, 503, 504}
                or any(
                    x in message
                    for x in (
                        'rate limit',
                        'quota',
                        'temporarily unavailable',
                        'timeout',
                        'timed out'
                    )
                )
            )

            if not retryable or attempt == attempts - 1:
                raise

            import random
            import time

            time.sleep(
                min(32.0, delay)
                + random.uniform(0, 1.0)
            )

            delay *= 2

    raise last_exc


def _drive_find_attachment(service, tenant_id, record_id):
    query = (
        "trashed = false and '" +
        str(GOOGLE_DRIVE_FOLDER_ID).replace("'", "\\'") +
        "' in parents and appProperties has { key='mfsk_tenant_id' and value='" +
        str(tenant_id).replace("'", "\\'") +
        "' } and appProperties has { key='mfsk_record_id' and value='" +
        str(record_id).replace("'", "\\'") +
        "' }"
    )
    response = _drive_retry(
        lambda: service.files().list(
            q=query,
            spaces='drive',
            fields='files(id,name,webViewLink,size)',
            pageSize=1,
            orderBy='createdTime desc',
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
        ).execute(),
        'Drive upload recovery lookup'
    )
    files = response.get('files') or []
    if not files:
        return None
    found = files[0]
    file_id = str(found.get('id') or '')
    if not file_id:
        return None
    url = str(
        found.get('webViewLink')
        or f'https://drive.google.com/open?id={file_id}'
    )
    return file_id, url, int(found.get('size') or 0)


def _drive_upload_attachment(
    tenant_id,
    record_id,
    attachment
):
    if attachment is None:
        return '', '', 0

    size = _attachment_size(attachment)

    if size <= 0:
        raise RuntimeError(
            'The selected document is empty.'
        )

    service = _drive_service()

    attachment.seek(0)

    mimetype = (
        getattr(attachment, 'type', '')
        or 'application/octet-stream'
    )

    metadata = {
        'name': safe(
            getattr(attachment, 'name', '')
            or ('document_' + str(record_id))
        ),
        'parents': [GOOGLE_DRIVE_FOLDER_ID],
        'appProperties': {
            'mfsk_tenant_id': str(tenant_id),
            'mfsk_record_id': str(record_id),
        },
    }


    existing = _drive_find_attachment(
        service,
        tenant_id,
        record_id
    )
    if existing:
        return existing


    response = None
    delay = 1.0
    request = None

    for attempt in range(7):
        try:
            existing = _drive_find_attachment(
                service, tenant_id, record_id
            )
            if existing:
                return existing

            if request is None:
                attachment.seek(0)
                media = MediaIoBaseUpload(
                    attachment,
                    mimetype=mimetype,
                    chunksize=-1,
                    resumable=True
                )
                request = _drive_retry(
                    lambda: service.files().create(
                        body=metadata,
                        media_body=media,
                        fields='id,name,webViewLink,size',
                    ),
                    'Drive upload initialization'
                )

            _, response = request.next_chunk()

            if response is not None:
                break

        except Exception as exc:
            status = getattr(exc, 'status_code', None)
            resp = getattr(exc, 'resp', None)
            if status is None and resp is not None:
                status = getattr(resp, 'status', None)

            message = str(exc).lower()
            retryable = (
                status in {400, 401, 403, 404, 408, 409, 429, 500, 502, 503, 504}
                and (
                    status not in {400, 401, 403, 404, 408, 409}
                    or any(x in message for x in ('rate limit','quota','resumable','upload session','temporarily unavailable','timeout','timed out'))
                )
            )

            if not retryable or attempt == 6:
                raise RuntimeError(
                    f'Google Drive upload failed: {exc}'
                ) from exc


            if status is not None and 400 <= int(status) < 500:
                request = None

            import random
            import time
            time.sleep(
                min(32.0, delay) + random.uniform(0, 1.0)
            )
            delay *= 2

    if response is None:
        raise RuntimeError(
            'Google Drive upload did not return a completed file.'
        )

    file_id = str(
        response.get('id') or ''
    )

    url = str(
        response.get('webViewLink')
        or f'https://drive.google.com/open?id={file_id}'
    )

    uploaded_size = int(
        response.get('size')
        or size
    )

    return file_id, url, uploaded_size


def _tenant_document_usage():
    rows = _q(
        'SELECT COALESCE(SUM(COALESCE(size_bytes,0)),0) '
        'AS total FROM attachments WHERE tenant_id=:tid',
        {'tid': _current_tenant_id()},
        fetch=True
    )

    return (
        int(rows[0]['total'] or 0)
        if rows else 0
    )


def _enforce_document_quota(new_size):
    limit = int(
        MAX_TOTAL_DOCUMENT_GB *
        1024 *
        1024 *
        1024
    )

    used = _tenant_document_usage()

    if used + int(new_size) > limit:
        raise RuntimeError(
            f'Document storage limit reached. '
            f'This family has used '
            f'{used / (1024**3):.2f} GB '
            f'of the configured '
            f'{MAX_TOTAL_DOCUMENT_GB:g} GB limit.'
        )


def save_once(
    sec,
    vals,
    attachment=None,
    row_label=''
):
    fp = _draft_fingerprint(
        sec,
        vals,
        attachment,
        row_label
    )

    saved = st.session_state.setdefault(
        'local_saved_fingerprints',
        {}
    )

    if fp in saved:
        return saved[fp][1], True

    rid = save(
        sec,
        vals,
        attachment,
        row_label
    )

    saved[fp] = (
        sec['k'],
        rid
    )

    return rid, False


def save(
    sec,
    vals,
    attachment=None,
    row_label=''
):
    now = datetime.now().isoformat(
        timespec='seconds'
    )

    rid = uuid.uuid4().hex

    attachment_size = _attachment_size(
        attachment
    )

    if attachment is not None:
        _enforce_document_quota(
            attachment_size
        )

    attachment_bytes = None

    if attachment is not None:
        attachment.seek(0)
        attachment_bytes = attachment.read()
        attachment.seek(0)
        if len(attachment_bytes) != attachment_size:
            raise RuntimeError('The selected document could not be read completely.')

    try:
        with _engine().begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO records(
                        id,
                        tenant_id,
                        section_key,
                        created_at,
                        updated_at,
                        row_label,
                        attachment_name,
                        attachment_path
                    )
                    VALUES (
                        :id,
                        :tid,
                        :s,
                        :c,
                        :u,
                        :l,
                        :an,
                        :ap
                    )
                """),
                {
                    'id': rid,
                    'tid': _current_tenant_id(),
                    's': sec['k'],
                    'c': now,
                    'u': now,
                    'l': row_label,
                    'an': (
                        attachment.name
                        if attachment else ''
                    ),
                    'ap': ''
                }
            )

            for f in fields(sec):
                conn.execute(
                    text(
                        'INSERT INTO record_values('
                        'record_id,tenant_id,field_name,field_value'
                        ') VALUES (:id,:tid,:f,:v)'
                    ),
                    {
                        'id': rid,
                        'tid': _current_tenant_id(),
                        'f': f,
                        'v': str(
                            vals.get(f, '')
                            or ''
                        )
                    }
                )

            if attachment:
                conn.execute(
                    text("""
                        INSERT INTO attachments(
                            record_id,
                            tenant_id,
                            filename,
                            mime_type,
                            data,
                            drive_file_id,
                            drive_url,
                            size_bytes,
                            pending_path,
                            upload_status,
                            upload_error
                        )
                        VALUES (
                            :id,
                            :tid,
                            :n,
                            :m,
                            :data,
                            '',
                            '',
                            :sz,
                            '',
                            'pending',
                            ''
                        )
                    """),
                    {
                        'id': rid,
                        'tid': _current_tenant_id(),
                        'n': attachment.name,
                        'm': attachment.type or '',
                        'sz': attachment_size,
                        'data': attachment_bytes
                    }
                )

    except Exception:


        raise

    return rid


def read(sec):
    rows = _q(
        '''
        SELECT
            r.id,
            r.created_at,
            r.updated_at,
            r.row_label,
            r.attachment_name,
            v.field_name,
            v.field_value
        FROM records r
        LEFT JOIN record_values v
          ON v.record_id=r.id
         AND v.tenant_id=r.tenant_id
        WHERE r.tenant_id=:tid
          AND r.section_key=:s
        ORDER BY r.created_at DESC
        ''',
        {
            'tid': _current_tenant_id(),
            's': sec['k']
        },
        fetch=True
    )

    headers = _placeholder_columns(sec)

    if not rows:
        return pd.DataFrame(
            columns=headers
        )

    grouped = {}

    for row in rows:
        rid = row['id']

        if rid not in grouped:
            grouped[rid] = {
                h: ''
                for h in headers
            }

            grouped[rid].update({
                'id': rid,
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'row_label': (
                    row.get('row_label')
                    or ''
                ),
                'attachment_name': (
                    row.get('attachment_name')
                    or ''
                )
            })

        if row.get('field_name') is not None:
            grouped[rid][
                row['field_name']
            ] = (
                row.get('field_value')
                or ''
            )

    return pd.DataFrame(
        list(grouped.values()),
        columns=headers
    )


GOOGLE_APPS_SCRIPT_URL = os.getenv(
    'GOOGLE_APPS_SCRIPT_URL',
    ''
).strip()

GOOGLE_SYNC_TOKEN = os.getenv(
    'GOOGLE_SYNC_TOKEN',
    ''
).strip()


def _all_records_for_sync():
    rows = _q(
        """
        SELECT
            r.id,
            r.section_key,
            r.created_at,
            r.updated_at,
            r.row_label,
            r.attachment_name,
            v.field_name,
            v.field_value
        FROM records r
        LEFT JOIN record_values v
          ON v.record_id=r.id
         AND v.tenant_id=r.tenant_id
        WHERE r.tenant_id=:tid
        ORDER BY r.created_at, v.field_name
        """,
        {
            'tid': _current_tenant_id()
        },
        fetch=True
    )

    by_id = {}

    for r in rows:
        rid = r['id']

        if rid not in by_id:
            by_id[rid] = {
                'record_id': rid,
                'section_key': r['section_key'],
                'created_at': r['created_at'],
                'updated_at': r['updated_at'],
                'row_label': (
                    r.get('row_label')
                    or ''
                ),
                'attachment_name': (
                    r.get('attachment_name')
                    or ''
                ),
                'values': {}
            }

        if r.get('field_name') is not None:
            by_id[rid]['values'][
                r['field_name']
            ] = (
                r.get('field_value')
                or ''
            )

    return list(
        by_id.values()
    )


def _upload_pending_attachment_row(r):
    if r.get('drive_file_id'):
        return (
            r['drive_file_id'],
            r.get('drive_url') or '',
            int(r.get('size_bytes') or 0)
        )

    path = str(
        r.get('pending_path')
        or ''
    )

    if path and Path(path).exists():
        upload = open(
            path,
            'rb'
        )

        upload.name = (
            r.get('filename')
            or Path(path).name
        )

        upload.type = (
            r.get('mime_type')
            or 'application/octet-stream'
        )

    else:
        raw = r.get('data')

        if raw is None:
            raise RuntimeError(
                f"Pending document "
                f"'{r.get('filename','document')}' "
                f"is missing from local storage."
            )

        if isinstance(raw, memoryview):
            raw = raw.tobytes()

        elif not isinstance(
            raw,
            (bytes, bytearray)
        ):
            raw = bytes(raw)

        upload = BytesIO(raw)

        upload.name = (
            r.get('filename')
            or (
                'document_' +
                str(r['record_id'])
            )
        )

        upload.type = (
            r.get('mime_type')
            or 'application/octet-stream'
        )

    try:
        _q(
            "UPDATE attachments "
            "SET upload_status='uploading',"
            "upload_error='' "
            "WHERE record_id=:rid "
            "AND tenant_id=:tid",
            {
                'rid': r['record_id'],
                'tid': _current_tenant_id()
            }
        )

        file_id, drive_url, uploaded_size = (
            _drive_upload_attachment(
                _current_tenant_id(),
                r['record_id'],
                upload
            )
        )

        _q(
            """
            UPDATE attachments
            SET
                drive_file_id=:fid,
                drive_url=:url,
                size_bytes=:sz,
                data=NULL,
                pending_path='',
                upload_status='uploaded',
                upload_error=''
            WHERE record_id=:rid
              AND tenant_id=:tid
            """,
            {
                'fid': file_id,
                'url': drive_url,
                'sz': (
                    uploaded_size
                    or int(
                        r.get('size_bytes')
                        or 0
                    )
                ),
                'rid': r['record_id'],
                'tid': _current_tenant_id()
            }
        )

        _q(
            'UPDATE records '
            'SET attachment_path=:url '
            'WHERE id=:rid '
            'AND tenant_id=:tid',
            {
                'url': drive_url,
                'rid': r['record_id'],
                'tid': _current_tenant_id()
            }
        )

        if path:
            try:
                Path(path).unlink(
                    missing_ok=True
                )
            except Exception:
                pass

        return (
            file_id,
            drive_url,
            uploaded_size
        )

    except Exception as exc:
        _q(
            "UPDATE attachments "
            "SET upload_status='pending',"
            "upload_error=:err "
            "WHERE record_id=:rid "
            "AND tenant_id=:tid",
            {
                'err': str(exc)[:1000],
                'rid': r['record_id'],
                'tid': _current_tenant_id()
            }
        )

        raise

    finally:
        try:
            upload.close()
        except Exception:
            pass


def finalize_pending_documents(
    progress=None
):
    rows = _q(
        """
        SELECT
            record_id,
            filename,
            mime_type,
            data,
            drive_file_id,
            drive_url,
            size_bytes,
            pending_path,
            upload_status,
            upload_error
        FROM attachments
        WHERE tenant_id=:tid
          AND COALESCE(drive_file_id,'')=''
        ORDER BY record_id
        """,
        {
            'tid': _current_tenant_id()
        },
        fetch=True
    )

    total = len(rows)
    uploaded = 0
    failed = []

    for index, row in enumerate(
        rows,
        1
    ):
        if progress:
            progress(
                index - 1,
                total,
                f"Uploading document {index} of {total}: "
                f"{row.get('filename') or 'document'}"
            )

        try:
            _upload_pending_attachment_row(
                row
            )

            uploaded += 1

        except Exception as exc:
            failed.append(
                (
                    row.get('filename')
                    or 'document',
                    str(exc)
                )
            )

            break

    if progress:
        progress(
            total if not failed else uploaded,
            total,
            'Document upload stage complete.'
        )

    return {
        'total': total,
        'uploaded': uploaded,
        'failed': failed
    }


def _migrate_legacy_attachments_for_sync():
    rows = _q(
        """
        SELECT
            record_id,
            filename,
            mime_type,
            data,
            drive_file_id,
            drive_url,
            size_bytes,
            pending_path,
            upload_status,
            upload_error
        FROM attachments
        WHERE tenant_id=:tid
          AND COALESCE(drive_file_id,'')=''
          AND (
              data IS NOT NULL
              OR COALESCE(pending_path,'')<>''
          )
        """,
        {
            'tid': _current_tenant_id()
        },
        fetch=True
    )

    for r in rows:
        _upload_pending_attachment_row(r)


def _attachment_links_for_sync():
    rows = _q(
        """
        SELECT
            record_id,
            filename,
            mime_type,
            drive_file_id,
            drive_url,
            size_bytes
        FROM attachments
        WHERE tenant_id=:tid
        """,
        {
            'tid': _current_tenant_id()
        },
        fetch=True
    )

    out = {}

    for r in rows:
        if (
            not r.get('drive_file_id')
            and not r.get('drive_url')
        ):
            continue

        out[r['record_id']] = {
            'filename': (
                r.get('filename')
                or ''
            ),
            'mime_type': (
                r.get('mime_type')
                or 'application/octet-stream'
            ),
            'drive_file_id': (
                r.get('drive_file_id')
                or ''
            ),
            'drive_url': (
                r.get('drive_url')
                or ''
            ),
            'size_bytes': int(
                r.get('size_bytes')
                or 0
            )
        }

    return out


def _new_submission_id():
    return uuid.uuid4().hex


def build_google_sync_payload(
    submission_id=None
):
    enabled, email_enabled, overdue_enabled, days = (
        _get_reminder_settings()
    )

    contacts = [
        {
            'name': n,
            'email': e
        }
        for _, n, e, _ in _get_contacts()
    ]

    return {
        'version': 4,
        'tenant_id': _current_tenant_id(),
        'tenant_name': st.session_state.get(
            'tenant_name',
            ''
        ),
        'submission_id': (
            submission_id
            or _new_submission_id()
        ),
        'submitted_at': datetime.now().isoformat(
            timespec='seconds'
        ),
        'auth_timestamp': int(
            datetime.now().timestamp() * 1000
        ),
        'auth_nonce': uuid.uuid4().hex,
        'records': _all_records_for_sync(),
        'attachment_links': _attachment_links_for_sync(),
        'reminders': {
            'enabled': enabled,
            'email_enabled': email_enabled,
            'overdue_enabled': overdue_enabled,
            'days_before': days,
            'contacts': contacts,
            'reminder_fields': REMINDER_FIELDS
        }
    }


def _submission_fingerprint(payload):
    stable = dict(payload)

    stable.pop(
        'submission_id',
        None
    )

    stable.pop(
        'submitted_at',
        None
    )

    stable.pop(
        'sync_token',
        None
    )

    stable.pop(
        'auth_timestamp',
        None
    )

    stable.pop(
        'auth_nonce',
        None
    )

    raw = json.dumps(
        stable,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':')
    ).encode('utf-8')

    return hashlib.sha256(
        raw
    ).hexdigest()


def submit_all_final():
    if (
        not GOOGLE_APPS_SCRIPT_URL
        or not GOOGLE_SYNC_TOKEN
    ):
        raise RuntimeError(
            'Google final submission is not configured. '
            'Set GOOGLE_APPS_SCRIPT_URL and GOOGLE_SYNC_TOKEN.'
        )

    progress_bar = st.progress(
        0,
        text='Preparing final submission…'
    )

    status_box = st.empty()

    def progress(
        done,
        total,
        message
    ):
        ratio = (
            1.0
            if total == 0
            else min(
                1.0,
                done / total
            )
        )

        progress_bar.progress(
            ratio,
            text=message
        )

        status_box.caption(message)

    result = finalize_pending_documents(
        progress=progress
    )

    if result['failed']:
        name, _ = result['failed'][0]

        progress_bar.empty()
        status_box.empty()

        raise RuntimeError(
            f"Document upload paused at '{name}'. "
            f"Press Submit All again to resume; "
            f"completed documents will not be uploaded again."
        )

    progress_bar.progress(
        1.0,
        text='All documents uploaded. Saving the complete family record…'
    )

    status_box.caption(
        'All documents are safely stored in Google Drive. '
        'Synchronizing the structured family record with Google Sheets…'
    )

    sync_result = sync_everything_to_google()

    progress_bar.empty()
    status_box.empty()

    return {
        'documents': result,
        'sheets': sync_result
    }


def sync_everything_to_google():
    if not GOOGLE_APPS_SCRIPT_URL:
        raise RuntimeError(
            'GOOGLE_APPS_SCRIPT_URL is not configured.'
        )

    if not GOOGLE_SYNC_TOKEN:
        raise RuntimeError(
            'GOOGLE_SYNC_TOKEN is not configured.'
        )

    state = st.session_state

    payload = build_google_sync_payload(
        state.get(
            'google_submission_id'
        )
    )

    fingerprint = _submission_fingerprint(
        payload
    )

    if (
        state.get(
            'google_submission_success'
        )
        and state.get(
            'google_submission_fingerprint'
        ) == fingerprint
    ):
        return {
            'success': True,
            'record_id': state.get(
                'google_submission_id'
            ),
            'duplicate': True,
            'rows': 0,
            'attachments': 0
        }

    if (
        state.get(
            'google_submission_fingerprint'
        ) != fingerprint
    ):
        payload['submission_id'] = (
            _new_submission_id()
        )

        payload['submitted_at'] = (
            datetime.now().isoformat(
                timespec='seconds'
            )
        )

        fingerprint = _submission_fingerprint(
            payload
        )

        state.google_submission_id = (
            payload['submission_id']
        )

        state.google_submission_fingerprint = (
            fingerprint
        )

        state.google_submission_success = False

    body = None
    delay = 1.0

    import random
    import time

    for attempt in range(7):


        payload['auth_timestamp'] = int(
            datetime.now().timestamp() * 1000
        )
        payload['auth_nonce'] = uuid.uuid4().hex

        signed_body = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(',', ':')
        )

        signature = hmac.new(
            GOOGLE_SYNC_TOKEN.encode('utf-8'),
            signed_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        envelope = {
            'payload': payload,
            'auth_signature': signature
        }

        raw = json.dumps(
            envelope,
            ensure_ascii=False,
            separators=(',', ':')
        ).encode('utf-8')

        request = urllib.request.Request(
            GOOGLE_APPS_SCRIPT_URL,
            data=raw,
            headers={
                'Content-Type': 'application/json'
            },
            method='POST'
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=120
            ) as response:
                body = response.read().decode(
                    'utf-8'
                )

            break

        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(
                'utf-8',
                errors='replace'
            )

            if (
                exc.code not in {
                    429,
                    500,
                    502,
                    503,
                    504
                }
                or attempt == 6
            ):
                raise RuntimeError(
                    f'Google sync failed ({exc.code}): '
                    f'{detail[:1000]}'
                ) from exc

            time.sleep(
                min(32.0, delay)
                + random.uniform(0, 1.0)
            )

            delay *= 2

        except (
            TimeoutError,
            urllib.error.URLError
        ) as exc:
            if attempt == 6:
                raise RuntimeError(
                    f'Google sync failed: {exc}'
                ) from exc

            time.sleep(
                min(32.0, delay)
                + random.uniform(0, 1.0)
            )

            delay *= 2

        except Exception as exc:
            raise RuntimeError(
                f'Google sync failed: {exc}'
            ) from exc

    if body is None:
        raise RuntimeError(
            'Google sync failed without a response.'
        )

    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        raise RuntimeError(
            'Google sync returned an invalid response.'
        )

    if not result.get('success'):
        raise RuntimeError(
            result.get(
                'error',
                'Google sync failed.'
            )
        )

    state.google_submission_success = True

    return result


REMINDER_FIELDS = {
    'lic_policy': [
        'Issue Date / Maturity Date :: Date of Maturity'
    ],
    'document_details': [
        'Expiry Date'
    ],
    'medi_claim': [
        'Issue Date / Maturity Date'
    ],
    'vehicle_insurance': [
        'Issue Date / Maturity Date :: Valid till'
    ],
    'fire_burglary': [
        'Issue Date / Maturity Date'
    ],
    'deposits': [
        'Due Date'
    ],
    'lockers': [
        'Rent Renewal Date'
    ],
    'ppf': [
        'Maturity Date'
    ],
    'pension': [
        'Due Date for Life Certificate'
    ],
    'atm_debit': [
        'Valid Thru'
    ],
    'credit_cards': [
        'Valid Thru'
    ],
    'passports': [
        'Expiry Date'
    ],
    'driving_license': [
        'Valid Till'
    ],
    'house_property': [
        'Next Due Date of House Tax'
    ],
}


def _settings():
    return {
        r['key']: r['value']
        for r in _q(
            'SELECT key,value FROM app_settings '
            'WHERE tenant_id=:tid',
            {
                'tid': _current_tenant_id()
            },
            fetch=True
        )
    }


def _get_reminder_settings():
    s = _settings()
    days = []

    for x in str(
        s.get(
            'days_before',
            '30,15,7,1'
        )
    ).split(','):
        try:
            n = int(x.strip())

            if n >= 0:
                days.append(n)

        except ValueError:
            pass

    return (
        s.get('enabled', '1') == '1',
        s.get('email_enabled', '1') == '1',
        s.get('overdue_enabled', '1') == '1',
        sorted(
            set(days),
            reverse=True
        )
    )


def _set_setting(key, value):
    _q(
        '''
        INSERT INTO app_settings(
            tenant_id,
            key,
            value,
            updated_at
        )
        VALUES (
            :tid,
            :k,
            :v,
            :t
        )
        ON CONFLICT(tenant_id,key)
        DO UPDATE SET
            value=:v,
            updated_at=:t
        ''',
        {
            'tid': _current_tenant_id(),
            'k': key,
            'v': str(value),
            't': datetime.now().isoformat(
                timespec='seconds'
            )
        }
    )


def _get_contacts():
    return [
        (
            r['id'],
            r['name'],
            r['email'],
            bool(r['active'])
        )
        for r in _q(
            'SELECT id,name,email,active '
            'FROM family_contacts '
            'WHERE tenant_id=:tid '
            'AND active=1 '
            'ORDER BY created_at',
            {
                'tid': _current_tenant_id()
            },
            fetch=True
        )
    ]


def _parse_reminder_date(value):
    if value is None or not str(value).strip():
        return None

    for fmt in (
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%d.%m.%Y',
        '%m/%d/%Y',
        '%m-%d-%Y',
        '%Y/%m/%d'
    ):
        try:
            return datetime.strptime(
                str(value).strip(),
                fmt
            ).date()

        except ValueError:
            pass

    try:
        return pd.to_datetime(
            value,
            dayfirst=True,
            errors='raise'
        ).date()

    except Exception:
        return None


def get_recent_reminder_failures(
    limit=10
):
    return [
        [
            r[k]
            for k in (
                'section_key',
                'record_id',
                'field_name',
                'due_date',
                'days_before',
                'email',
                'attempted_at',
                'status',
                'error'
            )
        ]
        for r in _q(
            """
            SELECT
                section_key,
                record_id,
                field_name,
                due_date,
                days_before,
                email,
                attempted_at,
                status,
                error
            FROM reminder_attempts
            WHERE tenant_id=:tid
              AND status='failed'
            ORDER BY attempted_at DESC
            LIMIT :n
            """,
            {
                'n': limit,
                'tid': _current_tenant_id()
            },
            fetch=True
        )
    ]


def _reminder_already_sent(
    section_key,
    record_id,
    field_name,
    due_date,
    days_before,
    email
):
    return bool(
        _q(
            """
            SELECT 1
            FROM reminder_log
            WHERE tenant_id=:tid
              AND section_key=:s
              AND record_id=:r
              AND field_name=:f
              AND due_date=:d
              AND days_before=:b
              AND email=:e
            LIMIT 1
            """,
            {
                'tid': _current_tenant_id(),
                's': section_key,
                'r': record_id,
                'f': field_name,
                'd': due_date.isoformat(),
                'b': days_before,
                'e': email
            },
            fetch=True
        )
    )


def get_reminder_snapshot(
    today=None
):
    today = today or date.today()
    out = []

    for sec in S:
        for field_name in REMINDER_FIELDS.get(
            sec['k'],
            []
        ):
            df = read(sec)

            if (
                df.empty
                or field_name not in df.columns
            ):
                continue

            for _, row in df.iterrows():
                due = _parse_reminder_date(
                    row.get(
                        field_name,
                        ''
                    )
                )

                if not due:
                    continue

                delta = (
                    due - today
                ).days

                out.append({
                    'section_key': sec['k'],
                    'section_title': sec['t'],
                    'record_id': str(
                        row.get(
                            'id',
                            ''
                        )
                    ),
                    'label': str(
                        row.get(
                            'row_label'
                        )
                        or sec['t']
                    ).strip(),
                    'field_name': field_name,
                    'due_date': due,
                    'status': (
                        'overdue'
                        if delta < 0
                        else (
                            'due_today'
                            if delta == 0
                            else 'upcoming'
                        )
                    ),
                    'overdue_days': (
                        abs(delta)
                        if delta < 0
                        else 0
                    ),
                    'days_until': delta
                })

    return out


def audit_reminder_schema():
    issues = []
    mapped = 0

    schema = {
        sec['k']: set(
            fields(sec)
        )
        for sec in S
    }

    for key, names in REMINDER_FIELDS.items():
        if key not in schema:
            issues.append(
                f'Missing section key: {key}'
            )
            continue

        for name in names:
            mapped += 1

            if name not in schema[key]:
                issues.append(
                    f'{key}: field "{name}" '
                    f'is not present in the schema.'
                )

    return {
        'ok': not issues,
        'mapped': mapped,
        'issues': issues
    }


def delete_contact(cid):
    _q(
        'DELETE FROM family_contacts '
        'WHERE id=:id AND tenant_id=:tid',
        {
            'id': cid,
            'tid': _current_tenant_id()
        }
    )


def add_contact(name, email):
    _q(
        'INSERT INTO family_contacts('
        'id,tenant_id,name,email,active,created_at'
        ') VALUES (:id,:tid,:n,:e,1,:t)',
        {
            'id': uuid.uuid4().hex,
            'tid': _current_tenant_id(),
            'n': name,
            'e': email,
            't': datetime.now().isoformat(
                timespec='seconds'
            )
        }
    )


def reminder_panel():
    enabled, email_enabled, overdue_enabled, days = (
        _get_reminder_settings()
    )

    audit = audit_reminder_schema()
    snapshot = get_reminder_snapshot(
        date.today()
    )

    due_count = sum(
        x['status'] == 'due_today'
        for x in snapshot
    )

    overdue_count = sum(
        x['status'] == 'overdue'
        for x in snapshot
    )

    contacts = _get_contacts()

    st.markdown(
        '<div class="section-head">'
        '<div class="section-icon">' +
        SVG_ICONS['bell'] +
        '</div>'
        '<div class="section-title">'
        'Family Renewal & Expiry Alerts'
        '</div>'
        '</div>'
        '<div class="section-body">',
        unsafe_allow_html=True
    )

    st.caption(
        'Automatic reminder emails are handled by Google Apps Script '
        'after the final family record is submitted. '
        'Streamlit does not send reminder emails.'
    )

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        'Due today',
        due_count
    )

    m2.metric(
        'Past due',
        overdue_count
    )

    m3.metric(
        'Recipients',
        len(contacts)
    )

    m4.metric(
        'Reminder windows',
        len(days)
    )

    if overdue_count:
        st.markdown('**Past-due items**')

        for item in [
            x
            for x in snapshot
            if x['status'] == 'overdue'
        ][:8]:
            safe_label = html.escape(
                str(
                    item.get(
                        'label',
                        ''
                    )
                )
            )

            safe_field = html.escape(
                str(
                    item.get(
                        'field_name',
                        ''
                    )
                )
            )

            due_text = item[
                'due_date'
            ].strftime(
                '%d %b %Y'
            )

            overdue_days = int(
                item.get(
                    'overdue_days',
                    0
                )
            )

            st.markdown(
                f'<div class="overdue-row">'
                f'<b>{safe_label}</b> · '
                f'{safe_field} · due '
                f'{due_text} · overdue by '
                f'{overdue_days} day(s)'
                f'</div>',
                unsafe_allow_html=True
            )

    with st.expander(
        'Reminder settings & family recipients',
        expanded=False
    ):
        c1, c2, c3 = st.columns(3)

        with c1:
            new_enabled = st.checkbox(
                'Enable automatic reminders',
                value=enabled,
                key='rem_enabled_ui'
            )

        with c2:
            new_email = st.checkbox(
                'Email notifications',
                value=email_enabled,
                key='rem_email_enabled_ui'
            )

        with c3:
            new_overdue = st.checkbox(
                'Daily past-due alerts',
                value=overdue_enabled,
                key='rem_overdue_ui'
            )

        new_days = st.multiselect(
            'Reminder windows',
            [30, 15, 7, 3, 1, 0],
            default=[
                x
                for x in days
                if x in [30, 15, 7, 3, 1, 0]
            ],
            format_func=lambda x:
                'On due date'
                if x == 0
                else f'{x} days before',
            key='rem_days_ui'
        )

        if st.button(
            'Save Reminder Settings',
            key='save_rem_settings_ui',
            type='primary',
            use_container_width=True
        ):
            _set_setting(
                'enabled',
                '1' if new_enabled else '0'
            )

            _set_setting(
                'email_enabled',
                '1' if new_email else '0'
            )

            _set_setting(
                'overdue_enabled',
                '1' if new_overdue else '0'
            )

            _set_setting(
                'days_before',
                ','.join(
                    map(
                        str,
                        sorted(
                            set(new_days),
                            reverse=True
                        )
                    )
                )
            )

            st.success(
                'Reminder settings saved. '
                'Submit the complete family record again '
                'to update Google.'
            )

        st.markdown(
            '#### Family email recipients'
        )

        for cid, name, email, active in contacts:
            c1, c2, c3 = st.columns(
                [2, 4, 1]
            )

            c1.write(name)
            c2.write(email)

            if c3.button(
                'Remove',
                key=f'rem_remove_{cid}'
            ):
                delete_contact(cid)
                st.rerun()

        c1, c2 = st.columns(2)

        with c1:
            new_name = st.text_input(
                'Family member name',
                key='rem_name_ui'
            )

        with c2:
            new_email = st.text_input(
                'Family member email',
                key='rem_email_ui'
            )

        if st.button(
            'Add Family Recipient',
            key='rem_add_ui',
            use_container_width=True
        ):
            if (
                not new_name.strip()
                or '@' not in new_email
                or '.' not in new_email.split('@')[-1]
            ):
                st.error(
                    'Enter a name and valid email address.'
                )

            else:
                try:
                    add_contact(
                        new_name.strip(),
                        new_email.strip()
                    )

                    st.success(
                        'Family recipient added. '
                        'Submit the complete family record again '
                        'to update Google.'
                    )

                    st.rerun()

                except Exception as exc:
                    st.error(
                        f'Could not add recipient: {exc}'
                    )

        if audit['ok']:
            st.success(
                f'Reminder schema audit passed: '
                f'{audit["mapped"]} mapped date fields verified.'
            )

        else:
            st.error(
                'Reminder schema audit failed.'
            )

            for issue in audit['issues']:
                st.write(issue)

    section_close()


def long_field(f):
    x = f.lower()

    return (
        len(f) > 38
        or any(
            w in x
            for w in [
                'address',
                'details',
                'location',
                'remarks',
                'instruction',
                'contents',
                'risk',
                'loan',
                'mortgage',
                'liabilities',
                'attorney',
                'signature',
                'property',
                'acquired'
            ]
        )
    )


def input_field(sec, f, key):
    if f in sec.get('sensitive', []):
        st.caption(
            f'{f} — sensitive field; value will not be stored.'
        )

    if long_field(f):
        return st.text_area(
            f,
            key=key,
            height=78
        )

    return st.text_input(
        f,
        key=key
    )


def uploader(sec, suffix, title=None):
    display_title = str(title or sec['t'])

    st.markdown(
        '<div class="upload">'
        '<div class="upload-title">'
        + html.escape(display_title)
        + '</div>'
        '<div class="upload-sub">'
        'PDF, PNG or JPG · 1 GB per file · stored securely with the family record'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    return st.file_uploader(
        display_title,
        type=[
            'pdf',
            'png',
            'jpg',
            'jpeg'
        ],
        key=f'up_{sec["k"]}_{suffix}',
        label_visibility='collapsed'
    )


def save_btn(label, key):
    return st.button(
        label,
        key=key,
        type='primary',
        use_container_width=True
    )


def section_header(sec):
    icon_key = PAGE_META.get(
        sec['p'],
        ('', 'document')
    )[1]

    svg = SVG_ICONS.get(
        icon_key,
        SVG_ICONS['document']
    )

    st.markdown(
        f'<div class="section-head">'
        f'<div class="section-icon">{svg}</div>'
        f'<div class="section-title">{sec["t"]}</div>'
        f'</div>'
        f'<div class="section-body">',
        unsafe_allow_html=True
    )


def section_close():
    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


def show_records(sec):
    df = read(sec)

    if df.empty:
        return

    st.markdown(
        '**Saved records**'
    )

    display = df.drop(
        columns=[
            'id',
            'created_at',
            'updated_at',
            'attachment_path'
        ],
        errors='ignore'
    ).copy()

    if 'attachment_name' in display:
        display.rename(
            columns={
                'attachment_name':
                    'Attachment'
            },
            inplace=True
        )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True
    )


def _draft_store():
    return st.session_state.setdefault(
        'page_drafts',
        {}
    )


def _remember_draft(
    sec,
    vals,
    attachments=None
):
    store = _draft_store()

    entry = store.setdefault(
        sec['k'],
        {
            'values': {},
            'attachment': None
        }
    )

    entry['values'] = dict(vals)

    if attachments is not None:
        entry['attachment'] = attachments


def render_fixed(sec):
    section_header(sec)

    store = _draft_store().setdefault(
        sec['k'],
        {
            'values': {},
            'attachment': {},
            'rows': {}
        }
    )

    store.setdefault(
        'rows',
        {}
    )

    for ri, (label, fs) in enumerate(
        sec['rows']
    ):
        st.markdown(
            '<div class="subcard">',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="subcard-title">'
            f'{label}'
            f'</div>',
            unsafe_allow_html=True
        )

        vals = {}

        for start in range(
            0,
            len(fs),
            2
        ):
            cs = st.columns(2)

            for j in range(2):
                i = start + j

                if i < len(fs):
                    with cs[j]:
                        vals[fs[i]] = input_field(
                            sec,
                            fs[i],
                            f'{sec["k"]}_{ri}_{safe(fs[i])}'
                        )

        att = uploader(
            sec,
            str(ri),
            label
        )

        store['rows'][ri] = {
            'values': dict(vals),
            'attachment': att
        }

        if save_btn(
            f'Save {label}',
            f'save_{sec["k"]}_{ri}'
        ):
            try:
                rid, duplicate = save_once(
                    sec,
                    vals,
                    att,
                    label
                )

                st.success(
                    f'{label} was already saved.'
                    if duplicate
                    else f'{label} saved successfully.'
                )

            except Exception as exc:
                st.error(
                    f'Save failed: {str(exc)}'
                )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    section_close()
    show_records(sec)


def render_simple(sec):
    section_header(sec)

    vals = {}
    fs = sec['fields']

    for start in range(
        0,
        len(fs),
        2
    ):
        cs = st.columns(2)

        for j in range(2):
            i = start + j

            if i < len(fs):
                with cs[j]:
                    vals[fs[i]] = input_field(
                        sec,
                        fs[i],
                        f'{sec["k"]}_{safe(fs[i])}'
                    )

    att = uploader(
        sec,
        'simple',
        sec['t']
    )

    _remember_draft(
        sec,
        vals,
        att
    )

    if save_btn(
        'Save Record',
        f'save_{sec["k"]}'
    ):
        try:
            rid, duplicate = save_once(
                sec,
                vals,
                att
            )

            st.success(
                'This record was already saved.'
                if duplicate
                else 'Saved successfully.'
            )

        except Exception as exc:
            st.error(
                f'Save failed: {str(exc)}'
            )

    section_close()
    show_records(sec)


def render_repeat(sec):
    section_header(sec)

    fs = fields(sec)

    if sec.get('sub'):
        st.caption(
            'Additional information shown inside the original '
            'table cells is captured as separate fields below.'
        )

    vals = {}

    for start in range(
        0,
        len(fs),
        2
    ):
        cs = st.columns(2)

        for j in range(2):
            i = start + j

            if i < len(fs):
                with cs[j]:
                    vals[fs[i]] = input_field(
                        sec,
                        fs[i],
                        f'{sec["k"]}_{safe(fs[i])}'
                    )

    att = uploader(
        sec,
        'repeat',
        sec['t']
    )

    _remember_draft(
        sec,
        vals,
        att
    )

    if save_btn(
        'Save Record',
        f'save_{sec["k"]}'
    ):
        for f in sec.get(
            'sensitive',
            []
        ):
            if f in vals:
                vals[f] = (
                    '[NOT STORED - SENSITIVE]'
                )

        try:
            rid, duplicate = save_once(
                sec,
                vals,
                att
            )

            st.success(
                'This record was already saved.'
                if duplicate
                else 'Saved successfully.'
            )

        except Exception as exc:
            st.error(
                f'Save failed: {str(exc)}'
            )

    section_close()
    show_records(sec)


def _reset_page_widgets(page):
    for sec in [
        x for x in S
        if x['p'] == page
    ]:
        for f in fields(sec):
            st.session_state.pop(
                f'{sec["k"]}_{safe(f)}',
                None
            )

        if sec['type'] == 'fixed':
            for ri, _ in enumerate(
                sec['rows']
            ):
                for f in fields(sec):
                    st.session_state.pop(
                        f'{sec["k"]}_{ri}_{safe(f)}',
                        None
                    )

                st.session_state.pop(
                    f'up_{sec["k"]}_{ri}',
                    None
                )

        else:
            st.session_state.pop(
                f'up_{sec["k"]}_'
                f'{"simple" if sec["type"] == "simple" else "repeat"}',
                None
            )

        st.session_state.get(
            'page_drafts',
            {}
        ).pop(
            sec['k'],
            None
        )

    saved = st.session_state.get(
        'local_saved_fingerprints',
        {}
    )

    for fp, item in list(
        saved.items()
    ):
        if (
            isinstance(item, tuple)
            and item[0] in {
                x['k']
                for x in S
                if x['p'] == page
            }
        ):
            saved.pop(
                fp,
                None
            )


def _save_all_current_page(page):
    saved = 0
    errors = []

    for sec in [
        x for x in S
        if x['p'] == page
    ]:
        entry = _draft_store().get(
            sec['k'],
            {}
        )

        try:
            if sec['type'] == 'fixed':
                for ri, (label, _) in enumerate(
                    sec['rows']
                ):
                    row = (
                        entry
                        .get('rows', {})
                        .get(ri, {})
                    )

                    row_vals = dict(
                        row.get(
                            'values'
                        )
                        or {}
                    )

                    row_att = row.get(
                        'attachment'
                    )

                    if (
                        any(
                            str(v).strip()
                            for v in row_vals.values()
                        )
                        or row_att is not None
                    ):
                        rid, duplicate = save_once(
                            sec,
                            row_vals,
                            row_att,
                            label
                        )

                        if not duplicate:
                            saved += 1

            else:
                vals = dict(
                    entry.get(
                        'values',
                        {}
                    )
                    or {}
                )

                row_att = entry.get('attachment')

                if (
                    (
                        not vals
                        or not any(
                            str(v).strip()
                            for v in vals.values()
                        )
                    )
                    and row_att is None
                ):
                    continue

                if sec.get('sensitive'):
                    for f in sec['sensitive']:
                        if f in vals:
                            vals[f] = (
                                '[NOT STORED - SENSITIVE]'
                            )

                rid, duplicate = save_once(
                    sec,
                    vals,
                    entry.get(
                        'attachment'
                    )
                )

                if not duplicate:
                    saved += 1

        except Exception as exc:
            errors.append(
                f'{sec["t"]}: {exc}'
            )

    return saved, errors


def page_actions(page):
    st.markdown(
        '<div class="bottom-actions">',
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(
        [1, 2]
    )

    with c1:
        if st.button(
            'Reset Form',
            key=f'reset_page_{page}',
            use_container_width=True
        ):
            _reset_page_widgets(page)
            st.rerun()

    with c2:
        if page == 11:
            if st.button(
                'Submit All',
                key='submit_all_final',
                type='primary',
                use_container_width=True
            ):
                try:
                    saved, errors = (
                        _save_all_current_page(11)
                    )

                    if errors:
                        raise RuntimeError(
                            'Could not save Page 11 locally: '
                            + '; '.join(errors)
                        )

                    with st.spinner(
                        'Finalizing the complete family record…'
                    ):
                        result = submit_all_final()

                    sheets = result.get(
                        'sheets',
                        {}
                    )

                    if sheets.get(
                        'duplicate'
                    ):
                        st.success(
                            'All documents are stored in Google Drive '
                            'and this exact family record is already '
                            'synchronized with Google Sheets.'
                        )
                    else:
                        st.success(
                            'Complete family record submitted successfully. '
                            'All documents are stored in Google Drive and '
                            'the structured record is synchronized with '
                            'Google Sheets.'
                        )

                except Exception as exc:
                    st.warning(
                        str(exc)
                    )

        else:
            if st.button(
                'Save All Above',
                key=f'save_all_page_{page}',
                type='primary',
                use_container_width=True
            ):
                saved, errors = (
                    _save_all_current_page(page)
                )

                if saved:
                    st.success(
                        f'{saved} record(s) saved from this page.'
                    )

                if errors:
                    for e in errors:
                        st.error(e)

                if (
                    not saved
                    and not errors
                ):
                    st.info(
                        'Nothing to save yet. '
                        'Fill in at least one field above.'
                    )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


def render_page(page):
    name, icon = PAGE_META[page]

    st.markdown(
        f'<div class="page-head">'
        f'<div>'
        f'<div class="kicker">PAGE {page}</div>'
        f'<div class="page-title">{name}</div>'
        f'</div>'
        f'<div class="counter">'
        f'Page {page} of {TOTAL_PAGES}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    st.progress(
        page / TOTAL_PAGES,
        text=f'Document progress · {page} / {TOTAL_PAGES}'
    )

    for sec in [
        x for x in S
        if x['p'] == page
    ]:
        if sec['type'] == 'fixed':
            render_fixed(sec)

        elif sec['type'] == 'repeat':
            render_repeat(sec)

        else:
            render_simple(sec)

    page_actions(page)


def dashboard():
    st.markdown(
        '<div class="page-head">'
        '<div>'
        '<div class="kicker">OVERVIEW</div>'
        '<div class="page-title">'
        'Family Information Dashboard'
        '</div>'
        '</div>'
        '<div class="counter">11 Pages</div>'
        '</div>',
        unsafe_allow_html=True
    )

    total = sum(
        len(read(x))
        for x in S
    )

    a, b, c = st.columns(3)

    a.metric(
        'Document Pages',
        '11'
    )

    b.metric(
        'Information Sections',
        len(S)
    )

    c.metric(
        'Saved Records',
        total
    )

    rows = []

    for p in range(2, 12):
        ss = [
            x for x in S
            if x['p'] == p
        ]

        rows.append([
            f'Page {p}',
            PAGE_META[p][0],
            len(ss),
            sum(
                len(read(x))
                for x in ss
            )
        ])

    st.dataframe(
        pd.DataFrame(
            rows,
            columns=[
                'Page',
                'Category',
                'Sections',
                'Saved Records'
            ]
        ),
        use_container_width=True,
        hide_index=True
    )

    google_export_panel()
    reminder_panel()


def google_export_panel():
    st.markdown(
        '<div class="section-head">'
        '<div class="section-icon">' +
        SVG_ICONS['document'] +
        '</div>'
        '<div class="section-title">'
        'Final Google Sync'
        '</div>'
        '</div>'
        '<div class="section-body">',
        unsafe_allow_html=True
    )

    st.markdown(
        '**Google Drive and Google Sheets are updated only '
        'from Submit All on Page 11.**'
    )

    section_close()


def google_export_page():
    st.markdown(
        '<div class="page-head">'
        '<div>'
        '<div class="kicker">GOOGLE SHEETS</div>'
        '<div class="page-title">'
        'Final Google Sync'
        '</div>'
        '</div>'
        '<div class="counter">'
        'One final request'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="welcome">'
        '<div class="welcome-art">' +
        SVG_ICONS['document'] +
        '</div>'
        '<div>'
        '<b>Ready to export</b>'
        '<span>'
        'Review the complete 11-page record. Submit All here '
        'uploads every pending document to Google Drive only now, '
        'then synchronizes the complete record to Google Sheets.'
        '</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    total = sum(
        len(read(x))
        for x in S
    )

    a, b, c = st.columns(3)

    a.metric(
        'Pages',
        '11'
    )

    b.metric(
        'Sections',
        len(S)
    )

    c.metric(
        'Saved Records',
        total
    )

    google_export_panel()

    st.markdown(
        '#### What gets exported'
    )

    st.markdown(
        '- All saved records from Pages 2–11\n'
        '- Supporting PDF/PNG/JPG documents stored in Google Drive, '
        'with links recorded in Google Sheets\n'
        '- Reminder settings and family email recipients\n'
        '- Reminder date mappings used by the automated Google Apps Script'
    )


st.set_page_config(
    page_title='My Family Should Know',
    page_icon=None,
    layout='wide',
    initial_sidebar_state='expanded'
)

css()
init_db()

if not auth_gate():
    st.stop()

_ensure_tenant_defaults()


with st.sidebar:
    st.markdown(
        '<div class="brand">'
        '<div class="brand-icon">' +
        house_svg() +
        '</div>'
        '<div class="brand-title">'
        'My Family<br>Should Know'
        '</div>'
        '<div class="brand-sub">'
        '11 Pages · Complete Coverage'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="side-heading">Main</div>',
        unsafe_allow_html=True
    )


    if '_pending_nav' in st.session_state:
        st.session_state.main_nav = (
            st.session_state.pop('_pending_nav')
        )

    main = st.radio(
        'Main',
        [
            'Dashboard',
            'Family Pages',
            'Google Sync'
        ],
        key='main_nav',
        label_visibility='collapsed'
    )

    st.markdown(
        '<div class="side-heading">'
        'Family record pages'
        '</div>',
        unsafe_allow_html=True
    )


    if main == 'Family Pages':
        opts = [
            f'Page {p}  ·  {PAGE_META[p][0]}'
            for p in range(2, 12)
        ]

        selected = st.radio(
            'Pages',
            opts,
            index=None,
            key='page_nav',
            label_visibility='collapsed'
        )

        page = None

        if selected:
            page = int(
                selected
                .split('Page ')[1]
                .split()[0]
            )
    else:


        st.session_state.pop('page_nav', None)
        page = None

    st.markdown(
        f'<div style="margin-top:14px;font-size:11px;opacity:.8">'
        f'Signed in as '
        f'<b>{html.escape(str(st.session_state.get("tenant_email","")))}</b>'
        f'</div>',
        unsafe_allow_html=True
    )

    if st.button(
        'Sign out',
        key='signout',
        use_container_width=True
    ):
        _logout()


h1, h2, h3, h4 = st.columns(
    [4, 1, 1, 1]
)

with h1:
    st.markdown(
        '<div class="topbar">'
        '<div>'
        '<div class="top-title">'
        'My Family Should Know'
        '</div>'
        '<div class="top-sub">'
        'Complete Family Information Management System'
        '</div>'
        '</div>'
        '<div class="secure">'
        'Secure & Organized'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

with h2:
    if st.button(
        'Dashboard',
        key='top_dashboard',
        use_container_width=True
    ):


        st.session_state['_pending_nav'] = 'Dashboard'
        st.rerun()

with h3:
    if st.button(
        'Family Pages',
        key='top_pages',
        use_container_width=True
    ):
        st.session_state['_pending_nav'] = 'Family Pages'
        st.rerun()

with h4:
    if st.button(
        'Google Sync',
        key='top_google',
        use_container_width=True
    ):


        st.session_state['_pending_nav'] = (
            'Google Sync'
        )
        st.rerun()


st.markdown(
    '<div class="welcome">'
    '<div class="welcome-art">' +
    house_svg() +
    '</div>'
    '<div>'
    '<b>Welcome</b>'
    '<span>'
    'Store, manage and organize important family information '
    'in one professional, secure place.'
    '</span>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)


if page is not None:
    render_page(page)

elif main == 'Dashboard':
    dashboard()

elif main == 'Family Pages':
    st.info('Select a page from the Family record pages list in the sidebar.')

elif main == 'Google Sync':
    google_export_page()


st.markdown(
    '<div class="footer">'
    'Your family data is stored in the configured application database. '
    '&nbsp;•&nbsp; Google Drive + Sheets sync is available when you are ready. '
    '&nbsp;•&nbsp; My Family Should Know'
    '</div>',
    unsafe_allow_html=True
)
