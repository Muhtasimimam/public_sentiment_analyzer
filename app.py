import streamlit as st
import asyncio
import pandas as pd
import gspread
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import json
import requests

# Dummy functions for sentiment analysis and fetching comments (replace these with actual code)
import random

def analyze_sentiment(text):
    sentiments = ["positive", "negative", "neutral", "mixed"]
    return random.choice(sentiments)

async def fetch_comments(speech_keywords):
    return ["This is a great speech!", "I don't agree with this idea."]  # Placeholder for fetching comments

# Function to authenticate and connect to Google Sheets
def authenticate_google_sheets():
    # Load credentials from the JSON file in your GitHub repository
    url = "https://raw.githubusercontent.com/Muhtasimimam/public_sentiment_analyzer/master/sentimentanalysisapp-457520-74eff8b32d78.json"
    response = requests.get(url)
    credentials_dict = response.json()

    # Use google-auth to authenticate
    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )

    # Use gspread to authorize and connect to Google Sheets
    client = gspread.authorize(credentials)

    # Open the sheet
    spreadsheet_id = "13Uwvi9FVy1Cv-NLYdwauvb1DjaSOTRZVCBz1OxyBupc"  # Replace with your actual sheet ID
    sheet = client.open_by_key(spreadsheet_id).sheet1
    return sheet

# Function to save data to Google Sheets
def save_to_google_sheets(speech, speech_sentiment, public_sentiments):
    sheet = authenticate_google_sheets()  # Authenticate and get the sheet
    # Append data to the sheet (you can modify this to insert data as needed)
    sheet.append_row([speech, speech_sentiment, ', '.join(public_sentiments)])

# Streamlit UI for user input
st.title("Real-Time Sentiment Analysis and Visualization")

# Get speech input from the user
speech_input = st.text_area("Enter Speech:", "Type the speech here...")

# Button to analyze and show results
if st.button('Analyze'):
    if speech_input:
        # Analyze the speech sentiment
        speech_sentiment = analyze_sentiment(speech_input)
        
        # Fetch public comments from Reddit based on the speech (automatically fetches reactions)
        comments = asyncio.run(fetch_comments(speech_input))
        
        if comments:
            # Analyze the sentiment of the fetched public reactions
            public_sentiments = [analyze_sentiment(comment) for comment in comments]

            # Save data to Google Sheets (Now using the updated function)
            save_to_google_sheets(speech_input, speech_sentiment, public_sentiments)

            # Display the results
            st.subheader("Speech Sentiment:")
            st.write(speech_sentiment)

            st.subheader("Public Reactions Sentiment:")
            st.write(public_sentiments)

            # Visualization of sentiment distribution (Bar Chart)
            st.subheader("Sentiment Distribution of Public Reactions")
            chart_data = pd.DataFrame({
                'Sentiment': ['Positive', 'Negative', 'Neutral'],
                'Count': [public_sentiments.count('positive'), public_sentiments.count('negative'), public_sentiments.count('neutral')]
            })
            st.bar_chart(chart_data.set_index('Sentiment'))

            # Confirmation of data saved
            st.write("Data successfully saved to Google Sheets!")
        else:
            st.error("No public comments found for the given speech.")
    else:
        st.error("Please enter a speech.")



