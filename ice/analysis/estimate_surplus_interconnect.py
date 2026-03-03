from attrs import define, field

from ice.analysis.config_base import BaseConfig, contains


@define(kw_only=True)
class SurplusInterconnectAnalysisConfig(BaseConfig):
    main_category: str = field(
        validator=contains(
            ["State", "Prime Mover", "Capacity", "ISO", "Balancing Authority"]
        )
    )

    data_year: int = field(default=2024, converter=int)


# # load egrid data
# egrid_fpath = DATA_DIR/"egrid2023_data_rev2.xlsx"

# sheets = ["GEN23","PLNT23","ST23","BA23"]
# pd.read_excel(egrid_fpath, sheet_name="GEN23")
