import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from sklearn.svm import SVR
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error


@st.cache(allow_output_mutation=True)  # add caching so we load the data only once
def load_data():
    return pd.read_csv("data/fifa19.csv", encoding="UTF-8", index_col=0)


def write():
    df = load_data()
    #st.write(df.head())

    st.header("Feature Correlation Analysis")
    st.write("""Let's explore the relationships between some of the quantitative
        variables in the dataset. Select an independent (x-axis) and a dependent
        (y-axis) variable below and see a scatter plot of these two variables with
        a fitted 5th degree polynomial line, and see their correlation coefficient
        as well. You may also select the "use color" checkbox and select a third
        variable to be represented by the color of the points on the plot. Hover
        your mouse over the points on the plot to see which player that point
        represents. Note that noise has been added to the variables in the plot due to
        the high number of overlapping points in the dataset, but the correlation
        coefficient is calculated using the original data.""")

    # Here, we remove the extra text around the wage to get it as an integer
    wage_array = df["Value"].to_numpy()
    fixed_wages = []
    for wage in wage_array:
        if wage[-1]=="M":
            wage = float(wage[1:-1])*1000000
        elif wage[-1]=="K":
            wage = float(wage[1:-1])*1000
        else:
            wage=0
        fixed_wages.append(wage)
    df["Player_Wage"] = fixed_wages
    df = df[df.Player_Wage!='']
    df["Player_Wage"] = df["Player_Wage"].astype(np.int64)*1000

    correlation_options = ['Age', 'Overall', 'Potential', 'Player_Wage', 'International Reputation',
                           'Skill Moves', 'Crossing','Finishing', 'HeadingAccuracy', 'ShortPassing',
                           'Volleys', 'Dribbling', 'Curve', 'FKAccuracy', 'LongPassing',
                           'BallControl', 'Acceleration', 'SprintSpeed', 'Agility', 'Reactions',
                           'Balance', 'ShotPower', 'Jumping', 'Stamina', 'Strength', 'LongShots',
                           'Aggression', 'Interceptions', 'Positioning', 'Vision', 'Penalties',
                           'Composure', 'Marking', 'StandingTackle', 'SlidingTackle', 'GKDiving',
                           'GKHandling', 'GKKicking', 'GKPositioning', 'GKReflexes']
    df_quant = df[correlation_options].copy().dropna()
    noise = np.random.normal(0,0.3,df_quant.shape)
    df_quant_noise = df_quant + noise
    df_quant_noise["Name"] = df["Name"].copy()
    df_quant_noise["Position"] = df["Position"].copy()

    x_var = st.selectbox("Independent Variable", options = correlation_options, index=0)
    y_var = st.selectbox("Dependent Variable", options = correlation_options, index=1)
    use_color = st.checkbox("Use Color?", value = False)

    if use_color:
        color_var = st.selectbox("Color Variable", options = correlation_options, index=2)
        chart = alt.Chart(df_quant_noise).mark_circle(color="#000000",size=10).encode(
        x=alt.X(x_var, scale=alt.Scale(zero=False)),
        y=alt.Y(y_var, scale=alt.Scale(zero=False)),
        color=alt.Y(color_var),
        tooltip = ["Name","Position"]
        )
    else:
        chart = alt.Chart(df_quant_noise).mark_circle(color="#000000",size=10,opacity=.3).encode(
        x=alt.X(x_var, scale=alt.Scale(zero=False)),
        y=alt.Y(y_var, scale=alt.Scale(zero=False)),
        tooltip = ["Name","Position"]
        )
    correlation = np.corrcoef(df_quant[x_var],df_quant[y_var])[0][1]
    st.write("Correlation: %.2f" % correlation)

    chart = chart + chart.transform_regression(x_var,y_var,method="poly",order=5).mark_line(color="#0000FF")
    chart = chart.properties(
        width=800, height=500
    ).interactive()

    st.write(chart)


    st.header("Machine Learning Exploration")
    st.write("""Now we will examine how well we can predict attributes of a player using this
        dataset. Below you can select a target variable and one or many predictor variables,
        and a support vector regression model will be built using the input. We split the dataset
        into a training set and a testing set, as is common practice in machine learning
        (see [here](https://developers.google.com/machine-learning/crash-course/training-and-test-sets/splitting-data)).
        You can see the mean-squared-error of the model on the testing portion of the
        data, as well as a plot of the residuals.
        A residual is the difference between the predicted values and the actual values, and
        thus for a perfect classifier all residuals would be 0.""")
    target_var = st.selectbox("Target Variable", options = correlation_options, index=1)
    features = st.multiselect("Predictor Variables", options = correlation_options)

    if features != []:
        df_X = df_quant[features]
        df_y = df_quant[target_var]

        X_train, X_test, y_train, y_test = train_test_split(
            df_X, df_y, test_size=0.25)

        clf = make_pipeline(StandardScaler(), SVR())
        clf.fit(X_train, y_train)
        test_preds = clf.predict(X_test)
        mse = mean_squared_error(y_test,test_preds)
        st.write("Testing MSE = $$\\frac{1}{n}\Sigma_{i=1}^n(y_i-\hat{y}_i)^2$$ = %.2f" % mse)
        residuals = y_test - test_preds
        ml_df = pd.DataFrame({"residuals":residuals, "y_test":y_test, "predictions":test_preds})
        ml_chart = alt.Chart(ml_df).mark_circle(color="#000000",size=10,opacity=.3).encode(
            x=alt.X("y_test", scale=alt.Scale(zero=False), title="Actual"),
            y=alt.Y("residuals", scale=alt.Scale(zero=False), title="Residuals")
        ).properties(
        width=800, height=500
        )
        ml_chart += alt.Chart(pd.DataFrame({'y': [0]})).mark_rule().encode(y='y')
        st.write(ml_chart)
