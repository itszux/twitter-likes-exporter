import datetime
import json
import os
import re
import requests
from pathlib import Path

class ParseTweetsJSONtoHTML():
    def __init__(self):
        self._output_html_directory = None
        self._tweets_as_json = None

        with open("config.json") as json_data_file:
            config_data = json.load(json_data_file)
            self.output_json_file_path = config_data.get('OUTPUT_JSON_FILE_PATH')
            self.download_images = config_data.get('DOWNLOAD_IMAGES')
            self.tweets_per_page = config_data.get('TWEETS_PER_PAGE')
            self.auto_open = config_data.get('AUTO_OPEN_HTML_FILE')

    def write_tweets_to_html(self):
        all_tweets = []
        for tweet_data in self.tweets_as_json:
                tweet_html = self.create_tweet_html(tweet_data)
                all_tweets.append(tweet_html)
        
        with open('tweet_likes_html/liked_tweets.js', 'w') as f:
            f.write(f'var tweets = {all_tweets}')

        main_html = f'''
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1.0, maximum-scale=1.0" />
            <title>Liked Tweets Export</title>
            <link rel="stylesheet" href="source/styles.css">
            <script src="source/masonry.pkgd.min.js"></script>
            <script src="source/main.js" defer></script>
            <script src="source/imagesloaded.pkgd.min.js"></script>
            <script src="source/BigPicture.min.js"></script>
            <script src="source/twemoji.min.js"></script>
            <script src="liked_tweets.js"></script>
            <script>
                var fitWidth = false;
                var tweetsPerPage = {self.tweets_per_page}
            </script>
        </head>
        <body>
            <h1>Liked Tweets</h1>
            <div id="tweet_list"></div>
            <ul class="pagination">
                <li><a id="first-page">First</a></li>
                <li><a id="prev-page">Previous</a></li>
                <li><span id="current-page">Page 1</span></li>
                <li><a id="next-page">Next</a></li>
                <li><a id="last-page">Last</a></li>
            </ul>
        </body>
        </html>'''
        with open(self.output_index_path, 'w', encoding='utf-8') as output_html:
            output_html.write(main_html)

    def create_tweet_html(self, tweet_data):
        parsed_datetime = datetime.datetime.strptime(tweet_data["tweet_info"]['tweet_created_at'], "%a %b %d %H:%M:%S +0000 %Y")
        # this removes the last shortened url from tweet_content (which is the tweet shortened url)
        tweet_content = re.sub(r'(https://t\.co/[A-Za-z0-9]+)(?![\s\S]*https://t\.co/[A-Za-z0-9]+)', '', tweet_data['tweet_info']['tweet_content'])
        entities = tweet_data["tweet_info"]["entities"]
        numbers = ["zero", "one", "two", "three", "four"]
        all_media = ''
        
        if self.download_images:
            user_image_src = f'images/avatars/{tweet_data["user_info"]["user_id"]}.jpg'
            full_path = Path(self.output_html_directory, user_image_src)
            self.save_remote_image(tweet_data["user_info"]["user_avatar_url"], full_path)
        else:
            user_image_src = tweet_data["user_info"]["user_avatar_url"]
        
        if tweet_data["tweet_info"]["tweet_media_urls"]:
            for media in tweet_data["tweet_info"]["tweet_media_urls"]:
                media_url, media_type, media_thumb = media['url'], media['type'], media['url_small']
                video_duration = media['video_duration_millis'] if media_type == 'video' else None
                
                media_name = media_url.split('?')[0].split("/")[-1] if media_type == "video" else media_url.split("/")[-1]
                media_thumb_name = media_thumb.split('?')[0].split('/')[-1]+'.jpg'
                if self.download_images:
                    media_path = f'images/tweets_media/{media_name}'
                    media_full_path = Path(self.output_html_directory, media_path)
                    self.save_remote_image(media_url, media_full_path)

                    media_thumb_path = f'images/tweets_thumbnails/{media_thumb_name}'
                    media_thumb_full_path = Path(self.output_html_directory, media_thumb_path)
                    self.save_remote_image(media_thumb, media_thumb_full_path)

                    if media_type == 'photo':
                        all_media += f"<div class='tweet_image' onclick=\"BigPicture({{el: this, imgSrc: '{media_path}'}})\"><img loading='lazy' src='{media_thumb_path}'></div>"
                    else:
                        all_media += f'<div class="tweet_image" onclick="BigPicture({{el: this, vidSrc: \'{media_path}\'}})">{self.get_svg("play")}<div class="video-duration">{self.convert_video_duration(video_duration) if media_type != "animated_gif" else "GIF"}</div><img loading="lazy" src="{media_thumb_path}"></div>'
                else:
                    user_image_path = media_thumb
                    if media_type == 'photo':
                        all_media += f"<div class='tweet_image' onclick=\"BigPicture({{el: this, imgSrc: '{media_url}'}})\"><img loading='lazy' src='{user_image_path}'></div>"
                    else:
                        all_media += f'<div class="tweet_image" onclick="BigPicture({{el: this, vidSrc: \'{media_url}\'}})">{self.get_svg("play")}<div class="video-duration">{self.convert_video_duration(video_duration) if media_type != "animated_gif" else "GIF"}</div><img loading="lazy" src="{user_image_path}"></div>'


        new_tweet_content = ''
        current_index = 0    
        # Sorting entities by start index to handle all occurrences
        sorted_entities = sorted(
            [(entity['indices'][0], entity['indices'][1], entity_type, entity) for entity_type, entity_list in entities.items() for entity in entity_list],
            key=lambda x: x[0]
        )

        for start_index, end_index, entity_type, entity in sorted_entities:
            if current_index < start_index:
                new_tweet_content += tweet_content[current_index:start_index]
            
            if entity_type == 'hashtags':
                new_tweet_content += f'<span class="hashtag"><a href="https://twitter.com/hashtag/{entity["text"]}?src=hashtag_click" target="_blank">#{entity["text"]}</a></span>'
            elif entity_type == 'urls':
                new_tweet_content += f'<span class="link"><a href="{entity["expanded_url"]}" target="_blank">{entity["display_url"]}</a></span>'
            elif entity_type == 'user_mentions':
                new_tweet_content += f'<span class="mention"><a href="https://twitter.com/{entity["screen_name"]}" target="_blank">@{entity["screen_name"]}</a></span>'
            
            current_index = end_index
        
        if current_index < len(tweet_content):
            new_tweet_content += tweet_content[current_index:]

        # Escaping double and single quotes
        if tweet_data["tweet_info"]["post_description"]:
            title = self.parse_text_for_html(tweet_data["tweet_info"]["post_description"].replace('"', '&quot;').replace("\\'", "\'"))
        else:
            title = ""

        tweet_skeleton = f'''
            <div class="tweet_wrapper">
                <div class="first-column">
                    <div class="tweet_author_image">
                        <img loading="lazy" src="{user_image_src}">
                    </div>
                </div>
                <div class="second-column">
                    <div class="tweet_author_wrapper">
                        <div class="author_context">
                            <div class="tweet_author_name">
                                <a href="https://www.twitter.com/{tweet_data["user_info"]['user_handle']}/" target="_blank">
                                    {self.parse_text_for_html(tweet_data["user_info"]['user_name'])}
                                </a>
                            </div>
                            {self.get_svg('verified', "verified" if tweet_data['user_info']['user_blue_verified'] else "not-verified")}
                            <div class="tweet_author_handle">
                                <a href="https://www.twitter.com/{tweet_data["user_info"]['user_handle']}/" target="_blank">
                                    @{self.parse_text_for_html(tweet_data["user_info"]['user_handle'])}
                                </a>
                            </div>
                            <div class="tweet_created_at"> · {self.format_time(parsed_datetime)}</div>
                        </div>
                    </div>
                    <div class="tweet_content">{self.parse_text_for_html(new_tweet_content)}</div>
                    <div class="tweet_images_wrapper {numbers[len(tweet_data["tweet_info"]["tweet_media_urls"])]}" 
                        title="{title}">
                        {all_media}
                    </div>
                    <div class="reply-to {'true' if tweet_data['tweet_info']['is_reply'] else 'false'}">
                        <a href="{tweet_data['tweet_info']['reply_url']}" target="_blank">
                            {self.get_svg('reply')}
                            Reply To...
                        </a>
                    </div>
                    <div class="quote {'true' if tweet_data['tweet_info']['is_quote'] else 'false'}">
                        <a href="{tweet_data['tweet_info']['quoted_url']}" target="_blank">
                            {self.get_svg('quote')}
                            Quoted Tweet
                        </a>
                    </div>
                    <div class="bottom-bar">
                        <div class="comments">
                            {self.get_svg('reply', 'bottom-bar-icon')}
                            {self.format_number(tweet_data['tweet_info']['tweet_reply_count'])}
                        </div>
                        <div class="retweets {'true' if tweet_data['interactions']['retweeted'] else ''}">
                            {self.get_svg('quote', 'bottom-bar-icon')}
                            {self.format_number(tweet_data['tweet_info']['tweet_retweet_quote_count'])}
                        </div>
                        <div class="likes {'true' if tweet_data['interactions']['favorited'] else ''}">
                            {self.get_svg('favorited', 'bottom-bar-icon')
                                if tweet_data['interactions']['favorited'] else
                            self.get_svg('not-favorited', 'bottom-bar-icon')}
                            {self.format_number(tweet_data['tweet_info']['tweet_favorite_count'])}
                        </div>
                        <div class="views">
                            {self.get_svg('views', 'bottom-bar-icon')}
                            {self.format_number(tweet_data['tweet_info']['tweet_views'])}
                        </div>
                        <div class="bookmarks {'true' if tweet_data['interactions']['bookmarked'] else ''}">
                            {self.get_svg('bookmarked', 'bottom-bar-icon')
                                if tweet_data['interactions']['bookmarked'] else
                            self.get_svg('not-bookmarked', 'bottom-bar-icon')}
                            {self.format_number(tweet_data['tweet_info']['tweet_bookmark_count'])}
                        </div>
                        <div class="original-tweet">
                            <a href="https://www.twitter.com/{tweet_data["user_info"]['user_handle']}/status/{tweet_data["tweet_info"]['tweet_id']}/" target="_blank">
                                {self.get_svg('original', 'bottom-bar-icon')}
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        '''
        return tweet_skeleton

    def save_remote_image(self, remote_url, local_path):
        if os.path.exists(local_path):
            return
        print(f"Downloading image {remote_url}...")
        img_data = requests.get(remote_url).content
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with local_path.open('wb') as handler:
            handler.write(img_data)

    def format_number(self, number):
        if number:
            if 1000 <= int(number) < 1_000_000:
                return '{:.1f}K'.format(int(number) / 1000)
            elif int(number) >= 1_000_000:
                return '{:.1f}M'.format(int(number) / 1_000_000)
            else:
                return str(number)
        return ''

    def convert_video_duration(self, ms):
        seconds = ms // 1000
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

    def format_time(self, parsed_datetime):
        current_datetime = datetime.datetime.utcnow()
        time_difference = current_datetime - parsed_datetime
    
        if time_difference.total_seconds() < 60:
            return f'{int(time_difference.total_seconds())}s'
        elif time_difference.total_seconds() < 3600:
            return f'{int(time_difference.total_seconds() / 60)}m'
        elif time_difference.total_seconds() < 86400:
            return f'{int(time_difference.total_seconds() / 3600)}h'
        elif parsed_datetime.year == current_datetime.year:
            return parsed_datetime.strftime('%b %d')
        else:
            return parsed_datetime.strftime('%b %d, %Y')

    def get_svg(self, type, svg_class=''):
        if type == 'play':
            return '''<svg viewBox="0 0 60 61" class="play-button"><g>
            <circle cx="30" cy="30.4219" fill="#333333" opacity="0.6" r="30"></circle>
            <path d="M22.2275 17.1971V43.6465L43.0304 30.4218L22.2275 17.1971Z" fill="white">
            </path></g></svg>'''
        elif type == "verified":
            return f'''<svg viewBox="0 0 22 22" class="{svg_class}"><g>
            <path d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246
            .223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75
            -1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647
            1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.608-.223-1.267
            -.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.688-.13.633
            -.08 1.29.144 1.896-.587.274-1.087.705-1.443 1.245-.356.54-.555 1.17-.574 1.817
            .02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.606-.274 1.263-.144
            1.896.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084
            1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276
            -.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22
            -.447 1.68-.907.46-.46.776-1.044.908-1.681s.075-1.299-.165-1.903c.586-.274 1.084
            -.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302
            2.072 2.072 4.4-4.794 1.347 1.246z"></path></g></svg>'''
        elif type == "reply":
            return f'''<svg viewBox="0 0 24 24" class={svg_class}><g>
            <path d="M1.751 10c0-4.42 3.584-8 8.005-8 h4.366c4.49 0 8.129 3.64 8.129 8.13 0 
            2.96-1.607 5.68-4.196 7.11 l-8.054 4.46v-3.69h-.067
            c-4.49.1-8.183-3.51-8.183-8.01zm8.005-6 c-3.317 0-6.005 2.69-6.005 6 0 3.37 2.77 
            6.08 6.138 6.01l.351-.01 h1.761v2.3l5.087-2.81c1.951-1.08 3.163-3.13
            3.163-5.36 0-3.39-2.744-6.13-6.129-6.13H9.756z"></path></g></svg>'''
        elif type == "quote":
            return f'''<svg viewBox="0 0 24 24" class={svg_class}><g>
            <path d="M4.5 3.88l4.432 4.14-1.364 1.46L5.5 7.55V16c0 1.1.896 2 2 
            2H13v2H7.5c-2.209 0-4-1.79-4-4V7.55L1.432 9.48.068 8.02 4.5 3.88zM16.5 
            6H11V4h5.5c2.209 0 4 1.79 4 4v8.45l2.068-1.93 1.364 1.46-4.432 4.14-4.432-4.14 
            1.364-1.46 2.068 1.93V8c0-1.1-.896-2-2-2z"></path></g></svg>'''
        elif type == "views":
            return f'''<svg viewBox="0 0 24 24" class="{svg_class}"><g>
            <path d="M8.75 21V3h2v18h-2zM18 21V8.5h2V21h-2zM4 21l.004-10h2L6 21H4zm9.248 
            0v-7h2v7h-2z"></path></g></svg>'''
        elif type == "original":
            return f'''<svg viewBox="0 0 24 24" class="{svg_class}"><g>
            <path d="M12 2.59l5.7 5.7-1.41 1.42L13 6.41V16h-2V6.41l-3.3 3.3-1.41-1.42L12 
            2.59zM21 15l-.02 3.51c0 1.38-1.12 2.49-2.5 2.49H5.5C4.11 21 3 19.88 3 18.5V15h2v3.5c0 
            .28.22.5.5.5h12.98c.28 0 .5-.22.5-.5L19 15h2z"></path></g></svg>
            '''
        elif type == "favorited":
            return f'''<svg viewBox="0 0 24 24" class="{svg_class}"><g>
            <path d="M20.884 13.19c-1.351 2.48-4.001 5.12-8.379 7.67l-.503.3-.504-.3c-4.379-2.55
            -7.029-5.19-8.382-7.67-1.36-2.5-1.41-4.86-.514-6.67.887-1.79 2.647-2.91 4.601-3.01 1.651
            -.09 3.368.56 4.798 2.01 1.429-1.45 3.146-2.1 4.796-2.01 1.954.1 3.714 1.22 4.601 3.01.896 
            1.81.846 4.17-.514 6.67z"></path></g></svg>'''
        elif type == "not-favorited":
            return f'''<svg viewBox="0 0 24 24" class="{svg_class}"><g>
            <path d="M16.697 5.5c-1.222-.06-2.679.51-3.89 2.16l-.805 1.09-.806-1.09C9.984 6.01 8.526 
            5.44 7.304 5.5c-1.243.07-2.349.78-2.91 1.91-.552 1.12-.633 2.78.479 4.82 1.074 1.97 3.257 
            4.27 7.129 6.61 3.87-2.34 6.052-4.64 7.126-6.61 1.111-2.04 1.03-3.7.477-4.82-.561-1.13
            -1.666-1.84-2.908-1.91zm4.187 7.69c-1.351 2.48-4.001 5.12-8.379 7.67l-.503.3-.504-.3c
            -4.379-2.55-7.029-5.19-8.382-7.67-1.36-2.5-1.41-4.86-.514-6.67.887-1.79 2.647-2.91 4.601
            -3.01 1.651-.09 3.368.56 4.798 2.01 1.429-1.45 3.146-2.1 4.796-2.01 1.954.1 3.714 1.22 
            4.601 3.01.896 1.81.846 4.17-.514 6.67z"></path></g></svg>'''
        elif type == "bookmarked":
            return f'''<svg viewBox="0 0 24 24" class="{svg_class}"><g>
            <path d="M4 4.5C4 3.12 5.119 2 6.5 2h11C18.881 2 20 3.12 20 4.5v18.44l-8-5.71-8 
            5.71V4.5z"></path></g></svg>
            '''
        elif type == "not-bookmarked":
            return f'''<svg viewBox="0 0 24 24" class="{svg_class}"><g><path d="M4 4.5C4 3.12 5.119 
            2 6.5 2h11C18.881 2 20 3.12 20 4.5v18.44l-8-5.71-8 5.71V4.5zM6.5 4c-.276 0-.5.22
            -.5.5v14.56l6-4.29 6 4.29V4.5c0-.28-.224-.5-.5-.5h-11z"></path></g></svg>
            '''

    def parse_text_for_html(self,input_text):
        return input_text.encode('ascii', 'xmlcharrefreplace').decode().replace('\n', '<br>')

    @property
    def output_index_path(self):
        return Path(self.output_html_directory, "index.html")

    @property
    def output_html_directory(self):
        if not self._output_html_directory:
            script_dir = os.path.dirname(__file__)
            self._output_html_directory = Path(script_dir, "tweet_likes_html")
        return self._output_html_directory

    @property
    def tweets_as_json(self):
        if not self._tweets_as_json:
            with open(self.output_json_file_path, 'rb') as json_file:
                self._tweets_as_json = json.load(json_file)

        return self._tweets_as_json

if __name__ == "__main__":
    parser = ParseTweetsJSONtoHTML()
    print(f"Saving tweets to {parser.output_index_path}...")
    parser.write_tweets_to_html()
    print(f"Done. Output file located at {parser.output_index_path}")
    if parser.auto_open:
        os.startfile(parser.output_index_path)