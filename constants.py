saps_ages = {1: "T1_1AGE0_4",
             2: "T1_1AGE5_9",
             3: "T1_1AGE10_14",
             4: "T1_1AGE15_19",
             5: "T1_1AGE20_24",
             6: "T1_1AGE25_29",
             7: "T1_1AGE30_34",
             8: "T1_1AGE35_39",
             9: "T1_1AGE40_44",
             10: "T1_1AGE45_49",
             11: "T1_1AGE50_54",
             12: "T1_1AGE55_59",
             13: "T1_1AGE60_64",
             14: "T1_1AGE65_69",
             15: "T1_1AGE70_74",
             16: "T1_1AGE75_79",
             17: "T1_1AGE80_84",
             18: "T1_1AGEGE_85"}

sexes = {1: "M", 2: "F"}

saps_marital_statuses = {1: "T1_2SGL",
                         2: "T1_2MAR",
                         3: "T1_2WID",
                         4: "T1_2SEP"}

saps_levels_of_education = {# No Formal Education
                            0: "T10_4_NF",

                            # Primary Education
                            11: "T10_4_P",
                            100: "T10_4_P",

                            # Lower Secondary
                            21: "T10_4_LS",
                            200: "T10_4_LS",

                            # Upper Secondary
                            22: "T10_4_US",
                            30: "T10_4_US",
                            32: "T10_4_US",
                            300: "T10_4_US",
                            303: "T10_4_US",
                            304: "T10_4_US",
                            343: "T10_4_US",
                            344: "T10_4_US",
                            399: "T10_4_US",

                            # Need to combine T10_4_TV and T10_4_ACCA into T10_4_PLC
                            # (Post Leaving Cert)
                            42: "T10_4_PLC",
                            400: "T10_4_PLC",
                            450: "T10_4_PLC",

                            # Higher Certificate
                            51: "T10_4_HC",
                            500: "T10_4_HC",
                            540: "T10_4_HC",
                            550: "T10_4_HC",
                            590: "T10_4_HC",
                            52: "T10_4_HC",

                            # Need to combine T10_4_ODND and T10_4_HDPQ into T10_4_DGR
                            # (degree)
                            60: "T10_4_DGR",
                            600: "T10_4_DGR",

                            # Postgraduate Degree
                            700: "T10_4_PD",

                            # Doctorate
                            800: "T10_4_D",

                            # Child
                            999: ""
                            }

saps_employment_statuses = {
                            # At Work
                            1: "T8_1_W",

                            # Need to combine T8_1_LFFJ, T8_1_STU and T8_1_LTU into T8_1_UNE
                            2: "T8_1_UNE",

                            # Retired
                            3: "T8_1_R",

                            # Unable to work
                            4: "T8_1_UTWSD",

                            # Student
                            5: "T8_1_S",

                            # Home duties
                            6: "T8_1_LAHF",

                            # Other (7 is compulsory military service which doesn't exist in Ireland)
                            8: "T8_1_OTH",

                            # Child (left out of SAPs tables)
                            9: ""
                            }

tables_and_characteristics_with_blanks = {
    'T1_1': ['T1_1AGE20_24M', 'T1_1AGE25_29M', 'T1_1AGE30_34M', 'T1_1AGE35_39M', 'T1_1AGE40_44M', 'T1_1AGE45_49M',
             'T1_1AGE50_54M', 'T1_1AGE55_59M', 'T1_1AGE60_64M', 'T1_1AGE65_69M', 'T1_1AGE70_74M', 'T1_1AGE75_79M',
             'T1_1AGE80_84M', 'T1_1AGEGE_85M', 'T1_1AGE20_24F', 'T1_1AGE25_29F', 'T1_1AGE30_34F', 'T1_1AGE35_39F',
             'T1_1AGE40_44F', 'T1_1AGE45_49F', 'T1_1AGE50_54F', 'T1_1AGE55_59F', 'T1_1AGE60_64F', 'T1_1AGE65_69F',
             'T1_1AGE70_74F', 'T1_1AGE75_79F', 'T1_1AGE80_84F', 'T1_1AGEGE_85F', 'T1_1AGE0_4M', 'T1_1AGE5_9M',
             'T1_1AGE10_14M', 'T1_1AGE15_19M', 'T1_1AGE0_4F', 'T1_1AGE5_9F', 'T1_1AGE10_14F', 'T1_1AGE15_19F'],
    'T1_2': ['T1_2SGLM', 'T1_2MARM', 'T1_2WIDM', 'T1_2SGLF', 'T1_2MARF', 'T1_2WIDF', 'T1_2SEPM', 'T1_2SEPF'],
    'T5_2': ['T5_2_1PP', 'T5_2_2PP', 'T5_2_3PP', 'T5_2_4PP', 'T5_2_5PP', 'T5_2_6PP', 'T5_2_7PP', 'T5_2_GE8PP'],
    'T8_1': ['T8_1_WM', 'T8_1_SM', 'T8_1_LAHFM', 'T8_1_RM', 'T8_1_UTWSDM', 'T8_1_OTHM', 'T8_1_WF', 'T8_1_SF',
             'T8_1_LAHFF', 'T8_1_RF', 'T8_1_UTWSDF', 'T8_1_OTHF', 'T8_1_UNEM', 'T8_1_UNEF', ""],
    'T10_': ['T10_4_NFM', 'T10_4_PM', 'T10_4_LSM', 'T10_4_USM', 'T10_4_HCM', 'T10_4_PDM', 'T10_4_DM', 'T10_4_NSM',
             'T10_4_NFF', 'T10_4_PF', 'T10_4_LSF', 'T10_4_USF', 'T10_4_HCF', 'T10_4_PDF', 'T10_4_DF', 'T10_4_NSF',
             'T10_4_PLCM', 'T10_4_DGRM', 'T10_4_PLCF', 'T10_4_DGRF', ""]}

tables_and_characteristics_with_nas = {
    'T1_1': ['T1_1AGE20_24M', 'T1_1AGE25_29M', 'T1_1AGE30_34M', 'T1_1AGE35_39M', 'T1_1AGE40_44M', 'T1_1AGE45_49M',
             'T1_1AGE50_54M', 'T1_1AGE55_59M', 'T1_1AGE60_64M', 'T1_1AGE65_69M', 'T1_1AGE70_74M', 'T1_1AGE75_79M',
             'T1_1AGE80_84M', 'T1_1AGEGE_85M', 'T1_1AGE20_24F', 'T1_1AGE25_29F', 'T1_1AGE30_34F', 'T1_1AGE35_39F',
             'T1_1AGE40_44F', 'T1_1AGE45_49F', 'T1_1AGE50_54F', 'T1_1AGE55_59F', 'T1_1AGE60_64F', 'T1_1AGE65_69F',
             'T1_1AGE70_74F', 'T1_1AGE75_79F', 'T1_1AGE80_84F', 'T1_1AGEGE_85F', 'T1_1AGE0_4M', 'T1_1AGE5_9M',
             'T1_1AGE10_14M', 'T1_1AGE15_19M', 'T1_1AGE0_4F', 'T1_1AGE5_9F', 'T1_1AGE10_14F', 'T1_1AGE15_19F'],
    'T1_2': ['T1_2SGLM', 'T1_2MARM', 'T1_2WIDM', 'T1_2SGLF', 'T1_2MARF', 'T1_2WIDF', 'T1_2SEPM', 'T1_2SEPF'],
    'T5_2': ['T5_2_1PP', 'T5_2_2PP', 'T5_2_3PP', 'T5_2_4PP', 'T5_2_5PP', 'T5_2_6PP', 'T5_2_7PP', 'T5_2_GE8PP'],
    'T8_1': ['T8_1_WM', 'T8_1_SM', 'T8_1_LAHFM', 'T8_1_RM', 'T8_1_UTWSDM', 'T8_1_OTHM', 'T8_1_WF', 'T8_1_SF',
             'T8_1_LAHFF', 'T8_1_RF', 'T8_1_UTWSDF', 'T8_1_OTHF', 'T8_1_UNEM', 'T8_1_UNEF', "T8_1_NA"],
    'T10_': ['T10_4_NFM', 'T10_4_PM', 'T10_4_LSM', 'T10_4_USM', 'T10_4_HCM', 'T10_4_PDM', 'T10_4_DM', 'T10_4_NSM',
             'T10_4_NFF', 'T10_4_PF', 'T10_4_LSF', 'T10_4_USF', 'T10_4_HCF', 'T10_4_PDF', 'T10_4_DF', 'T10_4_NSF',
             'T10_4_PLCM', 'T10_4_DGRM', 'T10_4_PLCF', 'T10_4_DGRF', "T10_4_NA"]}
