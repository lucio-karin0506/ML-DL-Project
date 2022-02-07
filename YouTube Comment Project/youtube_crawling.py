from googleapiclient.discovery import build

import json
import re
import pandas as pd

class Youtube:
    def __init__(self, YOUTUBE_API_KEY, YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION) -> None:
        self.YOUTUBE_API_KEY = YOUTUBE_API_KEY
        self.YOUTUBE_API_SERVICE_NAME = YOUTUBE_API_SERVICE_NAME
        self.YOUTUBE_API_VERSION = YOUTUBE_API_VERSION

        self.youtube = build(
                             self.YOUTUBE_API_SERVICE_NAME, 
                             self.YOUTUBE_API_VERSION, 
                             developerKey=self.YOUTUBE_API_KEY
                            )

    '''
        - getting search keyword result
        - parameter: search_word, max_results, order, part, jsonify
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
            with open(f'datasets/{search_word}.json', 'w', encoding='utf-8') as make_file:
                json.dump(video_info_list, make_file, ensure_ascii=False, indent='\t')

        return video_info_list

    '''
        - getting video info
        - parameter: video_info_list, part, to_csv
        - return: video info dataframe
    '''
    def get_video_info(self, video_info_list, part='snippet, contentDetails, statistics', to_csv=False):

        titles = [] # 동영상 제목
        ids = [] # 동영상 id
        dates = [] # 동영상 업로드 날짜
        category_ids = [] # 카테고리 id
        views = [] # 조회 수
        likes = [] # 좋아요 수
        comments = [] # 댓글 수
        duration_hour = [] # 재생길이 (시)
        duration_min = [] # 재생길이 (분)
        duration_sec = [] # 재생길이 (초)

        for video_info in video_info_list:

            video_id = video_info['videoId']

            if video_id != None:
                # youtube 객체에서 비디오 정보 리스트 받아옴
                response = self.youtube.videos().list(
                    id = video_id,
                    part = part
                ).execute()

                # 동영상 정보 없을 경우 '-'로 입력
                if response['items'] == []:
                    titles.append('-')
                    ids.append('-')
                    dates.append('-')
                    category_ids.append('-')
                    views.append('-')
                    likes.append('-')
                    comments.append('-')
                    duration_hour.append('-')
                    duration_min.append('-')
                    duration_sec.append('-')

                else:
                    items = response['items'][0]
                    titles.append(items['snippet']['title'])
                    ids.append(video_id)
                    dates.append(items['snippet']['publishedAt'].split('T')[0])
                    category_ids.append(items['snippet']['categoryId'])
                    views.append(items['statistics']['viewCount'])
                    likes.append(items['statistics']['likeCount'])
                    comments.append(items['statistics']['commentCount'])

                    duration = re.findall(r'\d+', items['contentDetails']['duration'])
                    if len(duration) == 3:
                        duration_hour.append(duration[0])
                        duration_min.append(duration[1])
                        duration_sec.append(duration[2])
                    elif len(duration) == 2:
                        duration_hour.append('-')
                        duration_min.append(duration[0])
                        duration_sec.append(duration[1])
                    else:
                        duration_hour.append('-')
                        duration_min.append('-')
                        duration_sec.append(duration[0])

        video_info_df = pd.DataFrame(
                [
                titles, ids, dates, category_ids, views, likes, comments,
                duration_hour, duration_min, duration_sec
            ]
        ).T

        video_info_df.columns=['title', 'id', 'upload_date', 'category_id', 'view', 'like', 'comment',
                               'hour', 'min', 'sec']

        if to_csv == True:
            video_info_df.to_csv('datasets/video_info.csv', encoding='utf-8-sig')

        return video_info_df

    '''
        - getting comment info
        - parameter: video_id, order, part, max_results, to_csv
        - return: comment dataframe
    '''
    def get_video_comment(self, video_id, part='snippet, replies', order='relevance', max_results=5, to_csv=False):

        comments = []

        # youtube api를 이용하여 댓글 response 받아옴
        comment_response = self.youtube.commentThreads().list(
            videoId = video_id,
            order = order,
            part = part,
            maxResults = max_results # 댓글은 한번에 최대 100개씩만 요청 가능
        ).execute()

        # comment_response 내용 전체를 순회할 때 까지
        while comment_response:

            # 댓글 저장
            for item in comment_response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append(
                    [
                        comment['textDisplay'],
                        comment['authorDisplayName'],
                        comment['publishedAt'],
                        comment['likeCount'],
                        'main-comment'
                    ]
                )

            # 댓글에 대한 답글 수집
            if item['snippet']['totalReplyCount'] > 0:
                for reply_item in item['replies']['comments']:
                    reply = reply_item['snippet']
                    comments.append(
                        [
                            reply['textDisplay'],
                            reply['authorDisplayName'],
                            reply['publishedAt'],
                            reply['likeCount'],
                            'reply-comment'
                        ]
                    )

            # 다음 페이지에 가져올 댓글 남을 경우, nextPageToken으로 API 재호출
            if 'nextPageToken' in comment_response:
                comment_response = self.youtube.commentThreads().list(
                    videoId = video_id,
                    order = order,
                    part = part,
                    pageToken = comment_response['nextPageToken'],
                    maxResults = max_results
                ).execute()

            else:
                break

        comment_df = pd.DataFrame(comments, columns=['comment', 'author', 'date', 'like', 'type'])

        if to_csv == True:
            comment_df.to_csv(f'datasets/{video_id}_comment_info.csv', encoding='utf-8-sig')

        return comment_df


if __name__ == '__main__':
    YOUTUBE_API_KEY = ''
    YOUTUBE_API_SERVICE_NAME = 'youtube'
    YOUTUBE_API_VERSION = 'v3'

    youtube = Youtube(YOUTUBE_API_KEY, YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION)

    # test for get_search_result
    # res = youtube.get_search_result('정찬성', max_results=10, jsonify=True)

    # test for get_video_info
    # video_info_df = youtube.get_video_info(res, to_csv=True)

    # test for get_video_comment
    comment_df = youtube.get_video_comment('hRPqJfo483c', max_results=20, to_csv=True)
    print(comment_df)