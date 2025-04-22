import streamlit as st
import asyncio
import pandas as pd
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from textblob import TextBlob
import praw

# Access Google credentials from Streamlit secrets (TOML format)
google_credentials = json.loads(st.secrets["google_credentials"]["json"])

# Define the Google Sheets API scopes
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets',
          "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

# Authenticate using the credentials from Streamlit Secrets
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_credentials, SCOPES)

# Authorize the credentials with gspread
client = gspread.authorize(creds)

# Open the Google Sheet by URL (replace with your sheet's URL)
sheet_url = 'https://docs.google.com/spreadsheets/d/13Uwvi9FVy1Cv-NLYdwauvb1DjaSOTRZVCBz1OxyBupc/edit?gid=0'  # Replace with your Google Sheets URL
sheet = client.open_by_url(sheet_url)

# Access the first worksheet
worksheet = sheet.sheet1  # Access the first sheet in the spreadsheet

# Fetch Reddit credentials from Streamlit secrets
reddit_client_id = st.secrets["reddit"]["client_id"]
reddit_client_secret = st.secrets["reddit"]["client_secret"]
reddit_user_agent = st.secrets["reddit"]["user_agent"]

# Set up Reddit API credentials securely
reddit = praw.Reddit(client_id=reddit_client_id, 
                     client_secret=reddit_client_secret, 
                     user_agent=reddit_user_agent)

# Function for sentiment analysis using TextBlob
def analyze_sentiment(text):
    # Use TextBlob for sentiment analysis
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity  # Returns value between -1 (negative) and 1 (positive)

    if sentiment > 0:
        return 'positive'
    elif sentiment < 0:
        return 'negative'
    else:
        return 'neutral'

# Function to fetch comments from Reddit based on speech keywords
async def fetch_comments(speech_keywords):
    comments = []
    # Searching Reddit for posts related to speech keywords
    try:
        for submission in reddit.subreddit('all').search(speech_keywords, limit=100):
            submission.comments.replace_more(limit=0)  # Avoid 'MoreComments' object
            for comment in submission.comments:
                comments.append(comment.body)
    except Exception as e:
        st.error(f"Error fetching comments: {e}")
    
    return comments

# Function to save sentiment data to Google Sheets
def save_to_google_sheets(speech, speech_sentiment, public_sentiments):
    timestamp = pd.to_datetime('now').strftime('%Y-%m-%d %H:%M:%S')

    # Initialize the counts for the public reactions
    positive_count = public_sentiments.count('positive')
    negative_count = public_sentiments.count('negative')
    neutral_count = public_sentiments.count('neutral')

    # Save speech sentiment and counts in one row (speech, speech sentiment, counts, timestamp)
    worksheet.append_row([speech, speech_sentiment, timestamp, positive_count, negative_count, neutral_count])

    # Save each public sentiment in a new row below the speech row
    for sentiment in public_sentiments:
        worksheet.append_row([speech, sentiment, timestamp, '', '', ''])  # Blank counts for public sentiments

    print("Data successfully saved to Google Sheets!")

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

            # Save data to Google Sheets
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

