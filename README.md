# Libcal booker RUG
> Python program that automatically reserves a booking for the university library of the RuG. Multiple individuals can be booked by the use of a single CSV file that contains the individuals and their desired reservations.

## Table of Contents
* [General Info](#general-information)
* [Setup](#setup)
* [Usage](#usage)
* [Project Status](#project-status)


## General Information
- Reservations for the university library are complex during busy periods, due to the fact that a lot of people want a reservation.
- This program allows a python script to book reservations from the command line.
- By setting up the script as for example, a crontab task, it can be executed at the same time as the reservations for a specific day become available.


## Setup
All of the used libraries from Python are built-in. 
The file `booker.csv` should be filled in as desired.
File `idFile.csv` gets created by `runCSV.py`.


## Usage
The project is executed by running `runCSV.py`. 
`runCSV.py` calls the file `UB_Booker_v2.py` for every individual row from `booker.csv`.

For debugging, the file `UB_Booker_v2.py` can be executed from the command line as well. If no CLI arguments are given, it falls back to hardcoded individual variables in `UB_Booker_v2.py`.

## Project Status
Project is: _no longer being worked on_. The project is broken. The personal need for this project disappeared.