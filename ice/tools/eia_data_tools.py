import copy

import numpy as np
import pandas as pd

from ice.tools.eia_860_file_tools import load_eia_860
from ice.tools.eia_923_file_tools import load_eia_923


def get_missing_ids_per_dataset(data_year=2024):
    plant = load_eia_860("Plant", year=data_year)
    gen = load_eia_860("Generator", year=data_year)
    perf = load_eia_923("SourceNDispo", year=data_year)

    plant["Plant Code"] = plant["Plant Code"].astype(int)
    gen["Plant Code"] = gen["Plant Code"].astype(int)
    perf["Plant Code"] = perf["Plant Code"].astype(int)

    common_plant_ids = list(
        set(plant["Plant Code"].to_list()).intersection(
            set(gen["Plant Code"].to_list())
        )
    )
    common_plant_ids = list(
        set(common_plant_ids).intersection(set(perf["Plant Code"].to_list()))
    )
    common_plant_ids.sort()

    all_plant_ids = set(
        plant["Plant Code"].to_list()
        + gen["Plant Code"].to_list()
        + perf["Plant Code"].to_list()
    )
    list(all_plant_ids.difference(common_plant_ids))

    dataset_name_to_df = {
        "EIA860-Plant": plant,
        "EIA860-Generator": gen,
        "EIA923": perf,
    }

    for dataset_name, df in dataset_name_to_df.items():
        df["Plant Code"]

    pass


def load_eia_data_by_plant(data_year=2024, return_missing_ids=False):
    plant = load_eia_860("Plant", year=data_year)
    gen = load_eia_860("Generator", year=data_year)
    perf = load_eia_923("SourceNDispo", year=data_year)
    perf_col_rename = {c: c.replace("\n", "") for c in perf.columns.to_list()}
    perf.rename(columns=perf_col_rename, inplace=True)

    shared_cols_860 = list(
        set(plant.columns.to_list()).intersection(set(gen.columns.to_list()))
    )
    shared_cols = list(set(shared_cols_860).intersection(set(perf.columns.to_list())))
    shared_cols_860.remove("Plant Code")
    shared_cols.remove("Plant Code")

    plant["Plant Code"] = plant["Plant Code"].astype(int)
    gen["Plant Code"] = gen["Plant Code"].astype(int)
    perf["Plant Code"] = perf["Plant Code"].astype(int)

    common_plant_ids = list(
        set(plant["Plant Code"].to_list()).intersection(
            set(gen["Plant Code"].to_list())
        )
    )
    common_plant_ids = list(
        set(common_plant_ids).intersection(set(perf["Plant Code"].to_list()))
    )
    common_plant_ids.sort()

    all_plant_ids = set(
        plant["Plant Code"].to_list()
        + gen["Plant Code"].to_list()
        + perf["Plant Code"].to_list()
    )
    missing_plant_ids = list(all_plant_ids.difference(common_plant_ids))

    plant.set_index(keys=["Plant Code"], inplace=True)
    gen.set_index(keys=["Plant Code"], inplace=True)
    perf.set_index(keys=["Plant Code"], inplace=True)

    # only use the data with shared data
    plant = plant.loc[common_plant_ids]
    gen = gen.loc[common_plant_ids]
    perf = perf.loc[common_plant_ids]

    # gen has multiple rows per plant id
    [c for c in gen.columns.to_list() if c not in shared_cols_860]
    perf_cols = [c for c in perf.columns.to_list() if c not in shared_cols]

    gen_summer_cols = [
        "Nameplate Capacity (MW)",
        "Winter Capacity (MW)",
        "Summer Capacity (MW)",
        "Minimum Load (MW)",
    ]
    gen_average_cols = ["Nameplate Power Factor"]

    # Summarize data of all generators in a plant
    for col in gen_summer_cols:
        gen[col] = pd.to_numeric(gen[col], errors="coerce").fillna(0)
        tot = gen.groupby(gen.index)[col].sum()
        plant = pd.concat([plant, tot], axis=1)
    # for col in gen_average_cols:
    #     gen[col] = pd.to_numeric(gen[col], errors='coerce').fillna(0)
    #     # avg = gen.groupby(gen.index)[col].mean()
    #     avg = gen.groupby(gen.index)[col].mean()
    #     plant = pd.concat([plant,avg],axis=1)
    for col in gen_average_cols:
        gen[col] = pd.to_numeric(gen[col], errors="coerce").fillna(0)
        weighted_avg = (
            gen.groupby(gen.index)[col]
            * gen.groupby(gen.index)["Nameplate Capacity (MW)"]
        ).sum() / gen.groupby(gen.index)["Nameplate Capacity (MW)"].sum()
        plant = pd.concat([plant, weighted_avg], axis=1)

    # Add in number of generators per plant
    # n_gen_per_plant = [len(gen.loc[ii]) for ii in plant.index.to_list()]
    # plant = pd.concat([plant, pd.DataFrame({"N Generators": n_gen_per_plant}, index=plant.index)], axis=1)

    # Summarize primary prime mover for plant
    n_gen_per_plant = [
        1
        if isinstance(gen.loc[ii]["Prime Mover"], str)
        else len(gen.loc[ii]["Prime Mover"].to_list())
        for ii in plant.index.to_list()
    ]
    plant = pd.concat(
        [plant, pd.DataFrame({"N Generators": n_gen_per_plant}, index=plant.index)],
        axis=1,
    )

    prime_mover_types = [
        [gen.loc[ii]["Prime Mover"]]
        if isinstance(gen.loc[ii]["Prime Mover"], str)
        else list(set(gen.loc[ii]["Prime Mover"].to_list()))
        for ii in plant.index.to_list()
    ]
    has_multi_prime_mover = [
        True if len(pm_type) > 1 else False for pm_type in prime_mover_types
    ]
    n_prime_mover_types_per_plant = [len(pm_type) for pm_type in prime_mover_types]

    prime_mover_data = {
        "N Prime Mover Types": n_prime_mover_types_per_plant,
        "Multi Prime Mover": has_multi_prime_mover,
        "Prime Mover Types": prime_mover_types,
    }
    plant = pd.concat(
        [plant, pd.DataFrame(prime_mover_data, index=plant.index)], axis=1
    )

    # Calculate the capacity factor
    perf["Gross Generation"] = pd.to_numeric(
        perf["Gross Generation"], errors="coerce"
    ).fillna(0)
    plant["Capacity Factor"] = perf["Gross Generation"] / (
        plant["Nameplate Capacity (MW)"] * 8760
    )
    plant["Capacity Factor"] = pd.to_numeric(
        plant["Capacity Factor"], errors="coerce"
    ).fillna(0)
    # more generator then plant, more plant than perf

    res = pd.concat([plant, perf[perf_cols]], axis=1)
    if return_missing_ids:
        return res, missing_plant_ids
    return res


def load_eia_data_by_plant_and_primemover(data_year=2024):
    # Sort data by prime-mover and plant ID
    plant = load_eia_860("Plant", year=data_year)
    gen = load_eia_860("Generator", year=data_year)
    perf = load_eia_923("SourceNDispo", year=data_year)
    perf_col_rename = {c: c.replace("\n", "") for c in perf.columns.to_list()}
    perf.rename(columns=perf_col_rename, inplace=True)

    plant["Plant Code"] = plant["Plant Code"].astype(int)
    gen["Plant Code"] = gen["Plant Code"].astype(int)
    perf["Plant Code"] = perf["Plant Code"].astype(int)

    common_plant_ids = list(
        set(plant["Plant Code"].to_list()).intersection(
            set(gen["Plant Code"].to_list())
        )
    )
    common_plant_ids = list(
        set(common_plant_ids).intersection(set(perf["Plant Code"].to_list()))
    )
    common_plant_ids.sort()

    all_plant_ids = set(
        plant["Plant Code"].to_list()
        + gen["Plant Code"].to_list()
        + perf["Plant Code"].to_list()
    )
    list(all_plant_ids.difference(common_plant_ids))

    plant.set_index(keys=["Plant Code"], inplace=True)
    gen.set_index(keys=["Plant Code"], inplace=True)
    perf.set_index(keys=["Plant Code"], inplace=True)

    # only use the data with shared data
    plant = plant.loc[common_plant_ids]
    gen = gen.loc[common_plant_ids]
    perf = perf.loc[common_plant_ids]

    # Plant ID: 260, multi prime movers
    # Plant ID 34 has single prime mover type
    # Plant ID 70 has 2 prie movers of same type
    plant["Prime Mover"] = [""] * len(plant)
    perf["Prime Mover"] = [""] * len(perf)
    perf["Gross Generation"] = pd.to_numeric(
        perf["Gross Generation"], errors="coerce"
    ).fillna(0)
    copy.deepcopy(perf["Gross Generation"].sum())

    gen["Nameplate Capacity (MW)"] = pd.to_numeric(
        gen["Nameplate Capacity (MW)"], errors="coerce"
    ).fillna(0)
    plant_capacity = gen.groupby(level=["Plant Code"])["Nameplate Capacity (MW)"].sum()
    plant_generation = perf.groupby(level=["Plant Code"])["Gross Generation"].sum()

    plant["Plant Generation"] = plant_generation
    plant["Capacity Factor"] = plant_generation / (plant_capacity * 8760)
    plant["Capacity Factor"] = pd.to_numeric(
        plant["Capacity Factor"], errors="coerce"
    ).fillna(0)

    for pid in common_plant_ids:
        # gen.loc[pid]
        # gen.loc[260]["Prime Mover"]
        if isinstance(gen.loc[pid, "Prime Mover"], str):
            plant.loc[pid, "Prime Mover"] = gen.loc[pid, "Prime Mover"]
            perf.loc[pid, "Prime Mover"] = gen.loc[pid, "Prime Mover"]
        else:
            prime_movers = list(set(gen.loc[pid, "Prime Mover"].to_list()))
            if len(prime_movers) == 1:
                plant.loc[pid, "Prime Mover"] = prime_movers[0]
                perf.loc[pid, "Prime Mover"] = prime_movers[0]
            else:
                temp_plant = pd.DataFrame()
                temp_perf = pd.DataFrame()

                for ppi, pm in enumerate(prime_movers):
                    pt = plant.loc[pid].copy(deep=True)
                    pt["Prime Mover"] = pm
                    temp_plant = pd.concat([temp_plant, pt], axis=1)

                    pf = perf.loc[pid].copy(deep=True)
                    pf["Prime Mover"] = pm
                    if ppi > 0:
                        pf["Gross Generation"] = 0.0
                    # TODO: adjust gross generation per prime mover type
                    temp_perf = pd.concat([temp_perf, pf], axis=1)

                temp_plant = temp_plant.T
                temp_perf = temp_perf.T
                # Drop the previous plant row
                plant.drop(index=pid, inplace=True)
                perf.drop(index=pid, inplace=True)
                # Add in the new rows
                plant = pd.concat([plant, temp_plant], axis=0)
                perf = pd.concat([perf, temp_perf], axis=0)
    plant.reset_index(names=["Plant Code"], inplace=True)
    perf.reset_index(names=["Plant Code"], inplace=True)
    gen.reset_index(names=["Plant Code"], inplace=True)

    plant.set_index(keys=["Plant Code", "Prime Mover"], inplace=True)
    gen.set_index(keys=["Plant Code", "Prime Mover"], inplace=True)
    perf.set_index(keys=["Plant Code", "Prime Mover"], inplace=True)

    plant.sort_index(inplace=True)
    gen.sort_index(inplace=True)
    perf.sort_index(inplace=True)
    []
    # n_gen_per_plant_pm = [[gen.loc[ii]["Prime Mover"]] if isinstance(gen.loc[ii]["Prime Mover"], str) else list(set(gen.loc[ii]["Prime Mover"].to_list())) for ii in common_plant_ids]

    gen_summer_cols = [
        "Nameplate Capacity (MW)",
        "Winter Capacity (MW)",
        "Summer Capacity (MW)",
        "Minimum Load (MW)",
    ]
    gen_average_cols = ["Nameplate Power Factor"]

    for col in gen_summer_cols:
        gen[col] = pd.to_numeric(gen[col], errors="coerce").fillna(0)
        tot = gen.groupby(level=["Plant Code", "Prime Mover"])[col].sum()
        plant = pd.concat([plant, tot], axis=1)

    for col in gen_average_cols:
        gen[col] = pd.to_numeric(gen[col], errors="coerce").fillna(0)
        # gen.groupby(level=["Plant Code","Prime Mover"])[col].sum()*gen.groupby(gen.index)["Nameplate Capacity (MW)"]
        weighted_avg = (
            gen.groupby(level=["Plant Code", "Prime Mover"])[col].sum()
            * gen.groupby(level=["Plant Code", "Prime Mover"])[
                "Nameplate Capacity (MW)"
            ].sum()
        ) / gen.groupby(level=["Plant Code", "Prime Mover"])[
            "Nameplate Capacity (MW)"
        ].sum()
        plant = pd.concat([plant, weighted_avg], axis=1)

    n_gen_per_plant_pm = [len(gen.loc[i]) for i in plant.index]
    plant = pd.concat(
        [plant, pd.DataFrame({"N Generators": n_gen_per_plant_pm}, index=plant.index)],
        axis=1,
    )

    # plant_capacity = gen.groupby(level=["Plant Code"])["Nameplate Capacity (MW)"].sum()
    # plant_generation = perf.groupby(level=["Plant Code"])["Gross Generation"].sum()

    # assert tot_generation_init==plant_generation.sum()

    # plant_cf = plant_generation/(plant_capacity*8760)

    # Calculate the capacity factor
    # TODO: The Gross generation is the gross generation per plant, not per prime mover
    # perf["Gross Generation"] = pd.to_numeric(perf["Gross Generation"], errors='coerce').fillna(0)

    # plant["Capacity Factor"] = perf["Gross Generation"]/(plant["Nameplate Capacity (MW)"]*8760)
    # plant["Capacity Factor"] = pd.to_numeric(plant["Capacity Factor"], errors="coerce").fillna(0)

    gen_per_pm_plant = (
        plant["Capacity Factor"] * plant["Nameplate Capacity (MW)"] * 8760
    )
    gen_per_pm_plant.name = "Prime Mover Generation"
    plant = pd.concat([plant, gen_per_pm_plant], axis=1)

    # Check that the sum of prime mover generation = plant generation
    pm_gen_per_plant = plant.groupby(level=["Plant Code"])[
        "Prime Mover Generation"
    ].sum()

    for pid, tot_pm_gen in pm_gen_per_plant.to_dict().items():
        plant_gen = plant.loc[pid]["Plant Generation"].values[0]

        assert np.isclose(plant_gen, tot_pm_gen, atol=0.1), f"{pid}"

    perf_cols = [c for c in perf.columns.to_list() if c not in plant.columns.to_list()]
    res = pd.concat([plant, perf[perf_cols]], axis=1)
    return res


# if __name__ == "__main__":
#     from ice import DATA_DIR
#     res = load_eia_data_by_plant_and_primemover()
#     res.loc[260].to_csv(DATA_DIR/"test_eia_grid_data_pid_260.csv")


[]
