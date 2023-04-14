import sqlite3

db = sqlite3.connect("cost_accounting_base.db")

sql = db.cursor()

sql.execute("""CREATE TABLE IF NOT EXISTS cost_accounting (
               date DATETIME,
               cost REAL
               )
               """)
db.commit()
