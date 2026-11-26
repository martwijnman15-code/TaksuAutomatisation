from .runtime import mydb, re

# crud managment
def query(query, params=None):
    cursor = mydb.cursor()

    try:
        cursor.execute(query, params or ())

        if cursor.with_rows:
            return cursor.fetchall()

        mydb.commit()
        return cursor.rowcount

    except mydb.connector.Error:
        mydb.rollback()
        raise

    finally:
        cursor.close()

def index_database(query, table):
    mycursor = mydb.cursor()

    mycursor.execute("SELECT " + query + " FROM " + table)
    myresult = mycursor.fetchall()
    mycursor.close()

    return myresult

def create_database(new_database):
    mycursor = mydb.cursor()

    mycursor.execute("CREATE DATABASE " + new_database)
    mycursor.execute(query)
    mydb.commit()

def create_table(new_table, columns):
    mycursor = mydb.cursor()

    query = "CREATE TABLE " + new_table + " ("

    # I choose for this solution, because you want to put more datatypes in a table
    # so I let it loop in a list that it is possible to do
    for i in range(len(columns)):
        column_name = columns[i][0]
        data_type = columns[i][1]

        query += column_name + " " + data_type

        if i < len(columns) - 1:
            query += ", "

    query += ")"

    mycursor.execute(query)
    mydb.commit()

def insert(database_name, table, columns):
    mycursor = mydb.cursor()

    query = "INSERT INTO " + table + " ("

    for i in range(len(columns)):
        column_name = columns[i][0]

        query += column_name

        if i < len(columns) - 1:
            query += ", "

    query += ") VALUES ("

    for i in range(len(columns)):
        query += "%s"

        if i < len(columns) - 1:
            query += ", "

    query += ")"

    values = []

    for i in range(len(columns)):
        values.append(columns[i][1])

    mycursor.execute(query, tuple(values))
    mydb.commit()

def update(database_name, table, id, columns):
    for name in [database_name, table] + [col[0] for col in columns]:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"Ongeldige database-, tabel- of kolomnaam: {name}")

    if not columns:
        raise ValueError("Geef minimaal één kolom mee")

    mycursor = mydb.cursor()

    try:
        assignments = []
        values = []

        for column_name, value in columns:
            assignments.append(f"`{column_name}` = %s")
            values.append(value)

        query = (
            f"UPDATE `{database_name}`.`{table}` "
            f"SET {', '.join(assignments)} WHERE `id` = %s"
        )

        values.append(id)
        mycursor.execute(query, values)
        mydb.commit()
    finally:
        mycursor.close()

def delete(database_name, table_name, id):
    mycursor = mydb.cursor()
    sql = "DELETE FROM " + table_name + " WHERE id = " + id
    mycursor.execute(id)
