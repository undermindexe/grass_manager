MIGRATIONS = [
    ("001_add_forward_email", "ALTER TABLE Accounts ADD COLUMN forward_email TEXT"),
    ("002_add_browser_context", "ALTER TABLE Accounts ADD COLUMN cookies TEXT"),
    ("003_add_storage_state", "ALTER TABLE Accounts ADD COLUMN storage_state TEXT"),
]
