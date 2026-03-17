from datetime import datetime
import os
import glob
import pandas
from tqdm import tqdm


def applyDateSplits(row, columns):
    if pandas.notna(row.CustomCoverageBegin) and pandas.notna(row.CustomCoverageEnd):
        row.CoverageBegin = row.CustomCoverageBegin
        row.CoverageEnd = row.CustomCoverageEnd
    elif pandas.notna(row.ManagedCoverageBegin) and pandas.notna(row.ManagedCoverageEnd):
        row.CoverageBegin = row.ManagedCoverageBegin
        row.CoverageEnd = row.ManagedCoverageEnd
    row.CoverageBegin = row.CoverageBegin.split("|")
    row.CoverageEnd = row.CoverageEnd.split("|")
    returned_rows = []
    if len(row.CoverageEnd) > 1:
        for i, coverage_end in enumerate(row.CoverageEnd):
            row_copy = row.copy()
            row_copy.CoverageBegin = row.CoverageBegin[i]
            row_copy.CoverageEnd = coverage_end
            if i != len(row.CoverageEnd)-1:
                row_copy.Embargo = pandas.NA
                row_copy.CustomEmbargo = pandas.NA
            returned_rows.append(dict(zip(columns, row_copy)))
    else:
        row.CoverageEnd = row.CoverageEnd[0]
        row.CoverageBegin = row.CoverageBegin[0]
        returned_rows = [row.to_dict()]
    return returned_rows


def reformatDate(date):
    hyphen_index = date.find("-")
    if hyphen_index == -1 and len(date) == 5:
        converted_date = pandas.to_datetime(
            int(date), unit='D', origin='1899-12-30')
    elif hyphen_index == 4:
        if int(date[:4]) <= 1678:
            converted_date = date[:4]
        elif int(date[:4]) >= 2038:
            converted_date = date[:4]
        else:
            converted_date = pandas.to_datetime(date, yearfirst=True)
    elif date == "Present":
        converted_date = pandas.to_datetime(datetime.today())
    elif date == "No Access" or date == "":
        converted_date = "No Access"
    else:
        converted_date = pandas.to_datetime(date)
    return converted_date


def roundStartDate(date):
    if pandas.isna(date) or isinstance(date, str):
        return date
    elif int(date.month) < 7:
        return date.year
    else:
        return date.year+1
    # If the date is before July 1, round to current. If after, round to next.


def roundEndDate(date):
    if pandas.isna(date) or isinstance(date, str):
        return date
    elif int(date.year) == int(datetime.today().year):
        return date.year
    elif int(date.month) >= 6:
        return date.year
    else:
        return (date.year-1)
    # If the date is before July 1, round to previous year. If after, round to current.
    # End dates in the current year are always rounded to current.


def applyRounding(row):
    if pandas.isna(row.CoverageBegin) or isinstance(row.CoverageBegin, str) or pandas.isna(row.CoverageEnd) or isinstance(row.CoverageEnd, str):
        row.CoverageBegin = roundStartDate(row.CoverageBegin)
        row.CoverageEnd = roundEndDate(row.CoverageEnd)
    else:
        if row.CoverageBegin.year == row.CoverageEnd.year:
            row.CoverageBegin = row.CoverageBegin.year
            row.CoverageEnd = row.CoverageEnd.year
        else:
            row.CoverageBegin = roundStartDate(row.CoverageBegin)
            row.CoverageEnd = roundEndDate(row.CoverageEnd)
    return row


def applyEmbargo(row):
    if pandas.notna(row.CustomEmbargo):
        number_index = row.CustomEmbargo.find(" ")
        embargo_duration = int(row.CustomEmbargo[:number_index])
        if row["CustomEmbargo"][-6:] == "months":  # Custom Embargos in Months
            if embargo_duration >= 6:
                embargo_duration = round(embargo_duration/11.999)
            else:
                return row
        elif row["CustomEmbargo"][-4:] == "days":  # Custom Embargos in Days
            if embargo_duration >= 365:
                embargo_duration = round(embargo_duration/365.25)
            elif embargo_duration >= 182.625:
                embargo_duration = 1
            else:
                return row
    elif pandas.notna(row.Embargo):
        number_index = row.Embargo.find(" ")
        embargo_duration = int(row.Embargo[:number_index])
        if row.Embargo[-6:] == "months":  # Embargos in Months
            if embargo_duration >= 6:
                embargo_duration = round(embargo_duration/11.999)
            else:
                return row
        elif row.Embargo[-4:] == "days":  # Embargos in Days
            if embargo_duration >= 365:
                embargo_duration = round(embargo_duration/365.25)
            elif embargo_duration >= 182.625:
                embargo_duration = 1
            else:
                return row
    else:
        return row
    row.Embargo = ""
    if (int(row.CoverageEnd) - int(row.CoverageBegin)) <= embargo_duration:
        row.CoverageEnd = "No Access"
        row.CoverageBegin = "No Access"
    else:
        row.CoverageEnd = int(row.CoverageEnd)-embargo_duration
    return row


if __name__ == "__main__":
    startTime = datetime.now()
    tqdm.pandas()

    folder_path = os.getcwd() + "/Input/*csv"
    files = glob.glob(folder_path)
    try:
        fileName = max(files, key=os.path.getmtime)
    except Exception as exc:
        raise FileNotFoundError("No input file found") from exc

    if fileName[-3:] == 'csv':
        df = pandas.read_csv(fileName, header=0, dtype="string", na_values='')
    elif fileName[-4:] == 'xlsx':
        df = pandas.read_excel(fileName, dtype='string', na_values='')
    else:
        print("Input file is not in .csv or .xlsx format, date conversion cannot be completed.")
        exit()
    localOnlyPackages = pandas.read_excel("LocalOnlyPackages.xlsx", usecols=[0])["PackageName"].to_list()

    # Sets names for all output files 
    LendableOutputFileName = "Output\\Dates_Reformatted - Lendable - " + \
        fileName[fileName.rfind("\\")+1:]
    LocalOutputFileName = "Output\\Dates_Reformatted - Local Only - " + \
        fileName[fileName.rfind("\\")+1:]
    NINE_NINE_NINE_LOG = "Output\\9999 dates.csv"
    NO_ACCESS_LOG = "Output\\No Access.csv"
    
    print("Output will be saved to:")
    print(LendableOutputFileName)
    print(LocalOutputFileName)
    print(NINE_NINE_NINE_LOG)
    print(NO_ACCESS_LOG)

    # Drops Unnecessary Columns
    df = df.loc[:, :'CustomEmbargo']

    # Creates the CoverageBegin and CoverageEnd columns
    newColumns = {"CoverageBegin": [
        ''] * len(df.index), "CoverageEnd": [''] * len(df.index)}
    df = df.assign(**newColumns)

    # Clears out any existing rows in the 9999 and No Access files
    with open(NINE_NINE_NINE_LOG, "w", encoding="UTF-8") as exceptionsFile:
        exceptionsFile.write(', '.join(df.columns))
    with open(NO_ACCESS_LOG, "w", encoding="UTF-8") as exceptionsFile:
        exceptionsFile.write(', '.join(df.columns))

    # Using new Apply Date Split function
    print("Splitting rows with multiple date ranges")
    splitRows = []
    for row in tqdm(df.iterrows()):
        splitDates = applyDateSplits(row[1], df.columns)
        splitRows += splitDates
    df = pandas.json_normalize(data=splitRows)
    print("Reformatting Coverage Start Dates")
    df["CoverageBegin"] = df["CoverageBegin"].progress_map(reformatDate)
    print("Reformatting Coverage End Dates")
    df["CoverageEnd"] = df["CoverageEnd"].progress_map(reformatDate)

    # Rounds start and end dates 
    print("Rounding dates")
    df = df.progress_apply(applyRounding, axis=1)
    
    # Applies Embargo periods
    print("Applying Embargo Period Adjustments")
    df = df.progress_apply(applyEmbargo, axis=1)

    # Drops original coverage date and embargo fields
    print("Dropping Unneeded Columns")
    df = df.drop(columns=['ManagedCoverageBegin', 'ManagedCoverageEnd', 'CustomCoverageBegin',
                        'CustomCoverageEnd', 'CoverageStatement', 'Embargo', 'CustomEmbargo'])

    # Logs records with No Access or 9999 Begin/End years
    rowsToDrop = []
    print(f"Logging No Access to {NO_ACCESS_LOG} and "
          f"9999 CoverageBegin or CoverageEnd years to {NINE_NINE_NINE_LOG}")
    nine_nine_nine_file = open(NINE_NINE_NINE_LOG, "a", encoding="UTF-8")
    no_access_file = open(NO_ACCESS_LOG, "a", encoding="UTF-8")
    for row in tqdm(df.iterrows()):
        rowIndex = row[0]
        row = row[1]
        if not pandas.isna(row.CoverageEnd):
            if row.CoverageEnd != 'No Access':
                if int(row.CoverageEnd) == 9999:
                    nine_nine_nine_file.write(
                        '\n'+', '.join(['' if v is None else str(v) for v in row.values]))
                    rowsToDrop.append(rowIndex)
            else:
                no_access_file.write(
                    '\n'+', '.join(['' if v is None else str(v) for v in row.values]))
                rowsToDrop.append(rowIndex)
        if not pandas.isna(row.CoverageBegin):
            if row.CoverageBegin != 'No Access':
                if int(row.CoverageBegin) == 9999 and rowIndex not in rowsToDrop:
                    nine_nine_nine_file.write(
                        '\n'+', '.join(['' if v is None else str(v) for v in row.values]))
                    rowsToDrop.append(rowIndex)
            elif rowIndex not in rowsToDrop:
                no_access_file.write(
                    '\n'+', '.join(['' if v is None else str(v) for v in row.values]))
                rowsToDrop.append(rowIndex)
    nine_nine_nine_file.close()
    no_access_file.close()

    # Drops any rows added to the 9999 or No Access exception files
    print("Dropping No Access and 9999 date rows")
    df.drop(index=rowsToDrop, axis=0, inplace=True)

    # Saves results
    print(f"Saving results to:\n\t{LocalOutputFileName}\n\t{LendableOutputFileName}")
    df.loc[df['PackageName'].isin(localOnlyPackages)].to_csv(LocalOutputFileName, index=False, encoding = 'UTF-8')
    df.loc[~df['PackageName'].isin(localOnlyPackages)].to_csv(LendableOutputFileName, index=False, encoding = 'UTF-8')
    endTime = datetime.now()
    print(f"Reformatting complete\nTotal Elapsed time: {endTime-startTime}")