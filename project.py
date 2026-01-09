import re
import pandas as pd
import json
import requests
from bs4 import BeautifulSoup
import csv
import time
import random

def clean_survey(url, foundation_clean): # args  url is survey_parsed and the other is cleaned foundation(lab) data
    df = pd.read_csv(url, encoding="latin1")
    fdf = pd.read_csv(foundation_clean, encoding="latin1")

    chosen_nutrients = {  #fixing inconsistency with naming and setting it to a specific more commonly utilized name and also displaying the amount from abbreviation to full name
            "Iron, Fe": "Iron(Milligrams)",
            "Calcium, Ca": "Calcium(Milligrams)",
            "Potassium, K": "Potassium(Milligrams)",
            "Vitamin A, RAE": "Vitamin A(Micrograms)",
            "Vitamin C, total ascorbic acid": "Vitamin C(Milligrams)",
            "Vitamin D (D2 + D3)": "Vitamin D(Micrograms)",
            "Protein": "Protein(Grams)",
            "Zinc, Zn": "Zinc(Milligrams)",
            "Magnesium, Mg": "Magnesium(Milligrams)",
            "Vitamin B-12": "Vitamin B-12(Micrograms)",
            "Energy" : "Calories"
        }

    df_filter = df[df["nutrient_name"].isin(chosen_nutrients.keys())]# filtering such that it is our nutreints from above table
    pivot_df = df_filter.pivot_table(index=["fdcId", "description"],columns="nutrient_name",values="amount")
    pivot_df = pivot_df.reset_index()  #fixes indexes
    pivot_df = pivot_df.rename(columns = chosen_nutrients) #fixes headers

    pivot_df = pivot_df.round(2) #can be considered an inconsistency fix and for simplicity
    word_filter = first_word_filter(pivot_df, fdf)

    word_filter.to_csv("cleaned_survey_nutrients.csv", index=False)
    return word_filter
    


def first_word_filter(survey_df, foundation_df):  ##potential inconsistency fix,since foundation foods have a limit of how much data/foods they have I adjust such that they are in survey.
    foundation_first = foundation_df["description"].str.split().str[0].str.lower().unique()
    survey_filtered = survey_df[survey_df["description"].str.split().str[0].str.lower().isin(foundation_first)]
    return survey_filtered

def clean_labData(json_input):  # please read above note in previous cell


#### for tmrw fix the grams or micrograms and make sure to stay consistent.

    chosen_nutrients = {  #fixing inconsistency with naming and setting it to a specific more commonly utilized name and also displaying the amount from abbreviation to full name
            "Iron, Fe": "Iron(Milligrams)",
            "Calcium, Ca": "Calcium(Milligrams)",
            "Potassium, K": "Potassium(Milligrams)",
            "Vitamin A, RAE": "Vitamin A(Micrograms)",
            "Vitamin C, total ascorbic acid": "Vitamin C(Milligrams)",
            "Vitamin D (D2 + D3)": "Vitamin D(Micrograms)",
            "Protein": "Protein(Grams)",
            "Zinc, Zn": "Zinc(Milligrams)",
            "Magnesium, Mg": "Magnesium(Milligrams)",
            "Vitamin B-12": "Vitamin B-12(Micrograms)",
        
        }
    with open(json_input, "r", encoding="latin1") as file:

        food_data = json.load(file)

    res = []
    for food in food_data["FoundationFoods"]:

        nutrients_dict = {"description": food["description"]}
        for label in chosen_nutrients.values(): #inconsistency fix, and also a place holder if the nutrient is not there
            nutrients_dict[label] = 0

        for nutrient in food["foodNutrients"]:
            nutrient_name = nutrient["nutrient"]["name"]
            if nutrient_name in chosen_nutrients:
                nutrients_dict[chosen_nutrients[nutrient_name]] = nutrient["amount"]

        res.append(nutrients_dict)

    df = pd.DataFrame(res)   #all keys becomes the first row(header) and values are listed in column
    df= df.round(2)
    df.to_csv("cleaned_foundation_nutrients.csv", index=False, encoding="latin1")
    print("worked central")
    return df








def scrape_cleaner(cleanedfoundation_csv, output_csv="calories.csv"):
    base_url = "https://www.nutritionvalue.org"
    headers = {"User-Agent": "Mozilla/5.0"}


    df = pd.read_csv(cleanedfoundation_csv, header=None, encoding = "latin1")
    first_words = df[0].str.split(',').str[0].str.lower().str.strip()
    unique_words = sorted(set(first_words)) #removed duplicate words so it dosent send extra requests, and also alphabetical
    
    result = []

    with open(output_csv, mode="w", newline="", encoding="latin1") as f:
        writer = csv.writer(f)
        writer.writerow(["First Word", "Average Calories per 100g"])

        for food in unique_words:
            time.sleep(random.uniform(4.2, 5.1)) # to avoid getting blocked
            search_url = f"https://www.nutritionvalue.org/search.php?food_query={food}"
            res = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")

            result_links = soup.select("a.table_item_name")[:1]  # only first search result(I wouldve done more, but I keep getting flagged for so many requests)  * pulls a tags with class 'table_item_name'

            calories_list = []

            for link in result_links:
                food_url = base_url + link['href']
                food_res = requests.get(food_url, headers=headers)
                food_soup = BeautifulSoup(food_res.text, "html.parser")



                cal_spot = food_soup.select_one("td#calories.right")
                text = cal_spot.text.strip()

                calories = float(text)


                span = food_soup.select_one("span#serving-size")
                grams = None

                if span:
                    grams_text = span.text.strip().split()[0]
                    grams = float(grams_text) #idk why it runs error when i cast into int

                if grams:  #inconsistency fix, adjusting for standard nutriton portion
                    cal_100g = (calories / grams) * 100
                    calories_list.append(cal_100g)

            if calories_list:
                calories_100g = int(calories_list[0])
                writer.writerow([food, calories_100g])
                result.append([food, calories_100g])
                print(f"{food}: {calories_100g}")
            else:
                writer.writerow([food, "No data"])
                
                result.append([food, "No data"])
                print(f"{food}: No data")
        return pd.DataFrame(result, columns=["First Word", "Average Calories per 100g"])


if __name__ == "__main__":
    clean_labData("FoodData_Central_foundation_food_json_2025-04-24.json")
    clean_survey("survey_parsed_nutrients.csv", "cleaned_foundation_nutrients.csv")
    



            
        
        
        
        
        
    






