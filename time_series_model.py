# Loading libs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#import seaborn as sns
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
#from sklearn.model_selection import train_test_split
from sklearn import preprocessing
from sklearn.linear_model import LassoLarsCV

# Reading data in
target = pd.read_excel('/Users/aurenferguson/Documents/timeseries_challenge/data/time_series_challenge.xlsx')

data = pd.read_excel('/Users/aurenferguson/Documents/timeseries_challenge/data/time_series_challenge.xlsx',
                     sheetname = 1)

#########################################
# Preparing data

# Renaming date column
target.rename(columns = {'Economic Variable X Seasonally Adjusted Month on Month Change' : 'economic_variable'}, inplace = True)

# converting date to date object
# There are mixed date formats so will split data, change to dates and combine
target_contain_dash = target[target.Date.str.contains('/', na = False)]
target_no_dash = target[~target.Date.str.contains('/', na = False)]

# Checks no rows left behind
assert len(target) == len(target_contain_dash) + len(target_no_dash)

# The 31/6 doesnt exist, changing it to the 30th
target_contain_dash.Date = target_contain_dash.Date.str.replace('31', '30')

# converting to dates
target_contain_dash.Date = pd.to_datetime(target_contain_dash.Date, format = '%d/%m/%Y')
target_no_dash.Date = pd.to_datetime(target_no_dash.Date, format = '%Y-%m-%d')

# combining df's
new_target = pd.concat([target_no_dash, target_contain_dash], ignore_index = True)

assert len(new_target) == len(target_contain_dash) + len(target_no_dash)

target = new_target

del(new_target, target_contain_dash, target_no_dash)

# setting Date as index
target.index = target.Date

# Dropping Date
target.drop('Date', axis = 1, inplace = True)

## Plotting variable
#target.economic_variable.plot()
#
## plotting Survey
#target.Survey.plot()

# plotting variable and Survey together
plt.plot(target.index, target.economic_variable)
plt.plot(target.index, target.Survey)
plt.title("Economic variable and Survey")
plt.legend()
plt.show()

# Seperating The week start date and end date into different column
def split_dates(df, old_col, take_position, sep):
    
    return df[old_col].str.split(' ').str.get(take_position)
    
data['end_date'] = split_dates(data, 'Week', 2, ' ')


# converting end date to date object
data['end_date'] = pd.to_datetime(data.end_date, format = "%Y-%m-%d")

# setting end date as index
data.index = data.end_date

# dropping unneeded cols
data.drop(['Week', 'end_date'], axis = 1,inplace = True)

# Aggregating data to be on same level as target, i.e. monthly
data = data.resample('M').sum()

# Joining the dataframe
combined_data = pd.merge(target, data,
                         left_index = True,
                         right_index = True,
                         how = 'left')

# calculating month on month difference for each input variable
month_change = combined_data.copy()

# getting columns to adjust
adjust_cols = month_change.columns.tolist()
adjust_cols = adjust_cols[1:]

for col in adjust_cols:
    month_change[col] = month_change[col].pct_change()
    
# Replace inf's with nan
month_change = month_change.replace([np.inf, -np.inf], np.nan)

# filling nans with zero
month_change = month_change.fillna(0)

####################################################################
# Adjusting variables for seasonality
season_adjust_df = month_change.copy()

season_cols = season_adjust_df.columns.tolist()[2:]

for col in season_cols:
    decomposition = seasonal_decompose(season_adjust_df[col])
    residual = decomposition.resid
    season_adjust_df[col] = residual
    
# Testing if residuals are stationary  
stationarity_cols = season_adjust_df.columns.tolist()[2:]
stationary_dict = {}
for col in  stationarity_cols:
    
    dftest = adfuller(season_adjust_df[col].dropna(), autolag='AIC')
    dfoutput = pd.Series(dftest[0:4], index=['Test Statistic','p-value','#Lags Used','Number of Observations Used'])
    for key,value in dftest[4].items():
        dfoutput['Critical Value (%s)'%key] = value
        
    dfoutput=dfoutput.to_frame().transpose()
    
    if (dfoutput['Test Statistic'] <= dfoutput['Critical Value (5%)'])[0]:
        stationary_dict[col] = True
        
    else:
        stationary_dict[col] = False

test_stationary = all(value == True for value in stationary_dict.values())

if test_stationary == True:
    print("All variables are stationary")
else:
    print("All variables aren't stationary")
    
#####################################################################
# Creating train and test data
    
# dropping Term nans
model_data = season_adjust_df.dropna(subset = stationarity_cols, how = 'all')

model_data_scale = model_data.copy()

# Scaling columns
model_scale_cols = model_data.columns.tolist()[1:]

for col in model_scale_cols:
    model_data_scale[col] = preprocessing.scale(model_data_scale[col].astype('float64'))


# getting data into x and y 
x = model_data_scale.iloc[:,1:]
y = model_data_scale.iloc[:,0]

# Fitting cross validated lars model
model = LassoLarsCV(cv = 10, precompute = False, normalize=False).fit(x, y)

# Printing coefs showing which terms were put in model
print(dict(zip(x.columns,model.coef_)))

# Scoring model
score = model.score(x,y)

# predicting 
x['prediction'] = model.predict(x)


# Plotting results
plt.plot(x.index, x.prediction)
plt.plot(y.index, y, c = 'r')
#plt.plot(x.index, x.Survey)
plt.title("Economic Variable and Prediction")
plt.legend()
plt.show()
###################

# creating output
output = x.prediction
output = output.to_frame()
output.to_csv("/Users/aurenferguson/Documents/timeseries_challenge/data/output.csv",
              date_format = "%Y%m%d")

