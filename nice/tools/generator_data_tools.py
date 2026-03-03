import calendar

from nice.tools.eia_860_file_tools import load_eia_860
from nice.tools.eia_923_file_tools import load_eia_923

eia_923_to_860_col_mapper = {
    "Plant Id": "Plant Code",
    "Operator Id": "Utility ID",
    "Plant State": "State",
    "Reported Prime Mover": "Prime Mover",  # not coming up in shared columns
    # Plant Name and Sector Name are shared
}

common_columns = ["State", "Plant Code", "Utility ID", "Prime Mover", "Sector Name"]


def load_eia_860_generator(data_year):
    gen_data = load_eia_860("Generator", year=data_year)
    gen_data["Plant Code"] = gen_data["Plant Code"].astype(int)
    drop_cols = [c for c in gen_data.columns.to_list() if "?" in c]
    gen_data = gen_data.drop(columns=drop_cols)
    return gen_data


def load_eia_923_storage(data_year):
    list_of_months = list(calendar.month_name)[1:]
    unique_data_cols = [f"Grossgen {month}" for month in list_of_months]
    unique_data_cols += ["Gross Generation (Megawatthours)"]

    gen_data = load_eia_923("M_12", sheet="Page 1 Energy Storage", year=data_year)
    gen_data.rename(columns=eia_923_to_860_col_mapper, inplace=True)
    gen_data["Plant Code"] = gen_data["Plant Code"].astype(int)
    # TODO: select only certain columns to return


def load_eia_923_generator(data_year):
    list_of_months = list(calendar.month_name)[1:]
    unique_data_cols = [f"Net Generation {month}" for month in list_of_months]
    unique_data_cols += ["Net Generation Year To Date"]
    # Other data cols are "Combined Heat And  Power Plant", "Generator Id", and "Sector Number"

    gen_data = load_eia_923("M_12", sheet="Page 4 Generator Data", year=data_year)
    gen_data.rename(columns=eia_923_to_860_col_mapper, inplace=True)
    gen_data["Plant Code"] = gen_data["Plant Code"].astype(int)
    # TODO: select only certain columns to return


def load_eia_923_generator_and_fuel(data_year):
    list_of_months = list(calendar.month_name)[1:]
    # Other data cols are "Combined Heat And  Power Plant", "Generator Id", and "Sector Number"
    ex_month = list_of_months[0]

    gen_data = load_eia_923(
        "M_12", sheet="Page 1 Generation and Fuel Data", year=data_year
    )
    gen_data.rename(columns=eia_923_to_860_col_mapper, inplace=True)
    gen_data["Plant Code"] = gen_data["Plant Code"].astype(int)

    colname_month_base = [
        c.split(ex_month)[0] for c in gen_data.columns.to_list() if ex_month in c
    ]
    monthly_col_names = []
    for monthly_data_col in colname_month_base:
        monthly_col_names += [f"{monthly_data_col}{m}" for m in list_of_months]
    # TODO: select only certain columns to return
    return gen_data


def get_plant_ids_for_dataset(dataset_desc, data_year):
    dataset_opts = [
        "EIA860-Plant",
        "EIA860-Generator",
        "EIA923-Gen&Fuel",
        "EIA923-Gen",
        "EIA923-Storage",
    ]
    if dataset_desc not in dataset_opts:
        msg = f"{dataset_desc} is not valid dataset option, valid options are {dataset_opts}"
        raise ValueError(msg)

    if "EIA860" in dataset_desc:
        file = dataset_desc.split("EIA860-")[-1]
        data = load_eia_860(file, year=data_year)
        data["Plant Code"] = data["Plant Code"].astype(int)
        return list(set(data["Plant Code"].to_list()))
    if "EIA923" in dataset_desc:
        desc_to_sheet = {
            "Gen&Fuel": "Page 1 Generation and Fuel Data",
            "Gen": "Page 4 Generator Data",
            "Storage": "Page 1 Energy Storage",
        }
        sheet = desc_to_sheet[dataset_desc.split("EIA923-")[-1]]
        data = load_eia_923("M_12", sheet=sheet, year=data_year)
        data.rename(columns=eia_923_to_860_col_mapper, inplace=True)
        data["Plant Code"] = data["Plant Code"].astype(int)
        return list(set(data["Plant Code"].to_list()))


# data_year = 2024


# # plant = load_eia_860("Plant", year=data_year) #16132 rows
# # n_plnts = len(list(set(plant["Plant Code"].to_list())))
# # print(f"EIA 860 Plant has {len(plant)} rows ({n_plnts} plants)") #26855 rows
# # EIA860 has 9 rows for Plant Code of 260
# # EIA 923 has 3 rows for Plant Code of 260

# gen = load_eia_860("Generator", year=data_year) #dont need utility name or technology
# n_plnts = len(list(set(gen["Plant Code"].to_list())))

# gen_base_cols = gen.columns.to_list()
# m12_sheets = ["Page 1 Generation and Fuel Data","Page 1 Energy Storage","Page 4 Generator Data"]
# # Page 1 Generation and Fuel Data has 17964 rows, 92 unique columns
# # Page 1 Energy Storage has 1273 rows, 66 unique columns
# # Page 4 Generator Data has 3557 rows, 24 unique columns

# print(f"EIA 860 has {len(gen)} rows ({n_plnts} plants) and {len(gen.columns.to_list())} columns")

# # first 12-16 columns of "Page 1 Generation and Fuel Data" seem similar
# # EIA 923 has NERC Region, Census Region, EIA Sector Number, NAICS Code, NERC Region, Sector Name, ReportedPrime Mover

# for ii,sht in enumerate(m12_sheets):
#     gen_1 = load_eia_923("M_12", sheet=sht,year=data_year)
#     gen_1.rename(columns=eia_923_to_860_col_mapper, inplace=True)
#     n_plnts = len(list(set(gen_1["Plant Code"].to_list())))
#     shared_cols = list(set(gen_1.columns.to_list()).intersection(set(gen.columns.to_list())))
#     unique_cols = list(set(gen_1.columns.to_list()).difference(shared_cols))
#     print(f"EIA 923 Monthly {sht} has {len(gen_1)} rows ({n_plnts} plants) and {len(unique_cols)} unique columns ({len(shared_cols)} shared columns)")
#     if ii==0:
#         e923_main_cols = list(set(gen_1.columns.to_list()))
#     else:
#         shared_sheet_cols = list(set(e923_main_cols).intersection(set(gen_1.columns.to_list())))
#         unique_sheet_cols = list(set(gen_1.columns.to_list()).difference(shared_sheet_cols))
#         print(f"- {len(shared_sheet_cols)} columns shared with Page 1, {len(unique_sheet_cols)} unique columns")
#         print(f"- Unique columns are: {unique_sheet_cols}\n")
# print(f"Shared columns are {shared_cols}")


# # gen_1 = load_eia_923("M_12", sheet="Page 1 Generation and Fuel Data",year=data_year)
# # gen_storage = load_eia_923("M_12", sheet="Page 1 Energy Storage",year=data_year)
# # gen_2 = load_eia_923("M_12", sheet="Page 4 Generator Data",year=data_year)
# []
