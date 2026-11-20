import os
from collections import Counter
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from google import genai
# from spotipy.cache_handler import MemoryCacheHandler

st.set_page_config(page_title="Spotify Roast",page_icon="🎵",layout="wide")

st.markdown("""
<style>
.stApp{background:linear-gradient(180deg,#121212,#191414)}
h1,h2,h3{color:#1DB954!important}
[data-testid='metric-container']{background:#181818;border-radius:18px;padding:15px}
.stButton button{background:#1DB954!important;color:white!important;border-radius:30px!important;border:none}
.stButton button:hover{transform:scale(1.05)}
.spotify-card {
    background: linear-gradient(
        145deg,
        #181818,
        #121212
    );

    border-radius: 22px;
    padding: 20px;
    margin-bottom: 20px;

    border: 1px solid #2a2a2a;

    color: white !important;

    transition: all 0.35s ease;
}

.spotify-card h1,
.spotify-card h2,
.spotify-card h3,
.spotify-card h4,
.spotify-card p,
.spotify-card div {

    color: white !important;
}

.spotify-card:hover {

    transform:
        translateY(-8px)
        scale(1.02);

    border: 1px solid #1DB954;

    box-shadow:
        0px 0px 15px rgba(
            29,
            185,
            84,
            0.35
        ),

        0px 0px 30px rgba(
            29,
            185,
            84,
            0.25
        );

    background:
        linear-gradient(
            145deg,
            #181818,
            #1a2a1e
        );
}

/* Artist title glow */

.spotify-card:hover h3 {

    color: #1DB954 !important;

    text-shadow:
        0 0 8px #1DB954,
        0 0 16px #1DB954;
}

/* Smooth image zoom */

.spotify-card img {

    transition:
        transform 0.4s ease;
}

.spotify-card:hover img {

    transform: scale(1.05);
}
}
</style>
""",unsafe_allow_html=True)

API_KEY=st.secrets["GEMINI_API_KEY"]
client=genai.Client(api_key=API_KEY)

# if "cache_handler" not in st.session_state:
#     st.session_state.cache_handler = MemoryCacheHandler()

sp_oauth = SpotifyOAuth(
    client_id=st.secrets["SPOTIFY_CLIENT_ID"],
    client_secret=st.secrets["SPOTIFY_CLIENT_SECRET"],
    redirect_uri=st.secrets["SPOTIFY_REDIRECT_URI"],
    scope="user-top-read user-read-private user-read-email",
    # cache_handler=st.session_state.cache_handler
    cache_path=None
)


# params=st.query_params
# if 'code' not in params:
#     st.title('🎵 Spotify Roast')
#     st.markdown('### Spotify Wrapped + AI Roast')
#     st.link_button('Login with Spotify',sp_oauth.get_authorize_url())
#     st.stop()

code = st.query_params.get("code")

if code and "token_info" not in st.session_state:
    try:
        token_info = sp_oauth.get_access_token(code)
        st.session_state["token_info"] = token_info

        # Remove code from URL so refreshes don't reuse it
        st.query_params.clear()
        st.rerun()

    except Exception as e:
        st.error(f"Login failed: {e}")
        st.stop()

if "token_info" not in st.session_state:
    st.title("🎵 Spotify Roast")
    st.link_button(
        "Login with Spotify",
        sp_oauth.get_authorize_url()
    )
    st.stop()

sp = spotipy.Spotify(
    auth=st.session_state["token_info"]["access_token"]
)

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()

user=sp.current_user()
artists_data=sp.current_user_top_artists(limit=20,time_range='medium_term')
tracks_data=sp.current_user_top_tracks(limit=20,time_range='medium_term')

artists=artists_data['items']
tracks=tracks_data['items']
artist_names=[a['name'] for a in artists]
track_names=[t['name'] for t in tracks]

page=st.sidebar.radio('Menu',['Dashboard','Roast Me','Music Personality'])

if page == "Dashboard":

    st.title("📊 Spotify Wrapped Dashboard")

    # ==========================
    # HERO SECTION
    # ==========================

    st.markdown(
        f"""
        <div class="spotify-card">
            <h2>🎵 {user['display_name']}</h2>
            <p>
            Your personal Spotify analytics dashboard.
            </p>
            <h4>🎤 Favorite Artist: {artist_names[0]}</h4>
            <h4>🎧 Favorite Track: {track_names[0]}</h4>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ==========================
    # PROFILE + PICTURE
    # ==========================

    col1, col2 = st.columns([1, 3])

    with col1:

        if user.get("images"):
            st.image(
                user["images"][0]["url"],
                width=180
            )

    with col2:

        st.subheader("👤 Spotify Profile")

        st.write(
            f"**Display Name:** {user['display_name']}"
        )

        st.write(
            f"**Followers:** {user['followers']['total']}"
        )

        st.write(
            f"**Country:** {user.get('country','Unknown')}"
        )

    # ==========================
    # STATS
    # ==========================

    c1, c2 = st.columns(2)

    c1.metric(
        "🎤 Artists",
        len(artist_names)
    )

    c2.metric(
        "🎧 Tracks",
        len(track_names)
    )

    # ==========================
    # QUICK INSIGHTS
    # ==========================

    st.subheader("🤖 Music Insights")

    st.info(
        f"""
        • Your most listened artist is **{artist_names[0]}**
        """
    )

    # ==========================
    # TABS
    # ==========================

    tab1, tab2, tab3 = st.tabs(
        [
            "🎤 Artists",
            "🎧 Tracks",
            "🏆 Fun Stats",
        ]
    )

    # --------------------------
    # ARTISTS
    # --------------------------

    with tab1:

        st.subheader("🎤 Your Top Artists")

        search_artist = st.text_input(
            "🔍 Search Artist"
        )

        filtered_artists = [
            artist
            for artist in artists
            if search_artist.lower()
            in artist["name"].lower()
        ]

        view_mode = st.radio(
            "View Mode",
            ["Cards", "List"],
            horizontal=True
        )

        if view_mode == "Cards":

            cols = st.columns(3)

            for idx, artist in enumerate(filtered_artists):

                with cols[idx % 3]:

                    st.markdown(
                        f"""
                        <div style="height:70px;">
                            <h3 style="color:#1DB954;">🎤 {artist['name']}</h3>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if artist.get("images"):

                        st.markdown(
                            f"""
                            <img src="{artist['images'][0]['url']}"
                                style="
                                    width:180px;
                                    height:180px;
                                    object-fit:cover;
                                    border-radius:12px;
                                ">
                            """,
                            unsafe_allow_html=True
                        )


                    # popularity = artist.get(
                    #     "popularity",
                    #     0
                    # )

                    # st.progress(
                    #     popularity / 100
                    # )

                    # st.caption(
                    #     f"Popularity: {popularity}/100"
                    # )

                    # if popularity >= 80:

                    #     st.success(
                    #         "🔥 Mainstream Favorite"
                    #     )

                    # elif popularity >= 60:

                    #     st.info(
                    #         "🎵 Popular Pick"
                    #     )

                    # else:

                    #     st.warning(
                    #         "💎 Hidden Gem"
                    #     )

                    st.markdown(
                        "</div>",
                        unsafe_allow_html=True
                    )

                    st.divider()

        else:

            artist_df = pd.DataFrame(
                {
                    "Artist": [
                        a["name"]
                        for a in filtered_artists
                    ]
                }
            )

            st.dataframe(
                artist_df,
                use_container_width=True
            )

        # st.divider()

        # st.subheader(
        #     "🌟 Artist Spotlight"
        # )

        # spotlight_artist = artists[0]

        # # col1, col2 = st.columns(
        # #     [1, 2]
        # # )

        # # with col1:

        # if spotlight_artist.get(
        #     "images"
        # ):

        #     st.image(
        #         spotlight_artist["images"][0]["url"],
        #         width=250,
        #     )

        # with col2:

        #     st.markdown(
        #         f"""
        #         ## {spotlight_artist['name']}

        #         **Popularity:** {spotlight_artist['popularity']}/100

        #         Your most listened artist right now.
        #         """
        #     )

        #     st.progress(
        #         spotlight_artist["popularity"] / 100
        #     )

        # st.divider()

        # st.subheader(
        #     "🏆 Top Artist Rankings"
        # )

        # ranking_df = pd.DataFrame(
        #     {
        #         "Artist": [
        #             a["name"]
        #             for a in artists[:10]
        #         ]
        #     }
        # )

        # fig = px.bar(
        #     ranking_df,
        #     x="Artist",
        #     y="Popularity",
        #     color="Popularity",
        #     color_continuous_scale="Greens",
        #     title="Artist Popularity Rankings"
        # )

        # st.plotly_chart(
        #     fig,
        #     use_container_width=True
        # )

    # --------------------------
    # TRACKS
    # --------------------------

    with tab2:

        st.subheader("🎧 Your Top Tracks")

        selected_track = st.selectbox(
            "🎵 Explore a Track",
            [track["name"] for track in tracks]
        )

        selected = next(
            t for t in tracks
            if t["name"] == selected_track
        )

        col1, col2 = st.columns([1, 3])

        with col1:

            if selected["album"]["images"]:

                st.image(
                    selected["album"]["images"][0]["url"],
                    width=220
                )

        with col2:

            st.markdown(
                f"""
                ## 🎵 {selected['name']}

                🎤 **Artist:** {selected['artists'][0]['name']}

                💿 **Album:** {selected['album']['name']}

                📅 **Released:** {selected['album']['release_date']}
                """
            )

            if selected["explicit"]:

                st.warning(
                    "🅴 Explicit Content"
                )

        st.divider()

        st.subheader("🏆 Top 10 Tracks")

        for rank, track in enumerate(tracks[:10], start=1):

            with st.container(border=True):

                c1, c2 = st.columns([1, 4])

                with c1:

                    if track["album"]["images"]:

                        st.image(
                            track["album"]["images"][-1]["url"],
                            width=70
                        )

                with c2:

                    explicit_badge = (
                        " 🅴"
                        if track["explicit"]
                        else ""
                    )

                    st.markdown(
                        f"""
                        ### #{rank} {track['name']}{explicit_badge}

                        🎤 {track['artists'][0]['name']}

                        💿 {track['album']['name']}
                        """
                    )
    # --------------------------
    # FUN STATS
    # --------------------------

    with tab3:

        personality_map = [
            "🎬 Main Character",
            "🌙 Night Rider",
            "☕ Indie Coffee Addict",
            "💔 Heartbreak Veteran",
            "🏋️ Gym Goblin"
        ]


        st.metric(
            "🔥 Roastability Score",
            min(
                100,
                50
            )
        )

        st.metric(
            "🎲 Music Chaos",
            min(
                100,
                len(artist_names) * 3
            )
        )

        st.metric(
            "📈 Mainstream Level",
            min(
                100,
                len(track_names) * 2
            )
        )

elif page=='Roast Me':
    st.title('🔥 Roast Me')
    score=min(100,max(50,50))
    fig=go.Figure(go.Indicator(mode='gauge+number',value=score,title={'text':'Roastability'}))
    st.plotly_chart(fig,use_container_width=True)
    if st.button('Generate Roast'):
        prompt=f'Roast this music taste. Artists:{artist_names} Tracks:{track_names}. Funny, friendly, under 250 words.'
        r=client.models.generate_content(model='gemini-3.1-flash-lite',contents=prompt)
        st.balloons()
        st.markdown(r.text)

else:
    st.title('🧠 Music Personality')
    if st.button('Analyze Personality'):
        prompt=f'Create a fun music personality profile from artists {artist_names}, tracks {track_names}.'
        r=client.models.generate_content(model='gemini-3.1-flash-lite',contents=prompt)
        st.markdown(r.text)
