"""
FranchiseOps AI - seed_data.py
Pre-seeds the database with realistic outlets, staff members, shift logs, and inventory benchmarks.
"""
from db import get_conn, init_db
from notifications import send_alert

def seed_all():
    init_db()
    with get_conn() as conn:
        # Seed Outlets
        if not conn.execute("SELECT count(*) FROM outlets").fetchone()[0]:
            outlets = [
                ("OUT-101", "Mumbai Flagship Store", "Mumbai (MH)", 145000, 112000, 24, 18.5, 4.2, "Tier 3 (At-Risk)", "High Attrition"),
                ("OUT-102", "Bengaluru Tech Hub Cafe", "Bengaluru (KA)", 285000, 165000, 32, 4.2, 4.8, "Tier 1 (Apex)", "Low Attrition"),
                ("OUT-103", "Delhi NCR Metro Express", "Delhi NCR (DL)", 210000, 155000, 28, 14.0, 4.5, "Tier 2 (Stable)", "Moderate Attrition"),
                ("OUT-104", "Hyderabad Central Hub", "Hyderabad (TG)", 125000, 118000, 18, 22.0, 3.8, "Tier 3 (At-Risk)", "Critical Attrition"),
                ("OUT-105", "Chennai Coastal Kiosk", "Chennai (TN)", 195000, 138000, 26, 6.5, 4.7, "Tier 1 (Apex)", "Low Attrition"),
                ("OUT-106", "Pune IT Park Outlet", "Pune (MH)", 172000, 129000, 22, 9.8, 4.4, "Tier 2 (Stable)", "Low Attrition"),
            ]
            conn.executemany("INSERT INTO outlets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)", outlets)

        # Seed Staff
        if not conn.execute("SELECT count(*) FROM staff").fetchone()[0]:
            staff = [
                ("ST-5001", "OUT-101", "Marcus Vance", "Shift Supervisor", 3920.0, 21.0, 2, 32, 4.5, 2, 0.82, "Retention Bonus Offered"),
                ("ST-5002", "OUT-101", "Elena Rostova", "Barista / Cashier", 2880.0, 19.5, 2, 26, 2.0, 2, 0.79, "Schedule Adjusted"),
                ("ST-5003", "OUT-102", "David Chen", "Store Manager", 5120.0, 3.5, 5, 41, 8.5, 4, 0.12, "Stable"),
                ("ST-5004", "OUT-104", "Samantha Diaz", "Kitchen Lead", 3360.0, 24.5, 1, 29, 3.0, 1, 0.89, "Immediate Review Required"),
                ("ST-5005", "OUT-105", "James Wilson", "Team Lead", 4000.0, 5.0, 4, 36, 6.0, 3, 0.18, "Stable"),
            ]
            conn.executemany("INSERT INTO staff (staff_id, outlet_id, employee_name, role, monthly_salary, weekly_overtime_hrs, job_satisfaction, employee_age, tenure_years, work_life_balance, predicted_attrition_prob, intervention_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", staff)

        # Seed Inventory
        if not conn.execute("SELECT count(*) FROM inventory_records").fetchone()[0]:
            inventory = [
                ("OUT-101", "Premium Coffee Beans (Kg)", 140, 320, 180, 0.84),
                ("OUT-101", "Organic Milk Syrups (L)", 85, 190, 100, 0.78),
                ("OUT-102", "Premium Coffee Beans (Kg)", 580, 450, 250, 0.12),
                ("OUT-104", "Eco-Packaging Cups (Box)", 40, 210, 150, 0.91),
                ("OUT-105", "Artisan Tea Blends (Kg)", 310, 220, 140, 0.15),
            ]
            conn.executemany("INSERT INTO inventory_records (outlet_id, sku_name, current_stock, weekly_demand, reorder_threshold, stockout_risk_prob) VALUES (?, ?, ?, ?, ?, ?)", inventory)
            conn.commit()

    send_alert("Email", "franchisee@franchiseops.ai", "Franchise Operations Initialized", "Database seeded with 6 regional outlets, staff logs, and inventory benchmarks.")
    print("✅ Database pre-seeded successfully.")
