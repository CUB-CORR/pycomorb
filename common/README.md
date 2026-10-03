# Codes and weights for the `Charlson Comorbidity Index` (CCI)

Original index:

- Charlson ME, Pompei P, Ales KL, MacKenzie CR. A new method of classifying prognostic comorbidity in longitudinal studies: development and validation. J Chronic Dis. 1987;40(5):373-83. doi: [10.1016/0021-9681(87)90171-8](https://doi.org/10.1016/0021-9681(87)90171-8). PMID: 3558716.
- Charlson M, Szatrowski TP, Peterson J, Gold J. Validation of a combined comorbidity index. J Clin Epidemiol. 1994 Nov;47(11):1245-51. doi: [10.1016/0895-4356(94)90129-5](https://doi.org/10.1016/0895-4356(94)90129-5). PMID: 7722560.

## Mappings (sorted by year)

- **Deyo et al. 1992** (ICD-9-CM, `implementation="deyo"`):<br>Deyo RA, Cherkin DC, Ciol MA. Adapting a clinical comorbidity index for use with ICD-9-CM administrative databases. J Clin Epidemiol. 1992 Jun;45(6):613-9. doi: [10.1016/0895-4356(92)90133-8](https://doi.org/10.1016/0895-4356(92)90133-8). PMID: 1607900.
- **Romano et al. 1993** (ICD-9-CM, `implementation="romano"`):<br>Romano PS, Roos LL, Jollis JG. Adapting a clinical comorbidity index for use with ICD-9-CM administrative data: differing perspectives. J Clin Epidemiol. 1993 Oct;46(10):1075-9; discussion 1081-90. doi: [10.1016/0895-4356(93)90103-8](https://doi.org/10.1016/0895-4356(93)90103-8). PMID: 8410092.
  - The implementation uses the codes as described in the recent revision in the Romano paper. In the original Romano table, no codes for "Rheumatologic disease" and "AIDS" are given. The mentioned codes for _hypertensive heart and renal disease with congestive heart failure_ are not included, as they were not yet in use by Romano et al
- **D'Hoore et al. 1996** (ICD-9-CM, `implementation="dhoore"`):<br>D'Hoore W, Bouckaert A, Tilquin C. Practical considerations on the use of the Charlson comorbidity index with administrative data bases. J Clin Epidemiol. 1996 Dec;49(12):1429-33. doi: [10.1016/s0895-4356(96)00271-5](https://doi.org/10.1016/s0895-4356(96)00271-5). PMID: 8991959.
- **Australia, Sundararajan et al. 2004** (ICD-10-AM, `implementation="australia"`):<br>Sundararajan V, Henderson T, Perry C, Muggivan A, Quan H, Ghali WA. New ICD-10 version of the Charlson comorbidity index predicted in-hospital mortality. J Clin Epidemiol. 2004 Dec;57(12):1288-94. doi: [10.1016/j.jclinepi.2004.03.012](https://doi.org/10.1016/j.jclinepi.2004.03.012). PMID: 15617955.
  - The categories are renamed the following way:
    - Cerebrovascular disease -> Cerebral vascular accident
    - Chronic pulmonary disease -> Pulmonary disease
    - Diabetes without chronic complication -> Diabetes
    - Diabetes with chronic complication -> Diabetes complications
    - Hemiplegia or paraplegia -> Paraplegia
    - Myocardial infarction -> Acute myocardial infarction
    - Peptic ulcer disease -> Peptic ulcer
    - Rheumatic disease -> Connective tissue disorder
    - Any malignancy, including lymphoma and leukemia, except malignant neoplasm of skin -> Cancer
    - Metastatic solid tumor -> Metastatic cancer
    - AIDS/HIV -> HIV
- **Quan et al. 2005** (ICD-9-CM and ICD-10, `implementation="quan"`):<br>Quan H, Sundararajan V, Halfon P, Fong A, Burnand B, Luthi JC, Saunders LD, Beck CA, Feasby TE, Ghali WA. Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10 administrative data. Med Care. 2005 Nov;43(11):1130-9. doi: [10.1097/01.mlr.0000182534.19832.83](https://doi.org/10.1097/01.mlr.0000182534.19832.83). PMID: 16224307.
- **Royal College of Surgeons (RCS), Armitage and van der Meulen 2010** (ICD-10, `implementation="rcs"`):<br>Armitage JN, van der Meulen JH; Royal College of Surgeons Co-morbidity Consensus Group. Identifying co-morbidity in surgical patients using administrative data with the Royal College of Surgeons Charlson Score. Br J Surg. 2010 May;97(5):772-81. doi: [10.1002/bjs.6930](https://doi.org/10.1002/bjs.6930). PMID: 20306528.
  - The categories are renamed the following way:
    - Rheumatic disease -> Rheumatological disease
  - `Peptic ulcer disease` is not included
  - Liver disease and Diabetes are NOT split into two categories depending on severity / complications
  - Always used with the RCS weights (see below)
- **Denmark, Thygesen et al. 2011** (ICD-10, `implementation="thygesen"`):<br>Thygesen SK, Christiansen CF, Christensen S, Lash TL, Sørensen HT. The predictive value of ICD-10 diagnostic coding used to assess Charlson comorbidity index conditions in the population-based Danish National Registry of Patients. BMC Med Res Methodol. 2011 May 28;11:83. doi: [10.1186/1471-2288-11-83](https://doi.org/10.1186/1471-2288-11-83). PMID: 21619668; PMCID: PMC3125388.
  - Keeps `Any tumor`, `Leukemia`, and `Lymphoma` as three separate categories, per its own ICD-10 coding, rather than the merged `Any malignancy`
- **Sweden, Ludvigsson et al. 2021** (ICD-9 and ICD-10, `implementation="sweden"`):<br>Ludvigsson JF, Appelros P, Askling J, Byberg L, Carrero JJ, Ekström AM, Ekström M, Smedby KE, Hagström H, James S, Järvholm B, Michaelsson K, Pedersen NL, Sundelin H, Sundquist K, Sundström J. Adaptation of the Charlson Comorbidity Index for Register-Based Research in Sweden. Clin Epidemiol. 2021 Jan 12;13:21-41. doi: [10.2147/CLEP.S282475](https://doi.org/10.2147/CLEP.S282475). Erratum in: Clin Epidemiol. 2023 Jun 19;15:753-754. doi: [10.2147/CLEP.S425901](https://doi.org/10.2147/CLEP.S425901). PMID: 33469380; PMCID: PMC7812935.
  - `CHARLSON_SWEDEN.csv`, generated by `common/version_SE/sweden.py` from the authors' SAS code ([bjoroeKI/Charlson-comorbidity-index-revisited](https://github.com/bjoroeKI/Charlson-comorbidity-index-revisited), `Charlson_SAS`)
  - The categories are renamed the following way:
    - Chronic pulmonary disease -> Chronic obstructive pulmonary disease (COPD) _and_ Other chronic pulmonary disease
    - Hemiplegia or paraplegia -> Hemiplegia, tetraplegia
    - Diabetes without chronic complication -> Diabetes
    - Diabetes with chronic complication -> Diabetes with end organ damage
    - Renal disease -> Moderate or severe kidney disease
    - Peptic ulcer disease -> (Peptic) Ulcer disease
    - Any malignancy, including lymphoma and leukemia, except malignant neoplasm of skin -> Any malignancy, including lymphoma and leukemia
    - Metastatic solid tumor -> Metastatic cancer
- **UK SHMI, NHS Digital v1.60 (June 2026)** (ICD-10, `implementation="uk_shmi"`):<br>[Summary Hospital-level Mortality Indicator (SHMI)](https://digital.nhs.uk/data-and-information/publications/statistical/shmi)
  - The SHMI ICD code mappings may be downloaded under the heading `Resources` -> `Methodology specifications`. The implementation is currently on [Version 1.60 (June 2026)](https://files.digital.nhs.uk/F9/B8CD11/SHMI%20specification%20v1.60.pdf)
  - Always used with the SHMI weights (see below)
  - The categories are renamed the following way:
    - Myocardial infarction -> Acute myocardial infarction
    - Cerebrovascular disease -> Cerebral vascular accident
    - Chronic pulmonary disease -> Pulmonary disease
    - Rheumatic disease -> Connective tissue disorder
    - Peptic ulcer disease -> Peptic ulcer
    - Mild liver disease -> Liver disease
    - Diabetes without chronic complication -> Diabetes
    - Diabetes with chronic complication -> Diabetes complications
    - Hemiplegia or paraplegia -> Paraplegia
    - Any malignancy, including lymphoma and leukemia, except malignant neoplasm of skin -> Cancer
    - Moderate or severe liver disease -> Severe liver disease
    - Metastatic solid tumor -> Metastatic cancer
    - AIDS/HIV -> HIV
- **Germany, Sokołowski et al. 2026** (ICD-10-GM, `implementation="sokolowski"`, requires `year_col`):<br>Sokołowski PP, Hagmann M, Maros ME, Kamdje Wabo G, Meerjanssen JM, Siegel F. Developing Country-Specific Charlson Comorbidity Index Mappings for Use With German Administrative Data: Methodological Comparative Study. JMIR Med Inform. 2026 Sep 3;14:e93923. doi: [10.2196/93923](https://doi.org/10.2196/93923). PMID: 42593349; PMCID: PMC13586706.
  - `CHARLSON_SOKOLOWSKI.csv`, generated by `common/modification_DE/germanmodification_sokolowksi.py` from the authors' year-specific ICD-10-GM mapping JSONs ([fabiansiegel/comorbidity_score](https://github.com/fabiansiegel/comorbidity_score), `comorbidity_score_calc/mappings/`)

## Weights (sorted by year)

- **Charlson et al. 1987** (`weights="charlson"`): see the original index above
- **RCS, Armitage and van der Meulen 2010** (`weights="rcs"`): see the RCS mapping above
  - "each disease category is given an equal weight in the RCS Charlson Score, as it was designed to be used as a simple count of co-morbid conditions"
  - consequently, categories not included in the RCS mapping and the age score have no weight (i.e., age is not part of the RCS score)
- **Quan et al. 2011** (`weights="quan"`):<br>Quan H, Li B, Couris CM, Fushimi K, Graham P, Hider P, Januel JM, Sundararajan V. Updating and validating the Charlson comorbidity index and score for risk adjustment in hospital discharge abstracts using data from 6 countries. Am J Epidemiol. 2011 Mar 15;173(6):676-82. doi: [10.1093/aje/kwq433](https://doi.org/10.1093/aje/kwq433). Epub 2011 Feb 17. PMID: 21330339.
- **UK SHMI, NHS Digital v1.60 (June 2026)** (`weights="uk_shmi"`): see the SHMI mapping above. A negative total is assigned a value of zero

# Codes and weights for the `Elixhauser Comorbidity Index` (ECI)

Original index:

- Elixhauser A, Steiner C, Harris DR, Coffey RM. Comorbidity measures for use with administrative data. Med Care. 1998 Jan;36(1):8-27. doi: [10.1097/00005650-199801000-00004](https://doi.org/10.1097/00005650-199801000-00004). PMID: 9431328.

## Mappings (sorted by year)

- **Elixhauser et al. 1998** (ICD-9-CM, `implementation="elixhauser"`): see the original index above
- **Quan et al. 2005** (ICD-9-CM and ICD-10, `implementation="quan"`):<br>Quan H, Sundararajan V, Halfon P, Fong A, Burnand B, Luthi JC, Saunders LD, Beck CA, Feasby TE, Ghali WA. Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10 administrative data. Med Care. 2005 Nov;43(11):1130-9. doi: [10.1097/01.mlr.0000182534.19832.83](https://doi.org/10.1097/01.mlr.0000182534.19832.83). PMID: 16224307.
- **AHRQ v3.7** (ICD-9-CM, `implementation="ahrq_icd9"`):<br>Agency for Healthcare Research and Quality. [Elixhauser Comorbidity Software, Version 3.7 (ICD-9-CM)](https://hcup-us.ahrq.gov/toolssoftware/comorbidity/comorbidity.jsp#download)<br>`ELIXHAUSER_AHRQ_ICD9.csv`, generated by `common/modification_US/clinicalmodification_ahrq_icd9.py`
  - The categories are renamed the following way:
    - Diabetes uncomplicated -> Diabetes without chronic complications
    - Diabetes complicated -> Diabetes with chronic complications
    - Hypertension uncomplicated _and_ Hypertension complicated -> Hypertension
  - `Cardiac arrhythmias` is not an AHRQ category and is not included
- **AHRQ Refined v2026.1** (ICD-10-CM, `implementation="ahrq_icd10"`, requires `year_col`):<br>Agency for Healthcare Research and Quality. [Elixhauser Comorbidity Software Refined for ICD-10-CM, v2026.1](https://hcup-us.ahrq.gov/toolssoftware/comorbidityicd10/comorbidity_icd10.jsp#down)<br>`ELIXHAUSER_AHRQ_ICD10.csv`, generated by `common/modification_US/clinicalmodification_ahrq_icd10.py`
  - The categories are renamed the following way:
    - Congestive heart failure -> Heart failure
    - Peripheral vascular disorders -> Peripheral vascular disease
    - Pulmonary circulation disorders -> Pulmonary circulation disease
    - Hypertension uncomplicated -> Hypertension, uncomplicated
    - Hypertension complicated -> Hypertension, complicated
    - Diabetes uncomplicated -> Diabetes without chronic complications
    - Diabetes complicated -> Diabetes with chronic complications
    - Peptic ulcer disease excluding bleeding -> Peptic ulcer disease
    - AIDS/HIV -> Acquired immune deficiency syndrome
    - Deficiency anemia -> Anemias due to other nutritional deficiencies
    - Blood loss anemia -> Chronic blood loss anemia (iron deficiency)
    - Solid tumor without metastasis -> Solid tumor without metastasis, malignant
    - Liver disease -> Liver disease, mild _and_ Liver disease, moderate to severe
    - Renal failure -> Renal failure, moderate _and_ Renal failure, severe
    - Rheumatoid arthritis/collagen vascular diseases -> Autoimmune conditions
  - `Cardiac arrhythmias` and `Fluid and electrolyte disorders` are not included
  - Adds new categories with no Quan equivalent: `Dementia`, `Leukemia`, `Solid tumor without metastasis, in situ`, `Cerebrovascular disease`, `Other thyroid disorders`, `Neurological disorders affecting movement`, `Seizures and epilepsy`

## Weights (sorted by year)

- **van Walraven et al. 2009** (`weights="van_walraven"`):<br>van Walraven C, Austin PC, Jennings A, Quan H, Forster AJ. A modification of the Elixhauser comorbidity measures into a point system for hospital death using administrative data. Med Care. 2009 Jun;47(6):626-33. doi: [10.1097/MLR.0b013e31819432e5](https://doi.org/10.1097/MLR.0b013e31819432e5). PMID: 19433995.
- **Thompson et al. 2015** (`weights="thompson_30"` or `weights="thompson_29"`):<br>Thompson NR, Fan Y, Dalton JE, Jehi L, Rosenbaum BP, Vadera S, Griffith SD. A new Elixhauser-based comorbidity summary measure to predict in-hospital mortality. Med Care. 2015 Apr;53(4):374-9. doi: [10.1097/MLR.0000000000000326](https://doi.org/10.1097/MLR.0000000000000326). PMID: 25769057; PMCID: PMC4812819.
- **AHRQ, Moore et al. 2017** (ICD-9-CM, `weights="ahrq"`, always used with `implementation="ahrq_icd9"`):<br>Moore BJ, White S, Washington R, Coenen N, Elixhauser A. Identifying Increased Risk of Readmission and In-hospital Mortality Using Hospital Administrative Data: The AHRQ Elixhauser Comorbidity Index. Med Care. 2017 Jul;55(7):698-705. doi: [10.1097/MLR.0000000000000735](https://doi.org/10.1097/MLR.0000000000000735). PMID: 28498196.
- **AHRQ Refined v2026.1** (ICD-10-CM, `weights="ahrq"`, always used with `implementation="ahrq_icd10"`): mortality index weights of the AHRQ software, merged into `ELIXHAUSER_WEIGHTS.csv` by `common/modification_US/clinicalmodification_ahrq_icd10.py`
- **Swiss, Sharma et al. 2021** (`weights="swiss"`):<br>Sharma N, Schwendimann R, Endrich O, Ausserhofer D, Simon M. Comparing Charlson and Elixhauser comorbidity indices with different weightings to predict in-hospital mortality: an analysis of national inpatient data. BMC Health Serv Res. 2021 Jan 6;21(1):13. doi: [10.1186/s12913-020-05999-5](https://doi.org/10.1186/s12913-020-05999-5). PMID: 33407455; PMCID: PMC7786470.

# Codes and weights for the `Combined Comorbidity Score` (CCS)

## Mappings (sorted by year)

- **Gagne et al. 2011** (ICD-9-CM, `score="combined"`, `icd_version="icd9"`):<br>Gagne JJ, Glynn RJ, Avorn J, Levin R, Schneeweiss S. A combined comorbidity score predicted mortality in elderly patients better than existing scores. J Clin Epidemiol. 2011 Jul;64(7):749-59. doi: [10.1016/j.jclinepi.2010.10.004](https://doi.org/10.1016/j.jclinepi.2010.10.004). Epub 2011 Jan 5. PMID: 21208778; PMCID: PMC3100405.
  - ICD-9-CM codes combine the Charlson conditions as mapped by Romano et al. 1993 and the Elixhauser conditions as mapped by Quan et al. 2005
- **Sun et al. 2017** (ICD-10-CM, `score="combined"`, `icd_version="icd10"`):<br>Sun JW, Rogers JR, Her Q, Welch EC, Panozzo CA, Toh S, Gagne JJ. Adaptation and Validation of the Combined Comorbidity Score for ICD-10-CM. Med Care. 2017 Dec;55(12):1046-1051. doi: [10.1097/MLR.0000000000000824](https://doi.org/10.1097/MLR.0000000000000824). PMID: 29087983.

## Weights

- **Gagne et al. 2011** (`score="combined"`): see the Gagne mapping above

# Codes and weights for the `Hospital Frailty Risk Score` (HFRS)

## Mappings

- **Gilbert et al. 2018** (ICD-10, `score="hfrs"`):<br>Gilbert T, Neuburger J, Kraindler J, Keeble E, Smith P, Ariti C, Arora S, Street A, Parker S, Roberts HC, Bardsley M, Conroy S. Development and validation of a Hospital Frailty Risk Score focusing on older people in acute care settings using electronic hospital records: an observational study. Lancet. 2018 May 5;391(10132):1775-1782. doi: [10.1016/S0140-6736(18)30668-8](https://doi.org/10.1016/S0140-6736(18)30668-8). Epub 2018 Apr 26. PMID: 29706364; PMCID: PMC5946808.
  - The ICD-10 codes and associated weights/categories can be found in the supplementary appendix of the paper

## Weights

- **Gilbert et al. 2018** (`score="hfrs"`): see the mapping above
