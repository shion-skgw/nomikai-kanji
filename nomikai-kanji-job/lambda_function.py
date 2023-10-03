import os
import pandas as pd
from datetime import (
    datetime,
    timedelta
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    TextMessage,
    PushMessageRequest
)

# 調整さん入力リマインド日付チェック
def is_remind():
    raw_deadline = os.environ["DEADLINE"] + " 00:00"
    deadline = datetime.strptime(raw_deadline, "%Y/%m/%d %H:%M")
    remind = deadline - timedelta(1)
    return remind < datetime.now() + timedelta(hours=9)

# 調整さん入力期限チェック
def is_deadline():
    raw_deadline = os.environ["DEADLINE"] + " 00:00"
    deadline = datetime.strptime(raw_deadline, "%Y/%m/%d %H:%M")
    return deadline < datetime.now() + timedelta(hours=9)

# 調整さん系ロジック

# 調整さん回答数を取得
def get_chouseisan_count(chouseisan_csv):
    return len(chouseisan_csv)

# 出席者最多の日程を取得
def get_most_dates(chouseisan_csv):
    # 参加者、コメント列を除外
    csv = chouseisan_csv.drop(columns=["参加者", "コメント"])
    # 点数化する
    csv = csv.replace("◯", 2) \
        .replace("△", 1) \
        .replace("×", 0)
    # 集計して返却
    return pd.to_numeric(csv.sum(), errors="coerce").idxmax()

# 会場の希望最多を取得
def get_popular_venue(chouseisan_csv):
    # コメント列を抽出
    csv = chouseisan_csv["コメント"]
    # 綺麗にする
    csv = csv.replace("^(?!.*[1１①2２②3３③]).*$", "", regex=True) \
        .replace(".*[1１①].*", "①", regex=True) \
        .replace(".*[2２②].*", "②", regex=True) \
        .replace(".*[3３③].*", "③", regex=True)
    # 集計して返却
    return csv[csv != ""].mode()[0]

# LINE系ロジック

# グループメンバー数を取得
def get_group_member_count(api_client):
    group_id = os.environ["GROUP_ID"]
    api_instance = MessagingApi(api_client)
    api_response = api_instance.get_group_member_count(group_id)
    return api_response.count

# メッセージ送信
def push_message(api_client, message):
    group_id = os.environ["GROUP_ID"]
    api_instance = MessagingApi(api_client)
    request = PushMessageRequest(to=group_id, messages=[TextMessage(text=message, type="text")])
    print(f"push_message: to={group_id}, msg={message}")
    api_instance.push_message(request)


# Lambdaハンドラー
def lambda_handler(event, context):
    # 調整さんCSV取得
    chouseisan_hash = os.environ["CHOUSEISAN_HASH"]
    chouseisan_url = f"https://chouseisan.com/schedule/List/createCsv?h={chouseisan_hash}&charset=utf-8&row=member"
    chouseisan_csv = pd.read_csv(chouseisan_url, header=1)

    # LINEクライアント生成
    configuration = Configuration(
        host = "https://api.line.me",
        access_token = os.environ["CHANNEL_ACCESS_TOKEN"]
    )
    api_client = ApiClient(configuration)

    try:
        if is_deadline():
            # 入力期限到来
            print("Deadline has arrived")
            most_dates = get_most_dates(chouseisan_csv)
            popular_venue = get_popular_venue(chouseisan_csv)
            message = f"調整さんの入力ありがとうございました。\n日程: {most_dates}\n会場: {popular_venue}"
            push_message(api_client, message)
    
        elif is_remind():
            # リマインド
            if get_group_member_count(api_client) > get_chouseisan_count(chouseisan_csv):
                # 調整さん未入力のメンバーがいる場合リマインド
                print("Need a reminder")
                deadline = os.environ["DEADLINE"]
                message = f"調整さんの入力期限は {deadline} です。入力お願いします。"
                push_message(api_client, message)
            else:
                print("No reminder needed")

    except Exception as e:
        print("Exception: %s\n" % e)

    api_client.close()

    return { "statusCode": 200 }
