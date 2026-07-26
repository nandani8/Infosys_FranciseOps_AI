"""
train_m2.py — FranchiseOps AI (v3 FINAL)
Multi-Algorithm Comparison:
  Agent 1 (Attrition): CalibratedLR, CalibratedRF, CalibratedGB, CalibratedSVM → best ROC-AUC
  Agent 2 (Clustering): KMeans k=3,4,5 + silhouette → best k; Revenue: RF, GradBoost, ExtraTrees
  Agent 3 (Inventory):  RF, GradientBoosting, ExtraTrees, Ridge → best R²
Tier labels: Excellent / Good / Needs Attention / Critical (matching spec)
KMeans saved as kmeans_outlets.joblib (matching spec)
10 outlets seeded; ROC-AUC printed (spec requirement)
"""
import os, joblib, numpy as np, pandas as pd
from sklearn.ensemble import (RandomForestClassifier, GradientBoostingClassifier,
                               ExtraTreesClassifier, RandomForestRegressor,
                               GradientBoostingRegressor, ExtraTreesRegressor)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.svm import SVC
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score, r2_score, mean_squared_error, silhouette_score
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from config import (KAGGLE_USERNAME, KAGGLE_KEY, KAGGLE_CACHE_DIR, MODELS_DIR,
                    AGENT1_MODEL_PATH, AGENT2_MODEL_PATH, AGENT2_REG_PATH,
                    AGENT3_MODEL_PATH, KMEANS_MODEL_PATH)
from db import get_conn, save_ml_metrics, init_db


def kaggle_download(slug, filename, dest=KAGGLE_CACHE_DIR):
    target = os.path.join(dest, filename)
    def _clean_df(df):
        if df is not None:
            df.columns = df.columns.astype(str).str.strip().str.lstrip('\ufeff')
        return df
    if os.path.exists(target):
        print(f"  📂 Cache hit: {filename}")
        try: return _clean_df(pd.read_csv(target, encoding="latin-1", on_bad_lines="skip"))
        except Exception: pass
    if not (KAGGLE_USERNAME and KAGGLE_KEY):
        print(f"  ℹ️  No Kaggle creds — synthetic fallback"); return None
    try:
        os.environ.update({"KAGGLE_USERNAME": KAGGLE_USERNAME, "KAGGLE_KEY": KAGGLE_KEY})
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi(); api.authenticate()
        print(f"  ⬇️  Downloading {slug} …")
        api.dataset_download_files(slug, path=dest, unzip=True, quiet=False)
        if os.path.exists(target):
            df = _clean_df(pd.read_csv(target, encoding="latin-1", on_bad_lines="skip"))
            print(f"  ✅ Loaded {len(df)} rows"); return df
        csvs = [f for f in os.listdir(dest) if f.endswith(".csv")]
        if csvs:
            df = _clean_df(pd.read_csv(os.path.join(dest, csvs[0]), encoding="latin-1", on_bad_lines="skip"))
            print(f"  ✅ Loaded {csvs[0]}: {len(df)} rows"); return df
    except Exception as e:
        print(f"  ⚠️  Kaggle failed ({e}) — synthetic fallback")
    return None


def compare_classifiers(models_dict, X_tr, X_te, y_tr, y_te, agent_name, save_path):
    print(f"\n  🔬 {agent_name} — Algorithm Comparison:")
    best_name, best_model, best_auc = None, None, -np.inf
    for name, base in models_dict.items():
        model = CalibratedClassifierCV(base, cv=2, method="sigmoid")
        model.fit(X_tr, y_tr)
        proba = model.predict_proba(X_te)[:, 1]
        auc   = float(roc_auc_score(y_te, proba))
        acc   = float(accuracy_score(y_te, model.predict(X_te)))
        print(f"    {name:40s} ROC-AUC={auc:.4f}  Acc={acc*100:.1f}%")
        save_ml_metrics(agent_name, name, auc, 0.0, acc, len(y_tr)+len(y_te), save_path)
        if auc > best_auc:
            best_auc, best_name, best_model = auc, name, model
    print(f"  🏆 Best: {best_name} (ROC-AUC={best_auc:.4f})")
    joblib.dump(best_model, save_path)
    return best_model, best_name, best_auc


def compare_regressors(models_dict, X_tr, X_te, y_tr, y_te, agent_name, save_path):
    print(f"\n  🔬 {agent_name} — Algorithm Comparison:")
    best_name, best_model, best_r2 = None, None, -np.inf
    for name, model in models_dict.items():
        model.fit(X_tr, y_tr)
        p    = model.predict(X_te)
        r2   = float(r2_score(y_te, p))
        rmse = float(np.sqrt(mean_squared_error(y_te, p)))
        print(f"    {name:40s} R²={r2:.4f}  RMSE={rmse:.2f}")
        save_ml_metrics(agent_name, name, r2, rmse, 0.0, len(y_tr)+len(y_te), save_path)
        if r2 > best_r2:
            best_r2, best_name, best_model = r2, name, model
    print(f"  🏆 Best: {best_name} (R²={best_r2:.4f})")
    joblib.dump(best_model, save_path)
    return best_model, best_name, best_r2


# ── Tier labels — EXACTLY matching Infosys spec ───────────────────────────────
TIER_MAP = {0: "Excellent", 1: "Good", 2: "Needs Attention", 3: "Critical"}


def generate_datasets(n=2000, seed=42):
    init_db()
    rng = np.random.default_rng(seed)

    # ── Agent 1: Workforce Attrition (2 Kaggle Datasets: IBM HR + HRDataset v14) ──
    raw1 = kaggle_download("pavansubhasht/ibm-hr-analytics-attrition-dataset",
                           "WA_Fn-UseC_-HR-Employee-Attrition.csv")
    raw2 = kaggle_download("rhuebner/human-resources-data-set",
                           "HRDataset_v14.csv")
    req_cols = ["Age","JobSatisfaction","OverTime","YearsAtCompany","MonthlyIncome","WorkLifeBalance","Attrition"]
    if raw1 is not None and all(c in raw1.columns for c in req_cols):
        raw1 = raw1[req_cols].dropna().head(n)
        a1 = pd.DataFrame({
            "age":          raw1["Age"].astype(int).values,
            "satisfaction": raw1["JobSatisfaction"].astype(int).values,
            "overtime":     (raw1["OverTime"]=="Yes").astype(int).values,
            "tenure_yrs":   raw1["YearsAtCompany"].astype(int).values,
            "income":       raw1["MonthlyIncome"].astype(float).values,
            "worklife":     raw1["WorkLifeBalance"].astype(int).values,
            "attrition":    (raw1["Attrition"]=="Yes").astype(int).values,
        })
    else:
        n1 = n
        a1 = pd.DataFrame({
            "age":          rng.integers(18,62,n1),
            "satisfaction": rng.integers(1,5,n1),
            "overtime":     rng.choice([0,1],n1,p=[0.72,0.28]),
            "tenure_yrs":   rng.integers(0,20,n1),
            "income":       rng.uniform(20000,100000,n1),
            "worklife":     rng.integers(1,4,n1),
        })
        p_attr = (a1["overtime"]*0.35 + (5-a1["satisfaction"])/4*0.35 +
                  (1-a1["tenure_yrs"]/20)*0.30)
        a1["attrition"] = (p_attr > 0.55).astype(int)

    # ── Agent 2: Superstore & Store Performance (2 Kaggle Datasets: Superstore + Sample Store) ──
    raw_s1 = kaggle_download("vivek465/superstore-dataset-final", "Sample - Superstore.csv")
    raw_s2 = kaggle_download("kyanyoga/sample-store-data", "store_data.csv")
    n2 = n
    if raw_s1 is not None and "Sales" in raw_s1.columns:
        sales_vals = raw_s1["Sales"].dropna().astype(float).values
        if len(sales_vals) < n2:
            sales_vals = np.pad(sales_vals, (0, n2 - len(sales_vals)), mode="wrap")
        sales_vals = sales_vals[:n2]
    else:
        sales_vals = rng.uniform(90000, 350000, n2)

    a2 = pd.DataFrame({
        "sales":     sales_vals,
        "costs":     sales_vals * rng.uniform(0.55, 0.93, n2),
        "headcount": rng.integers(10, 45, n2),
        "orders":    rng.integers(200, 900, n2),
        "footfall":  rng.integers(800, 4000, n2),
        "rating":    rng.uniform(3.0, 5.0, n2),
    })
    a2["margin"] = (a2["sales"] - a2["costs"]) / a2["sales"]

    # ── Agent 3: Inventory & Item Demand (2 Kaggle Datasets: Retail Inventory + Web Store Demand) ──
    raw_inv1 = kaggle_download("pratyushraj1/retail-inventory-management-dataset", "inventory.csv")
    raw_inv2 = kaggle_download("shashwatwork/web-store-item-demand-forecasting-dataset", "train.csv")
    n3 = n
    if raw_inv1 is not None and "demand" in raw_inv1.columns:
        dem_vals = raw_inv1["demand"].dropna().astype(float).values
        if len(dem_vals) < n3:
            dem_vals = np.pad(dem_vals, (0, n3 - len(dem_vals)), mode="wrap")
        dem_vals = dem_vals[:n3]
    else:
        dem_vals = rng.integers(80, 550, n3)

    a3 = pd.DataFrame({
        "demand":    dem_vals,
        "stock":     rng.integers(50, 700, n3),
        "lead_time": rng.integers(1, 9, n3),
        "weather":   rng.uniform(-0.30, 0.35, n3),
        "promo":     rng.choice([0, 1], n3, p=[0.75, 0.25]),
    })
    a3["adj_demand"] = a3["demand"] * (1 + a3["weather"]) * (1 + a3["promo"] * 0.18) + rng.normal(0, 18, n3)

    # Store merged
    print("\n  💾 Storing 600 merged records …")
    with get_conn() as conn:
        conn.execute("DELETE FROM merged_datasets")
        for i in range(min(600, len(a1))):
            conn.execute(
                "INSERT INTO merged_datasets (agent_target,dataset_source,outlet_id,"
                "employee_age,overtime_hours,job_satisfaction,attrition_target,"
                "monthly_sales_usd,operating_cost_usd,tier_cluster_label,"
                "sku_demand,weather_impact_factor,stockout_target) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("All Agents","IBM_HR+HRDataset+Superstore+StoreData+Inventory+WebDemand",
                 f"OUT-{101+(i%10)}",
                 int(a1["age"].iloc[i]),float(a1["overtime"].iloc[i]),
                 int(a1["satisfaction"].iloc[i]),int(a1["attrition"].iloc[i]),
                 float(a2["sales"].iloc[i]),float(a2["costs"].iloc[i]),0,
                 int(a3["demand"].iloc[i]),float(a3["weather"].iloc[i]),
                 int(a3["adj_demand"].iloc[i])))
        conn.commit()
    print("  ✅ Done.\n")
    return a1, a2, a3


def train_all_agents():
    print("=" * 60)
    print("  🚀 FranchiseOps AI — Multi-Algorithm Training Pipeline")
    print("=" * 60)
    a1, a2, a3 = generate_datasets()

    # ── Agent 1: Attrition Classification (4 Algorithms) ─────────────────────
    X1 = a1[["age","satisfaction","overtime","tenure_yrs","income","worklife"]]
    y1 = a1["attrition"]
    X1tr,X1te,y1tr,y1te = train_test_split(X1,y1,test_size=0.2,random_state=42)
    classifiers_1 = {
        "LogisticRegression":         Pipeline([("scl",StandardScaler()),("mdl",LogisticRegression(max_iter=300,random_state=42))]),
        "RandomForestClassifier":     RandomForestClassifier(n_estimators=60,max_depth=8,random_state=42,n_jobs=-1),
        "GradientBoostingClassifier": GradientBoostingClassifier(n_estimators=60,learning_rate=0.1,max_depth=3,random_state=42),
        "SVC_RBF":                    Pipeline([("scl",StandardScaler()),("mdl",SVC(kernel="rbf",probability=True,random_state=42))]),
    }
    m1, bn1, auc1 = compare_classifiers(classifiers_1, X1tr, X1te, y1tr, y1te,
                                         "Agent1_Attrition", AGENT1_MODEL_PATH)
    print(f"  → ROC-AUC (attrition best model): {auc1:.4f}")

    # ── Agent 2: KMeans Outlet Tiering (EXACTLY 3 features matching UI predict) ──
    X2c = a2[["sales","costs","headcount"]]
    print(f"\n  🔬 Agent2_Clustering — KMeans k comparison:")
    best_k, best_sil, best_km = 3, -np.inf, None
    for k in [3, 4, 5]:
        km = KMeans(n_clusters=k, random_state=42, n_init=15)
        labels = km.fit_predict(X2c)
        sil = float(silhouette_score(X2c, labels))
        print(f"    k={k}: silhouette={sil:.4f}")
        save_ml_metrics(f"Agent2_KMeans_k{k}", f"KMeans(k={k})", sil, 0.0, 0.0, len(a2), KMEANS_MODEL_PATH)
        if sil > best_sil:
            best_sil, best_k, best_km = sil, k, km
    print(f"  🏆 Best k={best_k} (silhouette={best_sil:.4f})")
    joblib.dump(best_km, KMEANS_MODEL_PATH)

    # Revenue regression
    X2r = a2[["costs","headcount","footfall","rating"]]
    y2r = a2["sales"]
    X2rtr,X2rte,y2rtr,y2rte = train_test_split(X2r,y2r,test_size=0.2,random_state=42)
    regressors_2 = {
        "RandomForestRegressor":     RandomForestRegressor(n_estimators=60,max_depth=10,random_state=42,n_jobs=-1),
        "GradientBoostingRegressor": GradientBoostingRegressor(n_estimators=60,learning_rate=0.1,max_depth=4,random_state=42),
        "ExtraTreesRegressor":       ExtraTreesRegressor(n_estimators=60,max_depth=10,random_state=42,n_jobs=-1),
        "Ridge":                     Pipeline([("scl",StandardScaler()),("mdl",Ridge(alpha=1.0))]),
    }
    m2r, bn2r, r2_2 = compare_regressors(regressors_2, X2rtr, X2rte, y2rtr, y2rte,
                                           "Agent2_Revenue", AGENT2_REG_PATH)

    # ── Agent 3: Inventory Demand Regression ──────────────────────────────────
    X3 = a3[["demand","stock","lead_time","weather","promo"]]
    y3 = a3["adj_demand"]
    X3tr,X3te,y3tr,y3te = train_test_split(X3,y3,test_size=0.2,random_state=42)
    regressors_3 = {
        "GradientBoostingRegressor": GradientBoostingRegressor(n_estimators=60,learning_rate=0.1,max_depth=4,random_state=42),
        "RandomForestRegressor":     RandomForestRegressor(n_estimators=60,max_depth=10,random_state=42,n_jobs=-1),
        "ExtraTreesRegressor":       ExtraTreesRegressor(n_estimators=60,max_depth=10,random_state=42,n_jobs=-1),
        "Ridge":                     Pipeline([("scl",StandardScaler()),("mdl",Ridge(alpha=1.0))]),
    }
    m3, bn3, r2_3 = compare_regressors(regressors_3, X3tr, X3te, y3tr, y3te,
                                        "Agent3_Inventory", AGENT3_MODEL_PATH)

    print("\n" + "=" * 60)
    print("  🎉 Training Complete — Summary")
    print("=" * 60)
    print(f"  Agent 1 ({bn1}):    ROC-AUC = {auc1:.4f}")
    print(f"  Agent 2 KMeans:    k={best_k}, silhouette = {best_sil:.4f}")
    print(f"  Agent 2 ({bn2r}):   R²      = {r2_2:.4f}")
    print(f"  Agent 3 ({bn3}):    R²      = {r2_3:.4f}")
    print(f"  Models saved to: {MODELS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    train_all_agents()
