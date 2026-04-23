import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

# ==========================================
# 設定部分
# ==========================================
TELEGRAM_TOKEN = "8671392597:AAFQQkLQ4HSiopBrEZQ7fpV458SU6hUd1nU"
CHAT_ID = "8797265697"

# 監視する銘柄リスト（大型株・主要銘柄）
tickers = {
    "6857.T": "アドバンテスト",
    "9983.T": "ファーストリテイリング",
    "8035.T": "東京エレクトロン",
    "9984.T": "ソフトバンクG",
    "4063.T": "信越化学工業",
    "8058.T": "三菱商事",
    "7203.T": "トヨタ自動車",
    "8306.T": "三菱UFJ",
    "7974.T": "任天堂",
    "5020.T": "ENEOS",
    "5713.T": "住友金属鉱山",
    "2914.T": "JT",
    "9432.T": "NTT",
    "6758.T": "ソニーG",
    "6367.T": "ダイキン",
    "4519.T": "中外製薬"
}

# ==========================================
# 処理部分
# ==========================================
def send_telegram_message(message):
    """Telegramにメッセージを送信する関数"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram送信エラー: {e}")

def check_bollinger_bands():
    """各銘柄の±2σを計算し、条件に合致すれば通知する関数"""
    hit_list_upper = [] # +2σ用
    hit_list_lower = [] # -2σ用
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] スクリーニング開始...")

    for ticker, company_name in tickers.items():
        try:
            # 過去60日分のデータを取得
            df = yf.download(ticker, period="60d", interval="1d", progress=False)

            if df.empty:
                print(f"データ取得失敗: {company_name}")
                continue

            # 終値データの抽出
            if isinstance(df.columns, pd.MultiIndex):
                close_prices = df['Close'][ticker]
            else:
                close_prices = df['Close']

            # ボリンジャーバンド計算 (20日)
            sma = close_prices.rolling(window=20).mean()
            std = close_prices.rolling(window=20).std()
            upper_band = sma + (std * 2) # +2σ
            lower_band = sma - (std * 2) # -2σ

            latest_close = float(close_prices.iloc[-1])
            latest_upper = float(upper_band.iloc[-1])
            latest_lower = float(lower_band.iloc[-1])

            # 判定：現在値が+2σ以上か
            if latest_close >= latest_upper:
                hit_list_upper.append(f"・<b>{company_name}</b> ({ticker})\n  現在値: {latest_close:,.1f}円 / +2σ: {latest_upper:,.1f}円")
            
            # 判定：現在値が-2σ以下か
            if latest_close <= latest_lower:
                hit_list_lower.append(f"・<b>{company_name}</b> ({ticker})\n  現在値: {latest_close:,.1f}円 / -2σ: {latest_lower:,.1f}円")
            
            print(f"確認済み: {company_name}")

        except Exception as e:
            print(f"エラー ({company_name}): {e}")

    # メッセージの組み立て
    text = ""
    if hit_list_upper:
        text += "<b>🚀 【+2σ超え：買われすぎ・強気】</b>\n\n" + "\n\n".join(hit_list_upper) + "\n\n"
    
    if hit_list_lower:
        if text: text += "------------------\n\n"
        text += "<b>🚨 【-2σ割れ：売られすぎ・弱気】</b>\n\n" + "\n\n".join(hit_list_lower) + "\n\n"

    # 結果の通知（ここに解説テキストを常に追加）
    if text:
        explanation = (
            "------------------\n"
            "💡 <b>【指標の解説】</b>\n"
            "<b>-2σ（下限）への到達:</b>\n価格が急落し、統計的な変動範囲の底に達したことを意味します。ここからの自律反発を狙う「逆張り」の指標としてよく使われます。\n\n"
            "<b>+2σ（上限）への到達:</b>\n価格が急騰し、統計的な範囲の天井に達したことを意味します。利益確定の目安にするほか、強い材料がある場合はさらに上昇が続く「順張り」のサイン（バンドウォーク）としても注目されます。"
        )
        text += explanation
        
        send_telegram_message(text)
        print("Telegramに通知を送信しました。")
    else:
        print("本日は該当銘柄がありませんでした。")

if __name__ == "__main__":
    check_bollinger_bands()
