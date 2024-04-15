import pandas as pd
import statistics
import math
import matplotlib.pyplot as plt

# read the entire data feed csv file of Thingspeak into data frame
data = pd.read_csv("FinalDataSet.csv")

# list the column names of imported data set
column_names = list(data.columns.values)
print("Column Name: ", column_names)

# check number of rows and columns of original imported data set
print(data.shape)
print("\nThe Analysis of Loaded Dataset is shown below: \n")

# create empty dataframe to save the processed data
df = pd.DataFrame(columns=['Sample', 'Conc', 'Conductivity', 'ConRoot', 'Molar'])

# finding unique values of sample IDs in the data set
SampleList = data.Sample.unique().tolist()  # finds the unique values of Sample IDs in Sample column and prepare list

for item in SampleList:
    FilteredDataSample = data[(data.Sample == item)]  # this will create filtered data based on sample ID
    ConcList = FilteredDataSample.Concentration.unique().tolist() # finds the unique values of concentrations for given sample and prepare list
    for concentration in ConcList:
        FilteredConcentration = FilteredDataSample[(FilteredDataSample.Concentration == concentration)] # this will create filtered data based on concentration of given sample
        mean_conductivity = round(statistics.mean(FilteredConcentration['Conductivity']), 2)
        conroot = round(math.sqrt(concentration), 2)  # calculates square root of concentration

        if concentration == 0:
            molar_conductance = float('inf')
        else:
            molar_conductance = round(((1000*mean_conductivity)/concentration), 2)

        addlist = [item, concentration, mean_conductivity, conroot, molar_conductance] # create list of all parameters
        df.loc[len(df)] = addlist

df = df.reset_index(drop=True)
print(df.to_string())

# filtering out specific sample related dataframe

print("\nFiltering Process for Specific Sample -----> \n")

sample1 = float(input("Enter plain water sample ID or else Enter 0: "))   # provide here the required sample for analysis (this sample is for plain water)
sample2 = float(input("Enter Specific Surfactant Sample ID: "))  # provide here the required specific sample with surfactant

filtered_df = df[(df.Sample == sample1) | (df.Sample == sample2)]
filtered_df = filtered_df.reset_index(drop=True)
print("\n\nFiltered DataFrame for Specific Sample: -----> ", sample1, " & ", sample2)
print("\n", filtered_df)


# calculation of slope

DataLength = len(filtered_df['Conc'])
print("\nList Length: ", DataLength)
SlopeList = []  # initialize empty list
i = 0  # initialize index for first row

while i < (DataLength-1):
    ydiff = filtered_df.iloc[i+1, 2] - filtered_df.iloc[i, 2]  # take difference in conductivity
    xdiff = filtered_df.iloc[i+1, 1] - filtered_df.iloc[i, 1]  # take difference in concentration
    i = i + 1
    slope = abs(round(ydiff/xdiff, 2))
    SlopeList.append(slope)

slope = float('nan')
SlopeList.append(slope)
print("\nLength of slope list: ", len(SlopeList))
print("\nSlope List: \n", SlopeList)

print("\n\nComplete dataframe with added Slope column: ----->\n")
filtered_df['Slope'] = SlopeList
print(filtered_df)

# Detecting minimum slope point and estimating CMC concentration and CMC mole value

row_num = filtered_df[filtered_df['Slope'] == min(SlopeList)].index  # locate specific row with minimum slope

target_conc = filtered_df.iloc[row_num-1, 1]  # locate CMC concentration
target_cond = filtered_df.iloc[row_num-1, 2]  # locate the specific conductivity of CMC for given sample
mole = filtered_df.iloc[row_num-1, 3]  # locate the CMC molar value
target_molar = filtered_df.iloc[row_num-1, 4]  # locate the molar conductance value

print("\n----- | ----- | ----- | ------| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- \n")
print("\nEstimated Parameter Values for provided Surfactant Sample: -----> ", sample1, " & ", sample2)
print("\nCritical Micelle Concentration (mg) for Surfactant: ")
print(target_conc)
print("\nSpecific Conductivity (microS/cm) of Surfactant Solution: ")
print(target_cond)
print("\nCMC Moles for Surfactant: ")
print(mole)
print("\nMolar Conductance (microS) of Surfactant: ")
print(target_molar)
print("\n\n Estimation is completed analysis is over...")

# Plotting graph of filtered dataframe

filtered_df.plot(kind='scatter', x='Conc', y='Conductivity')  # plots conductivity verses concentration
plt.title("Concentration Verses Conductivity Graph")
#filtered_df.plot(kind='scatter', x='ConRoot', y='Molar')  # plots Molar conductance verses root of concentration
#plt.title("Root of Concentration Verses Molar Conductance Graph")
plt.show()
