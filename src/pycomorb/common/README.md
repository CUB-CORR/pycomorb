# Codes for the `Charlson Comorbidity Index` (CCI)

Reference for CCI:

1. Charlson ME, Pompei P, Ales KL, MacKenzie CR. A new method of classifying prognostic comorbidity in longitudinal studies: development and validation. J Chronic Dis. 1987;40(5):373-83. doi: [10.1016/0021-9681(87)90171-8](<http://doi.org/10.1016/0021-9681(87)90171-8>). PMID: 3558716.
2. Charlson M, Szatrowski TP, Peterson J, Gold J. Validation of a combined comorbidity index. J Clin Epidemiol. 1994 Nov;47(11):1245-51. doi: [10.1016/0895-4356(94)90129-5](<http://doi.org/10.1016/0895-4356(94)90129-5>). PMID: 7722560.

References for ICD-9-CM and ICD-10 Coding Algorithms for Charlson Comorbidities:

3. Deyo RA, Cherkin DC, Ciol MA. Adapting a clinical comorbidity index for use with ICD-9-CM administrative databases. J Clin Epidemiol. 1992 Jun;45(6):613-9. doi: [10.1016/0895-4356(92)90133-8](https://doi.org/10.1016/0895-4356(92)90133-8). PMID: 1607900.
4. D'Hoore W, Bouckaert A, Tilquin C. Practical considerations on the use of the Charlson comorbidity index with administrative data bases. J Clin Epidemiol. 1996 Dec;49(12):1429-33. doi: [10.1016/s0895-4356(96)00271-5](https://doi.org/10.1016/s0895-4356(96)00271-5). PMID: 8991959.
5. Romano PS, Roos LL, Jollis JG. Adapting a clinical comorbidity index for use with ICD-9-CM administrative data: differing perspectives. J Clin Epidemiol. 1993 Oct;46(10):1075-9; discussion 1081-90. doi: [10.1016/0895-4356(93)90103-8](https://doi.org/10.1016/0895-4356(93)90103-8). PMID: 8410092.
    - The implementation uses the codes as described in the recent revision in the Romano paper. In the original Romano table, no codes for "Rheumatologic disease" and "AIDS" are given. The mentioned codes for _hypertensive heart  and  renal  disease  with  congestive heart  failure_ are not included, as they were not yet in use by Romano et al.
6. Quan H, Sundararajan V, Halfon P, Fong A, Burnand B, Luthi JC, Saunders LD, Beck CA, Feasby TE, Ghali WA. Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10 administrative data. Med Care. 2005 Nov;43(11):1130-9. doi: [10.1097/01.mlr.0000182534.19832.83](http://doi.org/10.1097/01.mlr.0000182534.19832.83). PMID: 16224307.

The following variants are also added:

- **Australia** (ICD-10 only, CAVE: ICD-10-AM):<br>Sundararajan V, Henderson T, Perry C, Muggivan A, Quan H, Ghali WA. New ICD-10 version of the Charlson comorbidity index predicted in-hospital mortality. J Clin Epidemiol. 2004 Dec;57(12):1288-94. doi: [10.1016/j.jclinepi.2004.03.012](http://doi.org/10.1016/j.jclinepi.2004.03.012). PMID: 15617955.
  - The categories are renamed the following way
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
- **Sweden** (CAVE: currently only the ICD-10 version is implemented):<br>Ludvigsson JF, Appelros P, Askling J, Byberg L, Carrero JJ, Ekström AM, Ekström M, Smedby KE, Hagström H, James S, Järvholm B, Michaelsson K, Pedersen NL, Sundelin H, Sundquist K, Sundström J. Adaptation of the Charlson Comorbidity Index for Register-Based Research in Sweden. Clin Epidemiol. 2021 Jan 12;13:21-41. doi: [10.2147/CLEP.S282475](http://doi.org/10.2147/CLEP.S282475). Erratum in: Clin Epidemiol. 2023 Jun 19;15:753-754. doi: [http://doi.org/10.2147/CLEP.S425901](http://doi.org/10.2147/CLEP.S425901). PMID: 33469380; PMCID: PMC7812935.
  - The categories are renamed / split the following way:
    - Chronic pulmonary disease -> Chronic obstructive pulmonary disease (COPD) _and_ Other chronic pulmonary disease
    - Hemiplegia or paraplegia -> Hemiplegia, tetraplegia
    - Diabetes without chronic complication -> Diabetes
    - Diabetes with chronic complication -> Diabetes with end organ damage
    - Renal disease -> Moderate or severe kidney disease
    - Peptic ulcer disease -> (Peptic) Ulcer disease
    - Any malignancy, including lymphoma and leukemia, except malignant neoplasm of skin -> Any malignancy, including lymphoma and leukemia
    - Metastatic solid tumor -> Metastatic cancer
- **UK**  (ICD-10 only):<br>[Summary Hospital-level Mortality Indicator (SHMI)](https://digital.nhs.uk/data-and-information/publications/statistical/shmi)
  - The SHMI ICD code mappings may be downloaded under the heading `Resources` -> `Methodology specifications`. The implementation is currently on Version 1.55 (March 2025 — "Deaths associated with hospitalisation, England, December 2023 - November 2024")
  - The categories are renamed within the SHMI the following way:
      1. Myocardial infarction -> Acute myocardial infarction
      4. Cerebrovascular disease -> Cerebral vascular accident
      6. Chronic pulmonary disease -> Pulmonary disease
      7. Rheumatic disease -> Connective tissue disorder
      8. Peptic ulcer disease -> Peptic ulcer
      9. Mild liver disease -> Liver disease
      10. Diabetes without chronic complication -> Diabetes
      11. Diabetes with chronic complication -> Diabetes complications
      12. Hemiplegia or paraplegia -> Paraplegia
      14. Any malignancy, including lymphoma and leukemia, except malignant neoplasm of skin -> Cancer
      15. Moderate or severe liver disease -> Severe liver disease
      16. Metastatic solid tumor -> Metastatic cancer
      17. AIDS/HIV -> HIV

# Codes for the `Elixhauser Comorbidity Index` (ECI)

Reference for ECI:

1. Elixhauser A, Steiner C, Harris DR, Coffey RM. Comorbidity measures for use with administrative data. Med Care. 1998 Jan;36(1):8-27. doi: [10.1097/00005650-199801000-00004](http://doi.org/10.1097/00005650-199801000-00004). PMID: 9431328.

Reference for ECI weights:

2. van Walraven C, Austin PC, Jennings A, Quan H, Forster AJ. A modification of the Elixhauser comorbidity measures into a point system for hospital death using administrative data. Med Care. 2009 Jun;47(6):626-33. doi: [10.1097/MLR.0b013e31819432e5](http://doi.org/10.1097/MLR.0b013e31819432e5). PMID: 19433995.
3. Thompson NR, Fan Y, Dalton JE, Jehi L, Rosenbaum BP, Vadera S, Griffith SD. A new Elixhauser-based comorbidity summary measure to predict in-hospital mortality. Med Care. 2015 Apr;53(4):374-9. doi: [10.1097/MLR.0000000000000326](http://doi.org/10.1097/MLR.0000000000000326). PMID: 25769057; PMCID: PMC4812819.
4. Moore BJ, White S, Washington R, Coenen N, Elixhauser A. Identifying Increased Risk of Readmission and In-hospital Mortality Using Hospital Administrative Data: The AHRQ Elixhauser Comorbidity Index. Med Care. 2017 Jul;55(7):698-705. doi: [10.1097/MLR.0000000000000735](http://doi.org/10.1097/MLR.0000000000000735). PMID: 28498196.

Reference for ICD-9-CM and ICD-10 Coding Algorithms for Elixhauser Comorbidities:

5. Quan H, Sundararajan V, Halfon P, Fong A, Burnand B, Luthi JC, Saunders LD, Beck CA, Feasby TE, Ghali WA. Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10 administrative data. Med Care. 2005 Nov;43(11):1130-9. doi: [10.1097/01.mlr.0000182534.19832.83](http://doi.org/10.1097/01.mlr.0000182534.19832.83). PMID: 16224307.
6. Agency for Healthcare Research and Quality. [ELIXHAUSER COMORBIDITY SOFTWARE REFINED FOR ICD-10-CM v2025.1](https://hcup-us.ahrq.gov/toolssoftware/comorbidityicd10/comorbidity_icd10.jsp)

# Codes for the `Combined Comorbidity Index` (GCI)

Reference for GCI:

1. Gagne JJ, Glynn RJ, Avorn J, Levin R, Schneeweiss S. A combined comorbidity score predicted mortality in elderly patients better than existing scores. J Clin Epidemiol. 2011 Jul;64(7):749-59. doi: [10.1016/j.jclinepi.2010.10.004](http://doi.org/10.1016/j.jclinepi.2010.10.004). Epub 2011 Jan 5. PMID: 21208778; PMCID: PMC3100405.

Reference for ICD-9-CM and ICD-10 Coding Algorithms for Combined Comorbidities:

2. Sun JW, Rogers JR, Her Q, Welch EC, Panozzo CA, Toh S, Gagne JJ. Adaptation and Validation of the Combined Comorbidity Score for ICD-10-CM. Med Care. 2017 Dec;55(12):1046-1051. doi: [10.1097/MLR.0000000000000824](http://doi.org/10.1097/MLR.0000000000000824). PMID: 29087983.

# Codes for the `Hospital Frailty Risk Score` (HRFS)

Referecnce for HRFS:

1. Gilbert T, Neuburger J, Kraindler J, Keeble E, Smith P, Ariti C, Arora S, Street A, Parker S, Roberts HC, Bardsley M, Conroy S. Development and validation of a Hospital Frailty Risk Score focusing on older people in acute care settings using electronic hospital records: an observational study. Lancet. 2018 May 5;391(10132):1775-1782. doi: [10.1016/S0140-6736(18)30668-8](http://doi.org/10.1016/S0140-6736(18)30668-8). Epub 2018 Apr 26. PMID: 29706364; PMCID: PMC5946808.
    - The ICD-10 codes and associated weights/categories can be found in the supplementary appendix of the paper.
