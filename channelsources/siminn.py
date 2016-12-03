import re
import datetime
import json

import requests

from channelsource import ChannelSource, USER_AGENT

SIMINN_URL = 'https://desktop.tv.siminn.is'
OREO_URL = SIMINN_URL + "/oreo-api"

class SiminnChannels(ChannelSource):

    def __init__(self, device_id):
        self._device_id = device_id
        self._renew_token()

        oreo_json = json.loads(self._get(SIMINN_URL + "/oreo-api/"))
        customer_url = OREO_URL + "/" + oreo_json['links']['customer']
        customer_json = json.loads(self._get(customer_url))
        channel_url = customer_json['links']['channels']
        self._channels = { x['name']: x for x in json.loads(self._get(OREO_URL + "/" + channel_url))}
        self.get_channel_playlist('RUV2')

    def _renew_token(self):
        request = requests.post(
            SIMINN_URL + '/oreo-api/auth',
            data={
                'app_version': 108,
                'device_id': self._device_id,
                'platform':'android',
            },
            headers={
                'User-Agent': USER_AGENT
            }
        )
        try:
            self._access_token = request.headers['authorization']
        except KeyError:
            raise Exception("Invalid device id")

    def channels(self):
        return self._channels.iterkeys()

    def _get(self, url):
        if not self._access_token:
            self._renew_token()
        headers = {'Authorization': self._access_token, 'User-Agent': USER_AGENT}
        request = requests.get(url,
                               headers=headers
                               )
        return request.content

    def _ticket_url(self, channelname):
        ticket_url = OREO_URL + "/" + self._channels[channelname]['links']['ticket']
        return json.loads(self._get(ticket_url))['ticket']

    def get_channel_playlist(self, name):
        ticket_url = self._ticket_url(name)
        playlist = self._get(ticket_url)
        relative_path = "/".join(ticket_url.split("/")[:-1])
        playlist = re.sub(r"(\d\d).m3u8", relative_path + r"/\1.m3u8",playlist)
        return playlist

    def preprocess_video_playlist(self, playlist, channel):
        ticket_url = self._ticket_url(channel)
        relative_path = "/".join(ticket_url.split("/")[:-1])
        playlist = re.sub(r"(.+\.ts)", relative_path + r"/\1",playlist)
        return playlist
