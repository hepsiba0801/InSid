# STEP 1: Import Libraries

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import os


# Always use the dataset/refined_employee_dataset.csv file
csv_path = os.path.join("dataset", "refined_employee_dataset.csv")
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"File not found: {csv_path}")
df = pd.read_csv(csv_path)


# STEP 3: Select Numerical Features for Analysis

numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()

# Remove target column if exists
if "is_emp_malicious" in numeric_cols:
    numeric_cols.remove("is_emp_malicious")

# Handle missing values
df[numeric_cols] = df[numeric_cols].fillna(0)


# STEP 4: Normalize Data

scaler = StandardScaler()
scaled_data = scaler.fit_transform(df[numeric_cols])


# STEP 5: Train Isolation Forest Model

model = IsolationForest(
    contamination=0.05,  # Adjust to control sensitivity
    n_estimators=200,
    random_state=42
)
model.fit(scaled_data)


# STEP 6: Get Raw Scores & Predictions

df["raw_score"] = model.decision_function(scaled_data)  # Higher = more normal
df["risk_score"] = (df["raw_score"] - df["raw_score"].min()) / (df["raw_score"].max() - df["raw_score"].min())


# STEP 7: Assign Anomaly Flags

def categorize_anomaly(score):
    if score >= 0.7:
        return "normal"
    elif score >= 0.4:
        return "suspicious"
    else:
        return "insider"

df["anomaly_flag"] = df["risk_score"].apply(categorize_anomaly)



# STEP 8: Save Results
output_file = "insider_threat_results.csv"
df.to_csv(output_file, index=False)
print(f"Results saved to {output_file}")



# STEP 9: Optional Visualization
plt.figure(figsize=(10, 6))
plt.hist(df["risk_score"], bins=50, alpha=0.7, color='blue')
plt.title("Risk Score Distribution")
plt.xlabel("Risk Score")
plt.ylabel("Number of Employees")
plt.tight_layout()
plt.savefig("risk_score_distribution.png")
print("Risk score distribution plot saved as risk_score_distribution.png")
plt.show()