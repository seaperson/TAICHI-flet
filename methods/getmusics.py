import json
import re
import time
from dataclasses import dataclass, field
from hashlib import md5
from typing import Optional, Generator, List
from urllib.parse import quote

from utils import HTMLSession
import requests
from urllib.parse import urlparse


@dataclass
class DataSong:
    source: str  # 渠道
    photo_url: str  # 图片链接
    big_photo_url: str  # 大图链接
    music_name: str  # 歌曲名称
    singer_name: str  # 歌手名称
    music_url: Optional[str] = field(default=None)  # 音乐链接
    lyrics_url: Optional[str] = field(default=None)  # 歌词链接


class HIFINI:
    headers = {
        # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        # "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
        "referer": "https://www.hifini.com",
    }
    search_url = "https://www.hifini.com/search-{target}-{page}.htm"
    recommend_url = "https://www.hifini.com/"
    base_url = "https://www.hifini.com/"

    @classmethod
    def search_musics(cls, target, page=1) -> Generator[DataSong, None, None]:
        if not target:
            for music in cls.recommend_musics():
                yield music
        else:
            session = HTMLSession(cls.headers)
            quota_target = quote(target).replace("%", "_")
            url = cls.search_url.format(target=quota_target, page=page)
            res = session.post(url)
            if res.status_code != 200:
                yield False, res.text
            else:
                body = res.html.xpath('//div[@class="media-body"]/div/a')
                if body:
                    for a in body:
                        if a.absolute_links:
                            detail_url = a.absolute_links.pop()
                            detail = cls.get_detail_music(detail_url, session)
                            if not detail:
                                continue
                            else:
                                yield DataSong(**detail)

    @classmethod
    def recommend_musics(cls) -> List[Generator[DataSong, None, None]]:
        session = HTMLSession(cls.headers)
        res = session.get(cls.recommend_url)
        if res.status_code != 200:
            yield False, res.text
        else:
            body = res.html.xpath('//div[@class="media-body"]/div/a')
            if body:
                for a in body:
                    if a.absolute_links:
                        detail_url = a.absolute_links.pop()
                        detail = cls.get_detail_music(detail_url, session)
                        if not detail:
                            continue
                        else:
                            yield DataSong(**detail)

    @classmethod
    def get_detail_music(cls, url, session=None):
        if session is None:
            session = HTMLSession(cls.headers)
        result = {}
        res = session.get(url)
        aplayer = res.html.xpath('//div[@class="aplayer"]')
        if not aplayer:
            return result
        else:
            strr2 = res.text
            music_url = re.findall(" url: '(.*?)',", strr2, re.S)
            if not music_url:
                return result
            music_name = re.findall(" title: '(.*?)',", strr2, re.S)
            if not music_name:
                return result
            photo_url = re.findall(" pic: '(.*?)'", strr2, re.S)
            if not photo_url:
                return result
            singer_name = re.findall(" author:'(.*?)',", strr2, re.S)
            if not singer_name:
                return result
            result.update(
                {
                    "source": "hifini",
                    "music_url": cls.base_url + music_url[0],
                    "music_name": music_name[0],
                    "photo_url": photo_url[0],
                    "big_photo_url": photo_url[0],
                    "singer_name": singer_name[0],
                }
            )
            print(cls.base_url + music_url[0])
            return result

class MiGu:
    headers = {
        'Referer': 'https://m.music.migu.cn/',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Mobile Safari/537.36'
    }
    search_url = "http://pd.musicapp.migu.cn/MIGUM3.0/v1.0/content/search_all.do"
    recommend_url = "http://pd.musicapp.migu.cn/MIGUM3.0/v1.0/content/search_all.do"
    download_url = "https://app.pd.nf.migu.cn/MIGUM3.0/v1.0/content/sub/listenSong.do?channel=mx&copyrightId={copyrightId}&contentId={contentId}&toneFlag={toneFlag}&resourceType={resourceType}&userId=15548614588710179085069&netType=00"
    player_url = "https://freetyst.nf.migu.cn"


    @classmethod
    def search_musics(cls, target) -> Generator[DataSong, None, None]:
        if not target:
            for music in cls.recommend_musics():
                yield music
        else:
            t = time.time() * 10000
            params = {"_t": t, "type": "YQM", "text": target, "page": 1, "v": "beta"}
            tar_str = json.dumps(params)
            s = md5(tar_str.encode()).hexdigest()
            params["token"] = s
            session = HTMLSession(cls.headers)
            res = session.post(cls.search_url, data=params)
            if res.status_code != 200 or res.json()["code"] != 200:
                yield False, res.text
            else:
                for data in res.json()["data"]["list"]:
                    music_name = data["name"]
                    singer_name = data["artist"] and data["artist"][0]["name"]
                    music_id = data["id"]
                    music_url = cls.base_music_url.format(id=music_id)
                    photo_url = data["pic"].format(size=40)
                    big_photo_url = data["pic"].format(size=500)
                    yield DataSong(
                        photo_url, big_photo_url, music_name, singer_name, music_url
                    )

    @classmethod
    def recommend_musics(cls) -> List[Generator[DataSong, None, None]]:
        params = {
            'ua': 'Android_migu',
            'version': '5.0.1',
            'text': "周杰伦",
            'pageNo': 1,
            'pageSize': 10,
            'searchSwitch': '{"song":1,"album":0,"singer":0,"tagSong":0,"mvSong":0,"songlist":0,"bestShow":1}',
        }
        print(params)
        session = requests.Session()
        res = session.get(cls.recommend_url, headers=cls.headers, params=params)
        if res.status_code != 200 or res.json()["code"] != "000000":
            yield False, res.text
        else:
            for data in res.json()["songResultData"]["result"]:
                music_name = data["name"]
                singers = [s.get("name", "") for s in data.get("singers", [])]
                singer_name = "、".join(singers)
                _photo_url = (
                        data.get("imgItems",[])[0].get("img")
                        #or data["album"].get("pic")
                        #or "https://picsum.photos/{size}"
                )

                photo_url = _photo_url.format(size=40)
                big_photo_url = _photo_url.format(size=500)

                # for rate in sorted(data.get('rateFormats', []), key=lambda x: int(x['size']), reverse=True):
                #     if (int(rate['size']) == 0) or (not rate.get('formatType', '')) or (
                #     not rate.get('resourceType', '')): continue
                #     download_url = cls.download_url.format(
                #         copyrightId=data['copyrightId'],
                #         contentId=data['contentId'],
                #         toneFlag=rate['formatType'],
                #         resourceType=rate['resourceType']
                #     )
                #     break
                param = {
                    "copyrightId": data.get("copyrightId", ""),
                    "resourceType": 2
                }
                r = (
                    session.get(
                        "https://c.musicapp.migu.cn/MIGUM2.0/v1.0/content/resourceinfo.do",
                        params=param,
                    )
                    .json()
                    .get("resource", [])
                )
                rate_list = r[0].get("newRateFormats", [])
                last_rate = rate_list[len(rate_list) - 1]
                # click.echo(last_rate)
                android_url = last_rate.get("androidUrl", "")
                o = urlparse(android_url)
                download_url = "https://freetyst.nf.migu.cn" + o.path

                music_url = download_url
                # 歌词
                lyrics_url = data.get("lyricUrl", data.get("trcUrl", ""))
                print(music_url)
                yield DataSong(
                    "migu",photo_url, big_photo_url, music_name, singer_name, music_url, lyrics_url
                )

class LiuMingYe:
    headers = {
        # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        # "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
        "origin": "https://tools.liumingye.cn",
    }
    search_url = "https://test.quanjian.com.cn/m/api/search"
    recommend_url = "https://test.quanjian.com.cn/m/api/home/recommend"
    base_music_url = "https://test.quanjian.com.cn/m/api/link/id/{id}/quality/128"

    @classmethod
    def search_musics(cls, target) -> Generator[DataSong, None, None]:
        if not target:
            for music in cls.recommend_musics():
                yield music
        else:
            t = time.time() * 10000
            params = {"_t": t, "type": "YQM", "text": target, "page": 1, "v": "beta"}
            tar_str = json.dumps(params)
            s = md5(tar_str.encode()).hexdigest()
            params["token"] = s
            session = HTMLSession(cls.headers)
            res = session.post(cls.search_url, data=params)
            if res.status_code != 200 or res.json()["code"] != 200:
                yield False, res.text
            else:
                for data in res.json()["data"]["list"]:
                    music_name = data["name"]
                    singer_name = data["artist"] and data["artist"][0]["name"]
                    music_id = data["id"]
                    music_url = cls.base_music_url.format(id=music_id)
                    photo_url = data["pic"].format(size=40)
                    big_photo_url = data["pic"].format(size=500)
                    yield DataSong(
                        "liumingye",photo_url, big_photo_url, music_name, singer_name, music_url
                    )

    @classmethod
    def recommend_musics(cls) -> List[Generator[DataSong, None, None]]:
        t = int(time.time() * 1000)
        params = {"_t": t}
        tar_str = json.dumps(params)
        s = md5(tar_str.encode()).hexdigest()
        params["token"] = s
        session = HTMLSession(cls.headers)
        print(params)
        res = session.post(cls.recommend_url, params=params)
        if res.status_code != 200 or res.json()["code"] != 200:
            yield False, res.text
        else:
            for data in res.json()["data"]["recommendSong"]:
                music_name = data["name"]
                singer_name = data["artist"] and data["artist"][0]["name"]
                _photo_url = (
                    data.get("pic")
                    or data["album"].get("pic")
                    or "https://picsum.photos/{size}"
                )
                photo_url = _photo_url.format(size=40)
                big_photo_url = _photo_url.format(size=500)
                if "url" in data and data["url"]:
                    music_url = data["url"]
                else:
                    if "hash" in data and data["hash"]:
                        music_id = data["hash"]
                    elif "id" in data and data["id"]:
                        music_id = data["id"]
                    else:
                        continue
                    music_url = cls.base_music_url.format(id=music_id)
                yield DataSong(
                    "liumingye",photo_url, big_photo_url, music_name, singer_name, music_url
                )
