# Importations & Settings

import streamlit as st
import pandas as pd
import copy
import altair as alt
import plotly.express as px
import json
import time

pd.options.mode.chained_assignment = None  # default='warn'


# %% Useful Functions

def timeit(method):
    def timed(*args, **kw):
        file = open("logs.txt", "a")

        start = time.time()
        result = method(*args, **kw)
        end = time.time()

        file.write('%f Execution time: %2.2f seconds\n' % (end, end - start))
        file.close()

        return result

    return timed


def createTabs(df1, df2):
    tab1, tab2 = st.tabs(['2019', '2020'])

    with tab1:
        st.dataframe(df1.head())

    with tab2:
        st.dataframe(df2.head())


def createDoubleDfTabs(df1, df1b, df2, df2b):
    tab1, tab2 = st.tabs(['2019', '2020'])

    with tab1:
        data1, data2 = st.columns([5, 3])

        with data1:
            st.dataframe(df1)

        with data2:
            st.dataframe(df1b)

    with tab2:
        data1, data2 = st.columns([5, 3])

        with data1:
            st.dataframe(df2)

        with data2:
            st.dataframe(df2b)


def percentageIncrease(a, b):
    return 100 * (b - a) / a


# %% Data Transformation Functions

@st.cache(allow_output_mutation=True)
def loadData(url):
    return pd.read_csv(url, sep=',', low_memory=False)


@st.cache
def chooseCol(df1, df2):
    cols = ['numero_disposition', 'date_mutation', 'nature_mutation', 'valeur_fonciere', 'code_postal', 'nom_commune',
            'code_departement', 'nombre_lots', 'type_local', 'surface_reelle_bati', 'nombre_pieces_principales',
            'surface_terrain', 'longitude', 'latitude']

    df1_copy = copy.deepcopy(df1[cols])  # I used a deepcopy not to
    df2_copy = copy.deepcopy(df2[cols])  # mutate last cached outputs

    return df1_copy, df2_copy


@st.cache
def modifyTypes(df1, df2):
    df1_copy = copy.deepcopy(df1)
    df2_copy = copy.deepcopy(df2)

    df1_copy['date_mutation'] = pd.to_datetime(df1_copy['date_mutation'])
    df1_copy['code_postal'] = df1_copy['code_postal'].apply(lambda x: str(x)[:-2].zfill(5))
    df1_copy['code_departement'] = df1_copy['code_departement'].apply(lambda x: str(x).zfill(2))

    df2_copy['date_mutation'] = pd.to_datetime(df2_copy['date_mutation'])
    df2_copy['code_postal'] = df2_copy['code_postal'].apply(lambda x: str(x)[:-2].zfill(5))
    df2_copy['code_departement'] = df2_copy['code_departement'].apply(lambda x: str(x).zfill(2))

    return df1_copy, df2_copy


@st.cache
def addDepName(df1, df2, dpt):
    df1_copy = copy.deepcopy(df1)
    df2_copy = copy.deepcopy(df2)

    df1_copy["nom_departement"] = df1_copy["code_departement"].map(dpt.set_index("code_departement")["nom_departement"])
    df2_copy["nom_departement"] = df2_copy["code_departement"].map(dpt.set_index("code_departement")["nom_departement"])

    return df1_copy, df2_copy


@st.cache
def deleteDuplicates(df1, df2):
    df1_copy = copy.deepcopy(df1).drop_duplicates()
    df2_copy = copy.deepcopy(df2).drop_duplicates()

    return df1_copy, df2_copy


@st.cache
def concatenation(df1, df2):
    df1_copy = copy.deepcopy(df1)
    df2_copy = copy.deepcopy(df2)

    return pd.concat([df1_copy, df2_copy])


# %% Visualization Functions

@st.cache
def dfMaisonMap(df):
    departments = ['75', '92', '93', '94']

    df_maison = df[df['code_departement'].isin(departments)]
    df_maison = df_maison[df_maison["type_local"] == "Maison"]

    df_maison_loc = df_maison[['latitude', 'longitude']].dropna()

    return df_maison, df_maison_loc


def maisonMap(df):
    # Dataframes
    df_maison, df_maison_loc = dfMaisonMap(df)

    # Title
    st.subheader('Map of houses in Paris and its inner suburbs by value (2019/2020)')

    # Slider for value
    df_maison_min = st.slider('Minimum Value', 0, 5000000, step=25000)

    # Update minimum value with slider
    df_maison_loc = df_maison_loc[df_maison['valeur_fonciere'] >= df_maison_min]

    # Mapping
    st.map(df_maison_loc)

    # Text
    st.write('We can observe that, in the inner suburbs of Paris, most of the houses are located in the 93 and 94 ('
             'mostly east of Paris). On the other hand, if we filter, we can see that the houses worth the most are '
             'rather located in Paris and in the 92 (mostly in the west). This is due to the fact that the richest '
             'cities with the highest real estate costs are in Hauts-de-Seine such as Neuilly-sur-Seine or '
             'Boulogne-Billancourt.')

    # Dataframe & Code
    maisonLocCode = '''def dfMaisonMap(df):
    departments = ['75', '92', '93', '94']

    df_maison = df[df['code_departement'].isin(departments)]
    df_maison = df_maison[df_maison["type_local"] == "Maison"]

    df_maison_loc = df_maison[['latitude', 'longitude']].dropna()

    return df_maison, df_maison_loc

# Dataframes
df_maison, df_maison_loc = dfMaisonMap(df)

# Slider for value
df_maison_min = st.slider('Minimum Value', 0, 5000000, step=25000)

# Update minimum value with slider
df_maison_loc = df_maison_loc[df_maison['valeur_fonciere'] >= df_maison_min]

# Mapping
st.map(df_maison_loc)'''

    with st.expander("Details"):
        st.dataframe(df_maison)
        st.code(maisonLocCode, 'python')


@st.cache(allow_output_mutation=True)
def dfMaisonBar(df):
    departments = ['77', '78', '91', '92', '93', '94', '95']

    df_maison = df[df['code_departement'].isin(departments)]
    df_maison.rename(columns={"nom_departement": "Department",
                              "valeur_fonciere": "Property Value"}, inplace=True)
    df_maison = df_maison[df_maison["type_local"] == "Maison"]

    val_maison_by_dep = df_maison.groupby('Department')['Property Value'].mean()
    val_maison_by_dep = val_maison_by_dep.sort_values()

    return df_maison, val_maison_by_dep


def maisonBar(df1, df2):
    # Dataframes
    df19_maison, val_maison_by_dep19 = dfMaisonBar(df1)
    df20_maison, val_maison_by_dep20 = dfMaisonBar(df2)

    # Title
    st.subheader('Mean value for houses in the departments of Ile-de-France excluding Paris (2019/2020)')

    # Chart
    val1 = val_maison_by_dep19.reset_index().assign(Year='2019')
    val2 = val_maison_by_dep20.reset_index().assign(Year='2020')
    val = pd.concat([val1, val2])

    bars = alt.Chart(val).mark_bar().encode(
        x='Year',
        y='Property Value',
        color='Year',
        column='Department'
    ).properties(width=61)

    st.altair_chart(bars)

    # Metrics
    idf_percent = percentageIncrease(val_maison_by_dep19.mean(),
                                     val_maison_by_dep20.mean())
    idf = ['{:,} €'.format(int(val_maison_by_dep20.mean())),
           f"+{'{:.0f}'.format(idf_percent)}% (2019)"]

    val_oise_percent = percentageIncrease(val_maison_by_dep19["Val-d'Oise"],
                                          val_maison_by_dep20["Val-d'Oise"])
    val_oise = ['{:,} €'.format(int(val_maison_by_dep20["Val-d'Oise"])),
                f"+{'{:.0f}'.format(val_oise_percent)}% (2019)"]

    yvelines_percent = percentageIncrease(val_maison_by_dep19["Yvelines"],
                                          val_maison_by_dep20["Yvelines"])
    yvelines = ['{:,} €'.format(int(val_maison_by_dep20["Yvelines"])),
                f"{'{:.0f}'.format(yvelines_percent)}% (2019)"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Ile-de-France (2020)", idf[0], idf[1])
    col2.metric("Val-d'Oise (2020)", val_oise[0], val_oise[1])
    col3.metric("Yvelines (2020)", yvelines[0], yvelines[1])

    # Text
    st.write("The department with the highest average in 2019 is the Hauts-de-Seine at around 1.25 million euros. "
             "This is due to the fact that the richest cities with the highest real estate costs are in "
             "Hauts-de-Seine. These include: Neuilly-sur-Seine, Boulogne-Billancourt or Levallois-Perret. In "
             "comparison, in 2020, the departments have for the most part oscillated a little, except for the "
             "Val-d'Oise which has particularly boomed. Its average has been multiplied by 8 approaching 3 million "
             "euros. This translates into an average of nearly 920,000 euros in the departments of Ile-de-France "
             "excluding Paris, an increase of 63% over the previous year.")

    # Dataframes & Code
    valMaisonCode = '''def dfMaisonBar(df):
    departments = ['77', '78', '91', '92', '93', '94', '95']

    df_maison = df[df['code_departement'].isin(departments)]
    df_maison.rename(columns={"nom_departement": "Department",
                              "valeur_fonciere": "Property Value"}, inplace=True)
    df_maison = df_maison[df_maison["type_local"] == "Maison"]

    val_maison_by_dep = df_maison.groupby('Department')['Property Value'].mean()
    val_maison_by_dep = val_maison_by_dep.sort_values()

    return df_maison, val_maison_by_dep

# Dataframes
df19_maison, val_maison_by_dep19 = dfMaisonBar(df1)
df20_maison, val_maison_by_dep20 = dfMaisonBar(df2)
    
# Chart
val1 = val_maison_by_dep19.reset_index().assign(Year='2019')
val2 = val_maison_by_dep20.reset_index().assign(Year='2020')
val = pd.concat([val1, val2])

bars = alt.Chart(val).mark_bar().encode(
    x='Year',
    y='Property Value',
    color='Year',
    column='Department'
).properties(width=61)
    
st.altair_chart(bars)

# Metrics
idf_percent = percentageIncrease(val_maison_by_dep19.mean(),
                                 val_maison_by_dep20.mean())
idf = ['{:,} €'.format(int(val_maison_by_dep20.mean())),
       f"+{'{:.0f}'.format(idf_percent)}% (2019)"]

val_oise_percent = percentageIncrease(val_maison_by_dep19["Val-d'Oise"],
                                      val_maison_by_dep20["Val-d'Oise"])
val_oise = ['{:,} €'.format(int(val_maison_by_dep20["Val-d'Oise"])),
            f"+{'{:.0f}'.format(val_oise_percent)}% (2019)"]

yvelines_percent = percentageIncrease(val_maison_by_dep19["Yvelines"],
                                      val_maison_by_dep20["Yvelines"])
yvelines = ['{:,} €'.format(int(val_maison_by_dep20["Yvelines"])),
            f"{'{:.0f}'.format(yvelines_percent)}% (2019)"]

col1, col2, col3 = st.columns(3)
col1.metric("Ile-de-France (2020)", idf[0], idf[1])
col2.metric("Val-d'Oise (2020)", val_oise[0], val_oise[1])
col3.metric("Yvelines (2020)", yvelines[0], yvelines[1])'''

    with st.expander("Details"):
        createDoubleDfTabs(df19_maison, val_maison_by_dep19, df20_maison, val_maison_by_dep20)
        st.code(valMaisonCode, 'python')


@st.cache(allow_output_mutation=True)
def dfArrondParis(df):
    df_val_paris = df[["valeur_fonciere", "surface_reelle_bati", "code_postal", "nom_departement"]]
    df_val_paris = df_val_paris[df_val_paris["nom_departement"] == "Paris"]
    df_val_paris["Arrondissement"] = df_val_paris["code_postal"].str[-2:]
    df_val_paris = df_val_paris[df_val_paris['surface_reelle_bati'] != 0]
    df_val_paris["Property value / m²"] = df_val_paris["valeur_fonciere"] / df_val_paris["surface_reelle_bati"]
    df_val_paris = df_val_paris[df_val_paris['Arrondissement'] != "0n"].dropna()

    df_val_by_arrond = df_val_paris.groupby("Arrondissement")["Property value / m²"].mean().sort_values()

    return df_val_paris, df_val_by_arrond


def m2Paris(df1, df2):
    # Dataframes
    df19_val_paris, df19_val_by_arrond = dfArrondParis(df1)
    df20_val_paris, df20_val_by_arrond = dfArrondParis(df2)

    val19 = df19_val_by_arrond.reset_index().assign(Year='2019')
    val20 = df20_val_by_arrond.reset_index().assign(Year='2020')
    val = pd.concat([val19, val20])

    # Title
    st.subheader('Average price per square meter per district of Paris (2019/2020)')

    # Checkboxes
    show2019 = st.checkbox('2019', True, key=11)
    show2020 = st.checkbox('2020', True, key=22)

    if not (show2019 or show2020):
        val['Property value / m²'] = 0

    elif show2019 and not show2020:
        val['Property value / m²'] = val['Property value / m²'].where(val['Year'] == '2019', 0)

    elif show2020 and not show2019:
        val['Property value / m²'] = val['Property value / m²'].where(val['Year'] == '2020', 0)

    # Chart
    bars = alt.Chart(val).mark_bar(opacity=0.7).encode(
        x=alt.X("Property value / m²", stack=None),
        y="Arrondissement",
        color='Year'
    ).interactive()

    st.altair_chart(bars, use_container_width=True)

    # Metrics
    paris_percent = percentageIncrease(df19_val_by_arrond.mean(),
                                       df20_val_by_arrond.mean())
    paris = ['{:,} €'.format(int(df20_val_by_arrond.mean())),
             f"{'{:.0f}'.format(paris_percent)}% (2019)"]

    district8_percent = percentageIncrease(df19_val_by_arrond["08"],
                                           df20_val_by_arrond["08"])
    district8 = ['{:,} €'.format(int(df20_val_by_arrond["08"])),
                 f"+{'{:.0f}'.format(district8_percent)}% (2019)"]

    district15_percent = percentageIncrease(df19_val_by_arrond["15"],
                                            df20_val_by_arrond["15"])
    district15 = ['{:,} €'.format(int(df20_val_by_arrond["15"])),
                  f"{'{:.0f}'.format(district15_percent)}% (2019)"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Paris (2020)", paris[0], paris[1])
    col2.metric("8th district (2020)", district8[0], district8[1])
    col3.metric("15th district (2020)", district15[0], district15[1])

    # Text
    st.write('The districts with the lowest prices are those often considered the most modest, often on the edge of '
             'Paris. In contrast, the apartments with the highest prices are those in the heart of the capital. The '
             '1st and 8th arrondissements are the most affluent with more than 190,000 euros per meter over the two '
             'years. Between 2019 and 2020 the average price of a square meter in Paris fell by 10%. The most '
             'affected district is the 15th with a price price reduced by almost 90%.')

    # Dataframes & Code
    valArrondCode = '''def dfArrondParis(df):
    df_val_paris = df[["valeur_fonciere", "surface_reelle_bati", "code_postal", "nom_departement"]]
    df_val_paris = df_val_paris[df_val_paris["nom_departement"] == "Paris"]
    df_val_paris["Arrondissement"] = df_val_paris["code_postal"].str[-2:]
    df_val_paris = df_val_paris[df_val_paris['surface_reelle_bati'] != 0]
    df_val_paris["Property value / m²"] = df_val_paris["valeur_fonciere"] / df_val_paris["surface_reelle_bati"]
    df_val_paris = df_val_paris[df_val_paris['Arrondissement'] != "0n"].dropna()

    df_val_by_arrond = df_val_paris.groupby("Arrondissement")["Property value / m²"].mean().sort_values()

    return df_val_paris, df_val_by_arrond

# Dataframes
df19_val_paris, df19_val_by_arrond = dfArrondParis(df1)
df20_val_paris, df20_val_by_arrond = dfArrondParis(df2)

val19 = df19_val_by_arrond.reset_index().assign(Year='2019')
val20 = df20_val_by_arrond.reset_index().assign(Year='2020')
val = pd.concat([val19, val20])
    
# Checkboxes
show2019 = st.checkbox('2019', True, key=11)
show2020 = st.checkbox('2020', True, key=22)

if not (show2019 or show2020):
    val['Property value / m²'] = 0

elif show2019 and not show2020:
    val['Property value / m²'] = val['Property value / m²'].where(val['Year'] == '2019', 0)

elif show2020 and not show2019:
    val['Property value / m²'] = val['Property value / m²'].where(val['Year'] == '2020', 0)

# Chart
bars = alt.Chart(val).mark_bar(opacity=0.7).encode(
    x=alt.X("Property value / m²", stack=None),
    y="Arrondissement",
    color='Year'
).interactive()

st.altair_chart(bars, use_container_width=True)

# Metrics
paris_percent = percentageIncrease(df19_val_by_arrond.mean(),
                                 df20_val_by_arrond.mean())
paris = ['{:,} €'.format(int(df20_val_by_arrond.mean())),
         f"{'{:.0f}'.format(paris_percent)}% (2019)"]

district8_percent = percentageIncrease(df19_val_by_arrond["08"],
                                      df20_val_by_arrond["08"])
district8 = ['{:,} €'.format(int(df20_val_by_arrond["08"])),
             f"+{'{:.0f}'.format(district8_percent)}% (2019)"]

district15_percent = percentageIncrease(df19_val_by_arrond["15"],
                                      df20_val_by_arrond["15"])
district15 = ['{:,} €'.format(int(df20_val_by_arrond["15"])),
              f"{'{:.0f}'.format(district15_percent)}% (2019)"]

col1, col2, col3 = st.columns(3)
col1.metric("Paris (2020)", paris[0], paris[1])
col2.metric("8th district (2020)", district8[0], district8[1])
col3.metric("15th district (2020)", district15[0], district15[1])'''

    with st.expander("Details"):
        createDoubleDfTabs(df19_val_paris, df19_val_by_arrond, df20_val_paris, df20_val_by_arrond)
        st.code(valArrondCode, 'python')


@st.cache
def dfAppartVersailles(df):
    appart_versailles = df[["date_mutation", "valeur_fonciere",
                            "surface_reelle_bati", "type_local", "nom_commune"]]
    appart_versailles = appart_versailles[appart_versailles["nom_commune"] == "Versailles"]
    appart_versailles = appart_versailles[appart_versailles["type_local"] == "Appartement"]
    appart_versailles["Property value / m²"] = appart_versailles["valeur_fonciere"] / appart_versailles[
        "surface_reelle_bati"]
    appart_versailles["Month"] = appart_versailles["date_mutation"].dt.strftime('%Y-%m')

    appart_by_month = appart_versailles.groupby('Month')['Property value / m²'].mean()

    return appart_versailles, appart_by_month


def appartVersailles(df):
    # Dataframes
    appart_versailles, appart_by_month = dfAppartVersailles(df)

    # Title
    st.subheader('Average price per square meter of an apartment in Versailles over the months (2019/2020)')

    # Chart
    st.bar_chart(appart_by_month)

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Mean", '{:,.2f}'.format(appart_by_month.mean()))
    col2.metric("Median", '{:,.2f}'.format(appart_by_month.median()))
    col3.metric("Standard Deviation", '{:,.2f}'.format(appart_by_month.std()))

    # Text
    st.write('The price per square meter in Versailles between 2019 and 2020 generally varies between 6,300 and 9,'
             '700 euros. Only the months of October 2019, December 2019 and September 2020 stand out as being much '
             'more expensive than the others, even reaching around 30,000 euros for the last two.')

    # Dataframes & Code
    appartCode = '''def dfAppartVersailles(df):
    appart_versailles = df[["date_mutation", "valeur_fonciere",
                            "surface_reelle_bati", "type_local", "nom_commune"]]
    appart_versailles = appart_versailles[appart_versailles["nom_commune"] == "Versailles"]
    appart_versailles = appart_versailles[appart_versailles["type_local"] == "Appartement"]
    appart_versailles["Property value / m²"] = appart_versailles["valeur_fonciere"] / appart_versailles[
        "surface_reelle_bati"]
    appart_versailles["Month"] = appart_versailles["date_mutation"].dt.strftime('%Y-%m')

    appart_by_month = appart_versailles.groupby('Month')['Property value / m²'].mean()

    return appart_versailles, appart_by_month
    
# Dataframes
appart_versailles, appart_by_month = dfAppartVersailles(df)

# Chart
st.bar_chart(appart_by_month)

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Mean", '{:,.2f}'.format(appart_by_month.mean()))
col2.metric("Median", '{:,.2f}'.format(appart_by_month.median()))
col3.metric("Standard Deviation", '{:,.2f}'.format(appart_by_month.std()))'''

    with st.expander("Details"):
        data1, data2 = st.columns([5, 3])

        with data1:
            st.dataframe(appart_versailles)

        with data2:
            st.dataframe(appart_by_month)

        st.code(appartCode, 'python')


@st.cache
def dfSalesType(df):
    type_sales = df[["date_mutation", "type_local"]].dropna()
    type_sales["Month"] = type_sales["date_mutation"].dt.strftime('%Y-%m')
    type_sales = type_sales.groupby(['type_local', 'Month']).size().reset_index()
    type_sales.rename(columns={0: 'Number of sales',
                               'type_local': 'Local type'}, inplace=True)
    return type_sales


def salesType(df):
    # Dataframe
    type_sales = dfSalesType(df)

    # Title
    st.subheader('Evolution of the number of sales by type of premises over the months (2019/2020)')

    # Chart
    lines = alt.Chart(type_sales).mark_line(point=True).encode(
        x='Month',
        y='Number of sales',
        color='Local type',
    ).interactive()

    st.altair_chart(lines, use_container_width=True)

    # Text
    st.write('Sales for each type of premises evolve more or less in the same way over the months. There are always '
             'more houses sold than apartments, more apartments than outbuildings and more outbuildings than '
             'industrial or commercial premises. July 2019 was the month with the most sales for each type of '
             'premises. The number of sales then dropped significantly as April 2020 approached due to Covid-19 and '
             'the onset of the lockdown (except for industrial and commercial premises, which were slightly '
             'affected). Sales then gradually rebounded during the year without reaching the levels of the previous '
             'year. Only industrial and commercial premises sales remained roughly stable. The months of August '
             'nevertheless remain periods with fewer sales because many people are on vacation and the new school '
             'year is close at hand.')

    # Dataframes & Code
    typeSalesCode = '''def dfSalesType(df):
    type_sales = df[["date_mutation", "type_local"]].dropna()
    type_sales["Month"] = type_sales["date_mutation"].dt.strftime('%Y-%m')
    type_sales = type_sales.groupby(['type_local', 'Month']).size().reset_index()
    type_sales.rename(columns={0: 'Number of sales', 
                               'type_local': 'Local type'}, inplace=True)
    return type_sales

# Dataframe
type_sales = dfSalesType(df)

# Chart
lines = alt.Chart(type_sales).mark_line(point=True).encode(
    x='Month',
    y='Number of sales',
    color='Local type',
).interactive()

st.altair_chart(lines, use_container_width=True)'''

    with st.expander("Details"):
        st.dataframe(type_sales)
        st.code(typeSalesCode, 'python')


@st.cache
def dfSalesRegion(df, dpt):
    region_sales = df[["date_mutation", "code_departement"]]

    region_sales["Region"] = region_sales["code_departement"].map(dpt.set_index("code_departement")["nom_region"])
    region_sales["Month"] = region_sales["date_mutation"].dt.strftime('%Y-%m')

    region_sales = region_sales.groupby(['Region', 'Month']).size().reset_index()
    region_sales.rename(columns={0: 'Number of sales'}, inplace=True)

    return region_sales


def salesRegion(df, dpt):
    # Dataframe
    region_sales = dfSalesRegion(df, dpt)

    # Title
    st.subheader('Heat map of the number of sales by month and by region across 2019 and 2020')

    # Chart
    heatmap = alt.Chart(region_sales).mark_rect().encode(
        x='Month:O',
        y=alt.Y('Region:O', sort='-color'),
        color=alt.Color('Number of sales:Q', scale=alt.Scale(scheme='goldred'))
    )

    st.altair_chart(heatmap, use_container_width=True)

    # Text
    st.write('We note that 5 of the regions make very few sales compared to the others (Reunion, Guyana, Corsica, '
             'Martinique and Guadeloupe). This is explained by the fact that they are islands and are much smaller '
             'than the metropolitan regions. The regions with the most sales are Ile-de-France, Auvergne-Rhône-Alpes, '
             'Nouvelle-Aquitaine and Occitanie. This is due to the fact that they are either large or highly '
             'populated and attractive regions. The periods with the most sales were July and December 2019. Sales '
             'then generally declined in 2020, particularly in April, due to the arrival of Covid-19 and lockdown. '
             'The months of August were also periods with less sales. It is a transition month between school years '
             'and many people are on vacation.')

    # Dataframes & Code
    regionSalesCode = '''def dfSalesRegion(df, dpt):
    region_sales = df[["date_mutation", "code_departement"]]

    region_sales["Region"] = region_sales["code_departement"].map(dpt.set_index("code_departement")["nom_region"])
    region_sales["Month"] = region_sales["date_mutation"].dt.strftime('%Y-%m')

    region_sales = region_sales.groupby(['Region', 'Month']).size().reset_index()
    region_sales.rename(columns={0: 'Number of sales'}, inplace=True)

    return region_sales

# Dataframe
region_sales = dfSalesRegion(df, dpt)

# Chart
heatmap = alt.Chart(region_sales).mark_rect().encode(
    x='Month:O',
    y='Region:O',
    color=alt.Color('Number of sales:Q',scale=alt.Scale(scheme='goldred'))
)

st.altair_chart(heatmap, use_container_width=True)'''

    with st.expander("Details"):
        st.dataframe(region_sales)
        st.code(regionSalesCode, 'python')


@st.cache
def dfMostApartments(df1, df2):
    most_apart1 = df1.groupby(['nom_departement', 'type_local'])['type_local'].count()
    most_apart1 = most_apart1[:, 'Appartement'].sort_values(ascending=False)[:10].reset_index()
    most_apart1.rename(columns={"type_local": "2019"}, inplace=True)

    most_apart2 = df2.groupby(['nom_departement', 'type_local'])['type_local'].count()
    most_apart2 = most_apart2[:, 'Appartement'].sort_values(ascending=False)[:10].reset_index()
    most_apart2.rename(columns={"type_local": "2020"}, inplace=True)

    most_apart = most_apart1.join(most_apart2['2020'])
    most_apart['Average'] = most_apart.mean(axis=1).astype('int64')
    most_apart.rename(columns={"nom_departement": "Department"}, inplace=True)

    return most_apart


def mostApartments(df1, df2):
    # Dataframe
    most_apart = dfMostApartments(df1, df2)

    # Title
    st.subheader('Distribution of apartments among the 10 departments which have the most (Average for 2019 and 2020)')

    # Chart
    base = alt.Chart(most_apart).encode(
        theta=alt.Theta("Average:Q", stack=True),
        radius=alt.Radius("Average", scale=alt.Scale(type="sqrt", zero=True, rangeMin=20)),
        color=alt.Color("Department:N", sort=alt.EncodingSortField(field="Average", op="count", order='ascending')),
    )
    pie = base.mark_arc(innerRadius=20)
    text = base.mark_text(radiusOffset=20).encode(text="Average:Q")

    st.altair_chart(pie + text, use_container_width=True)

    # Text
    st.write('It is in the departments of Paris, Alpes-Maritimes, Rhône and Bouches-du-Rhône that we find the largest '
             'number of apartments. This can be explained by the fact that these three departments include some of '
             'the largest cities in the country, such as Paris, the capital, as well as Marseille, Lyon and Nice. The '
             'number of apartments is greater in metropolises like these. Paris alone represents almost the combined '
             'total of the departments of Rhône and Bouches-du-Rhône.')

    # Dataframes & Code
    mostApartCode = '''def dfMostApartments(df1, df2):
    most_apart1 = df1.groupby(['nom_departement', 'type_local'])['type_local'].count()
    most_apart1 = most_apart1[:, 'Appartement'].sort_values(ascending=False)[:10].reset_index()
    most_apart1.rename(columns={"type_local": "2019"}, inplace=True)

    most_apart2 = df2.groupby(['nom_departement', 'type_local'])['type_local'].count()
    most_apart2 = most_apart2[:, 'Appartement'].sort_values(ascending=False)[:10].reset_index()
    most_apart2.rename(columns={"type_local": "2020"}, inplace=True)

    most_apart = most_apart1.join(most_apart2['2020'])
    most_apart['Average'] = most_apart.mean(axis=1).astype('int64')
    most_apart.rename(columns={"nom_departement": "Department"}, inplace=True)

    return most_apart
    
# Chart
base = alt.Chart(most_apart).encode(
    theta=alt.Theta("Average:Q", stack=True),
    radius=alt.Radius("Average", scale=alt.Scale(type="sqrt", zero=True, rangeMin=20)),
    color=alt.Color("Department:N", sort=alt.EncodingSortField(field="Average", op="count", order='ascending')),
)
pie = base.mark_arc(innerRadius=20)
text = base.mark_text(radiusOffset=20).encode(text="Average:Q")

st.altair_chart(pie+text, use_container_width=True)'''

    with st.expander("Details"):
        st.dataframe(most_apart)
        st.code(mostApartCode, 'python')


@st.cache
def dfSurfaceDep(df):
    dep_france = json.load(open("departements-version-simplifiee.geojson", "r"))
    # Source : https://github.com/gregoiredavid/france-geojson/blob/master/departements-version-simplifiee.geojson

    dep_id_map = {}
    for feature in dep_france["features"]:
        feature["id"] = feature["properties"]["nom"]
        dep_id_map[feature["properties"]["code"]] = feature["id"]

    dep_surface = df[["surface_reelle_bati", "code_departement"]]
    dep_surface.rename(columns={"surface_reelle_bati": "Real surface"}, inplace=True)
    dep_surface = dep_surface.groupby("code_departement").mean().reset_index()[:-4]
    dep_surface["id"] = dep_surface["code_departement"].apply(lambda x: dep_id_map[x])

    return dep_surface, dep_france


def surfaceDep(df):
    # Dataframes
    dep_surface, departments = dfSurfaceDep(df)

    # Title
    st.subheader('Choropleth map of the average real surface per department in metropolitan France (2019/2020)')

    # Map
    dep_map = px.choropleth(dep_surface,
                            locations="id",
                            geojson=departments,
                            color="Real surface",
                            scope="europe",
                            hover_name="id",
                            hover_data=["Real surface"],
                            center={"lat": 46, "lon": 2.21})

    dep_map.update_geos(fitbounds="locations", visible=False)

    config = {'displaylogo': False,
              'modeBarButtonsToRemove': ['select2d', 'lasso2d']}

    st.plotly_chart(dep_map, config=config, use_container_width=True)

    # Text
    st.write('The departments with the smallest average real area are logically the departments with the largest '
             'cities. The average mass is found in the rest of the country. In the end, the department with the '
             'highest average surface is Ardèche. The one with the lowest is obviously Paris.')

    # Dataframes & Code
    depSurfaceCode = '''def dfSurfaceDep(df):
    dep_france = json.load(open("departements-version-simplifiee.geojson", "r"))
    # Source : https://github.com/gregoiredavid/france-geojson/blob/master/departements-version-simplifiee.geojson

    dep_id_map = {}
    for feature in dep_france["features"]:
        feature["id"] = feature["properties"]["nom"]
        dep_id_map[feature["properties"]["code"]] = feature["id"]

    dep_surface = df[["surface_reelle_bati", "code_departement"]]
    dep_surface.rename(columns={"surface_reelle_bati": "Real surface"}, inplace=True)
    dep_surface = dep_surface.groupby("code_departement").mean().reset_index()[:-4]
    dep_surface["id"] = dep_surface["code_departement"].apply(lambda x: dep_id_map[x])

    return dep_surface, dep_france

# Dataframes
dep_surface, departments = dfSurfaceDep(df)

# Map
dep_map = px.choropleth(dep_surface,
                        locations="id",
                        geojson=departments,
                        color="Real surface",
                        scope="europe",
                        hover_name="id",
                        hover_data=["Real surface"],
                        center={"lat": 46, "lon": 2.21})

dep_map.update_geos(fitbounds="locations", visible=False)

config = {'displaylogo': False,
          'modeBarButtonsToRemove': ['select2d', 'lasso2d']}

st.plotly_chart(dep_map, config=config, use_container_width=True)'''

    with st.expander("Details"):
        st.dataframe(dep_surface)
        st.code(depSurfaceCode, 'python')


# %% Main Function

@timeit
def main():
    # Page configuration

    st.set_page_config(
        page_title="Property Values France • Dashboard"
    )

    # App header

    st.title('Property values in France (2019/2020)')

    # Load data

    df19 = loadData('full_2019.csv')
    df20 = loadData('full_2020.csv')

    loadCode = '''def loadData(url):
    return pd.read_csv(url, sep=',', low_memory=False)

df19 = loadData('full_2019.csv')
df20 = loadData('full_2020.csv')'''

    st.header('Loading data')

    st.code(loadCode, 'python')
    if st.button('Show Dataframe', 0):
        createTabs(df19, df20)

    # Clean & transform data

    st.header('Cleaning & transforming data')

    # Choose columns

    df19_cols, df20_cols = chooseCol(df19, df20)

    choiceColCode = '''def chooseCol(df1, df2):
    cols = ['numero_disposition', 'date_mutation', 'nature_mutation', 'valeur_fonciere', 'code_postal', 'nom_commune',
            'code_departement', 'nombre_lots', 'type_local', 'surface_reelle_bati', 'nombre_pieces_principales',
            'surface_terrain', 'longitude', 'latitude']

    df1_copy = copy.deepcopy(df1[cols])  # I used a deepcopy not to
    df2_copy = copy.deepcopy(df2[cols])  # mutate last cached outputs

    return df1_copy, df2_copy

df19_cols, df20_cols = chooseCol(df19, df20)'''

    st.markdown('#### Choice of columns')
    st.code(choiceColCode, 'python')
    if st.button('Show Dataframe', 1):
        createTabs(df19_cols, df20_cols)

    # Modify types

    df19_modified, df20_modified = modifyTypes(df19_cols, df20_cols)

    modifTypeCode = '''def modifyTypes(df1, df2):
    df1_copy = copy.deepcopy(df1)
    df2_copy = copy.deepcopy(df2)

    df1_copy['date_mutation'] = pd.to_datetime(df1_copy['date_mutation'])
    df1_copy['code_postal'] = df1_copy['code_postal'].apply(lambda x: str(x)[:-2].zfill(5))
    df1_copy['code_departement'] = df1_copy['code_departement'].apply(lambda x: str(x).zfill(2))

    df2_copy['date_mutation'] = pd.to_datetime(df2_copy['date_mutation'])
    df2_copy['code_postal'] = df2_copy['code_postal'].apply(lambda x: str(x)[:-2].zfill(5))
    df2_copy['code_departement'] = df2_copy['code_departement'].apply(lambda x: str(x).zfill(2))

    return df1_copy, df2_copy

df19_modified, df20_modified = modifyTypes(df19_cols, df20_cols)'''

    st.markdown('#### Modify wrong types')
    st.code(modifTypeCode, 'python')
    if st.button('Show Dataframe', 2):
        createTabs(df19_modified, df20_modified)

    # Add department_names column

    dep = loadData("departements-france.csv")  # Departments & Regions
    # Source : https://www.data.gouv.fr/fr/datasets/departements-de-france/

    df19_complete, df20_complete = addDepName(df19_modified, df20_modified, dep)

    depNameCode = '''def addDepName(df1, df2, dpt):
    df1_copy = copy.deepcopy(df1)
    df2_copy = copy.deepcopy(df2)

    df1_copy["nom_departement"] = df1_copy["code_departement"].map(dpt.set_index("code_departement")["nom_departement"])
    df2_copy["nom_departement"] = df2_copy["code_departement"].map(dpt.set_index("code_departement")["nom_departement"])

    return df1_copy, df2_copy

dep = loadData("departements-france.csv")  # Departments & Regions
# Source : https://www.data.gouv.fr/fr/datasets/departements-de-france/

df19_complete, df20_complete = addDepName(df19_modified, df20_modified, dep)'''

    st.markdown('#### New column with department name')
    st.code(depNameCode, 'python')
    if st.button('Show Dataframe', 3):
        createTabs(df19_complete, df20_complete)

    # Drop duplicates

    df19_clean, df20_clean = deleteDuplicates(df19_complete, df20_complete)

    dropDuplicateCode = '''def deleteDuplicates(df1, df2):
    df1_copy = copy.deepcopy(df1).drop_duplicates()
    df2_copy = copy.deepcopy(df2).drop_duplicates()

    return df1_copy, df2_copy

df19_clean, df20_clean = deleteDuplicates(df19_complete, df20_complete)'''

    st.markdown('#### Drop duplicates')
    st.code(dropDuplicateCode, 'python')
    createTabs(df19_clean, df20_clean)

    # Concatenation

    df_clean = concatenation(df19_clean, df20_clean)

    concatenationCode = '''def concatenation(df1, df2):
    df1_copy = copy.deepcopy(df1)
    df2_copy = copy.deepcopy(df2)
    
    return pd.concat([df1_copy, df2_copy])
    
df_clean = concatenation(df19_clean, df20_clean)'''

    st.markdown('#### Concatenated dataframe')
    st.code(concatenationCode, 'python')

    # Data visualization

    st.header('Data interpretation & visualization')

    # Geographical representation of houses in the inner suburbs / value (2019/2020)

    maisonMap(df_clean)

    # Mean value for houses in the departments of Île-de-France excluding Paris (2019/2020)

    maisonBar(df19_clean, df20_clean)

    # Average price per square meter per district of Paris (2019/2020)

    m2Paris(df19_clean, df20_clean)

    # Average price per square meter of an apartment in Versailles over the months (2019/2020)

    appartVersailles(df_clean)

    # Evolution of the number of sales by type of premises over the months (2019/2020)

    salesType(df_clean)

    # Heat map of the number of sales by month and by region across 2019 and 2020

    salesRegion(df_clean, dep)

    # Distribution of apartments among the 10 departments which have the most (Average for 2019 and 2020)

    mostApartments(df19_clean, df20_clean)

    # Choropleth map of the average real surface per department in metropolitan France (2019/2020)

    surfaceDep(df_clean)


if __name__ == "__main__":
    main()
