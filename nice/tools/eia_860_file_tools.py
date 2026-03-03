from pathlib import Path

import pandas as pd

from nice import DATA_DIR


def prime_mover_to_desc():
    prime_mover_code = {
        "BA": "Battery Storage",
        "CE": "Compressed Air Storage",
        "CP": "CSP",
        "FW": "Flywheel Storage",
        "PS": "Pumped Hydro Storage",
        "ES": "Other Storage",
        "ST": "Steam turbine",
        "GT": "Gas turbine",
        "IC": "Internal Combustion Engine",
        "CA": "Combined Cycle Steam Part",
        "CT": "Combined Cycle Combustion Turbine Part",
        "CS": "Combined Cycle Sincle Shaft",
        "CC": "Combined Cycle Total Unit",
        "HA": "Hydrokinetic Axial Flow Turbine",
        "HB": "Hydrokinetic Wave Buoy",
        "HK": "Hydrokinetic Other",
        "HY": "Hydroelectric Turbine",
        "BT": "Turbines used in a Binary Cycle",
        "PV": "Photovoltaic",
        "WT": "Onshore Wind",
        "WS": "Offshore Wind",
        "FC": "Fuel Cell",
        "OT": "Other",
    }
    return prime_mover_code


def load_eia_860(file: str, sheet: str = None, year: int = 2024):
    eia860_files_to_sheets = {
        "Utility": ["Utility"],
        "Plant": ["Plant"],
        "Generator": ["Operable", "Proposed", "Retired and Canceled"],
        "Wind": ["Operable", "Retired and Canceled"],
        "Solar": ["Operable", "Retired and Canceled"],
        "Energy_Storage": ["Operable", "Proposed", "Retired and Canceled"],
        "Multifuel": ["Operable", "Proposed", "Retired and Canceled"],
        "Owner": ["Ownership"],
        # "EnviroAssoc": ["Boiler Generator", "Boiler Cooling"], #Boilers
        # "EnviroEquip": [], #Boilers
        # "Layout": ["Field Directory"], # and Reference Tables
    }
    EIA_860_dir = DATA_DIR / f"eia860{year}"

    if not any(file in k for k in eia860_files_to_sheets):
        msg = f"{file} is not a recognized file name. Options are {eia860_files_to_sheets.keys()}"
        raise ValueError(msg)

    files = list(Path(EIA_860_dir).glob(f"*{file}*"))
    fpath = EIA_860_dir / files[0]

    if sheet is None:
        file_basename = [k for k in eia860_files_to_sheets if file in k]
        sheets_for_file = eia860_files_to_sheets[file_basename[0]]
        if len(sheets_for_file) == 1:
            sheet = sheets_for_file[0]
        else:
            sheet = "Operable"

    data = pd.read_excel(fpath, sheet_name=sheet, header=1)
    if "Plant Code" in data.columns.to_list():
        nan_idx = data[data["Plant Code"].isna()].index
        if len(nan_idx) > 0:
            data.drop(index=nan_idx, inplace=True)

    return data


# if __name__ == "__main__":
#     # plants with CF<0.2 are nonbaseload and have nonbaseload factor of 1
#     # plants with  CF>0.8 are baseload and have a baseload factor of 0
#     plant = load_eia_860("Plant") #Latitude, Longitude, NERC Region, Primary Purpose (NAICS Code), State, Sector, Sector Name, Grid Voltage (kW), Energy Storage
#     gen = load_eia_860("Generator") #utility id, plant code, nameplate capacity, power factor, minimum load, prime mover
#     gen[gen["Plant Code"]==1] #"Nameplate Capacity (MW)", "Nameplate Power Factor", 'Minimum Load (MW)', 'Summer Capacity (MW)', 'Winter Capacity (MW)'
#     shared_cols = list(set(plant.columns.to_list()).intersection(set(gen.columns.to_list())))
#     # CFACT = (GENNTAN) / (NAMEPCAP * 8760).
#     # GENNTAN is reported net generation from EIA 923

#     []
