import os
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    TextMessage,
    PushMessageRequest
)

# メッセージ送信
def push_message(api_client, message):
    group_id = os.environ["GROUP_ID"]
    api_instance = MessagingApi(api_client)
    request = PushMessageRequest(to=group_id, messages=[TextMessage(text=message, type="text")])
    print(f"push_message: to={group_id}, msg={message}")
    api_instance.push_message(request)

# イベントタイプ取得
def get_event_type(event):
    if "events" in event.keys() and len(event["events"]) > 0 and "type" in event["events"][0].keys():
        return event["events"][0]["type"]
    else:
        return "unknown"

# Lambdaハンドラー
def lambda_handler(event, context):
    event_type = get_event_type(event)
    if event_type != "memberJoined":
        print(f"skip: event_type={event_type}")
        return { "statusCode": 200 }

    # LINEクライアント生成
    configuration = Configuration(
        host = "https://api.line.me",
        access_token = os.environ["CHANNEL_ACCESS_TOKEN"]
    )
    api_client = ApiClient(configuration)

    try:
        chouseisan_hash = os.environ["CHOUSEISAN_HASH"]
        deadline = os.environ["DEADLINE"]
        message = f"〜の歓迎会やります！\n" \
            + f"\n" \
            + f"{deadline}までに、調整さんの入力お願いします！\n" \
            + f"https://chouseisan.com/s?h={chouseisan_hash}\n" \
            + f"\n" \
            + f"また、会場の候補は↓です！\n" \
            + f"ご希望があれば、調整さんのコメントに番号で記載してください！\n" \
            + f"\n" \
            + f"①: あああああ\n" \
            + f"②: いいいいい\n" \
            + f"③: ううううう"
        push_message(api_client, message)

    except Exception as e:
        print("Exception: %s\n" % e)

    api_client.close()

    return { "statusCode": 200 }
