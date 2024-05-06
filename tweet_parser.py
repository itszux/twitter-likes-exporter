class TweetParser():
    def __init__(self, raw_tweet_json):
        self.is_valid_tweet = True
        self.raw_tweet_json = raw_tweet_json
        self._media_urls = None

        if not raw_tweet_json["content"].get("itemContent", None):
            self.is_valid_tweet = False
            return

        self.key_data = raw_tweet_json["content"]["itemContent"]["tweet_results"]["result"]
        if not self.key_data.get("legacy", None):
            if not self.key_data.get('tweet', None):
                self.is_valid_tweet = False
            else:
                self.key_data = self.key_data['tweet']

    def tweet_as_json(self):
        return {
            "tweet_info": {
                "tweet_id": self.key_data["legacy"]["id_str"],
                "tweet_content": self.key_data["legacy"]["full_text"],
                "tweet_media_urls": self.media_urls,
                "entities": self.entities,
                "tweet_created_at": self.key_data["legacy"]["created_at"],
                "tweet_views": self.key_data["views"].get('count', None),
                "tweet_favorite_count": self.key_data["legacy"]["favorite_count"],
                "tweet_bookmark_count": self.key_data["legacy"]["bookmark_count"],
                "tweet_reply_count": self.key_data["legacy"]["reply_count"],
                "tweet_retweet_quote_count": self.key_data["legacy"]["quote_count"] + self.key_data["legacy"]["retweet_count"],
                "is_quote": self.key_data["legacy"]["is_quote_status"],
                "quoted_url": self.get_quoted,
                "is_reply": True if self.key_data["legacy"].get('in_reply_to_screen_name', False) else False,
                "reply_url":  self.get_reply,
                "nsfw": True if self.raw_tweet_json["content"]["itemContent"]["tweet_results"]["result"].get('mediaVisibilityResults', False) else False
            },
            "user_info": {
                "user_id": self.key_data["legacy"]["user_id_str"],
                "user_handle": self.user_data["legacy"]["screen_name"],
                "user_name": self.user_data["legacy"]["name"],
                "user_avatar_url": self.user_data["legacy"]["profile_image_url_https"],
                "user_blue_verified": self.user_data["is_blue_verified"],
            },
            "interactions": {
                "bookmarked": self.key_data["legacy"]["bookmarked"],
                "favorited": self.key_data["legacy"]["favorited"],
                "retweeted": self.key_data["legacy"]["retweeted"],
            }
        }

    @property
    def user_data(self):
        return self.key_data["core"]["user_results"]["result"]

    @property
    def get_quoted(self):
        if self.key_data["legacy"]["is_quote_status"]:
            return self.key_data["legacy"]["quoted_status_permalink"]['expanded']
        return None

    @property
    def get_reply(self):
        if self.key_data["legacy"].get("in_reply_to_screen_name", False):
            return f"https://twitter.com/{self.key_data['legacy']['in_reply_to_screen_name']}/status/{self.key_data['legacy']['in_reply_to_status_id_str']}/"
        return None

    @property
    def entities(self):
        all_entities = self.key_data["legacy"]["entities"]
        if all_entities.get('media', False):
            all_entities.pop('media')
        return all_entities

    @property
    def media_urls(self):
        if self._media_urls is None:
            self._media_urls = []
            media_entries = self.key_data["legacy"]["entities"].get("media", [])
            for entry in media_entries:
                if entry['type'] == 'photo':
                    url_split = entry['media_url_https'].split('.')
                    url_small = '.'.join(url_split[:-1]) + f"?format={url_split[-1]}&name=small"
                    info = {
                        "type": 'photo',
                        "url": entry['media_url_https'],
                        "url_small": url_small
                    }
                    self._media_urls.append(info)
                elif (entry['type'] == 'video') or (entry['type'] == 'animated_gif'):
                    url_split = entry['media_url_https'].split('.')
                    url_small = '.'.join(url_split[:-1]) + f"?format={url_split[-1]}&name=small"
                    info = {
                        "type": entry['type'],
                        "url": entry['video_info']['variants'][-1]['url'],
                        "url_small": url_small
                    }
                    if entry['type'] == 'video':
                        info['video_duration_millis'] = entry['video_info']['duration_millis']
                    self._media_urls.append(info)
        return self._media_urls