from pathlib import Path

import pandas as pd

from ice import DATA_DIR


def load_eia_923(file: str, sheet: str = None, year: int = 2024):
    eia923_files_to_sheets = {
        "Annual_Env": [
            "8B Annual Byproduct Disposition",
            "8B Financial Information",
            "8C Air Emissions Control Info",
            "8C FGD Operation & Maintenance",
            "8D Cooling System Information",
        ],
        "SourceNDispo": ["Source_and_disposition"],
        "M_12": [
            "Page 1 Generation and Fuel Data",  # monthly data on fuel consumption and net generation
            "Page 1 Energy Storage",  # monthly net generation and gross generation, gross gen > net gen
            "Page 4 Generator Data",  # monthly
            "Page 6 Plant Frame",  # has balancing authority info
        ],
    }
    EIA_923_dir = DATA_DIR / f"f923_{year}"

    if not any(file in k for k in eia923_files_to_sheets):
        msg = f"{file} is not a recognized file name. Options are {eia923_files_to_sheets.keys()}"
        raise ValueError(msg)

    files = list(Path(EIA_923_dir).glob(f"*{file}*"))
    fpath = EIA_923_dir / files[0]

    if sheet is None:
        file_basename = [k for k in eia923_files_to_sheets if file in k]
        sheets_for_file = eia923_files_to_sheets[file_basename[0]]
        if len(sheets_for_file) == 1:
            sheet = sheets_for_file[0]
        else:
            msg = f"{sheet} is an unrecognized sheet name. Options include {sheets_for_file}"
            raise ValueError(msg)
    if file == "M_12":
        data = pd.read_excel(fpath, sheet_name=sheet, header=5)
        col_rename = {c: c.replace("\n", " ") for c in data.columns.to_list()}
    else:
        data = pd.read_excel(fpath, sheet_name=sheet, header=4)
        col_rename = {c: c.replace("\n", "") for c in data.columns.to_list()}
    data.rename(columns=col_rename, inplace=True)

    return data
