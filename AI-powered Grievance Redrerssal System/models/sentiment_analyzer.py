import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Download VADER lexicon on first run
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    print("Downloading VADER lexicon...")
    nltk.download('vader_lexicon', quiet=True)

class SentimentAnalyzer:
    """Analyze sentiment of complaints using VADER"""
    
    def __init__(self):
        print("Loading VADER sentiment analyzer...")
        self.analyzer = SentimentIntensityAnalyzer()
        print("Sentiment analyzer loaded!")
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment of complaint text
        
        Args:
            text: Complaint text
            
        Returns:
            Sentiment label: 'Urgent/Frustrated', 'Angry', 'Neutral', 'Satisfied'
        """
        try:
            scores = self.analyzer.polarity_scores(text)
            compound_score = scores['compound']
            
            # Determine sentiment based on compound score
            if compound_score <= -0.5:
                return 'Angry'
            elif compound_score <= -0.2:
                return 'Frustrated'
            elif compound_score >= 0.2:
                return 'Satisfied'
            else:
                return 'Neutral'
        
        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")
            return 'Neutral'
    
    def get_sentiment_score(self, text):
        """
        Get detailed sentiment scores
        
        Args:
            text: Complaint text
            
        Returns:
            Dictionary with positive, negative, neutral, and compound scores
        """
        try:
            return self.analyzer.polarity_scores(text)
        except Exception as e:
            print(f"Error getting sentiment scores: {str(e)}")
            return {'neg': 0, 'neu': 1, 'pos': 0, 'compound': 0}

# Global instance
sentiment_analyzer = None

def get_sentiment_analyzer():
    """Get or create sentiment analyzer instance"""
    global sentiment_analyzer
    if sentiment_analyzer is None:
        sentiment_analyzer = SentimentAnalyzer()
    return sentiment_analyzer
