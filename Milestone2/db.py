import sqlite3
from config import DB_PATH

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_conn() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS outlets (
            outlet_id TEXT PRIMARY KEY, outlet_name TEXT, city TEXT,
            monthly_revenue REAL, monthly_costs REAL, staff_headcount INTEGER,
            avg_overtime_hours REAL, customer_satisfaction REAL,
            tier_cluster TEXT, attrition_risk_level TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS staff (
            staff_id TEXT PRIMARY KEY, outlet_id TEXT, employee_name TEXT,
            role TEXT, monthly_salary REAL, weekly_overtime_hrs REAL,
            job_satisfaction INTEGER, employee_age INTEGER, tenure_years REAL,
            work_life_balance INTEGER, predicted_attrition_prob REAL,
            intervention_status TEXT DEFAULT 'Active')""")
        conn.execute("""CREATE TABLE IF NOT EXISTS inventory_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT, outlet_id TEXT,
            sku_name TEXT, current_stock INTEGER, weekly_demand INTEGER,
            reorder_threshold INTEGER, stockout_risk_prob REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS merged_datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT, agent_target TEXT, dataset_source TEXT,
            outlet_id TEXT, employee_age INTEGER, overtime_hours REAL,
            job_satisfaction INTEGER, attrition_target INTEGER, monthly_sales_usd REAL,
            operating_cost_usd REAL, tier_cluster_label INTEGER, sku_demand INTEGER,
            weather_impact_factor REAL, stockout_target INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE,
            email TEXT UNIQUE, password_hash TEXT,
            security_question TEXT, security_answer_hash TEXT,
            role TEXT DEFAULT 'User',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        try: conn.execute("ALTER TABLE users ADD COLUMN security_question TEXT")
        except Exception: pass
        try: conn.execute("ALTER TABLE users ADD COLUMN security_answer_hash TEXT")
        except Exception: pass
        conn.execute("""CREATE TABLE IF NOT EXISTS ml_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT, model_name TEXT, r2_score REAL,
            rmse REAL, accuracy REAL, training_rows INTEGER,
            file_path TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT, recipient TEXT, subject TEXT, message TEXT,
            status TEXT DEFAULT 'Sent',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.commit()

def save_ml_metrics(agent_name, model_name, r2, rmse, acc, rows, path):
    with get_conn() as conn:
        conn.execute("INSERT INTO ml_models "
                     "(agent_name,model_name,r2_score,rmse,accuracy,training_rows,file_path) "
                     "VALUES (?,?,?,?,?,?,?)",
                     (agent_name, model_name, r2, rmse, acc, rows, path))
        conn.commit()

def load_chat_history(username, conn_fn=None, limit=60):
    fn = conn_fn or get_conn
    with fn() as conn:
        rows = conn.execute(
            "SELECT role,content FROM chat_history WHERE username=? "
            "ORDER BY id DESC LIMIT ?", (username, limit)).fetchall()
    return [{"role":r[0],"content":r[1]} for r in reversed(rows)]

def save_chat_message(username, role, content, conn_fn=None):
    fn = conn_fn or get_conn
    with fn() as conn:
        conn.execute("INSERT INTO chat_history (username,role,content) VALUES (?,?,?)",
                     (username, role, content))
        conn.commit()

def clear_chat_history(username, conn_fn=None):
    fn = conn_fn or get_conn
    with fn() as conn:
        conn.execute("DELETE FROM chat_history WHERE username=?", (username,))
        conn.commit()
