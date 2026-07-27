import pickle
import pandas as pd

with open("first_names.pkl", "rb") as f:
    data = pickle.load(f)

rows = []

for name, info in data.items():
    gender = info.get("gender", {})
    country = info.get("country", {})
    rank = info.get("rank", {})

    female_prob = gender.get("F", 0)
    male_prob = gender.get("M", 0)

    if male_prob > female_prob:
        predicted_gender = "Male"
        gender_probability = male_prob
    elif female_prob > male_prob:
        predicted_gender = "Female"
        gender_probability = female_prob
    else:
        predicted_gender = "Unknown"
        gender_probability = None

    top_country = max(country, key=country.get) if country else None
    top_country_probability = country.get(top_country) if top_country else None
    top_country_rank = rank.get(top_country) if top_country else None

    rows.append({
        "name": name,
        "predicted_gender": predicted_gender,
        "male_probability": male_prob,
        "female_probability": female_prob,
        "gender_probability": gender_probability,
        "top_country": top_country,
        "top_country_probability": top_country_probability,
        "top_country_rank": top_country_rank
    })

df = pd.DataFrame(rows)

df.to_csv("first_names_clean.csv", index=False, encoding="utf-8-sig")

print(df.head())
print("Saved as first_names_clean.csv")