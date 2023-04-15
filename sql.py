import sqlite3

db = sqlite3.connect("cost_accounting_base.db")

sql = db.cursor()

sql.execute("""CREATE TABLE cost_accounting (
               telegram_id BIGINT,
               date        DATETIME,
               cost        REAL,
               CONSTRAINT PK_cost_accounting PRIMARY KEY (date)
               );
               """)
db.commit()
db.close()
