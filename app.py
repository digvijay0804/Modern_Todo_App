import os
import datetime
import time
import psycopg2
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify

app = Flask(__name__)
def get_db_connection():
  """Establish a connection to PostgreSQL using DATABASE_URL."""
  while True:
      try:
          conn = psycopg2.connect(os.environ['DATABASE_URL'])
          return conn
      except OperationalError as e:
          print(f"Database connection failed: {e}. Retrying...")
          time.sleep(1)
# def initialize_database():
#     """Create table if not exists."""
#     conn = get_db_connection()
#     cur = conn.cursor()
  
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS my_table (
#             id SERIAL PRIMARY KEY,
#             name TEXT NOT NULL,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         );
#     """)
  
#     conn.commit()
#     cur.close()
#     conn.close()
# @app.route("/test-db")
# def test_db():
#     """Insert and return data from my_table to confirm DB works."""
#     conn = get_db_connection()
#     cur = conn.cursor(cursor_factory=RealDictCursor)


#     cur.execute("INSERT INTO my_table (name) VALUES (%s) RETURNING *;", ("test_name",))
#     new_row = cur.fetchone()
  
#     conn.commit()
#     cur.close()
#     conn.close()
  
#     return jsonify({
#         "message": "Database is working!",
#         "inserted_row": new_row
#     })
# ---------------- Ensure Tables Exist ---------------- #
@app.before_first_request
def setup_tables():
  """Create required tables if they don’t exist."""
  conn = get_db_connection()
  cur = conn.cursor()
  cur.execute("""
      CREATE TABLE IF NOT EXISTS students (
          student_id SERIAL PRIMARY KEY,
          first_name VARCHAR(50),
          last_name VARCHAR(50),
          birth_date DATE,
          email VARCHAR(100),
          enrolled_date DATE
      );
  """)
  cur.execute("""
      CREATE TABLE IF NOT EXISTS items (
          id SERIAL PRIMARY KEY,
          name VARCHAR(255) NOT NULL,
          description TEXT
      );
  """)
  conn.commit()
  cur.close()
  conn.close()
# ---------------- Root Endpoint ---------------- #
@app.route("/")
def home():
  return "Flask API with Prometheus metrics is running 🚀"
# ---------------- Students API ---------------- #
@app.route("/students", methods=["POST"])
def add_student():
  data = request.get_json()
  try:
      conn = get_db_connection()
      cur = conn.cursor()
      cur.execute("""
          INSERT INTO students (first_name, last_name, birth_date, email, enrolled_date)
          VALUES (%s, %s, %s, %s, %s)
          RETURNING student_id;
      """, (
          data.get("first_name"),
          data.get("last_name"),
          data.get("birth_date"),
          data.get("email"),
          data.get("enrolled_date"),
      ))
      student_id = cur.fetchone()[0]
      conn.commit()
      cur.close()
      conn.close()
      return jsonify({"message": "Student added successfully", "student_id": student_id}), 201
  except Exception as e:
      return jsonify({"error": str(e)}), 500
@app.route("/students", methods=["GET"])
def get_students():
  try:
      conn = get_db_connection()
      cur = conn.cursor(cursor_factory=RealDictCursor)
      cur.execute("SELECT * FROM students;")
      students = cur.fetchall()
      cur.close()
      conn.close()
      return jsonify(students), 200
  except Exception as e:
      return jsonify({"error": str(e)}), 500
@app.route("/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
  try:
      conn = get_db_connection()
      cur = conn.cursor(cursor_factory=RealDictCursor)
      cur.execute("SELECT * FROM students WHERE student_id = %s;", (student_id,))
      student = cur.fetchone()
      cur.close()
      conn.close()
      if student:
          return jsonify(student), 200
      else:
          return jsonify({"message": "Student not found"}), 404
  except Exception as e:
      return jsonify({"error": str(e)}), 500

# ---------------- Items API ---------------- #
@app.route('/items', methods=['POST'])
def create_item():
  data = request.get_json()
  name = data.get('name')
  description = data.get('description')
  if not name:
      return jsonify({'error': 'Name is required'}), 400
  conn = get_db_connection()
  cur = conn.cursor()
  cur.execute(
      "INSERT INTO items (name, description) VALUES (%s, %s) RETURNING id;",
      (name, description)
  )
  new_id = cur.fetchone()[0]
  conn.commit()
  cur.close()
  conn.close()
  return jsonify({'id': new_id, 'name': name, 'description': description}), 201
@app.route('/items', methods=['GET'])
def get_all_items():
  conn = get_db_connection()
  cur = conn.cursor()
  cur.execute("SELECT id, name, description FROM items;")
  items = cur.fetchall()
  cur.close()
  conn.close()
  return jsonify([
      {'id': item[0], 'name': item[1], 'description': item[2]} for item in items
  ])
@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
  conn = get_db_connection()
  cur = conn.cursor()
  cur.execute("SELECT id, name, description FROM items WHERE id = %s;", (item_id,))
  item = cur.fetchone()
  cur.close()
  conn.close()
  if item is None:
      return jsonify({'error': 'Item not found'}), 404
  return jsonify({'id': item[0], 'name': item[1], 'description': item[2]})
@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
  data = request.get_json()
  name = data.get('name')
  description = data.get('description')
  if not name and not description:
      return jsonify({'error': 'At least one field (name or description) is required'}), 400
  conn = get_db_connection()
  cur = conn.cursor()
  cur.execute("SELECT id FROM items WHERE id = %s;", (item_id,))
  if cur.fetchone() is None:
      cur.close()
      conn.close()
      return jsonify({'error': 'Item not found'}), 404
  cur.execute(
      "UPDATE items SET name = %s, description = %s WHERE id = %s;",
      (name, description, item_id)
  )
  conn.commit()
  cur.close()
  conn.close()
  return jsonify({'id': item_id, 'name': name, 'description': description})
@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
  conn = get_db_connection()
  cur = conn.cursor()
  cur.execute("SELECT id FROM items WHERE id = %s;", (item_id,))
  if cur.fetchone() is None:
      cur.close()
      conn.close()
      return jsonify({'error': 'Item not found'}), 404
  cur.execute("DELETE FROM items WHERE id = %s;", (item_id,))
  conn.commit()
  cur.close()
  conn.close()
  return jsonify({'message': f'Item with id {item_id} deleted successfully.'})
if __name__ == '__main__':
   os.environ.setdefault(
       'DATABASE_URL','postgresql://admin:12345@my_postgres:5432/mydatabase' )
# postgresql://     his tells psycopg2: Connect using the PostgreSQL database driver.
#Sahil              This is the PostgreSQL username
#12345             password for the database that you set
#localhost          url of you continer
#5432               this port number whre your continer is listening
#postgres     this defult db name that se 
   app.run(host='0.0.0.0', port=5000, debug=True)


