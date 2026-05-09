import sqlite3

conn = sqlite3.connect('farm_pay.db')
cursor = conn.cursor()
cursor.execute('DROP TABLE IF EXISTS farmer_profiles')
print ('Successfull')

conn.commit()
conn.close()