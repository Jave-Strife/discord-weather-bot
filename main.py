import json
from Weather import *

# APIの読み込み
with open("config.json", encoding ="utf-8") as f:
    config = json.load( f )

# APIのキーを変数に格納
OWM_KEY = config["OpenWeatherMap"]["key"]
WEBHOOK_URL = config["Discord"]["webhook"]
webhook_id = WEBHOOK_URL.split("/")[5]
webhook_token = WEBHOOK_URL.split("/")[6]

# 地名データの読み込み
with open("city_data.json", encoding ="utf-8") as f:

    # 地名データを配列に格納
    city_data = json.load( f )["city_data"]

# コマンド配列の生成
commands = ["current", "hourly", "daily"]

# 地名データの分だけ繰り返し
for i in range( len( city_data ) ):

    # コマンド配列の分だけ繰り返し
    for j in range( len( commands ) ):

        # 天気インスタンスを生成
        # OpenWeatherMapのAPIキー,Discordのwebhook_id,Discordのwebhook_token,地名,緯度,経度
        weather = Weather( OWM_KEY, webhook_id, webhook_token, city_data[i]["name"], city_data[i]["latitude"], city_data[i]["longitude"], commands[j] )

        # 天気情報をDiscordに投稿
        weather.post()