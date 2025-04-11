

MIGRATIONS = [
    (
        "001_add_forward_email",
        "ALTER TABLE Accounts ADD COLUMN forward_email TEXT"
    ),
]