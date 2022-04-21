"""Beskrivelse"""
#!/usr/bin/python3

import sqlite3
from sqlite3 import Error
import csv

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    connection = None
    try:
        connection = sqlite3.connect(db_file)
        print(sqlite3.version)

        # Creating a cursor object to execute
        # SQL queries on a database table
        cursor = connection.cursor()

        # Table Definition
        create_table = '''CREATE TABLE enhet(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    a TEXT NOT NULL,
                    b TEXT NOT NULL,
                    c TEXT NOT NULL,
                    d TEXT NOT NULL,
                    e TEXT NOT NULL,
                    f TEXT NOT NULL,
                    g TEXT NOT NULL,
                    h TEXT NOT NULL,
                    i TEXT NOT NULL,
                    j TEXT NOT NULL,
                    k TEXT NOT NULL,
                    l TEXT NOT NULL,
                    m TEXT NOT NULL,
                    n TEXT NOT NULL,
                    o TEXT NOT NULL);
                    '''

        # Creating the table into our
        # database
        cursor.execute(create_table)

        # Opening the csv file
        file = open('er_subset.csv')

        # Reading the contents of the
        # person-records.csv file
        contents = csv.reader(file)

        # SQL query to insert data into the
        # person table
        insert_records = "INSERT INTO enhet (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o) VALUES(?, ?)"

        # Importing the contents of the file
        # into our person table
        cursor.executemany(insert_records, contents)

        # SQL query to retrieve all data from
        # the person table To verify that the
        # data of the csv file has been successfully
        # inserted into the table
        select_all = "SELECT * FROM enhet"
        rows = cursor.execute(select_all).fetchall()

        # Output to the console screen
        for r in rows:
            print(r)

        # Committing the changes
        connection.commit()
    
        # closing the database connection
        connection.close()

    except Error as e:
        print(e)
    
    finally:
        if connection:
            connection.close()
 
if __name__ == '__main__':
    create_connection(r"er_sqlite10.db")