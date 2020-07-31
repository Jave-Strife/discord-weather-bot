import json
import random
import re
import string
import urllib
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from io import BytesIO
from pprint import pprint
from discord import Webhook, RequestsWebhookAdapter, Embed, File
from bs4 import BeautifulSoup

class Weather():

    def __init__( self, owm_key, webhook_id, webhook_token, location, command ):
        self.owm_key = owm_key
        self.webhook_id = webhook_id
        self.webhook_token = webhook_token
        self.location = location
        self.command = command


    def post( self ):

        # 緯度・経度を取得
        latlon = self.__get_latlon()

        # 緯度・経度を基に天気情報を取得
        weather_data = self.__get_weather_data( latlon[0], latlon[1] )[self.command]

        # グラフ用の配列を生成
        arr_graph = []

        # コマンド名に応じた処理
        if self.command == "current":

            embed_title = "の現在の天気"
            embed_color = self.__set_embed_color( weather_data["weather"][0]["icon"] )

        elif self.command == "hourly":

            embed_title = "の3時間毎の予報"
            embed_color = 0x7289DA

        elif self.command == "daily":

            embed_title = "の週間予報"
            embed_color = 0x7289DA

        # 初期設定
        embed = Embed(
            title = self.location + embed_title,
            description = "{0}現在".format( datetime.now().strftime("%Y/%m/%d %H:%M:%S") ),
            color = embed_color
        )

        '''
        # ヘッダーの追加
        embed.set_author(
            name ="Powered by OpenWeatherMap",
            url ="https://openweathermap.org/",
            icon_url ="https://upload.wikimedia.org/wikipedia/commons/1/15/OpenWeatherMap_logo.png"
        )
        '''

        # フッターの追加
        embed.set_footer(
            text ="Powered by OpenWeatherMap",
            icon_url ="https://upload.wikimedia.org/wikipedia/commons/1/15/OpenWeatherMap_logo.png"
        )

        # フィールドの追加
        # 現在の天気
        if self.command == "current":

            # サムネイル(天気アイコン)の追加(currentのみ)
            #w_icon_url = "https://openweathermap.org/img/w/{0}.png".format( weather_data["weather"][0]["icon"] )
            w_icon_url = "https://openweathermap.org/img/wn/{0}@2x.png".format( weather_data["weather"][0]["icon"] )
            embed.set_thumbnail(
                url = w_icon_url
            )

            # 天候
            embed.add_field(
                name =":newspaper:天候",
                value = weather_data["weather"][0]["description"],
                inline = False
            )

            # 気温
            embed.add_field(
                name =":thermometer:気温(℃)",
                value = "{0}".format( float( weather_data["temp"] ) ),
                inline = False
            )

            # 湿度
            embed.add_field(
                name =":droplet:湿度(%)",
                value = "{0}".format( weather_data["humidity"] ),
                inline = False
            )

            # 気圧
            embed.add_field(
                name =":control_knobs:気圧(hPa)",
                value = "{0}".format( weather_data["pressure"] ),
                inline = False
            )

        # 3時間毎の予報
        elif self.command == "hourly":

            # 配列の定義
            time = []           # 時刻
            description = []    # 天候
            temp = []           # 気温
            humidity = []       # 湿度
            pressure = []       # 気圧

            # 24時間後までのデータを取得
            for i in range( round( len( weather_data ) / 2 ) ):

                # 3時間毎のデータのみを配列に格納
                if i % 3 == 0:

                    # UNIX時間を変換
                    dt = self.__convert_unix_to_datetime( weather_data[i]["dt"] )

                    # 時刻
                    time.append( dt[0] )

                    # 天候
                    description.append( weather_data[i]["weather"][0]["description"] )

                    # 気温
                    temp.append( float( weather_data[i]["temp"] ) )

                    # 湿度
                    humidity.append( weather_data[i]["humidity"] )

                    # 気圧
                    pressure.append( weather_data[i]["pressure"] )

            # グラフ用のデータを生成
            arr_graph.append({
                "時刻": time,
                "気温(℃)": temp,
                "湿度(%)": humidity,
                "気圧(hPa)": pressure
            })

        # 週間予報
        elif self.command == "daily":

            # 配列の定義
            date = []           # 日付
            description = []    # 天候
            temp_high = []      # 最高気温
            temp_low = []       # 最低気温
            humidity = []       # 湿度
            pressure = []       # 気圧

            # 7日分のデータのみを配列に格納
            for i in range( len( weather_data ) - 1 ):

                # UNIX時間を変換
                dt = self.__convert_unix_to_datetime( weather_data[i]["dt"] )

                # 日付
                date.append( dt[1] )

                # 天候
                description.append( weather_data[i]["weather"][0]["description"] )

                # 最高気温
                temp_high.append( float( weather_data[i]["temp"]["max"] ) )

                # 最低気温
                temp_low.append( float( weather_data[i]["temp"]["min"] ) )

                # 湿度
                humidity.append( weather_data[i]["humidity"] )

                # 気圧
                pressure.append( weather_data[i]["pressure"] )

            # グラフ用のデータを生成
            arr_graph.append({
                "日付": date,
                "最高気温(℃)": temp_high,
                "最低気温(℃)": temp_low,
                "湿度(%)": humidity,
                "気圧(hPa)": pressure
            })

        # 投稿する
        webhook = Webhook.partial( self.webhook_id, self.webhook_token, adapter = RequestsWebhookAdapter() )
        if self.command == "current":

            # メッセージのみを投稿
            webhook.send( embed = embed )

        else:

            # グラフを生成
            graph = self.__make_graph( arr_graph )

            # メッセージにグラフを追加
            file = File(
                fp = graph[0],
                filename = graph[1]
            )
            embed.set_image(
                url ="attachment://{0}".format( graph[1] )
            )

            # メッセージとグラフを投稿
            webhook.send( embed = embed, file = file )


    # 入力された地名から緯度・経度を取得する関数
    def __get_latlon( self ):

        # 基となるURL
        base_url = "http://www.geocoding.jp/api/"
        params = {"q": self.location }

        # URLにクエリをセット
        url = urllib.request.Request("{0}?{1}".format( base_url, urllib.parse.urlencode( params ) ) )

        # URLを開く
        try:
            req = urllib.request.urlopen( url )
            html = req.read()
            #print( req.geturl() )

            # 取得したURL内を検索
            soup = BeautifulSoup( html.decode("utf-8"), "html.parser")

            # 存在しない地名だった場合
            if not soup.find("lat"):

                # ( 0, 0 )を返す
                return "0", "0"

            # URL内から緯度・経度の要素を抽出
            lat = str( soup.find("lat").string )
            lon = str( soup.find("lng").string )

            #print( html.decode("utf-8") )
            return lat, lon

        except urllib.error.HTTPError as e:

            return "0", "0"


    # 緯度・経度から天気情報(JSON)を取得する関数
    def __get_weather_data( self, lat, lon ):

        # 基となるURL
        base_url = "https://api.openweathermap.org/data/2.5/onecall"

        # 送信するクエリパラメータを生成
        lang = "ja"
        units = "metric"
        appid = self.owm_key
        params = {"lang": lang, "units": units, "appid": appid, "lat": lat, "lon": lon }

        try:

            # URLにクエリをセット
            url = urllib.request.Request("{0}?{1}".format( base_url, urllib.parse.urlencode( params ) ) )

            # URLを開く
            req = urllib.request.urlopen( url )
            #print( req.geturl() )

            # 天気情報を変数に格納
            weather_data = json.loads( req.read() )

            # 取得したJSONファイルを返す
            return weather_data

        except urllib.error.HTTPError as e:

            pass

        '''
        # ローカルの天気情報を使用(テスト用)
        with open("test_weather_data.json", "r", encoding ="utf-8") as f:
            return json.load( f )
        '''


    # 天気画像に応じたサイドバーの色を指定する関数
    def __set_embed_color( self, icon_name ):

        # 快晴,晴れ(昼)
        if re.search("01d", icon_name ) or re.search("02d", icon_name ):
            color = 0xF7941D
        # 快晴,晴れ(夜)
        elif re.search("01n", icon_name ) or re.search("02n", icon_name ):
            color = 0x8477BC
        # 曇り
        elif re.search("03", icon_name ) or re.search("04", icon_name ):
            color = 0xD8D8D8
        # 雨
        elif re.search("09", icon_name ) or re.search("10", icon_name ):
            color = 0x45B3FF
        # 雷
        elif re.search("11", icon_name ):
            color = 0xE4E400
        # 雪
        elif re.search("13", icon_name ):
            color = 0xC0FFFF
        else:
            color = 0x7289DA

        return color


    # UNIX時間を日時に変換して返す関数
    def __convert_unix_to_datetime( self, dt_unix ):

        # UNIX時間を変換
        dt = datetime.fromtimestamp( dt_unix )

        # 時刻を整形
        dt_time = dt.strftime("%H:%M")

        # 曜日リスト
        list_week = ["日","月","火","水","木","金","土"]

        # 日付を整形
        dt_date = dt.strftime("%Y/%m/%d({0})").format( list_week[ int( dt.strftime("%w") ) ] )

        return dt_time, dt_date


    # 今日の日時を取得する関数
    def __get_today( self ):

        # 曜日リスト
        list_week = ["日","月","火","水","木","金","土"]

        # 現在日時を整形
        dt = datetime.now().strftime("%Y/%m/%d({0}) %H:%M:%S").format( list_week[ int( datetime.now().strftime("%w") ) ] )

        return dt


    # グラフを生成し、そのパスを返す関数
    def __make_graph( self, org_data ):

        # グラフ用のデータに加工
        df = pd.DataFrame( org_data[0] )
        #pprint( df )

        # データに応じて生成するグラフを決める
        # 3時間毎の予報
        if "時刻" in org_data[0]:

            # グラフの台紙(Figure)を生成
            fig, ax = plt.subplots( figsize = ( 6.4, 4.8 ) )

            # グラフ名を指定
            fig.suptitle("{0} 3時間毎の予報({1} 現在)".format( self.location, self.__get_today() ) )

        # 週間予報
        elif "日付" in org_data[0]:

            # グラフの台紙(Figure)を生成
            fig, ax = plt.subplots( figsize = ( 7.2, 5.4 ) )

            # グラフ名を指定
            fig.suptitle("{0} 週間予報({1} 現在)".format( self.location, self.__get_today() ) )

        # 軸を削除
        ax.axis("off")
        ax.axis("tight")

        # テーブルを生成
        ax.table(
            cellText = df.values,
            colLabels = df.columns,
            loc = "center",
            bbox = [ 0, 0, 1, 1 ]
        )

        # グラフを表示
        #plt.show()

        # 空のメモリを生成
        sio = BytesIO()

        # グラフの拡張子を指定
        ext = "png"

        # グラフをメモリ上に保存
        plt.savefig( sio, format = ext )

        # メモリ上のグラフを変数に格納
        with BytesIO( sio.getvalue() ) as b:
            img = BytesIO( b.getvalue() )

        # グラフを表示しない
        plt.close( fig )

        # ファイル名を出力
        send_file = "{0}.{1}".format( self.__log_file_name(), ext )
        #print( send_file )

        return img, send_file


    # ログファイル名を生成する関数
    def __log_file_name( self ):

        random_string = "".join([random.choice( string.ascii_letters + string.digits ) for i in range( 12 )])
        return datetime.now().strftime("%Y%m%d_%H%M%S_{0}_{1}".format( self.command, random_string ) )