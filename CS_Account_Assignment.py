import pandas as pd

# Defining lifecycle stages and their weights
stages = {
    "Onboarding": 3.5,
    "Adoption": 3,
    "Value Realization": 1.5,
    "Maintenance/Renewal": 0.25,
}

# Defining weights for license count bands
license_bands = {
    range(50, 99): 1,
    range(100, 249): 1.1,
    range(250, 499): 1.2,
    range(500, 999): 1.3,
    range(1000, 99999): 1.4,
}


def get_license_band_weight(licenses):
    for band, weight in license_bands.items():
        if licenses in band:
            return weight


# Existing CSM Data, including time zone residency and languages - Will have to build something else that populates this array from SFDC
csmdata = [
    {
        "name": "John Jones",
        "customers": [
            {
                "name": "Customer A",
                "stage": "Onboarding",
                "licenses": 140,
                "industry": "Finance",
            },
            {
                "name": "Customer B",
                "stage": "Value Realization",
                "licenses": 400,
                "industry": "Manufacturing",
            },
            {
                "name": "Customer C",
                "stage": "Maintenance/Renewal",
                "licenses": 234,
                "industry": "Finance",
            },
            {
                "name": "Customer D",
                "stage": "Adoption",
                "licenses": 320,
                "industry": "Manufacturing",
            },
        ],
        "language": "English",
        "timezone": "US-Eastern",
    },
    {
        "name": "Jane Smith",
        "customers": [
            {
                "name": "Customer E",
                "stage": "Maintenance/Renewal",
                "licenses": 412,
                "industry": "Medical",
            },
            {
                "name": "Customer F",
                "stage": "Adoption",
                "licenses": 268,
                "industry": "Software",
            },
            {
                "name": "Customer G",
                "stage": "Adoption",
                "licenses": 112,
                "industry": "Manufacturing",
            },
            {
                "name": "Customer H",
                "stage": "Onboarding",
                "licenses": 520,
                "industry": "Software",
            },
        ],
        "language": "English",
        "timezone": "US-Pacific",
    },
    {
        "name": "Mike Brown",
        "customers": [
            {
                "name": "Customer I",
                "stage": "Maintenance/Renewal",
                "licenses": 76,
                "industry": "Manufacturing",
            },
            {
                "name": "Customer J",
                "stage": "Maintenance/Renewal",
                "licenses": 112,
                "industry": "Medical",
            },
            {
                "name": "Customer K",
                "stage": "Onboarding",
                "licenses": 230,
                "industry": "Finance",
            },
            {
                "name": "Customer L",
                "stage": "Onboarding",
                "licenses": 315,
                "industry": "Software",
            },
        ],
        "language": "English",
        "timezone": "Western-European",
    },
]

df = pd.DataFrame(csmdata)


# Calculate bandwidth score for each CSM
def calculate_bandwidth(row):
    score = 0
    for customer in row.customers:
        score += stages[customer["stage"]] * get_license_band_weight(
            customer["licenses"]
        )
    return score


df["bandwidth"] = df.apply(calculate_bandwidth, axis=1)

# Define the incoming customer's details
incoming_customer = {
    "name": "ACME Corp",
    "language": "English",
    "timezone": "US-Eastern",
    "industry": "Software",
    "licenses": 800,
}

# Filter out language-incompatible CSMs
df = df[df.language == incoming_customer["language"]]

# Filter by timezone
timezones = {
    "US-Eastern": [-5, -4],
    "US-Central": [-6, -5],
    "US-Mountain": [-7, -6],
    "US-Pacific": [-8, -7],
    "Western-European": [0, 1],
    "Central-European": [1, 2],
    "Eastern-European": [2, 3],
    "Indian": [5.5, 6.5],
    "Australian": [8, 10],
    "Singaporean": [8, 8],
    "Japanese": [9, 9],
    "Chinese": [8, 8],
    "Korean": [9, 9],
    "Taiwanese": [8, 8],
    "Brazilian": [-3, -3],
    "Mexican": [-6, -5],
    "Canadian": [-5, -4],
    "Russian": [3, 4],
    "South African": [2, 2],
}

incoming_timezone_hours = timezones[incoming_customer["timezone"]]

df = df[
    df.timezone.apply(lambda x: abs(incoming_timezone_hours[0] - timezones[x][0]) <= 5)
]


# Assign industry factor
def industry_factor(row):
    industry_customers = [
        customer
        for customer in row.customers
        if customer["industry"] == incoming_customer["industry"]
    ]
    return len(industry_customers)


df["industry_factor"] = df.apply(industry_factor, axis=1)

# Combine bandwidth and industry factor
industry_weight = (
    1.1  # if the new customer has industry overlap with the CSM, we give it a 10% boost
)
df["load_score"] = df.bandwidth + (df.industry_factor * industry_weight)

# Print incoming customer information
print(
    f"\nCaclulating CSM recommendation for incoming customer '{incoming_customer['name']}':"
)
print(f"Customer Licenses: {incoming_customer['licenses']}")
print(f"Customer Language: {incoming_customer['language']}")
print(f"Customer Timezone: {incoming_customer['timezone']}")
print(f"Customer Industry: {incoming_customer['industry']}")

# Print load scores
print("\nCSM Bandwidth Scores:")
for i, row in df.iterrows():
    print(f"CSM: {row['name']}, Bandwidth Score: {row['load_score']}")

# Get the CSM with the lowest load_score
recommended_csm = df[df.load_score == df.load_score.min()].name.values[0]

print(f"\nRecommended CSM for the incoming customer is: {recommended_csm}")
