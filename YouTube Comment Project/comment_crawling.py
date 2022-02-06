from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import json

class Youtube_Comment:
    def __init__(self, YOUTUBE_API_KEY, YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION) -> None:
        self.YOUTUBE_API_KEY = YOUTUBE_API_KEY
        self.YOUTUBE_API_SERVICE_NAME = YOUTUBE_API_SERVICE_NAME
        self.YOUTUBE_API_VERSION = YOUTUBE_API_VERSION

        self.youtube = build(self.YOUTUBE_API_SERVICE_NAME, self.YOUTUBE_API_VERSION, developerKey=self.YOUTUBE_API_KEY)

    '''
        - getting search keyword result
        - parameter: search_word, max_results, order, part
        - return: video_info_list
    '''
    def get_search_result(self, search_word, max_results=5, order='relevance', part='snippet', jsonify=False):

        # 검색 결과 response 딕셔너리 값 받아옴
        search_response = self.youtube.search().list(
            q = search_word,
            order = order,
            maxResults = max_results,
            part = part
        ).execute()

        # video_info_dict 개별 영상 정보 담는 곳
        video_info_list = []
        search_response_items = search_response['items']

        for item in search_response_items:
            video_info_dict = {}
            # video_id
            item_id = item['id']
            if 'videoId' in item_id:
                video_info_dict['videoId'] = item_id['videoId']
            else:
                video_info_dict['videoId'] = 'None'

            # upload date & title
            item_snippet = item['snippet']
            video_info_dict['uploadDate'] = item_snippet['publishedAt']
            video_info_dict['title'] = item_snippet['title']

            video_info_list.append(video_info_dict)

        # json file 생성
        if jsonify == True:
            with open(f'{search_word}.json', 'w', encoding='utf-8') as make_file:
                json.dump(video_info_list, make_file, ensure_ascii=False, indent='\t')

        return video_info_list


if __name__ == '__main__':
    YOUTUBE_API_KEY = 'AIzaSyBw_a4y-3pDJSPpHRX6CdbaCudxuWWGe_A'
    YOUTUBE_API_SERVICE_NAME = 'youtube'
    YOUTUBE_API_VERSION = 'v3'

    youtube = Youtube_Comment(YOUTUBE_API_KEY, YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION)

    # test for get_search_result
    res = youtube.get_search_result('정찬성', max_results=10)