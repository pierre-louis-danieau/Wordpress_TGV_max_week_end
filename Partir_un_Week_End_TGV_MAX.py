import requests
import json
from datetime import datetime
from datetime import timedelta
import pandas as pd
import streamlit as st
from PIL import Image
import locale
from dateutil import parser
from streamlit.scriptrunner import get_script_run_ctx as get_report_ctx




def param(df_ville_origine):
    values_origine = df_ville_origine.values.flatten()
    option_origine = st.sidebar.selectbox(
        "Ville d'origine",
        values_origine,
        index = list(values_origine).index('PARIS (intramuros)'))

    today = datetime.now()
    option_date_depart = st.sidebar.date_input(
        "Date de départ",
        today,
        min_value = today,
        max_value = today + timedelta(days=29)
        )

    option_date_retour = st.sidebar.date_input(
        "Date de retour",
        option_date_depart,
        min_value = option_date_depart,
        max_value = today + timedelta(days=29)
        )

        

    bouton_launch_search=st.sidebar.button("Rechercher")
    return option_origine,option_date_depart,option_date_retour,bouton_launch_search



def dataframe_train_aller(url): 
    response_API_tgv = requests.get(url)
    data = response_API_tgv.text
    parse_json = json.loads(data)
    arr = []
    for i in range(len(parse_json['records'])):
        record = parse_json['records'][i]['fields']
        date = record['date']
        heure_arrivee = datetime.strptime(record['heure_arrivee'], '%H:%M')
        heure_depart = datetime.strptime(record['heure_depart'], '%H:%M')
        origine = record['origine']
        destination = record['destination']
        tgv_jeune_senior = (record['od_happy_card'])
        data_point = [origine, destination, date, heure_depart, heure_arrivee, tgv_jeune_senior]
        arr.append(data_point)

    df = pd.DataFrame(arr, columns = ["Origine", "Destination", "Date", "Heure de départ", "Heure d'arrivée", "Places disponibles"])
    df = df.sort_values(by=['Date','Heure de départ'])
    df["Heure d'arrivée"] = df["Heure d'arrivée"].apply(lambda x : x.strftime("%H:%M")+4*' ')
    df['Heure de départ'] = df['Heure de départ'].apply(lambda x : x.strftime("%H:%M")+4*' ')
    df['Places disponibles'] = df['Places disponibles'].apply(lambda x: 'PEUT ÊTRE'+4*' ' if x =="NON" else 'OUI'+10*' ')
    df = df.reset_index(drop=True)
    return df


def dataframe_train_retour(df_train_aller,option_origine,option_date_retour):
    destination = df_train_aller['Destination'].unique()
    day_r = option_date_retour.day
    month_r = option_date_retour.month
    year_r = option_date_retour.year
    dest_save = []
    for dest in destination :
        url = 'https://ressources.data.sncf.com/api/records/1.0/search/?dataset=tgvmax&q=&rows=10000&sort=-date&facet=date&facet=origine&facet=destination&facet=od_happy_card&refine.origine={}&refine.date={}%2F{}%2F{}&refine.destination={}&refine.od_happy_card=OUI'.format(dest,year_r,month_r,day_r,option_origine)
        df_train_filter_retour = dataframe_train_aller(url)
        if df_train_filter_retour.shape[0]>0:
            dest_save.append([dest,df_train_filter_retour])
    
    return pd.DataFrame(dest_save,columns=['Destination','dataframe'] )






def color_df(val):
     if val =="OUI"+10*' ':
          color = '#8DEF7B'
     else :
          color = '#FC9F60'
     return f'background-color: {color}'



#####Compute time long##############

@st.cache(suppress_st_warning=True, show_spinner=False,hash_funcs={'_json.Scanner': hash})
def compute_time_long(option_origine,option_date_depart,option_date_retour):
    find = False
    day_d = option_date_depart.day
    month_d = option_date_depart.month
    year_d = option_date_depart.year
    url = 'https://ressources.data.sncf.com/api/records/1.0/search/?dataset=tgvmax&q=&rows=10000&sort=-date&facet=date&facet=origine&facet=destination&facet=od_happy_card&refine.origine={}&refine.date={}%2F{}%2F{}&refine.od_happy_card=OUI'.format(option_origine,year_d,month_d,day_d)
    df_train_filter_aller = dataframe_train_aller(url)
    dest_save = dataframe_train_retour(df_train_filter_aller,option_origine,option_date_retour)
    if df_train_filter_aller.shape[0] >0 and dest_save.shape[0]>0:
        find = True
    return df_train_filter_aller,dest_save, find


def update_counter():
    st.session_state.radio_change = True

############### MAIN Programm #########################


if __name__ == "__main__":

    st.set_page_config(
    page_title="Maxplorateur",
    page_icon="🚅",
    layout="wide",
    initial_sidebar_state="expanded",
    )

    ## Hide menu
    hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden; }
    footer {visibility: hidden;}
    </style>
    """
    st.markdown(hide_menu_style, unsafe_allow_html=True)

    image = Image.open('7135.jpg')
    col1_first, col2_first = st.columns([2,1])

    ctx = get_report_ctx()
    id = ctx.session_id

    with col1_first:
        st.markdown("<h2 style='color: RoyalBlue;'>Un Week end en TGV Max</h2>", unsafe_allow_html=True)
        st.write("""
            **Partez découvrir gratuitement la France le temps d'un Week-End  !**
            
            Définissez vos critères dans la barre de gauche !
            """)


          
    with col2_first:
        st.image(image, caption='@Macrovector', width = 300)


    if 'radio_change' not in st.session_state:
        st.session_state['radio_change'] = 0
        
    if 'destination_df' not in st.session_state:
        st.session_state['destination_df'] = []

    if 'aller_df' not in st.session_state :
        st.session_state['aller_df'] =[]



    st.sidebar.markdown("# 1️⃣ - Partir un Week-End")
    locale.setlocale(locale.LC_TIME,'')

    ## Hide menu
    hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden; }
    footer {visibility: hidden;}
    </style>
    """
    st.markdown(hide_menu_style, unsafe_allow_html=True)
    ## End hide menu

    df_ville_origine = pd.read_csv('ville_origine.csv')
    del df_ville_origine['Unnamed: 0']


    option_origine,option_date_depart,option_date_retour,bouton_launch_search = param(df_ville_origine)

    if bouton_launch_search == True :
        with st.spinner('Recherche en cours... Cela peut prendre quelques secondes !'):
            df_train_filter_aller,dest_save, find = compute_time_long(option_origine,option_date_depart,option_date_retour)
        text = "<h5>🎉 Nous avons trouvé <font color=RoyalBlue>{}</font> destinations au départ de <font color=RoyalBlue>{}</font> avec allers-retours !</h5>".format(dest_save.shape[0],option_origine)
        st.markdown(text, unsafe_allow_html=True)
        if find:
            dest_save = dest_save.sort_values(by=['Destination'])
            multi_select_dest = st.radio(label = '', options = dest_save.Destination.values,horizontal=True,on_change=update_counter)
            st.session_state['destination_df'] = dest_save
            st.session_state['aller_df'] = df_train_filter_aller

            df_aller_select = df_train_filter_aller[df_train_filter_aller['Destination']==multi_select_dest].reset_index(drop=True)
            df_retour_select = dest_save[dest_save['Destination']==multi_select_dest]['dataframe'].values[0].reset_index(drop=True)

            st.markdown("<h5>1. Voici la liste des trains <font color=RoyalBlue>allers</font> : </h5>", unsafe_allow_html=True)
            st.dataframe(df_aller_select.style.applymap(color_df, subset=[df_aller_select.columns[-1]]),3000)
            st.markdown("<h5>2. Voici la liste des trains <font color=RoyalBlue>retours</font> : </h5>", unsafe_allow_html=True)
            st.dataframe(df_retour_select.style.applymap(color_df, subset=[df_retour_select.columns[-1]]),3000)

            st.write(' ')
        
        else:
            st.write("Aucune destination n'est accessible gratuitement avec un aller retour depuis la ville d'origine choisi et les dates choisies. Ré essaye avec de nouveaux critères !")

    
    if bouton_launch_search == False and st.session_state.radio_change == True:
        st.session_state.radio_change = False
        destination_df = st.session_state['destination_df']
        df_train_filter_aller = st.session_state['aller_df']
        destination_df = destination_df.sort_values(by=['Destination'])
        text = "<h5>🎉 Nous avons trouvé <font color=RoyalBlue>{}</font> destinations au départ de <font color=RoyalBlue>{}</font> avec allers-retours !</h5>".format(destination_df.shape[0],option_origine)
        st.markdown(text, unsafe_allow_html=True)
        multi_select_dest = st.radio(label = '',options = destination_df.Destination.values,horizontal=True,on_change=update_counter)
        
        
        df_aller_select = df_train_filter_aller[df_train_filter_aller['Destination']==multi_select_dest].reset_index(drop=True)
        df_retour_select = destination_df[destination_df['Destination']==multi_select_dest]['dataframe'].values[0].reset_index(drop=True)

        st.markdown("<h4>1. Voici la liste des trains <font color=RoyalBlue>allers</font> : </h4>", unsafe_allow_html=True)
        st.dataframe(df_aller_select.style.applymap(color_df, subset=[df_aller_select.columns[-1]]),3000)
        st.markdown("<h4>2. Voici la liste des trains <font color=RoyalBlue>retours</font> : </h4>", unsafe_allow_html=True)
        st.dataframe(df_retour_select.style.applymap(color_df, subset=[df_retour_select.columns[-1]]),3000)


