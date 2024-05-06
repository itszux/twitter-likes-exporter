import json
import requests

from tweet_parser import TweetParser

class TweetDownloader():

    def __init__(self):
        # Load in user specific data from config.json file
        with open("config.json") as json_data_file:
            config_data = json.load(json_data_file)
            self.twitter_user_id = config_data.get('USER_ID')
            self.header_authorization = config_data.get('HEADER_AUTHORIZATION')
            self.header_cookie = config_data.get('HEADER_COOKIES')
            self.header_csrf = config_data.get('HEADER_CSRF')
            self.output_json_file_path = config_data.get('OUTPUT_JSON_FILE_PATH')
        self.retrieved_likes = 0

    def retrieve_all_likes(self):
        all_tweets = []

        likes_page = self.retrieve_likes_page()
        page_cursor = self.get_cursor(likes_page)
        old_page_cursor = None
        current_page = 1

        while likes_page and page_cursor and page_cursor != old_page_cursor:
            print(f"Fetching likes page: {current_page} ({len(likes_page)})...")
            current_page += 1            
            for raw_tweet in likes_page:
                try:
                    tweet_parser = TweetParser(raw_tweet)
                    if tweet_parser.is_valid_tweet:
                        all_tweets.append(tweet_parser.tweet_as_json())
                except KeyError as e:
                    # TODO: We should have an option to dump such tweet structures.
                    pass # Ignore tweets that are not of interest to us.
            old_page_cursor = page_cursor
            likes_page = self.retrieve_likes_page(cursor=page_cursor)
            page_cursor = self.get_cursor(likes_page)

        self.retrieved_likes = len(all_tweets)
        with open(self.output_json_file_path, 'w') as f:
            f.write(json.dumps(all_tweets, indent=4))

    def retrieve_likes_page(self, cursor=None):
        likes_url = 'https://twitter.com/i/api/graphql/RaAkBb4XXis-atDL3rV-xw/Likes'
        variables_data_encoded = json.dumps(self.likes_request_variables_data(cursor=cursor))
        features_data_encoded = json.dumps(self.likes_request_features_data())
        response = requests.get(
            likes_url,
            params={"variables": variables_data_encoded, "features": features_data_encoded},
            headers=self.likes_request_headers()
        )
        return self.extract_likes_entries(response.json())

    def extract_likes_entries(self, raw_data):
        return raw_data['data']['user']['result']['timeline_v2']['timeline']['instructions'][0]['entries']

    def get_cursor(self, page_json):
        return page_json[-1]['content']['value']

    def likes_request_variables_data(self, cursor=None):
        variables_data = {
            "userId": self.twitter_user_id,
            "count": 100,
            "includePromotedContent": False,
            "withClientEventToken": False,
            "withBirdwatchNotes": False,
            "withVoice": True,
            "withV2Timeline": True
        }
        if cursor:
            variables_data["cursor"] = cursor
        return variables_data

    def likes_request_headers(self):
        return {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': self.header_authorization,
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
            'Cookie': self.header_cookie,
            'x-twitter-active-user': 'yes',
            'x-twitter-client-language': 'en',
            'x-csrf-token': self.header_csrf,
            'x-twitter-auth-type': 'OAuth2Session'
        }

    def likes_request_features_data(self):
        return {
            "rweb_tipjar_consumption_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "communities_web_enable_tweet_community_results_fetch": True,
            "c9s_tweet_anatomy_moderator_badge_enabled": True,
            "articles_preview_enabled": False,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": True,
            "tweet_awards_web_tipping_enabled": False,
            "creator_subscriptions_quote_tweet_preview_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "tweet_with_visibility_results_prefer_gql_media_interstitial_enabled": True,
            "rweb_video_timestamps_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_enhance_cards_enabled": False
        }

if __name__ == '__main__':
    downloader = TweetDownloader()
    print(f'Starting retrieval of likes for Twitter user {downloader.twitter_user_id}...')
    downloader.retrieve_all_likes()
    print(f'Done. {downloader.retrieved_likes} Likes JSON saved to: {downloader.output_json_file_path}')
