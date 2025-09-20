# 1. download all the relevant ICD-10-GM versions from https://www.bfarm.de/DE/Kodiersysteme/Services/Downloads/_node.html
# 2. unzip them into a folder, e.g. data/icd10gm
# 3. take only the transfer files (e.g. icd10gm2013syst_umsteiger_2012_2013.txt for 2012->2013) and put them into a separate folder, e.g. data/icd10gm/transfers
# 4. run this script in that folder

import polars as pl

files = [
    "umsteiger20042005.txt",  # 2004->2005, renamed from 'umsteiger.txt' for clarity
    "umsteiger20052006.txt",  # 2005->2006, renamed from 'umsteiger.txt' for clarity
    "umsteiger20062007.txt",  # 2006->2007, renamed from 'Umsteiger.txt' for clarity
    "umsteiger20072008.txt",  # 2007->2008
    "umsteiger_icd10gmsyst2008_icd10gmsyst2009.txt",  # 2008->2009
    "umsteiger_icd10gmsyst2009_icd10gmsyst2010.txt",  # 2009->2010
    "umsteiger_icd10gmsyst2010_icd10gmsyst2011.txt",  # 2010->2011
    "umsteiger_icd10gmsyst2011_icd10gmsyst2012.txt",  # 2011->2012
    "icd10gm2013syst_umsteiger_2012_2013.txt",  # 2012->2013
    "icd10gm2014syst_umsteiger_2013_2014.txt",  # 2013->2014
    "icd10gm2015syst_umsteiger_2014_2015.txt",  # 2014->2015
    "icd10gm2016syst_umsteiger_2015_2016.txt",  # 2015->2016
    "icd10gm2017syst_umsteiger_2016_2017.txt",  # 2016->2017
    "icd10gm2018syst_umsteiger_2017_2018.txt",  # 2017->2018
    "icd10gm2019syst_umsteiger_2018_2019.txt",  # 2018->2019
    "icd10gm2020syst_umsteiger_2019_2020.txt",  # 2019->2020
    "icd10gm2021syst_umsteiger_2020_2021.txt",  # 2020->2021
    "icd10gm2022syst_umsteiger_2021_2022.txt",  # 2021->2022
    "icd10gm2023syst_umsteiger_2022_2023_20221206.txt",  # 2022->2023
    "icd10gm2024syst_umsteiger_2023_20221206_2024.txt",  # 2023->2024
    "icd10gm2025syst_umsteiger_2024_2025.txt",  # 2024->2025
]
years = range(2004, 2025)

df = None
for year, file in zip(years, files):
    print(f"Processing {year}->{year+1}: {file}")
    if df is None:
        df = pl.DataFrame(schema={str(year): pl.Utf8})

    year_df = (
        pl.read_csv(
            file,
            separator=";",
            has_header=False,
            null_values=["", " "],  # , "UNDEF"],
            schema={
                str(year): pl.Utf8,  # Alte_Kodiernummer
                str(year + 1): pl.Utf8,  # Neue_Kodiernummer
                "A1": pl.Utf8,
                "A2": pl.Utf8,
            },
        )
        .drop("A1", "A2")
        # Clean up codes: remove dots, uppercase
        .with_columns(
            pl.col(str(year))
            .str.replace_all(r"\.", "")
            .replace("UNDEF", f"UNDEF{year}")
            .str.to_uppercase(),
            pl.col(str(year + 1))
            .str.replace_all(r"\.", "")
            .replace("UNDEF", f"UNDEF{year}")
            .str.to_uppercase(),
        )
        .filter(pl.col(str(year)).ne_missing(pl.col(str(year + 1))))
        .unique()
    )
    df = df.join(year_df, on=str(year), how="full", coalesce=True)
    
# Propagate codes forward to fill in unmapped codes
for year in years:
    df = df.with_columns(
        pl.when(pl.col(str(year + 1)).is_null())
        .then(pl.col(str(year)))
        .otherwise(pl.col(str(year + 1)))
        .alias(str(year + 1))
    )
# Propagate codes backward to fill in unmapped codes
for year in reversed(years):
    df = df.with_columns(
        pl.when(pl.col(str(year)).is_null())
        .then(pl.col(str(year + 1)))
        .otherwise(pl.col(str(year)))
        .alias(str(year))
    )

df.write_csv("icd10gm.csv")
