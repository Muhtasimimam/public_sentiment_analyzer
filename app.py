import streamlit as st
import asyncio
import pandas as pd
import gspread
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import json
import requests
from textblob import TextBlob
import praw

# Dummy function for sentiment analysis
def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity

    if sentiment > 0:
        return "positive"
    elif sentiment < 0:
        return "negative"
    else:
        return "neutral"

# Initialize PRAW for Reddit with provided credentials
def initialize_reddit():
    reddit = praw.Reddit(
        client_id="1RaMfs_A_fvRgbUoucCBcA",  # Replace with your Reddit client_id
        client_secret=""nou-mUwL8_qalRm5fghACv-AiLl5Uw",  # Replace with your Reddit client_secret
        user_agent="PublicSentimentAnalyzer"  # Replace with your Reddit user_agent
    )
    return reddit

async def fetch_comments(speech_keywords):
    reddit = initialize_reddit()
    subreddit = reddit.subreddit('all')  # You can replace 'all' with any specific subreddit
    comments = []

    # Search for posts based on the speech keywords
    for submission in subreddit.search(speech_keywords, limit=10):  # Increased the limit to 10
        submission.comments.replace_more(limit=0)  # Avoid loading 'More Comments'
        for comment in submission.comments.list():
            comments.append(comment.body)  # Collect comment bodies

    return comments

# Function to authenticate and connect to Google Sheets
def authenticate_google_sheets():
    url = "https://raw.githubusercontent.com/Muhtasimimam/public_sentiment_analyzer/master/sentimentanalysisapp-457520-74eff8b32d78.json"
    response = requests.get(url)
    credentials_dict = response.json()

    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )

    client = gspread.authorize(credentials)

    spreadsheet_id = "13Uwvi9FVy1Cv-NLYdwauvb1DjaSOTRZVCBz1OxyBupc"  # Replace with your actual sheet ID
    sheet = client.open_by_key(spreadsheet_id).sheet1
    return sheet

# Function to save data to Google Sheets
def save_to_google_sheets(speech, speech_sentiment, public_sentiments):
    sheet = authenticate_google_sheets()  # Authenticate and get the sheet
    sheet.append_row([speech, speech_sentiment, ', '.join(public_sentiments)])

# Streamlit UI for user input
st.title("Real-Time Sentiment Analysis and Visualization")

speech_input = st.text_area("Enter Speech:", "Type the speech here...")

if st.button('Analyze'):
    if speech_input:
        speech_sentiment = analyze_sentiment(speech_input)

        comments = asyncio.run(fetch_comments(speech_input))

        if comments:
            public_sentiments = [analyze_sentiment(comment) for comment in comments]

            # Save to Google Sheets
            save_to_google_sheets(speech_input, speech_sentiment, public_sentiments)

            st.subheader("Speech Sentiment:")
            st.write(speech_sentiment)

            st.subheader("Public Reactions Sentiment:")
            st.write(public_sentiments)

            st.subheader("Sentiment Distribution of Public Reactions")

            # Count the occurrences of each sentiment in public sentiments
            sentiment_counts = {
                'positive': public_sentiments.count('positive'),
                'negative': public_sentiments.count('negative'),
                'neutral': public_sentiments.count('neutral')
            }

            # Convert the sentiment_counts to a DataFrame
            chart_data = pd.DataFrame(list(sentiment_counts.items()), columns=['Sentiment', 'Count'])

            # Display the bar chart
            st.bar_chart(chart_data.set_index('Sentiment'))

            st.write("Data successfully saved to Google Sheets!")
        else:
            st.error("No public comments found for the given speech.")
    else:
        st.error("Please enter a speech.")

