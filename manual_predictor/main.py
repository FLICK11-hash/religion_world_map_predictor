# 2024 Data from ar.inspiredpencil.com
# 2007 Data from https://age-of-the-sage.org/mysticism/world_religions_populations.html
# 1990-1900 Data from google AI overview simply because I couldn't find realiable and easy to interpret data anywhere else

data_2024 = {
    "year": 2024,
    "christianity": 0.31,
    "islam": 0.248,
    "unaffiliated": 0.155,
    "hinduism": 0.151,
    "buddhism": 0.069,
    "judaism": 0.002,
    "other": 0.065
}

data_2007 = {
    "year": 2007,
    "christianity": 0.3333,
    "islam": 0.21,
    "unaffiliated": 0.14,
    "hinduism": 0.1326,
    "buddhism": 0.0584,
    "judaism": 0.0023,
    "other": 0.1234
}

data_1990 = {
    "year": 1990,
    "christianity": 0.33,
    "islam": 0.19,
    "unaffiliated": 0.11,
    "hinduism": 0.13,
    "buddhism": 0.06,
    "judaism": 0.002,
    "other": 0.178
}

data_1970 = {
    "year": 1970,
    "christianity": 0.33,
    "islam": 0.20,
    "unaffiliated": 0.09,
    "hinduism": 0.13,
    "buddhism": 0.06,
    "judaism": 0.002,
    "other": 0.188
}

data_1950 = {
    "year": 1950,
    "christianity": 0.333,
    "islam": 0.134,
    "unaffiliated": 0.05,
    "hinduism": 0.131,
    "buddhism": 0.06,
    "judaism": 0.003,
    "other": 0.289
}

data_1920 = {
    "year": 1920,
    "christianity": 0.33,
    "islam": 0.20,
    "unaffiliated": 0.10,
    "hinduism": 0.13,
    "buddhism": 0.06,
    "judaism": 0.002,
    "other": 0.178
}

data_1900 = {
    "year": 1900,
    "christianity": 0.34,
    "islam": 0.12,
    "unaffiliated": 0.10,
    "hinduism": 0.13,
    "buddhism": 0.06,
    "judaism": 0.002,
    "other": 0.248
}


years = [
    data_1900,
    data_1920,
    data_1950,
    data_1970,
    data_1990,
    data_2007,
    data_2024
]

# placeholder
average_religion_change_per_year = {}

for religion in data_2024:
    # skips the year value because we don't need it to compute it
    if religion == "year":
        continue

    total_change = 0

    for i in range(len(years) - 1):
        first = years[i]
        second = years[i + 1]

        annual_change = ((second[religion] - first[religion]) / (second["year"] - first["year"]))

        total_change += annual_change

    average_religion_change_per_year[religion] = total_change / (len(years) - 1)

print(average_religion_change_per_year)

prediction_2100 = data_2024.copy()
prediction_2100["year"] = 2100

prediction_2500 = data_2024.copy()
prediction_2500["year"] = 2500

prediction_3026 = data_2024.copy()
prediction_3026["year"] = 3026

year_2100_sum = 0
year_2500_sum = 0
year_3026_sum = 0
for religion in average_religion_change_per_year:
    prediction_2100[religion] += average_religion_change_per_year[religion] * 76
    prediction_2500[religion] += average_religion_change_per_year[religion] * 476
    prediction_3026[religion] += average_religion_change_per_year[religion] * 1002

    # No negative #'s
    if prediction_2100[religion] < 0:
        prediction_2100[religion] = 0
    if prediction_2500[religion] < 0:
        prediction_2500[religion] = 0
    if prediction_3026[religion] < 0:
        prediction_3026[religion] = 0

    # summing
    year_2100_sum += prediction_2100[religion]
    year_2500_sum = prediction_2500[religion]
    year_3026_sum = prediction_3026[religion]

for religion in average_religion_change_per_year:
    prediction_2100[religion] = prediction_2100[religion]/year_2100_sum
    prediction_2500[religion] = prediction_2500[religion]/year_2500_sum
    prediction_3026[religion] = prediction_3026[religion]/year_3026_sum
    
    


print(average_religion_change_per_year)
print(prediction_2100)
print(prediction_2500)
print(prediction_3026)

