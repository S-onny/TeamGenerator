import streamlit as st
import pandas as pd
import random
from google.oauth2 import service_account
import gspread

# Authenticate and connect to Google Sheets
@st.cache_resource
def get_gspread_client():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

@st.cache_resource
def load_data():
    client = get_gspread_client()
    sheet = client.open("FC 파란 출결표").sheet1  # Update with your sheet name
    all_data = sheet.get_all_values()
    headers = all_data[0]  # First row contains column names
    data = all_data[2:]  # Data starts from the third row
    df = pd.DataFrame(data, columns=headers)
    
    # Convert skill column to numeric type
    df["기본기"] = pd.to_numeric(df["기본기"], errors='coerce')
    return df

def generate_teams(players, num_teams, players_per_team):
    random.shuffle(players)
    
    # Separate goalkeepers and field players
    gks = [p for p in players if p["포지션"] == "GK"]
    fds = [p for p in players if p["포지션"] == "FD"]

    # Sort players by skill level in descending order
    all_players = gks + fds
    all_players.sort(key=lambda x: x["기본기"], reverse=True)
    
    teams = [[] for _ in range(num_teams)]
    team_skill = [0] * num_teams
    team_female_count = [0] * num_teams
    
    # Assign goalkeepers if available
    for i in range(min(num_teams, len(gks))):
        teams[i].append(gks[i])
        team_skill[i] += gks[i]["기본기"]
        if gks[i]["성별"] == "F":
            team_female_count[i] += 1
    
    # Assign field players while balancing skill and female distribution
    for p in all_players[len(gks):]:
        best_team = None
        for i in range(num_teams):
            if len(teams[i]) < players_per_team:
                if best_team is None or (team_skill[i] < team_skill[best_team] or (team_skill[i] == team_skill[best_team] and team_female_count[i] < team_female_count[best_team])):
                    best_team = i

        if best_team is not None:
            teams[best_team].append(p)
            team_skill[best_team] += p["기본기"]
            if p["성별"] == "F":
                team_female_count[best_team] += 1
    
    return teams, team_skill

# Streamlit UI
st.title("Football Team Generator")
data = load_data()

# Select players from list
selected_players = st.multiselect("Select players for this match:", data["FC 파란 명단"].tolist())
num_teams = st.number_input("Number of teams:", min_value=2, max_value=6, value=3)
players_per_team = st.number_input("Players per team:", min_value=3, max_value=11, value=6)

df_selected = data[data["FC 파란 명단"].isin(selected_players)].to_dict("records")

if st.button("Generate Teams"):
    teams, skills = generate_teams(df_selected, num_teams, players_per_team)
    cols = st.columns(num_teams)

    for i, (team, skill) in enumerate(zip(teams, skills)):
        with cols[i]:
            st.markdown(f"""<div style='border: 2px solid #0099FF; padding: 10px; margin: 10px; height: auto; overflow-y: auto;>" <h3>Team {i+1} (Total Skill: {skill})</h3><ul>""", unsafe_allow_html=True)
            st.subheader(f"Team {i+1} (Total Skill: {skill})")
            for player in team:
                st.write(f"<li>{player['FC 파란 명단']}({player['성별']}) - Skill: {player['기본기']} - {'GK' if player['포지션'] == 'GK' else 'FD'}</li>", unsafe_allow_html=True)
            st.markdown("</ul></div>", unsafe_allow_html=True)