import pandas as pd
from fuzzywuzzy import process
from sklearn.linear_model import LinearRegression
import csv
import matplotlib.pyplot as plt
import plotly.express as px


#insight 1
def nutri_comp():

    foundation_df = pd.read_csv("cleaned_foundation_nutrients.csv", encoding="latin1")
    
    survey_df = pd.read_csv("cleaned_survey_nutrients.csv", encoding="latin1")

    
    nutrient_cols = [col for col in foundation_df.columns if col != "description"]

    foundation_avg = {}
    survey_avg = {}

    for col in nutrient_cols:
        
        if col in ["Vitamin A(Micrograms)", "Vitamin D(Micrograms)"]:
            # Filterrows where value is 0
            foundation_nonzero = foundation_df[foundation_df[col] != 0][col]
            survey_nonzero = survey_df[survey_df[col] != 0][col]

            foundation_avg[col] = foundation_nonzero.mean()
            survey_avg[col] = survey_nonzero.mean()
            
        else:
            
            foundation_avg[col] = foundation_df[col].mean()
            survey_avg[col] = survey_df[col].mean()


    comparison = pd.DataFrame({
        "Foundation Avg": pd.Series(foundation_avg),
        "Survey Avg": pd.Series(survey_avg)
    })
    comparison = comparison.round(2)

    print("Average Nutrient Comparison (Foundation vs Survey):")
    print(comparison)

    return comparison



#insight 2

def top5():

    foundation_df = pd.read_csv("cleaned_foundation_nutrients.csv", encoding="latin1")
    survey_df = pd.read_csv("cleaned_survey_nutrients.csv", encoding="latin1")


    foundation_df["first_word"] = foundation_df["description"].str.split().str[0].str.lower()
    survey_df["first_word"] = survey_df["description"].str.split().str[0].str.lower()

    nutrient_cols = [col for col in foundation_df.columns if col not in ["description", "first_word"]]

    
    print("Select a nutrient from the list:\n")
    
    for idx, col in enumerate(nutrient_cols, 1):
        print(f"{idx}. {col}")

    # User input
    try:
        user_in = int(input("\nEnter the number of the nutrient: "))
        
        if user_in < 1 or user_in > len(nutrient_cols):
            
            print("Number out of range.")
            return
    except ValueError:
        
        print("Invalid input. Please enter a number.")
        return

    selected = nutrient_cols[user_in - 1]

    # Group both datasets by first word and get top 5
    f_top = foundation_df.groupby("first_word")[selected].mean().sort_values(ascending=False).head(5)
    s_top = survey_df.groupby("first_word")[selected].mean().sort_values(ascending=False).head(5)

    
    print(f"\nFoundation Data - Top 5 Categories by '{selected}':")
    for i, food in enumerate(f_top.index, 1):
        print(f"{i}. {food.capitalize()}")

    print(f"\nSurvey Data - Top 5 Categories by '{selected}':")
    for i, food in enumerate(s_top.index, 1):
        print(f"{i}. {food.capitalize()}")
    
#insight 3
def discrepancies():
    
    foundation_df = pd.read_csv("cleaned_foundation_nutrients.csv", encoding="latin1")
    survey_df = pd.read_csv("cleaned_survey_nutrients.csv", encoding="latin1")

    
    foundation_df["first_word"] = foundation_df["description"].str.lower().str.split().str[0]
    survey_df["first_word"] = survey_df["description"].str.lower().str.split().str[0]

    
    nutrient_cols = [
        "Calcium(Milligrams)", "Iron(Milligrams)", "Magnesium(Milligrams)",
        "Potassium(Milligrams)", "Protein(Grams)", "Vitamin B-12(Micrograms)",
        "Vitamin C(Milligrams)", "Zinc(Milligrams)"
    ]

    
    f_grouped = foundation_df.groupby("first_word")[nutrient_cols].mean()
    s_grouped = survey_df.groupby("first_word")[nutrient_cols].mean()

    
    joined = f_grouped.join(s_grouped, lsuffix="_foundation", rsuffix="_survey", how="inner")

    
    joined["Mean Nutrient Difference"] = joined.apply(
        lambda row: sum(abs(row[f"{col}_foundation"] - row[f"{col}_survey"]) for col in nutrient_cols) / len(nutrient_cols),
        axis=1
    )

    
    result_df = joined.reset_index()
    result_df = result_df[["first_word", "Mean Nutrient Difference"]].sort_values(by="Mean Nutrient Difference", ascending=False)

    print("Nutrient Consistency Between Survey vs Foundation Sources:")
    print(result_df)
    result_df.to_csv("full_discrepancy_table.csv", index=False)

    return result_df


#insight 4




def calorie_comparison():
    
    survey = pd.read_csv("cleaned_survey_nutrients.csv", encoding="latin1")
    calories = pd.read_csv("calories.csv", encoding="latin1")

    
    def make_key(description):
        words = description.lower().split()
        return " ".join(words[:5]) if len(words) >= 5 else " ".join(words)

    survey["group_key"] = survey["description"].apply(make_key)
    calories["group_key"] = calories["First Word"].str.lower()

    # Deduplicate calories by group_key
    calories_avg = calories.groupby("group_key")["Average Calories per 100g"].mean().reset_index()
    survey_avg = survey.groupby("group_key")["Calories"].mean().reset_index()

    
    seen = set()
    matched_rows = []

    for _, row in survey_avg.iterrows():
        s_key = row["group_key"]
        s_cal = row["Calories"]

        result = process.extractOne(s_key, calories_avg["group_key"], score_cutoff=85)
        if result:
            match_key, score = result[0], result[1]
            if match_key in seen:
                continue
            seen.add(match_key)
            c_cal = calories_avg.loc[calories_avg["group_key"] == match_key, "Average Calories per 100g"].values[0]
            percent_diff = abs(s_cal - c_cal) / c_cal * 100
            matched_rows.append((s_key, round(s_cal, 2), round(c_cal, 2), percent_diff))

    
    result_df = pd.DataFrame(matched_rows, columns=[
        "Food Group", "Survey Avg Calories", "Verified Avg Calories", "_Percent Difference"
    ])

    # Accuracy summary
    total = len(result_df)
    outside_margin = result_df[result_df["_Percent Difference"] > 30]
    percent_outside = (len(outside_margin) / total) * 100 if total > 0 else 0

    
    result_df_display = result_df.drop(columns=["_Percent Difference"])
    print(result_df_display.to_string(index=False))

    print(f"\n {percent_outside:.2f}% of matched food groups have survey calorie estimates that differ "
          f"by more than 30% from acutal values")

    return result_df_display

#insight 5
DAILY_VALUES = {
    'Iron': 18,         # mg
    'Calcium': 1300,      # mg
    'Potassium': 4700,   # mg
    'Vitamin A': 900,    # mcg
    'Vitamin C': 90,      # mg
    'Vitamin D': 20,     # mcg
    'Protein': 50,      # g
    'Zinc': 11,           # mg
    'Magnesium': 420,    # mg
    'Vitamin B-12': 2.4, # mcg
}

def most_common_nutrient(file_path, output_csv='primary_nutrients.csv'):
    df = pd.read_csv(file_path)
    
   
    nutrient_map = {
        
        'Iron(Milligrams)': ('Iron', 'mg'),
        'Calcium(Milligrams)': ('Calcium', 'mg'),
        'Potassium(Milligrams)': ('Potassium', 'mg'),
        'Vitamin A(Micrograms)': ('Vitamin A', 'mcg'),
        'Vitamin C(Milligrams)': ('Vitamin C', 'mg'),
        'Vitamin D(Micrograms)': ('Vitamin D', 'mcg'),
        'Protein(Grams)': ('Protein', 'g'),
        'Zinc(Milligrams)': ('Zinc', 'mg'),
        'Magnesium(Milligrams)': ('Magnesium', 'mg'),
        'Vitamin B-12(Micrograms)': ('Vitamin B-12', 'mcg')
    }
    
    results = []
    
    for _, row in df.iterrows():
        food = row['description']
        max_dv_percent = 0
        primary_nutrient = None
        
        for col in df.columns:
            if col in nutrient_map:
                nutrient_name, unit = nutrient_map[col]
                amount = row[col]
                dv = DAILY_VALUES.get(nutrient_name, 1)  
                dv_percent = (amount / dv) * 100 if dv else 0
                
                if dv_percent > max_dv_percent:
                    max_dv_percent = dv_percent
                    primary_nutrient = nutrient_name
        
        results.append({
            
            'Food': food,
            'Primary Nutrient (by %DV)': primary_nutrient,
            '% Daily Value': round(max_dv_percent, 1)
        })
    
    result_df = pd.DataFrame(results)
    sorted_df = result_df.sort_values('% Daily Value', ascending=False)
    
    
    sorted_df.to_csv(output_csv, index=False)
    return sorted_df



def pie(file_path):
    df = pd.read_csv(file_path)
    nutrient_counts = df['Primary Nutrient (by %DV)'].value_counts().reset_index()
    nutrient_counts.columns = ['Primary Nutrient', 'Count']

    fig = px.pie(
        nutrient_counts,
        names='Primary Nutrient',
        values='Count',
        title='Distribution of Primary Nutrients by %DV',
        hole=0.3
    )

    fig.update_traces(textinfo='percent+label')
    fig.show()
    
def most_consistent(result_df):
    
    bottom = result_df.sort_values("Mean Nutrient Difference", ascending=True).head(15)

    plt.figure(figsize=(10, 6))
    plt.barh(bottom["first_word"], bottom["Mean Nutrient Difference"], color="mediumseagreen")
    plt.xlabel("Mean Nutrient Difference")
    plt.title("Top 15 Most Nutritionally Consistent Food Groups")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()

def plot_nutrient_stacks():
    df = pd.read_csv("cleaned_survey_nutrients.csv", encoding="latin1")
    df["group"] = df["description"].str.split().str[0].str.lower()

    nutrients = ["Protein(Grams)", "Calcium(Milligrams)", "Iron(Milligrams)", "Vitamin C(Milligrams)", "Potassium(Milligrams)"]

    grouped = df.groupby("group")[nutrients].mean().round(2)
    top_groups = grouped.sum(axis=1).sort_values(ascending=False).head(8).index
    display_df = grouped.loc[top_groups]

    display_df.plot(kind='bar', stacked=True, figsize=(12, 6), colormap='tab20')
    plt.title("Nutrient Contributions by Food Group")
    plt.ylabel("Average Nutrient Amount")
    plt.xlabel("Food Group")
    plt.xticks(rotation=45)
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.show()











if __name__ == "__main__":
    nutri_comp()
    #top5()
    discrepancies()
    calorie_comparison()
    print(most_common_nutrient('cleaned_foundation_nutrients.csv'))
    most_consistent
    plot_nutrient_stacks()
    pie('primary_nutrients.csv')


    
    
    
    
