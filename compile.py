import pandas as pd

# Load files
sub_path = "C:\\Users\\mohit\\Downloads\\submission.csv"
sample_path = "C:\\Users\\mohit\\Downloads\\sep-25-dl-gen-ai-nppe-1\\face_dataset\\sample_submission.csv"

submission = pd.read_csv(sub_path)
sample = pd.read_csv(sample_path)

print("Original submission:")
print(submission.head())

print("Sample submission format:")
print(sample.head())

# --- Build required columns ---
required_cols = sample.columns.tolist()

# --- Determine mapping ---
mapping = {}

# Identify ID-like column
id_candidates = ["id", "image_id", "img", "filename", "name"]
for c in submission.columns:
    if c.lower() in id_candidates:
        mapping[c] = "id"
        break

# Identify gender
gender_candidates = ["gender", "sex", "g"]
for c in submission.columns:
    if c.lower() in gender_candidates:
        mapping[c] = "gender"
        break

# Identify age
age_candidates = ["age", "years"]
for c in submission.columns:
    if c.lower() in age_candidates:
        mapping[c] = "age"
        break

# Rename columns
submission_renamed = submission.rename(columns=mapping)

# Ensure all required columns exist
missing = [c for c in required_cols if c not in submission_renamed.columns]
if missing:
    print("WARNING: Missing columns:", missing)

# Reorder columns
submission_final = submission_renamed[required_cols]

# Sort by id
submission_final = submission_final.sort_values("id").reset_index(drop=True)

# Ensure age values are integers (no floats)
if "age" in submission_final.columns:
    submission_final["age"] = pd.to_numeric(submission_final["age"], errors="coerce")
    if submission_final["age"].isnull().any():
        print("WARNING: Some age values could not be converted to numeric and are NaN")
    # Round to nearest integer and convert to pandas nullable integer dtype so CSV shows integers
    submission_final["age"] = submission_final["age"].round().astype("Int64")

# Save
out_path = "C:\\Users\\mohit\\Downloads\\submission_formatted.csv"
submission_final.to_csv(out_path, index=False)

out_path
