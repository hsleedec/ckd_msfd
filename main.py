import requests
import os

token = os.environ.get('TELEGRAM_TOKEN')
chat_id = os.environ.get('TELEGRAM_CHAT_ID')

# 그냥 깡으로 메시지 하나 쏴보기
res = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                    data={'chat_id': chat_id, 'text': "🚀 아빠! 나 연결됐어! 이제 한미약품 찾으러 갈게!"})
print(res.json()) # 깃허브 로그에 결과 찍기
