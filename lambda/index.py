# lambda/index.py
import json
import os
import urllib.request
import urllib.error

API_ENDPOINT = os.environ.get("API_ENDPOINT")

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event, indent=2))
        
        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)
        
        # 会話履歴を使用
        messages = conversation_history.copy()
        
        # ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })

        # messagesをstringに変換
        messages_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        request_payload = {
            "prompt": messages_str,
            "max_new_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True
        }

        # APIの呼び出し
        headers = {
            "Content-Type": "application/json",
        }
        data = json.dumps(request_payload).encode('utf-8')
        req = urllib.request.Request(API_ENDPOINT, data=data, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(req) as response:
                response_body = json.loads(response.read().decode('utf-8'))
                print("Response from API:", json.dumps(response_body, indent=2, ensure_ascii=False))
        except urllib.error.HTTPError as e:
            print("HTTPError:", e.code, e.reason)
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }
        except urllib.error.URLError as e:
            print("URLError:", e.reason)
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }
        
        # アシスタントの応答を取得
        assistant_response = response_body['generated_text']
        
        # アシスタントの応答を会話履歴に追加
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            }, ensure_ascii=False, indent=2)
        }
        
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            }, ensure_ascii=False, indent=2)
        }
