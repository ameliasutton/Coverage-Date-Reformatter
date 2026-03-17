# Coverage Date Reformatter 
Copyright (C) 2025-2026  Amelia Sutton

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  

See the file "[COPYING](COPYING)" for more details.

## Introduction
A simple script to reformat resource coverage start and end dates.

## Requirements
* pandas
* tqdm
## Optional Requirements
* pyinstaller
  

## Basic Setup:
- In the folder containing the script create two sub-folders "Input" and "Output"
- Create an Excel file named "LocalOnlyPackages.xlsx", in the first column, list the names of the packages that are local only.
- Place your input file in the Input folder. 
  - Input must be formatted as an Excel spreadsheet or CSV file
  - Package names should be in a column labeled PackageName
  - Coverage date fields should be labeled as 
    - ManagedCoverageBegin	
    - ManagedCoverageEnd	
    - CustomCoverageBegin	
    - CustomCoverageEnd	
    - Embargo
    - CustomEmbargo
  - Any columns that you want to remain in the output file should be placed before the Coverage date fields
- Run the script via the console using ` python dateReformatting.py`
- Alternatively, run the buildExecutable.bat to generate an .exe file to run. (This requires pyinstaller, but the resulting .exe can be run on a computer without python installed)