import ctypes
import base64
import json
import os
import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass
from ctypes import wintypes
from html import unescape
from pathlib import Path
from tkinter import messagebox, ttk
from urllib import parse, request
from urllib.error import HTTPError, URLError


APP_TITLE = "AI 翻译助手"
APP_ICON = "app_icon.ico"


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_path(name: str) -> Path:
    bundled = Path(getattr(sys, "_MEIPASS", app_base_dir()))
    candidate = bundled / name
    if candidate.exists():
        return candidate
    return app_base_dir() / name


CONFIG_PATH = app_base_dir() / "translator_config.json"

SPEECH_CULTURES = {
    "zh-CN": "zh-CN",
    "zh-TW": "zh-TW",
    "en": "en-US",
    "ja": "ja-JP",
    "ko": "ko-KR",
    "fr": "fr-FR",
    "de": "de-DE",
    "es": "es-ES",
    "it": "it-IT",
    "pt": "pt-BR",
    "ru": "ru-RU",
    "ar": "ar-SA",
    "hi": "hi-IN",
    "ne": "ne-NP",
    "my": "my-MM",
    "th": "th-TH",
    "vi": "vi-VN",
    "id": "id-ID",
    "nl": "nl-NL",
    "pl": "pl-PL",
    "tr": "tr-TR",
    "sv": "sv-SE",
    "uk": "uk-UA",
    "el": "el-GR",
    "he": "he-IL",
    "tl": "fil-PH",
}

BLUE = "#1a73e8"
TEXT = "#1f3552"
MUTED = "#7a8799"
BORDER = "#d7dee8"
BG = "#f5f8fc"
PANEL = "#ffffff"


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndCaret", wintypes.HWND),
        ("rcCaret", wintypes.RECT),
    ]


IS_WINDOWS = sys.platform.startswith("win")
CREATE_NO_WINDOW = 0x08000000 if IS_WINDOWS else 0
if IS_WINDOWS:
    USER32 = ctypes.WinDLL("user32", use_last_error=True)
    KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
    SW_RESTORE = 9
    GA_ROOT = 2
    GW_HWNDNEXT = 2
    VK_CONTROL = 0x11
    VK_RETURN = 0x0D
    VK_V = 0x56
    KEYEVENTF_KEYUP = 0x0002
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
else:
    USER32 = None
    KERNEL32 = None
    SW_RESTORE = 9
    GA_ROOT = 2
    GW_HWNDNEXT = 2
    VK_CONTROL = 0x11
    VK_RETURN = 0x0D
    VK_V = 0x56
    KEYEVENTF_KEYUP = 0x0002
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004


LANGUAGES = [
    ("zh-CN", "简体中文"),
    ("zh-TW", "繁体中文"),
    ("en", "英语"),
    ("hi", "印地语"),
    ("id", "印度尼西亚语"),
    ("ms", "马来语"),
    ("it", "意大利语"),
    ("tl", "菲律宾语"),
    ("ceb", "宿务语"),
    ("my", "缅甸语"),
    ("pt-BR", "葡萄牙语（巴西）"),
    ("pt-PT", "葡萄牙语（葡萄牙）"),
    ("pt", "葡萄牙语"),
    ("es", "西班牙语"),
    ("vi", "越南语"),
    ("lo", "老挝语"),
    ("th", "泰语"),
    ("hmn", "苗语"),
    ("ja", "日语"),
    ("zu", "祖鲁语"),
    ("hu", "匈牙利语"),
    ("hr", "克罗地亚语"),
    ("eo", "世界语"),
    ("ckb", "中库尔德语"),
    ("uz", "乌兹别克语"),
    ("hy", "亚美尼亚语"),
    ("sd", "信德语"),
    ("is", "冰岛语"),
    ("chr", "切罗基语"),
    ("gl", "加利西亚语"),
    ("ca", "加泰罗尼亚语"),
    ("kn", "卡纳达语"),
    ("lb", "卢森堡语"),
    ("rom", "吉普赛语"),
    ("kk", "哈萨克语"),
    ("iu", "因纽特语"),
    ("tr", "土耳其语"),
    ("tg", "塔吉克语"),
    ("see", "塞内卡语"),
    ("oj", "奥吉布瓦语"),
    ("osa", "奥塞治语"),
    ("cy", "威尔士语"),
    ("dz", "宗卡语"),
    ("km", "高棉语"),
    ("ko", "韩语"),
    ("ru", "俄语"),
    ("fr", "法语"),
    ("de", "德语"),
    ("mn", "蒙古语"),
    ("ne", "尼泊尔语"),
    ("af", "南非荷兰语"),
    ("ar", "阿拉伯语"),
    ("ta", "泰米尔语"),
    ("as", "阿萨姆语"),
    ("bn", "孟加拉语"),
    ("eu", "巴斯克语"),
    ("be", "白俄罗斯语"),
    ("bg", "保加利亚语"),
    ("cs", "捷克语"),
    ("da", "丹麦语"),
    ("nl", "荷兰语"),
    ("fi", "芬兰语"),
    ("ff", "富拉语"),
    ("su", "巽他语"),
    ("ku", "库尔德语"),
    ("yi", "意第绪语"),
    ("lv", "拉脱维亚语"),
    ("nn", "挪威尼诺斯克语"),
    ("ti", "提格利尼亚语"),
    ("sl", "斯洛文尼亚语"),
    ("ps", "普什图语"),
    ("ky", "柯尔克孜语"),
    ("ka", "格鲁吉亚语"),
    ("mi", "毛利语"),
    ("bs", "波斯尼亚语"),
    ("ht", "海地克里奥尔语"),
    ("ga", "爱尔兰语"),
    ("et", "爱沙尼亚语"),
    ("xh", "科萨语"),
    ("co", "科西嘉语"),
    ("lt", "立陶宛语"),
    ("so", "索马里语"),
    ("yo", "约鲁巴语"),
    ("nv", "纳瓦霍语"),
    ("sn", "绍纳语"),
    ("ug", "维吾尔语"),
    ("gd", "苏格兰盖尔语"),
    ("el", "希腊语"),
    ("gu", "古吉拉特语"),
    ("he", "希伯来语"),
    ("la", "拉丁语"),
    ("ml", "马拉雅拉姆语"),
    ("mni-Mtei", "曼尼普尔语"),
    ("mr", "马拉地语"),
    ("no", "挪威语"),
    ("or", "奥里亚语"),
    ("fa", "波斯语"),
    ("pl", "波兰语"),
    ("pa", "旁遮普语"),
    ("ro", "罗马尼亚语"),
    ("sa", "梵语"),
    ("sw", "斯瓦希里语"),
    ("sv", "瑞典语"),
    ("te", "泰卢固语"),
    ("uk", "乌克兰语"),
    ("ur", "乌尔都语"),
    ("si", "僧伽罗语"),
    ("sr", "塞尔维亚语"),
    ("sk", "斯洛伐克语"),
    ("bo", "藏语"),
    ("fy", "西弗里西亚语"),
    ("az", "阿塞拜疆语"),
    ("am", "阿姆哈拉语"),
    ("sq", "阿尔巴尼亚语"),
    ("tt", "鞑靼语"),
    ("mk", "马其顿语"),
    ("mg", "马拉加斯语"),
    ("mt", "马耳他语"),
    ("ny", "齐切瓦语"),
    ("ccp", "Chakma"),
    ("lis", "Lisu"),
    ("myh", "Makah"),
    ("mez", "Menominee"),
    ("one", "Oneida"),
    ("crk", "Plains Cree"),
    ("rhg", "Rohingya"),
    ("uzs", "Southern Uzbek"),
]

LANGUAGE_NAMES = dict(LANGUAGES)
LANGUAGE_CODES = {name: code for code, name in LANGUAGES}
LANGUAGE_LABELS = [name for _, name in LANGUAGES]

UI_LANGUAGES = [
    ("zh-CN", "中文（简体）"),
    ("zh-TW", "中文（繁體）"),
    ("en", "English"),
    ("ja", "日本語"),
    ("ko", "한국어"),
    ("fr", "Français"),
    ("de", "Deutsch"),
    ("es", "Español"),
    ("it", "Italiano"),
    ("pt", "Português"),
    ("ru", "Русский"),
    ("ar", "العربية"),
    ("hi", "हिन्दी"),
    ("ne", "नेपाली"),
    ("my", "မြန်မာ"),
    ("th", "ไทย"),
    ("vi", "Tiếng Việt"),
    ("id", "Bahasa Indonesia"),
    ("nl", "Nederlands"),
    ("pl", "Polski"),
    ("tr", "Türkçe"),
    ("sv", "Svenska"),
    ("uk", "Українська"),
    ("el", "Ελληνικά"),
    ("he", "עברית"),
]
UI_LANGUAGE_NAMES = dict(UI_LANGUAGES)
UI_LANGUAGE_CODES = {name: code for code, name in UI_LANGUAGES}
UI_LANGUAGE_LABELS = [name for _, name in UI_LANGUAGES]

UI_TEXT = {
    "zh-CN": {
        "app_title": "AI 翻译助手",
        "ready": "准备就绪",
        "translate_tab": "翻译",
        "settings_tab": "设置",
        "font_tab": "文字大小",
        "display_tab": "界面语言",
        "swap_languages": "⇅ 交换语言",
        "translate": "翻译",
        "copy_output": "复制译文",
        "clear": "清空",
        "listen_input": "麦克风",
        "speak_input": "朗读输入",
        "speak_output": "朗读译文",
        "back_translation": "回翻译",
        "back_to": "回翻译为：{source}",
        "always_on_top": "软件界面永远置顶",
        "ui_language": "软件界面显示语言",
        "translation_method": "翻译方式",
        "ai_translate": "AI 翻译",
        "google_translate": "Google 翻译",
        "microsoft_translate": "Microsoft 翻译",
        "microsoft_key": "Microsoft API KEY",
        "microsoft_region": "Microsoft 区域",
        "microsoft_key_help": "选择 Microsoft 回翻译时使用；也可以设置环境变量 MICROSOFT_TRANSLATOR_KEY / MICROSOFT_TRANSLATOR_REGION。",
        "ai_platform": "AI 平台",
        "country": "国家特色",
        "gender": "我的性别",
        "gemini_key": "Gemini API KEY",
        "gemini_key_help": "一行输入一个密钥；当前一个失败时会自动尝试下一行。",
        "gemini_model": "Gemini 模型",
        "groq_key": "Groq API KEY",
        "groq_key_help": "Groq 同样支持多行密钥轮换。",
        "groq_model": "Groq 模型",
        "my_languages": "我的语言（最多三种）",
        "their_languages": "对方语言（最多三种）",
        "back_setting": "回翻译",
        "back_platform_setting": "回翻译平台",
        "back_yes": "是，显示回翻译小界面",
        "back_no": "否，不进行回翻译",
        "save_settings": "保存设置",
        "text_size_title": "翻译框文字大小",
        "interface_language_title": "软件界面显示语言",
        "interface_language_hint": "选择软件菜单、按钮和提示使用的语言。保存后重启软件会完整生效。",
        "input_font_size": "输入文字大小",
        "output_font_size": "译文文字大小",
        "back_font_size": "回翻译文字大小",
        "text_size_hint": "这里控制输入、翻译、回翻译三个文字区域的大小；系统界面文字会随窗口缩放自动变化。",
        "settings_saved": "设置已保存",
        "settings_saved_body": "设置已经保存并应用。界面显示语言会在下次启动时完整生效。",
        "input_required": "请输入需要翻译的文字",
        "same_language": "上下语言相同，请先切换其中一个语言",
        "translating": "正在翻译...",
        "listening": "正在听写，请对着默认麦克风说话...",
        "speaking": "正在使用默认扬声器朗读...",
        "done": "完成：{provider}",
        "failed": "翻译失败",
        "speech_failed": "语音功能失败",
        "speech_done": "语音输入完成",
        "speech_no_text": "没有可朗读的文字",
        "copied": "译文已复制",
        "pasted_external": "译文已输入到外部窗口",
        "sent_external": "译文已发送到外部窗口，输入框已清空",
        "paste_target_missing": "没有找到外部输入窗口，已复制译文",
        "paste_failed": "输入到外部窗口失败，已复制译文",
        "no_output": "没有可复制的译文",
        "cleared": "已清空",
        "swapped": "已交换上下语言",
    },
    "en": {
        "app_title": "AI Translator",
        "ready": "Ready",
        "translate_tab": "Translate",
        "settings_tab": "Settings",
        "font_tab": "Text Size",
        "display_tab": "Interface",
        "swap_languages": "⇅ Swap Languages",
        "translate": "Translate",
        "copy_output": "Copy",
        "clear": "Clear",
        "listen_input": "Mic",
        "speak_input": "Speak Input",
        "speak_output": "Speak Translation",
        "back_translation": "Back Translation",
        "back_to": "Back to: {source}",
        "always_on_top": "Always keep window on top",
        "ui_language": "Interface language",
        "translation_method": "Translation Method",
        "ai_translate": "AI Translate",
        "google_translate": "Google Translate",
        "microsoft_translate": "Microsoft Translate",
        "microsoft_key": "Microsoft API KEY",
        "microsoft_region": "Microsoft region",
        "microsoft_key_help": "Used when Microsoft is selected for back translation. You can also set MICROSOFT_TRANSLATOR_KEY / MICROSOFT_TRANSLATOR_REGION.",
        "ai_platform": "AI Platform",
        "country": "Country context",
        "gender": "My gender",
        "gemini_key": "Gemini API KEY",
        "gemini_key_help": "Enter one key per line; the next key is tried if the current one fails.",
        "gemini_model": "Gemini Model",
        "groq_key": "Groq API KEY",
        "groq_key_help": "Groq also supports multi-line key rotation.",
        "groq_model": "Groq Model",
        "my_languages": "My Languages (up to 3)",
        "their_languages": "Other Languages (up to 3)",
        "back_setting": "Back Translation",
        "back_platform_setting": "Back-translation platform",
        "back_yes": "Yes, show the back-translation box",
        "back_no": "No, do not back-translate",
        "save_settings": "Save Settings",
        "text_size_title": "Translation Box Text Size",
        "interface_language_title": "Interface Language",
        "interface_language_hint": "Choose the language used by menus, buttons, and messages. Restart the app for the full interface to refresh.",
        "input_font_size": "Input text size",
        "output_font_size": "Translation text size",
        "back_font_size": "Back-translation text size",
        "text_size_hint": "These settings control the three text boxes. The rest of the interface scales automatically with the window.",
        "settings_saved": "Settings Saved",
        "settings_saved_body": "Settings have been saved and applied. The interface language fully applies after restart.",
        "input_required": "Enter text to translate",
        "same_language": "Source and target languages are the same.",
        "translating": "Translating...",
        "listening": "Listening through the default microphone...",
        "speaking": "Speaking through the default speaker...",
        "done": "Done: {provider}",
        "failed": "Translation failed",
        "speech_failed": "Speech failed",
        "speech_done": "Speech input complete",
        "speech_no_text": "No text to speak",
        "copied": "Translation copied",
        "pasted_external": "Translation pasted into the external window",
        "sent_external": "Translation sent to the external window; input cleared",
        "paste_target_missing": "No external input window found; translation copied",
        "paste_failed": "Could not paste into the external window; translation copied",
        "no_output": "Nothing to copy",
        "cleared": "Cleared",
        "swapped": "Languages swapped",
    },
    "ja": {
        "app_title": "AI 翻訳アシスタント",
        "ready": "準備完了",
        "translate_tab": "翻訳",
        "settings_tab": "設定",
        "font_tab": "文字サイズ",
        "display_tab": "表示言語",
        "swap_languages": "⇅ 言語を交換",
        "translate": "翻訳",
        "copy_output": "翻訳をコピー",
        "clear": "クリア",
        "back_translation": "逆翻訳",
        "back_to": "逆翻訳先：{source}",
        "always_on_top": "ウィンドウを常に最前面に表示",
        "ui_language": "画面表示言語",
        "translation_method": "翻訳方式",
        "ai_translate": "AI 翻訳",
        "google_translate": "Google 翻訳",
        "microsoft_translate": "Microsoft 翻訳",
        "microsoft_key": "Microsoft API KEY",
        "microsoft_region": "Microsoft リージョン",
        "microsoft_key_help": "逆翻訳で Microsoft を選ぶ場合に使用します。環境変数 MICROSOFT_TRANSLATOR_KEY / MICROSOFT_TRANSLATOR_REGION も使えます。",
        "ai_platform": "AI プラットフォーム",
        "country": "国の特徴",
        "gender": "自分の性別",
        "gemini_key": "Gemini API KEY",
        "gemini_key_help": "1行に1つのキーを入力。失敗すると次のキーを試します。",
        "gemini_model": "Gemini モデル",
        "groq_key": "Groq API KEY",
        "groq_key_help": "Groq も複数行キーの切り替えに対応しています。",
        "groq_model": "Groq モデル",
        "my_languages": "自分の言語（最大3つ）",
        "their_languages": "相手の言語（最大3つ）",
        "back_setting": "逆翻訳",
        "back_platform_setting": "逆翻訳プラットフォーム",
        "back_yes": "はい、逆翻訳欄を表示する",
        "back_no": "いいえ、逆翻訳しない",
        "save_settings": "設定を保存",
        "text_size_title": "翻訳欄の文字サイズ",
        "interface_language_title": "画面表示言語",
        "interface_language_hint": "メニュー、ボタン、メッセージの表示言語を選びます。完全な反映には再起動してください。",
        "input_font_size": "入力文字サイズ",
        "output_font_size": "翻訳文字サイズ",
        "back_font_size": "逆翻訳文字サイズ",
        "text_size_hint": "ここでは3つのテキスト欄の文字サイズを設定します。他の画面文字はウィンドウに合わせて自動調整されます。",
        "settings_saved": "設定を保存しました",
        "settings_saved_body": "設定を保存して適用しました。画面表示言語は次回起動時に完全に反映されます。",
        "input_required": "翻訳するテキストを入力してください",
        "same_language": "上下の言語が同じです。",
        "translating": "翻訳中...",
        "done": "完了：{provider}",
        "failed": "翻訳に失敗しました",
        "copied": "翻訳をコピーしました",
        "pasted_external": "外部ウィンドウに翻訳を入力しました",
        "sent_external": "外部ウィンドウへ送信し、入力欄をクリアしました",
        "paste_target_missing": "外部入力ウィンドウが見つかりません。翻訳をコピーしました",
        "paste_failed": "外部ウィンドウへの入力に失敗しました。翻訳をコピーしました",
        "no_output": "コピーできる翻訳がありません",
        "cleared": "クリアしました",
        "swapped": "言語を交換しました",
    },
}

UI_TEXT["zh-TW"] = {
    **UI_TEXT["zh-CN"],
    "app_title": "AI 翻譯助手",
    "ready": "準備就緒",
    "settings_tab": "設定",
    "font_tab": "文字大小",
    "display_tab": "介面語言",
    "swap_languages": "⇅ 交換語言",
    "copy_output": "複製譯文",
    "back_translation": "回翻譯",
    "back_to": "回翻譯為：{source}",
    "always_on_top": "軟體介面永遠置頂",
    "ui_language": "軟體介面顯示語言",
    "interface_language_title": "軟體介面顯示語言",
    "interface_language_hint": "選擇軟體選單、按鈕和提示使用的語言。儲存後重新啟動會完整生效。",
    "translation_method": "翻譯方式",
    "google_translate": "Google 翻譯",
    "country": "國家特色",
    "gender": "我的性別",
    "my_languages": "我的語言（最多三種）",
    "their_languages": "對方語言（最多三種）",
    "back_yes": "是，顯示回翻譯小介面",
    "back_no": "否，不進行回翻譯",
    "text_size_title": "翻譯框文字大小",
    "input_font_size": "輸入文字大小",
    "output_font_size": "譯文文字大小",
    "back_font_size": "回翻譯文字大小",
    "settings_saved": "設定已儲存",
    "settings_saved_body": "設定已儲存並套用。介面顯示語言會在下次啟動時完整生效。",
    "input_required": "請輸入需要翻譯的文字",
    "same_language": "上下語言相同，請先切換其中一個語言",
    "translating": "正在翻譯...",
    "failed": "翻譯失敗",
    "copied": "譯文已複製",
    "no_output": "沒有可複製的譯文",
    "cleared": "已清空",
    "swapped": "已交換上下語言",
}

UI_TEXT["ko"] = {
    **UI_TEXT["en"],
    "app_title": "AI 번역 도우미",
    "ready": "준비됨",
    "translate_tab": "번역",
    "settings_tab": "설정",
    "font_tab": "글자 크기",
    "display_tab": "인터페이스",
    "swap_languages": "⇅ 언어 교환",
    "translate": "번역",
    "copy_output": "번역 복사",
    "clear": "지우기",
    "back_translation": "역번역",
    "back_to": "역번역 대상: {source}",
    "always_on_top": "창을 항상 위에 표시",
    "ui_language": "인터페이스 언어",
    "interface_language_title": "인터페이스 언어",
    "interface_language_hint": "메뉴, 버튼, 메시지에 사용할 언어를 선택하세요. 전체 적용은 앱 재시작 후 반영됩니다.",
    "translation_method": "번역 방식",
    "ai_translate": "AI 번역",
    "google_translate": "Google 번역",
    "ai_platform": "AI 플랫폼",
    "country": "국가/지역 맥락",
    "gender": "내 성별",
    "my_languages": "내 언어(최대 3개)",
    "their_languages": "상대 언어(최대 3개)",
    "back_setting": "역번역",
    "back_yes": "예, 역번역 창 표시",
    "back_no": "아니요, 역번역 안 함",
    "save_settings": "설정 저장",
    "text_size_title": "번역창 글자 크기",
    "input_font_size": "입력 글자 크기",
    "output_font_size": "번역 글자 크기",
    "back_font_size": "역번역 글자 크기",
    "settings_saved": "설정 저장됨",
    "input_required": "번역할 텍스트를 입력하세요",
    "translating": "번역 중...",
    "failed": "번역 실패",
    "copied": "번역을 복사했습니다",
    "cleared": "지웠습니다",
}

UI_TEXT["fr"] = {
    **UI_TEXT["en"],
    "app_title": "Assistant de traduction IA",
    "ready": "Prêt",
    "translate_tab": "Traduire",
    "settings_tab": "Réglages",
    "font_tab": "Taille du texte",
    "display_tab": "Interface",
    "swap_languages": "⇅ Échanger les langues",
    "translate": "Traduire",
    "copy_output": "Copier",
    "clear": "Effacer",
    "back_translation": "Rétro-traduction",
    "back_to": "Retour vers : {source}",
    "always_on_top": "Toujours au premier plan",
    "ui_language": "Langue de l’interface",
    "interface_language_title": "Langue de l’interface",
    "interface_language_hint": "Choisissez la langue des menus, boutons et messages. Redémarrez l’application pour l’appliquer entièrement.",
    "translation_method": "Mode de traduction",
    "ai_translate": "Traduction IA",
    "google_translate": "Google Traduction",
    "ai_platform": "Plateforme IA",
    "country": "Contexte pays",
    "gender": "Mon genre",
    "my_languages": "Mes langues (3 max.)",
    "their_languages": "Langues de l’autre personne (3 max.)",
    "back_setting": "Rétro-traduction",
    "back_yes": "Oui, afficher la rétro-traduction",
    "back_no": "Non, ne pas rétro-traduire",
    "save_settings": "Enregistrer",
    "text_size_title": "Taille du texte des zones",
    "input_font_size": "Taille du texte saisi",
    "output_font_size": "Taille de la traduction",
    "back_font_size": "Taille de la rétro-traduction",
    "settings_saved": "Réglages enregistrés",
    "input_required": "Saisissez le texte à traduire",
    "translating": "Traduction...",
    "failed": "Échec de la traduction",
    "copied": "Traduction copiée",
    "cleared": "Effacé",
}

UI_TEXT["de"] = {
    **UI_TEXT["en"],
    "app_title": "KI-Übersetzungsassistent",
    "ready": "Bereit",
    "translate_tab": "Übersetzen",
    "settings_tab": "Einstellungen",
    "font_tab": "Textgröße",
    "display_tab": "Oberfläche",
    "swap_languages": "⇅ Sprachen tauschen",
    "translate": "Übersetzen",
    "copy_output": "Kopieren",
    "clear": "Leeren",
    "back_translation": "Rückübersetzung",
    "back_to": "Zurück nach: {source}",
    "always_on_top": "Fenster immer im Vordergrund",
    "ui_language": "Sprache der Oberfläche",
    "interface_language_title": "Sprache der Oberfläche",
    "interface_language_hint": "Wählen Sie die Sprache für Menüs, Schaltflächen und Meldungen. Starten Sie die App neu, damit alles übernommen wird.",
    "translation_method": "Übersetzungsmethode",
    "ai_translate": "KI-Übersetzung",
    "google_translate": "Google Übersetzer",
    "ai_platform": "KI-Plattform",
    "country": "Länderkontext",
    "gender": "Mein Geschlecht",
    "save_settings": "Speichern",
    "text_size_title": "Textgröße der Übersetzungsfelder",
    "input_font_size": "Eingabetextgröße",
    "output_font_size": "Übersetzungstextgröße",
    "back_font_size": "Rückübersetzungstextgröße",
    "settings_saved": "Einstellungen gespeichert",
    "input_required": "Text zum Übersetzen eingeben",
    "translating": "Übersetzen...",
    "failed": "Übersetzung fehlgeschlagen",
    "copied": "Übersetzung kopiert",
    "cleared": "Geleert",
}

UI_TEXT["es"] = {
    **UI_TEXT["en"],
    "app_title": "Asistente de traducción IA",
    "ready": "Listo",
    "translate_tab": "Traducir",
    "settings_tab": "Ajustes",
    "font_tab": "Tamaño de texto",
    "display_tab": "Interfaz",
    "swap_languages": "⇅ Intercambiar idiomas",
    "translate": "Traducir",
    "copy_output": "Copiar",
    "clear": "Borrar",
    "back_translation": "Retraducción",
    "back_to": "Retraducir a: {source}",
    "always_on_top": "Mantener ventana siempre arriba",
    "ui_language": "Idioma de la interfaz",
    "interface_language_title": "Idioma de la interfaz",
    "interface_language_hint": "Elige el idioma de menús, botones y mensajes. Reinicia la aplicación para aplicarlo por completo.",
    "translation_method": "Método de traducción",
    "ai_translate": "Traducción IA",
    "google_translate": "Google Traductor",
    "ai_platform": "Plataforma IA",
    "country": "Contexto del país",
    "gender": "Mi género",
    "save_settings": "Guardar",
    "text_size_title": "Tamaño del texto",
    "input_font_size": "Tamaño del texto de entrada",
    "output_font_size": "Tamaño del texto traducido",
    "back_font_size": "Tamaño de la retraducción",
    "settings_saved": "Ajustes guardados",
    "input_required": "Introduce texto para traducir",
    "translating": "Traduciendo...",
    "failed": "Error de traducción",
    "copied": "Traducción copiada",
    "cleared": "Borrado",
}

UI_TEXT["ru"] = {
    **UI_TEXT["en"],
    "app_title": "AI помощник перевода",
    "ready": "Готово",
    "translate_tab": "Перевод",
    "settings_tab": "Настройки",
    "font_tab": "Размер текста",
    "display_tab": "Интерфейс",
    "swap_languages": "⇅ Поменять языки",
    "translate": "Перевести",
    "copy_output": "Копировать",
    "clear": "Очистить",
    "back_translation": "Обратный перевод",
    "back_to": "Обратно на: {source}",
    "always_on_top": "Окно всегда поверх остальных",
    "ui_language": "Язык интерфейса",
    "interface_language_title": "Язык интерфейса",
    "interface_language_hint": "Выберите язык меню, кнопок и сообщений. Перезапустите приложение для полного применения.",
    "translation_method": "Способ перевода",
    "ai_translate": "AI перевод",
    "google_translate": "Google перевод",
    "ai_platform": "AI платформа",
    "country": "Контекст страны",
    "gender": "Мой пол",
    "save_settings": "Сохранить",
    "text_size_title": "Размер текста в полях",
    "input_font_size": "Размер ввода",
    "output_font_size": "Размер перевода",
    "back_font_size": "Размер обратного перевода",
    "settings_saved": "Настройки сохранены",
    "input_required": "Введите текст для перевода",
    "translating": "Перевод...",
    "failed": "Ошибка перевода",
    "copied": "Перевод скопирован",
    "cleared": "Очищено",
}

EXTRA_UI_TEXT = {
    "it": {
        "app_title": "Assistente traduttore AI",
        "ready": "Pronto",
        "translate_tab": "Traduci",
        "settings_tab": "Impostazioni",
        "font_tab": "Dimensione testo",
        "display_tab": "Interfaccia",
        "translate": "Traduci",
        "copy_output": "Copia",
        "clear": "Cancella",
        "ui_language": "Lingua interfaccia",
        "interface_language_title": "Lingua interfaccia",
        "interface_language_hint": "Scegli la lingua di menu, pulsanti e messaggi. Riavvia per applicarla completamente.",
        "save_settings": "Salva",
    },
    "pt": {
        "app_title": "Assistente de tradução AI",
        "ready": "Pronto",
        "translate_tab": "Traduzir",
        "settings_tab": "Definições",
        "font_tab": "Tamanho do texto",
        "display_tab": "Interface",
        "translate": "Traduzir",
        "copy_output": "Copiar",
        "clear": "Limpar",
        "ui_language": "Idioma da interface",
        "interface_language_title": "Idioma da interface",
        "interface_language_hint": "Escolha o idioma de menus, botões e mensagens. Reinicie para aplicar tudo.",
        "save_settings": "Guardar",
    },
    "ar": {
        "app_title": "مساعد الترجمة بالذكاء الاصطناعي",
        "ready": "جاهز",
        "translate_tab": "ترجمة",
        "settings_tab": "الإعدادات",
        "font_tab": "حجم النص",
        "display_tab": "الواجهة",
        "translate": "ترجمة",
        "copy_output": "نسخ",
        "clear": "مسح",
        "ui_language": "لغة الواجهة",
        "interface_language_title": "لغة الواجهة",
        "interface_language_hint": "اختر لغة القوائم والأزرار والرسائل. أعد تشغيل التطبيق للتطبيق الكامل.",
        "save_settings": "حفظ",
    },
    "hi": {
        "app_title": "AI अनुवाद सहायक",
        "ready": "तैयार",
        "translate_tab": "अनुवाद",
        "settings_tab": "सेटिंग",
        "font_tab": "टेक्स्ट आकार",
        "display_tab": "इंटरफेस",
        "translate": "अनुवाद",
        "copy_output": "कॉपी",
        "clear": "साफ करें",
        "ui_language": "इंटरफेस भाषा",
        "interface_language_title": "इंटरफेस भाषा",
        "interface_language_hint": "मेनू, बटन और संदेशों की भाषा चुनें। पूरा बदलाव देखने के लिए ऐप फिर खोलें।",
        "save_settings": "सहेजें",
    },
    "ne": {
        "app_title": "AI अनुवाद सहायक",
        "ready": "तयार",
        "translate_tab": "अनुवाद",
        "settings_tab": "सेटिङ",
        "font_tab": "पाठ आकार",
        "display_tab": "इन्टरफेस",
        "translate": "अनुवाद",
        "copy_output": "प्रतिलिपि",
        "clear": "खाली",
        "ui_language": "इन्टरफेस भाषा",
        "interface_language_title": "इन्टरफेस भाषा",
        "interface_language_hint": "मेनु, बटन र सन्देशको भाषा छान्नुहोस्। पूर्ण लागू गर्न एप पुनः खोल्नुहोस्।",
        "save_settings": "सुरक्षित",
    },
    "my": {
        "app_title": "AI ဘာသာပြန် ကူညီသူ",
        "ready": "အသင့်",
        "translate_tab": "ဘာသာပြန်",
        "settings_tab": "ဆက်တင်",
        "font_tab": "စာလုံးအရွယ်",
        "display_tab": "မျက်နှာပြင်",
        "translate": "ဘာသာပြန်",
        "copy_output": "ကူးယူ",
        "clear": "ရှင်း",
        "ui_language": "မျက်နှာပြင်ဘာသာ",
        "interface_language_title": "မျက်နှာပြင်ဘာသာစကား",
        "interface_language_hint": "မီနူး၊ ခလုတ်နှင့် စာသားများအတွက် ဘာသာစကားကို ရွေးပါ။ အပြည့်အစုံပြောင်းရန် ပြန်ဖွင့်ပါ။",
        "save_settings": "သိမ်း",
    },
    "th": {
        "app_title": "ผู้ช่วยแปล AI",
        "ready": "พร้อม",
        "translate_tab": "แปล",
        "settings_tab": "ตั้งค่า",
        "font_tab": "ขนาดตัวอักษร",
        "display_tab": "ภาษา UI",
        "translate": "แปล",
        "copy_output": "คัดลอก",
        "clear": "ล้าง",
        "ui_language": "ภาษาอินเทอร์เฟซ",
        "interface_language_title": "ภาษาอินเทอร์เฟซ",
        "interface_language_hint": "เลือกภาษาของเมนู ปุ่ม และข้อความ รีสตาร์ทเพื่อให้มีผลครบถ้วน",
        "save_settings": "บันทึก",
    },
    "vi": {
        "app_title": "Trợ lý dịch AI",
        "ready": "Sẵn sàng",
        "translate_tab": "Dịch",
        "settings_tab": "Cài đặt",
        "font_tab": "Cỡ chữ",
        "display_tab": "Giao diện",
        "translate": "Dịch",
        "copy_output": "Sao chép",
        "clear": "Xóa",
        "ui_language": "Ngôn ngữ giao diện",
        "interface_language_title": "Ngôn ngữ giao diện",
        "interface_language_hint": "Chọn ngôn ngữ menu, nút và thông báo. Khởi động lại để áp dụng đầy đủ.",
        "save_settings": "Lưu",
    },
    "id": {
        "app_title": "Asisten Terjemahan AI",
        "ready": "Siap",
        "translate_tab": "Terjemah",
        "settings_tab": "Pengaturan",
        "font_tab": "Ukuran teks",
        "display_tab": "Antarmuka",
        "translate": "Terjemah",
        "copy_output": "Salin",
        "clear": "Hapus",
        "ui_language": "Bahasa antarmuka",
        "interface_language_title": "Bahasa antarmuka",
        "interface_language_hint": "Pilih bahasa menu, tombol, dan pesan. Mulai ulang agar seluruh tampilan berubah.",
        "save_settings": "Simpan",
    },
    "nl": {
        "app_title": "AI vertaalassistent",
        "ready": "Gereed",
        "translate_tab": "Vertalen",
        "settings_tab": "Instellingen",
        "font_tab": "Tekstgrootte",
        "display_tab": "Interface",
        "translate": "Vertalen",
        "copy_output": "Kopiëren",
        "clear": "Wissen",
        "ui_language": "Interfacetaal",
        "interface_language_title": "Interfacetaal",
        "interface_language_hint": "Kies de taal voor menu's, knoppen en meldingen. Herstart voor volledige toepassing.",
        "save_settings": "Opslaan",
    },
    "pl": {
        "app_title": "Asystent tłumaczenia AI",
        "ready": "Gotowe",
        "translate_tab": "Tłumacz",
        "settings_tab": "Ustawienia",
        "font_tab": "Rozmiar tekstu",
        "display_tab": "Interfejs",
        "translate": "Tłumacz",
        "copy_output": "Kopiuj",
        "clear": "Wyczyść",
        "ui_language": "Język interfejsu",
        "interface_language_title": "Język interfejsu",
        "interface_language_hint": "Wybierz język menu, przycisków i komunikatów. Uruchom ponownie, aby zastosować w pełni.",
        "save_settings": "Zapisz",
    },
    "tr": {
        "app_title": "AI Çeviri Asistanı",
        "ready": "Hazır",
        "translate_tab": "Çevir",
        "settings_tab": "Ayarlar",
        "font_tab": "Metin boyutu",
        "display_tab": "Arayüz",
        "translate": "Çevir",
        "copy_output": "Kopyala",
        "clear": "Temizle",
        "ui_language": "Arayüz dili",
        "interface_language_title": "Arayüz dili",
        "interface_language_hint": "Menü, düğme ve iletilerin dilini seçin. Tam uygulama için yeniden başlatın.",
        "save_settings": "Kaydet",
    },
    "sv": {
        "app_title": "AI-översättningsassistent",
        "ready": "Redo",
        "translate_tab": "Översätt",
        "settings_tab": "Inställningar",
        "font_tab": "Textstorlek",
        "display_tab": "Gränssnitt",
        "translate": "Översätt",
        "copy_output": "Kopiera",
        "clear": "Rensa",
        "ui_language": "Gränssnittsspråk",
        "interface_language_title": "Gränssnittsspråk",
        "interface_language_hint": "Välj språk för menyer, knappar och meddelanden. Starta om för full effekt.",
        "save_settings": "Spara",
    },
    "uk": {
        "app_title": "AI помічник перекладу",
        "ready": "Готово",
        "translate_tab": "Переклад",
        "settings_tab": "Налаштування",
        "font_tab": "Розмір тексту",
        "display_tab": "Інтерфейс",
        "translate": "Перекласти",
        "copy_output": "Копіювати",
        "clear": "Очистити",
        "ui_language": "Мова інтерфейсу",
        "interface_language_title": "Мова інтерфейсу",
        "interface_language_hint": "Виберіть мову меню, кнопок і повідомлень. Перезапустіть застосунок для повного оновлення.",
        "save_settings": "Зберегти",
    },
    "el": {
        "app_title": "Βοηθός μετάφρασης AI",
        "ready": "Έτοιμο",
        "translate_tab": "Μετάφραση",
        "settings_tab": "Ρυθμίσεις",
        "font_tab": "Μέγεθος κειμένου",
        "display_tab": "Διεπαφή",
        "translate": "Μετάφραση",
        "copy_output": "Αντιγραφή",
        "clear": "Καθαρισμός",
        "ui_language": "Γλώσσα διεπαφής",
        "interface_language_title": "Γλώσσα διεπαφής",
        "interface_language_hint": "Επιλέξτε γλώσσα για μενού, κουμπιά και μηνύματα. Κάντε επανεκκίνηση για πλήρη εφαρμογή.",
        "save_settings": "Αποθήκευση",
    },
    "he": {
        "app_title": "עוזר תרגום AI",
        "ready": "מוכן",
        "translate_tab": "תרגום",
        "settings_tab": "הגדרות",
        "font_tab": "גודל טקסט",
        "display_tab": "ממשק",
        "translate": "תרגם",
        "copy_output": "העתק",
        "clear": "נקה",
        "ui_language": "שפת ממשק",
        "interface_language_title": "שפת ממשק",
        "interface_language_hint": "בחר שפה לתפריטים, כפתורים והודעות. הפעל מחדש כדי להחיל באופן מלא.",
        "save_settings": "שמור",
    },
}

for code, text in EXTRA_UI_TEXT.items():
    UI_TEXT[code] = {**UI_TEXT["en"], **text}

GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
    "gemini-3.1-flash-lite-preview",
]

GROQ_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]

DEFAULT_CONFIG = {
    "always_on_top": False,
    "ui_language": "zh-CN",
    "translation_mode": "google",
    "use_ai": False,
    "ai_provider": "gemini",
    "gemini_keys": "",
    "groq_keys": "",
    "gemini_model": "gemini-2.0-flash",
    "groq_model": "llama-3.3-70b-versatile",
    "translation_platform": "Google",
    "back_platform": "Google",
    "microsoft_key": "",
    "microsoft_region": "",
    "my_languages": ["en", "zh-CN", "ja"],
    "their_languages": ["zh-CN", "en", "ja"],
    "source_lang": "en",
    "target_lang": "zh-CN",
    "country": "",
    "gender": "不指定",
    "back_translate": True,
    "input_font_size": 13,
    "output_font_size": 13,
    "back_font_size": 11,
}


@dataclass
class TranslationResult:
    text: str
    back_text: str
    provider: str
    warning: str = ""


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return DEFAULT_CONFIG.copy()

    config = DEFAULT_CONFIG.copy()
    config.update({key: value for key, value in data.items() if key in config})
    if config.get("translation_mode") not in ("ai", "google"):
        config["translation_mode"] = "ai" if config.get("use_ai") else "google"
    config["use_ai"] = config.get("translation_mode") == "ai"
    if config.get("ai_provider") not in ("gemini", "groq"):
        config["ai_provider"] = "gemini"
    if config.get("ui_language") not in UI_LANGUAGE_NAMES:
        config["ui_language"] = "zh-CN"
    for size_key, default_size in (
        ("input_font_size", 13),
        ("output_font_size", 13),
        ("back_font_size", 11),
    ):
        try:
            config[size_key] = min(32, max(8, int(config.get(size_key, default_size))))
        except (TypeError, ValueError):
            config[size_key] = default_size
    config["my_languages"] = normalize_language_list(config.get("my_languages"), DEFAULT_CONFIG["my_languages"])
    config["their_languages"] = normalize_language_list(config.get("their_languages"), DEFAULT_CONFIG["their_languages"])

    if config.get("source_lang") not in LANGUAGE_NAMES:
        config["source_lang"] = config["my_languages"][0]
    if config.get("target_lang") not in LANGUAGE_NAMES:
        config["target_lang"] = config["their_languages"][0]
    return config


def save_config(config: dict) -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=2)


def normalize_language_list(value, fallback: list[str]) -> list[str]:
    result = []
    if isinstance(value, list):
        for code in value:
            if code in LANGUAGE_NAMES and code not in result:
                result.append(code)

    for code in fallback:
        if len(result) >= 3:
            break
        if code in LANGUAGE_NAMES and code not in result:
            result.append(code)

    return result[:3]


def api_keys(raw: str) -> list[str]:
    return [line.strip() for line in raw.splitlines() if line.strip()]


def read_http_json(url: str, payload: object | None = None, headers: dict | None = None, timeout: int = 30):
    data = None
    request_headers = {"User-Agent": "AI-Translator-App/1.0"}
    if headers:
        request_headers.update(headers)

    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    req = request.Request(url, data=data, headers=request_headers)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:400]}") from exc
    except URLError as exc:
        raise RuntimeError(f"网络连接失败：{exc.reason}") from exc

    return json.loads(body)


def speech_culture(language_code: str) -> str:
    return SPEECH_CULTURES.get(language_code, language_code)


def _powershell_base64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def clean_powershell_error(detail: str) -> str:
    detail = detail.strip()
    if detail.startswith("#< CLIXML"):
        parts = re.findall(r'<S S="Error">(.*?)</S>', detail, flags=re.DOTALL)
        detail = "\n".join(parts) if parts else detail

    detail = detail.replace("_x000D__x000A_", "\n").replace("_x000A_", "\n").replace("_x000D_", "\r")
    detail = re.sub(r"<[^>]+>", " ", detail)
    detail = unescape(detail)
    detail = re.sub(r"\s+", " ", detail).strip()

    if "Windows 语音识别包" in detail and "没有安装" in detail:
        culture_match = re.search(r"没有安装\s+([A-Za-z]{2,3}(?:-[A-Za-z0-9]+)?)\s+的 Windows 语音识别包", detail)
        culture = culture_match.group(1) if culture_match else "当前语言"
        return (
            f"系统没有安装 {culture} 的 Windows 语音识别包。"
            "请在 Windows 设置 > 时间和语言 > 语言和区域 中为该语言添加“语音识别”，"
            "或者先切换到已经安装语音识别的输入语言。"
        )
    return detail or "Windows 语音服务执行失败。"


def run_powershell_script(script: str, timeout: int = 30) -> str:
    if not IS_WINDOWS:
        raise RuntimeError("当前语音功能仅支持 Windows。")

    script = (
        "$ProgressPreference = 'SilentlyContinue'\n"
        "$ErrorActionPreference = 'Stop'\n"
        "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8\n"
        + script
    )
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-STA",
            "-ExecutionPolicy",
            "Bypass",
            "-EncodedCommand",
            encoded,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        creationflags=CREATE_NO_WINDOW,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(clean_powershell_error(detail))
    return completed.stdout.strip()


def recognize_speech(language_code: str, seconds: int = 8) -> str:
    culture_b64 = _powershell_base64(speech_culture(language_code))
    script = f"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Speech
$cultureName = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{culture_b64}'))
$culture = [System.Globalization.CultureInfo]::GetCultureInfo($cultureName)
$recognizer = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() |
    Where-Object {{ $_.Culture.Name -eq $culture.Name -or $_.Culture.TwoLetterISOLanguageName -eq $culture.TwoLetterISOLanguageName }} |
    Select-Object -First 1
if ($null -eq $recognizer) {{
    throw "没有安装 $cultureName 的 Windows 语音识别包。请在系统语言设置里添加该语言的语音识别。"
}}
$engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine $recognizer
try {{
    $engine.SetInputToDefaultAudioDevice()
    $grammar = New-Object System.Speech.Recognition.DictationGrammar
    $engine.LoadGrammar($grammar)
    $result = $engine.Recognize([TimeSpan]::FromSeconds({int(seconds)}))
    if ($null -eq $result -or [string]::IsNullOrWhiteSpace($result.Text)) {{
        throw "没有识别到语音。"
    }}
    Write-Output $result.Text
}} finally {{
    $engine.Dispose()
}}
"""
    return run_powershell_script(script, timeout=seconds + 8).strip()


def speak_text(text: str, language_code: str) -> None:
    text_b64 = _powershell_base64(text)
    culture_b64 = _powershell_base64(speech_culture(language_code))
    script = f"""
Add-Type -AssemblyName System.Speech
$text = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{text_b64}'))
$cultureName = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{culture_b64}'))
$culture = [System.Globalization.CultureInfo]::GetCultureInfo($cultureName)
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {{
    $synth.SetOutputToDefaultAudioDevice()
    $voice = $synth.GetInstalledVoices() |
        Where-Object {{
            $_.Enabled -and ($_.VoiceInfo.Culture.Name -eq $culture.Name -or $_.VoiceInfo.Culture.TwoLetterISOLanguageName -eq $culture.TwoLetterISOLanguageName)
        }} |
        Select-Object -First 1
    if ($null -ne $voice) {{
        $synth.SelectVoice($voice.VoiceInfo.Name)
    }}
    $synth.Volume = 100
    $synth.Rate = 0
    $synth.Speak($text)
}} finally {{
    $synth.Dispose()
}}
"""
    run_powershell_script(script, timeout=max(20, min(120, len(text) // 8 + 20)))


GOOGLE_LANGUAGE_MAP = {
    "pt-BR": "pt",
    "pt-PT": "pt",
}


def google_language_code(language_code: str) -> str:
    return GOOGLE_LANGUAGE_MAP.get(language_code, language_code)


def google_translate(text: str, source_lang: str, target_lang: str) -> str:
    params = parse.urlencode(
        {
            "client": "gtx",
            "sl": google_language_code(source_lang),
            "tl": google_language_code(target_lang),
            "dt": "t",
            "q": text,
        }
    )
    data = read_http_json(f"https://translate.googleapis.com/translate_a/single?{params}", timeout=20)
    parts = data[0] if data and isinstance(data, list) else []
    translated = "".join(part[0] for part in parts if part and part[0])
    if not translated:
        raise RuntimeError("Google 翻译没有返回内容")
    return translated


MICROSOFT_LANGUAGE_MAP = {
    "zh-CN": "zh-Hans",
    "zh-TW": "zh-Hant",
    "pt-BR": "pt",
    "pt-PT": "pt",
    "tl": "fil",
}


def microsoft_language_code(language_code: str) -> str:
    return MICROSOFT_LANGUAGE_MAP.get(language_code, language_code)


def microsoft_translate(text: str, source_lang: str, target_lang: str, config: dict | None = None) -> str:
    config = config or {}
    key = (config.get("microsoft_key") or os.environ.get("MICROSOFT_TRANSLATOR_KEY") or "").strip()
    region = (config.get("microsoft_region") or os.environ.get("MICROSOFT_TRANSLATOR_REGION") or "").strip()
    if not key:
        raise RuntimeError("Microsoft 回翻译需要 Microsoft Translator API KEY。请在设置页填写，或设置 MICROSOFT_TRANSLATOR_KEY 环境变量。")

    params = parse.urlencode(
        {
            "api-version": "3.0",
            "from": microsoft_language_code(source_lang),
            "to": microsoft_language_code(target_lang),
        }
    )
    headers = {
        "Accept": "application/json",
        "Ocp-Apim-Subscription-Key": key,
    }
    if region:
        headers["Ocp-Apim-Subscription-Region"] = region

    data = read_http_json(
        f"https://api.cognitive.microsofttranslator.com/translate?{params}",
        payload=[{"Text": text}],
        headers=headers,
        timeout=20,
    )
    translations = data[0].get("translations", []) if data and isinstance(data, list) else []
    translated = translations[0].get("text", "").strip() if translations else ""
    if not translated:
        raise RuntimeError("Microsoft 翻译没有返回内容")
    return translated


def regular_translate(text: str, source_lang: str, target_lang: str, platform: str = "Google", config: dict | None = None) -> tuple[str, str]:
    if platform == "Microsoft":
        return microsoft_translate(text, source_lang, target_lang, config), "Microsoft"
    return google_translate(text, source_lang, target_lang), "Google"


def translation_prompt(text: str, source_lang: str, target_lang: str, config: dict, back_translate: bool = False) -> str:
    source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
    target_name = LANGUAGE_NAMES.get(target_lang, target_lang)
    country = config.get("country", "").strip() or "未指定"
    gender = config.get("gender", "不指定")
    purpose = "This is a back translation for checking meaning." if back_translate else "This is a direct translation."
    return (
        f"{purpose}\n"
        f"Translate from {source_name} to {target_name}.\n"
        f"Country or regional context: {country}.\n"
        f"Speaker gender: {gender}.\n"
        "If the target language uses grammatical gender, honorifics, or regional wording, choose forms that match the context.\n"
        "Return only the translated text. Do not add explanations, labels, markdown, or quotes.\n\n"
        "Text:\n"
        f"{text}"
    )


def gemini_translate(text: str, source_lang: str, target_lang: str, config: dict, key: str, back_translate: bool = False) -> str:
    model = config.get("gemini_model") or GEMINI_MODELS[0]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{parse.quote(model)}:generateContent?key={parse.quote(key)}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": translation_prompt(text, source_lang, target_lang, config, back_translate)}],
            }
        ],
        "generationConfig": {"temperature": 0.2},
    }
    data = read_http_json(url, payload=payload)
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini 没有返回候选结果")
    parts = candidates[0].get("content", {}).get("parts", [])
    translated = "".join(part.get("text", "") for part in parts).strip()
    if not translated:
        raise RuntimeError("Gemini 返回内容为空")
    return translated


def groq_translate(text: str, source_lang: str, target_lang: str, config: dict, key: str, back_translate: bool = False) -> str:
    payload = {
        "model": config.get("groq_model") or GROQ_MODELS[0],
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": "You are a precise translation engine. Return only the translated text.",
            },
            {
                "role": "user",
                "content": translation_prompt(text, source_lang, target_lang, config, back_translate),
            },
        ],
    }
    data = read_http_json(
        "https://api.groq.com/openai/v1/chat/completions",
        payload=payload,
        headers={"Authorization": f"Bearer {key}"},
    )
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("Groq 没有返回候选结果")
    translated = choices[0].get("message", {}).get("content", "").strip()
    if not translated:
        raise RuntimeError("Groq 返回内容为空")
    return translated


def translate_with_ai(text: str, source_lang: str, target_lang: str, config: dict, back_translate: bool = False) -> tuple[str, str]:
    provider = config.get("ai_provider", "gemini")
    key_field = "gemini_keys" if provider == "gemini" else "groq_keys"
    keys = api_keys(config.get(key_field, ""))
    if not keys:
        raise RuntimeError("没有可用的 AI API KEY")

    errors = []
    for index, key in enumerate(keys, start=1):
        try:
            if provider == "gemini":
                return gemini_translate(text, source_lang, target_lang, config, key, back_translate), f"Gemini #{index}"
            return groq_translate(text, source_lang, target_lang, config, key, back_translate), f"Groq #{index}"
        except Exception as exc:
            errors.append(f"第 {index} 个密钥失败：{exc}")

    raise RuntimeError("; ".join(errors))


def translate_text(text: str, source_lang: str, target_lang: str, config: dict, back_translate: bool = False) -> tuple[str, str, str]:
    if back_translate:
        translated, provider = regular_translate(text, source_lang, target_lang, config.get("back_platform", "Google"), config)
        return translated, provider, ""

    translation_mode = config.get("translation_mode") or ("ai" if config.get("use_ai") else "google")
    if translation_mode == "ai":
        translated, provider = translate_with_ai(text, source_lang, target_lang, config, back_translate)
        return translated, provider, ""

    translated, provider = regular_translate(text, source_lang, target_lang, config.get("translation_platform", "Google"), config)
    return translated, provider, ""


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0, background=BG)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas, style="App.TFrame")
        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.content.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._update_width)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _update_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _update_width(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _on_mousewheel(self, event):
        if self.winfo_containing(event.x_root, event.y_root) in self.winfo_children_recursive():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def winfo_children_recursive(self):
        children = set()
        stack = [self]
        while stack:
            widget = stack.pop()
            children.add(widget)
            stack.extend(widget.winfo_children())
        return children


class LanguageBar(ttk.Frame):
    def __init__(self, parent, on_change):
        super().__init__(parent, style="Panel.TFrame")
        self.on_change = on_change
        self.language_codes = []
        self.active_code = ""
        self.buttons = []
        self.more_var = tk.StringVar()

        self.button_area = ttk.Frame(self, style="Panel.TFrame")
        self.button_area.grid(row=0, column=0, sticky="w")
        self.more_var.set("更多语言")
        self.more = ttk.Combobox(self, textvariable=self.more_var, values=LANGUAGE_LABELS, state="readonly", width=8)
        self.more.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.more.bind("<<ComboboxSelected>>", self._select_from_more)

    def set_languages(self, language_codes: list[str], active_code: str):
        self.language_codes = normalize_language_list(language_codes, language_codes or DEFAULT_CONFIG["my_languages"])
        self.active_code = active_code if active_code in LANGUAGE_NAMES else self.language_codes[0]
        if self.active_code not in self.language_codes:
            self.language_codes[-1] = self.active_code
        self.render()

    def render(self):
        for button in self.buttons:
            button.destroy()
        self.buttons.clear()

        for index, code in enumerate(self.language_codes):
            is_active = code == self.active_code
            button = tk.Button(
                self.button_area,
                text=LANGUAGE_NAMES.get(code, code),
                relief="flat",
                borderwidth=0,
                padx=7,
                pady=4,
                cursor="hand2",
                font="TranslatorLangBoldFont" if is_active else "TranslatorLangFont",
                fg=BLUE if is_active else TEXT,
                bg=PANEL,
                activeforeground=BLUE,
                activebackground=PANEL,
                command=lambda value=code: self._select(value),
            )
            button.grid(row=0, column=index, sticky="w")
            self.buttons.append(button)

    def _select(self, code: str):
        self.active_code = code
        self.render()
        self.on_change(code, self.language_codes)

    def _select_from_more(self, _event=None):
        code = LANGUAGE_CODES.get(self.more_var.get())
        if not code:
            return
        if code not in self.language_codes:
            self.language_codes[-1] = code
        self._select(code)
        self.more_var.set("更多语言")


class LanguagePicker(ttk.Frame):
    def __init__(self, parent, title: str, selected: list[str]):
        super().__init__(parent, style="Panel.TFrame")
        self.title = title
        self.selected = list(selected)
        self.buttons: dict[str, tk.Button] = {}
        self.columns = 0

        self.title_label = ttk.Label(self, text=title, style="Section.TLabel")
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.grid_columnconfigure(0, weight=1)
        self.options = ttk.Frame(self, style="Panel.TFrame")
        self.options.grid(row=1, column=0, sticky="ew")
        self.bind("<Configure>", self._on_options_resize)
        self.options.bind("<Configure>", self._on_options_resize)
        self._render_options()

    def _column_count(self) -> int:
        width = max(self.options.winfo_width(), self.winfo_width())
        if width >= 560:
            return 4
        if width >= 390:
            return 3
        if width >= 230:
            return 2
        return 1

    def _on_options_resize(self, _event=None):
        columns = self._column_count()
        if columns != self.columns:
            self._render_options(columns)
        else:
            self._update_button_geometry(columns)

    def _render_options(self, columns: int | None = None):
        columns = columns or self._column_count()
        if columns == self.columns and self.buttons:
            self._update_button_geometry(columns)
            return
        self.columns = columns
        for button in self.buttons.values():
            button.destroy()
        self.buttons.clear()
        for column in range(4):
            self.options.grid_columnconfigure(column, weight=0)
        for column in range(columns):
            self.options.grid_columnconfigure(column, weight=1, uniform="language")
        wrap = self._button_wraplength(columns)
        for index, (code, label) in enumerate(LANGUAGES):
            button = tk.Button(
                self.options,
                relief="solid",
                borderwidth=1,
                padx=4,
                pady=5,
                cursor="hand2",
                font="TranslatorBodyFont",
                justify="center",
                anchor="center",
                wraplength=wrap,
                command=lambda value=code: self.toggle(value),
            )
            button.grid(row=index // columns, column=index % columns, sticky="nsew", padx=3, pady=4)
            self.buttons[code] = button
        self.refresh()

    def _button_wraplength(self, columns: int) -> int:
        width = max(self.options.winfo_width(), self.winfo_width(), 180)
        return max(76, min(180, int((width - (columns - 1) * 6) / max(columns, 1)) - 18))

    def _update_button_geometry(self, columns: int | None = None):
        columns = columns or self.columns or self._column_count()
        wrap = self._button_wraplength(columns)
        self.title_label.configure(wraplength=max(120, self.winfo_width() - 8))
        for button in self.buttons.values():
            button.configure(wraplength=wrap)

    def toggle(self, code: str):
        if code in self.selected:
            if len(self.selected) == 1:
                messagebox.showinfo("保留一种语言", f"{self.title} 至少需要选择一种语言。")
                return
            self.selected.remove(code)
        else:
            if len(self.selected) >= 3:
                messagebox.showinfo("最多三种语言", f"{self.title} 最多只能选择三种语言。")
                return
            self.selected.append(code)
        self.refresh()

    def refresh(self):
        for code, button in self.buttons.items():
            active = code in self.selected
            button.configure(
                text=("✓ " if active else "  ") + LANGUAGE_NAMES[code],
                fg=BLUE if active else TEXT,
                bg="#eaf2ff" if active else PANEL,
                activebackground="#eaf2ff" if active else "#f2f5f9",
                highlightbackground=BLUE if active else BORDER,
            )

    def value(self) -> list[str]:
        return list(self.selected)

    def set_selected(self, selected: list[str]):
        self.selected = normalize_language_list(selected, self.selected or [LANGUAGES[0][0]])
        self.refresh()


class TranslatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self.result_queue: queue.Queue[tuple[str, TranslationResult | Exception]] = queue.Queue()
        self.translation_running = False
        self.speech_running = False
        self.speaking_running = False
        self.ui_scale = 1.0
        self.last_external_hwnd = None
        self.pending_translation_source = ""
        self.last_translation_source = ""
        self.ready_to_paste = False
        self.ready_to_send_external = False
        self.external_send_hwnd = None
        self.external_focus_hwnd = None
        self.external_caret_point = None
        self.external_restore_topmost = False
        self.current_page = "translate"
        self.process_id = int(KERNEL32.GetCurrentProcessId()) if IS_WINDOWS and KERNEL32 is not None else 0

        self.title(self._ui("app_title"))
        self._apply_window_icon()
        self.minsize(330, 240)
        self.geometry("700x540")
        self.configure(bg=BG)
        self._setup_fonts()
        self._setup_styles()
        self.attributes("-topmost", bool(self.config_data.get("always_on_top")))
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._refresh_language_bars()
        self._refresh_back_panel()
        self.bind("<Configure>", self._on_window_resize)
        self.bind("<Return>", self._submit_from_keyboard)
        self.bind("<Control-Return>", self._submit_from_keyboard)
        self.after(250, self._track_foreground_window)
        self.after(100, self._poll_results)

    def _apply_window_icon(self):
        icon_path = resource_path(APP_ICON)
        if not icon_path.exists():
            return
        try:
            self.iconbitmap(default=str(icon_path))
        except tk.TclError:
            pass

    def _ui(self, key: str) -> str:
        language = self.config_data.get("ui_language", "zh-CN")
        return UI_TEXT.get(language, UI_TEXT["zh-CN"]).get(key, UI_TEXT["zh-CN"].get(key, key))

    def _setup_fonts(self):
        self.font_specs = {
            "header": ("TranslatorHeaderFont", 18, "bold"),
            "section": ("TranslatorSectionFont", 13, "bold"),
            "body": ("TranslatorBodyFont", 10, "normal"),
            "body_bold": ("TranslatorBodyBoldFont", 10, "bold"),
            "muted": ("TranslatorMutedFont", 9, "normal"),
            "status": ("TranslatorStatusFont", 9, "normal"),
            "lang": ("TranslatorLangFont", 11, "normal"),
            "lang_bold": ("TranslatorLangBoldFont", 11, "bold"),
            "mono": ("TranslatorMonoFont", 10, "normal"),
            "input": ("TranslatorInputFont", self.config_data.get("input_font_size", 13), "normal"),
            "output": ("TranslatorOutputFont", self.config_data.get("output_font_size", 13), "normal"),
            "back": ("TranslatorBackFont", self.config_data.get("back_font_size", 11), "normal"),
        }
        self.fonts = {}
        for key, (name, size, weight) in self.font_specs.items():
            family = "Consolas" if key == "mono" else "Microsoft YaHei UI"
            self.fonts[key] = tkfont.Font(self, name=name, family=family, size=size, weight=weight)

    def _font_name(self, key: str) -> str:
        return self.font_specs[key][0]

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("App.TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("Header.TLabel", background=BG, foreground=TEXT, font=self._font_name("header"))
        style.configure("Section.TLabel", background=PANEL, foreground=TEXT, font=self._font_name("section"))
        style.configure("SectionBg.TLabel", background=BG, foreground=TEXT, font=self._font_name("section"))
        style.configure("Label.TLabel", background=PANEL, foreground=TEXT, font=self._font_name("body"))
        style.configure("Muted.TLabel", background=PANEL, foreground=MUTED, font=self._font_name("muted"))
        style.configure("MutedBg.TLabel", background=BG, foreground=MUTED, font=self._font_name("muted"))
        style.configure("Status.TLabel", background=BG, foreground=MUTED, font=self._font_name("status"))
        style.configure("Primary.TButton", font=self._font_name("body_bold"))
        style.configure("TButton", font=self._font_name("body"))
        style.configure("Small.TButton", font=self._font_name("muted"), padding=(4, 1))
        style.configure("TCheckbutton", background=PANEL, foreground=TEXT, font=self._font_name("body"))
        style.configure("TRadiobutton", background=PANEL, foreground=TEXT, font=self._font_name("body"))

    def _build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ttk.Frame(self, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        header.grid_columnconfigure(0, weight=1)
        ttk.Label(header, text=self._ui("app_title"), style="Header.TLabel").grid(row=0, column=0, sticky="w")
        self.status_var = tk.StringVar(value=self._ui("ready"))
        ttk.Label(header, textvariable=self.status_var, style="Status.TLabel").grid(row=0, column=1, sticky="e")

        self.nav = ttk.Frame(self, style="App.TFrame")
        self.nav.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 4))
        self.nav.grid_columnconfigure(4, weight=1)
        self.nav_buttons = {}
        for column, (page_name, text) in enumerate(
            (
                ("translate", self._ui("translate_tab")),
                ("settings", self._ui("settings_tab")),
                ("font", self._ui("font_tab")),
                ("display", self._ui("display_tab")),
            )
        ):
            button = tk.Button(
                self.nav,
                text=text,
                width=9,
                height=1,
                relief="solid",
                borderwidth=1,
                cursor="hand2",
                font=self._font_name("body_bold"),
                fg=TEXT,
                bg=PANEL,
                activebackground="#eaf2ff",
                command=lambda value=page_name: self.show_page(value),
            )
            button.grid(row=0, column=column, sticky="w", padx=(0, 4))
            self.nav_buttons[page_name] = button

        self.page_host = ttk.Frame(self, style="App.TFrame")
        self.page_host.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 8))
        self.page_host.grid_rowconfigure(0, weight=1)
        self.page_host.grid_columnconfigure(0, weight=1)

        self.translate_page = ttk.Frame(self.page_host, style="App.TFrame")
        self.settings_page = ttk.Frame(self.page_host, style="App.TFrame")
        self.font_page = ttk.Frame(self.page_host, style="App.TFrame")
        self.display_page = ttk.Frame(self.page_host, style="App.TFrame")
        for page in (self.translate_page, self.settings_page, self.font_page, self.display_page):
            page.grid(row=0, column=0, sticky="nsew")

        self._build_translate_page()
        self._build_settings_page()
        self._build_font_page()
        self._build_display_page()
        self.show_page("translate")

    def show_page(self, page_name: str):
        pages = {
            "translate": self.translate_page,
            "settings": self.settings_page,
            "font": self.font_page,
            "display": self.display_page,
        }
        self.current_page = page_name
        pages[page_name].tkraise()
        for name, button in self.nav_buttons.items():
            selected = name == page_name
            button.configure(bg="#eaf2ff" if selected else PANEL, fg=BLUE if selected else TEXT)
        if page_name == "translate":
            self.after_idle(self._focus_input_text_end)

    def _build_translate_page(self):
        page = self.translate_page
        page.grid_rowconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=0)
        page.grid_columnconfigure(0, weight=1)

        self.translate_panes = tk.PanedWindow(
            page,
            orient=tk.VERTICAL,
            sashwidth=7,
            sashrelief="raised",
            bd=0,
            bg=BG,
            opaqueresize=True,
        )
        self.translate_panes.grid(row=0, column=0, sticky="nsew", pady=(0, 6))

        self.source_panel = self._panel(self.translate_panes)
        self.source_panel.grid_rowconfigure(1, weight=1)
        self.source_panel.grid_columnconfigure(0, weight=1)
        top_source = ttk.Frame(self.source_panel, style="Panel.TFrame")
        top_source.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 2))
        top_source.grid_columnconfigure(0, weight=1)
        self.source_bar = LanguageBar(top_source, self._source_language_changed)
        self.source_bar.grid(row=0, column=0, sticky="w")
        self.input_text = tk.Text(
            self.source_panel,
            wrap="word",
            undo=True,
            relief="flat",
            font=self._font_name("input"),
            foreground=TEXT,
            background=PANEL,
            insertbackground=TEXT,
            padx=8,
            pady=6,
        )
        self.input_text.grid(row=1, column=0, sticky="nsew")
        self.input_text.bind("<Return>", self._submit_from_keyboard)
        self.input_text.bind("<Control-Return>", self._submit_from_keyboard)
        self.input_text.bind("<Shift-Return>", self._insert_newline)
        source_audio = ttk.Frame(self.source_panel, style="Panel.TFrame")
        source_audio.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 6))
        self.listen_button = ttk.Button(
            source_audio,
            text="🎙",
            width=3,
            style="Small.TButton",
            command=self.start_speech_input,
        )
        self.listen_button.grid(row=0, column=0, sticky="w")
        self.speak_input_button = ttk.Button(
            source_audio,
            text="🔊",
            width=3,
            style="Small.TButton",
            command=self.speak_input_text,
        )
        self.speak_input_button.grid(row=0, column=1, sticky="w", padx=(6, 0))
        self.clear_input_button = ttk.Button(
            source_audio,
            text=self._ui("clear"),
            width=6,
            style="Small.TButton",
            command=self.clear_texts,
        )
        self.clear_input_button.grid(row=0, column=2, sticky="w", padx=(6, 0))
        self.swap_button = ttk.Button(
            source_audio,
            text=self._ui("swap_languages"),
            width=9,
            style="Small.TButton",
            command=self.swap_languages,
        )
        self.swap_button.grid(row=0, column=3, sticky="w", padx=(6, 0))
        self.translate_panes.add(self.source_panel, minsize=54)

        self.target_panel = self._panel(self.translate_panes)
        self.target_panel.grid_rowconfigure(1, weight=1)
        self.target_panel.grid_columnconfigure(0, weight=1)
        self.target_bar = LanguageBar(self.target_panel, self._target_language_changed)
        self.target_bar.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 2))
        self.output_text = tk.Text(
            self.target_panel,
            wrap="word",
            relief="flat",
            font=self._font_name("output"),
            foreground=TEXT,
            background=PANEL,
            padx=8,
            pady=6,
            state="disabled",
        )
        self.output_text.grid(row=1, column=0, sticky="nsew")
        target_audio = ttk.Frame(self.target_panel, style="Panel.TFrame")
        target_audio.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 6))
        self.speak_output_button = ttk.Button(
            target_audio,
            text="🔊",
            width=3,
            style="Small.TButton",
            command=self.speak_output_text,
        )
        self.speak_output_button.grid(row=0, column=0, sticky="w")
        self.translate_panes.add(self.target_panel, minsize=54)

        self.back_panel = self._panel(self.translate_panes)
        self.back_panel.grid_rowconfigure(1, weight=1)
        self.back_panel.grid_columnconfigure(0, weight=1)
        self.back_title_var = tk.StringVar(value=self._ui("back_translation"))
        ttk.Label(self.back_panel, textvariable=self.back_title_var, style="Section.TLabel").grid(
            row=0, column=0, sticky="w", padx=8, pady=(6, 0)
        )
        self.back_text = tk.Text(
            self.back_panel,
            wrap="word",
            relief="flat",
            height=3,
            font=self._font_name("back"),
            foreground=TEXT,
            background=PANEL,
            padx=8,
            pady=4,
            state="disabled",
        )
        self.back_text.grid(row=1, column=0, sticky="nsew")
        self.translate_panes.add(self.back_panel, minsize=38)
        self.back_panel_visible = True
        self.after(200, self._set_initial_pane_sizes)

        actions = ttk.Frame(page, style="App.TFrame")
        actions.grid(row=1, column=0, sticky="ew")
        actions.grid_columnconfigure(0, weight=1)
        self.translate_button = ttk.Button(actions, text=self._ui("translate"), style="Primary.TButton", command=self._submit_from_keyboard)
        self.translate_button.grid(row=0, column=1, padx=(8, 0))
        ttk.Button(actions, text=self._ui("copy_output"), command=self.copy_output).grid(row=0, column=2, padx=(8, 0))
        ttk.Button(actions, text=self._ui("clear"), command=self.clear_texts).grid(row=0, column=3, padx=(8, 0))

    def _build_settings_page(self):
        scroller = ScrollableFrame(self.settings_page)
        scroller.grid(row=0, column=0, sticky="nsew")
        self.settings_page.grid_rowconfigure(0, weight=1)
        self.settings_page.grid_columnconfigure(0, weight=1)
        content = scroller.content
        content.grid_columnconfigure(0, weight=1)

        top_panel = self._panel(content)
        top_panel.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        top_panel.grid_columnconfigure(1, weight=1)
        self.always_on_top_var = tk.BooleanVar(value=bool(self.config_data.get("always_on_top")))
        ttk.Checkbutton(
            top_panel,
            text=self._ui("always_on_top"),
            variable=self.always_on_top_var,
            command=lambda: self.attributes("-topmost", bool(self.always_on_top_var.get())),
        ).grid(
            row=0, column=0, sticky="w", padx=18, pady=(16, 8)
        )
        self.ui_language_var = tk.StringVar(value=UI_LANGUAGE_NAMES.get(self.config_data.get("ui_language", "zh-CN"), "中文（简体）"))
        self._labeled_combo(top_panel, 1, self._ui("ui_language"), self.ui_language_var, UI_LANGUAGE_LABELS)

        engine_panel = self._panel(content)
        engine_panel.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        engine_panel.grid_columnconfigure(0, weight=1)
        ttk.Label(engine_panel, text=self._ui("translation_method"), style="Section.TLabel").grid(
            row=0, column=0, sticky="w", padx=18, pady=(18, 12)
        )

        selected_mode = self.config_data.get("translation_mode") or ("ai" if self.config_data.get("use_ai") else "google")
        self.translation_mode_var = tk.StringVar(value=selected_mode)
        self.use_ai_var = tk.BooleanVar(value=selected_mode == "ai")
        self.translation_platform_var = tk.StringVar(value=self.config_data.get("translation_platform", "Google"))
        self.back_platform_var = tk.StringVar(value=self.config_data.get("back_platform", "Google"))
        mode_frame = ttk.Frame(engine_panel, style="Panel.TFrame")
        mode_frame.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 12))
        ttk.Radiobutton(
            mode_frame,
            text=self._ui("ai_translate"),
            variable=self.translation_mode_var,
            value="ai",
            command=self._refresh_translation_method_visibility,
        ).grid(row=0, column=0, padx=(0, 22))
        ttk.Radiobutton(
            mode_frame,
            text=self._ui("google_translate"),
            variable=self.translation_mode_var,
            value="google",
            command=self._refresh_translation_method_visibility,
        ).grid(row=0, column=1)

        self.ai_options_panel = ttk.Frame(engine_panel, style="Panel.TFrame")
        self.ai_options_panel.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))
        self.ai_options_panel.grid_columnconfigure(1, weight=1)

        self.ai_provider_var = tk.StringVar(value=self.config_data.get("ai_provider", "gemini"))
        provider_frame = ttk.Frame(self.ai_options_panel, style="Panel.TFrame")
        provider_frame.grid(row=0, column=1, sticky="w", padx=12, pady=8)
        ttk.Label(self.ai_options_panel, text=self._ui("ai_platform"), style="Label.TLabel").grid(row=0, column=0, sticky="w", padx=0, pady=8)
        ttk.Radiobutton(
            provider_frame,
            text="Gemini",
            variable=self.ai_provider_var,
            value="gemini",
            command=self._refresh_translation_method_visibility,
        ).grid(row=0, column=0, padx=(0, 18))
        ttk.Radiobutton(
            provider_frame,
            text="Groq AI",
            variable=self.ai_provider_var,
            value="groq",
            command=self._refresh_translation_method_visibility,
        ).grid(row=0, column=1)

        self.country_var = tk.StringVar(value=self.config_data.get("country", ""))
        self.gender_var = tk.StringVar(value=self.config_data.get("gender", "不指定"))
        self._labeled_entry(self.ai_options_panel, 1, self._ui("country"), self.country_var, "输入国家名称，AI会用当地特色翻译")
        self._labeled_combo(self.ai_options_panel, 2, self._ui("gender"), self.gender_var, ["不指定", "男性", "女性", "中性"])

        self.gemini_panel = ttk.Frame(self.ai_options_panel, style="Panel.TFrame")
        self.gemini_panel.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.gemini_panel.grid_columnconfigure(1, weight=1)
        self.gemini_keys = self._labeled_text(self.gemini_panel, 0, self._ui("gemini_key"), self.config_data.get("gemini_keys", ""))
        ttk.Label(self.gemini_panel, text=self._ui("gemini_key_help"), style="Muted.TLabel").grid(
            row=1, column=1, sticky="w", padx=12, pady=(0, 8)
        )
        self.gemini_model_var = tk.StringVar(value=self.config_data.get("gemini_model", GEMINI_MODELS[0]))
        self._labeled_combo(self.gemini_panel, 2, self._ui("gemini_model"), self.gemini_model_var, GEMINI_MODELS)

        self.groq_panel = ttk.Frame(self.ai_options_panel, style="Panel.TFrame")
        self.groq_panel.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.groq_panel.grid_columnconfigure(1, weight=1)
        self.groq_keys = self._labeled_text(self.groq_panel, 0, self._ui("groq_key"), self.config_data.get("groq_keys", ""))
        ttk.Label(self.groq_panel, text=self._ui("groq_key_help"), style="Muted.TLabel").grid(
            row=1, column=1, sticky="w", padx=12, pady=(0, 8)
        )
        self.groq_model_var = tk.StringVar(value=self.config_data.get("groq_model", GROQ_MODELS[1]))
        self._labeled_combo(self.groq_panel, 2, self._ui("groq_model"), self.groq_model_var, GROQ_MODELS)

        self.language_panel = self._panel(content)
        self.language_panel.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self.language_panel.grid_columnconfigure(0, weight=1)
        self.language_panel.grid_columnconfigure(1, weight=1)
        self.my_picker = LanguagePicker(self.language_panel, self._ui("my_languages"), self.config_data.get("my_languages", []))
        self.their_picker = LanguagePicker(self.language_panel, self._ui("their_languages"), self.config_data.get("their_languages", []))
        self.language_panel.bind("<Configure>", self._layout_language_pickers)
        self.after_idle(self._layout_language_pickers)

        back_panel = self._panel(content)
        back_panel.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        back_panel.grid_columnconfigure(1, weight=1)
        ttk.Label(back_panel, text=self._ui("back_setting"), style="Section.TLabel").grid(row=0, column=0, sticky="w", padx=18, pady=(18, 12))
        self.back_translate_var = tk.BooleanVar(value=bool(self.config_data.get("back_translate")))
        ttk.Radiobutton(back_panel, text=self._ui("back_yes"), variable=self.back_translate_var, value=True).grid(
            row=1, column=0, sticky="w", padx=18, pady=6
        )
        ttk.Radiobutton(back_panel, text=self._ui("back_no"), variable=self.back_translate_var, value=False).grid(
            row=2, column=0, sticky="w", padx=18, pady=6
        )
        ttk.Label(back_panel, text=self._ui("back_platform_setting"), style="Label.TLabel").grid(
            row=3, column=0, sticky="w", padx=18, pady=(12, 6)
        )
        back_platform_frame = ttk.Frame(back_panel, style="Panel.TFrame")
        back_platform_frame.grid(row=4, column=0, sticky="w", padx=18, pady=(0, 18))
        ttk.Radiobutton(
            back_platform_frame,
            text=self._ui("google_translate"),
            variable=self.back_platform_var,
            value="Google",
        ).grid(row=0, column=0, padx=(0, 22))
        ttk.Radiobutton(
            back_platform_frame,
            text=self._ui("microsoft_translate"),
            variable=self.back_platform_var,
            value="Microsoft",
        ).grid(row=0, column=1)
        self.microsoft_key_var = tk.StringVar(value=self.config_data.get("microsoft_key", ""))
        self.microsoft_region_var = tk.StringVar(value=self.config_data.get("microsoft_region", ""))
        self._labeled_entry(back_panel, 5, self._ui("microsoft_key"), self.microsoft_key_var, "")
        self._labeled_entry(back_panel, 6, self._ui("microsoft_region"), self.microsoft_region_var, "例如 eastasia / westus / global")
        ttk.Label(back_panel, text=self._ui("microsoft_key_help"), style="Muted.TLabel").grid(
            row=7, column=1, sticky="w", padx=12, pady=(0, 18)
        )

        actions = ttk.Frame(content, style="App.TFrame")
        actions.grid(row=4, column=0, sticky="ew", pady=(0, 24))
        actions.grid_columnconfigure(0, weight=1)
        ttk.Button(actions, text=self._ui("save_settings"), style="Primary.TButton", command=self.save_settings).grid(row=0, column=1, padx=(8, 0))
        self._refresh_translation_method_visibility()

    def _layout_language_pickers(self, event=None):
        if not hasattr(self, "language_panel"):
            return
        width = event.width if event is not None else self.language_panel.winfo_width()
        stacked = width < 620
        mode = "stacked" if stacked else "side_by_side"
        if getattr(self, "language_layout_mode", None) == mode:
            self.my_picker._on_options_resize()
            self.their_picker._on_options_resize()
            return

        self.language_layout_mode = mode
        self.my_picker.grid_forget()
        self.their_picker.grid_forget()

        if stacked:
            self.language_panel.grid_columnconfigure(0, weight=1, uniform="")
            self.language_panel.grid_columnconfigure(1, weight=0, uniform="")
            self.language_panel.grid_rowconfigure(0, weight=0)
            self.language_panel.grid_rowconfigure(1, weight=0)
            self.my_picker.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 8))
            self.their_picker.grid(row=1, column=0, sticky="ew", padx=18, pady=(8, 18))
        else:
            self.language_panel.grid_columnconfigure(0, weight=1, uniform="language_picker")
            self.language_panel.grid_columnconfigure(1, weight=1, uniform="language_picker")
            self.language_panel.grid_rowconfigure(0, weight=0)
            self.language_panel.grid_rowconfigure(1, weight=0)
            self.my_picker.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
            self.their_picker.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)

        self.after_idle(self.my_picker._on_options_resize)
        self.after_idle(self.their_picker._on_options_resize)

    def _build_font_page(self):
        self.font_page.grid_columnconfigure(0, weight=1)
        panel = self._panel(self.font_page)
        panel.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        panel.grid_columnconfigure(1, weight=1)

        ttk.Label(panel, text=self._ui("text_size_title"), style="Section.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", padx=18, pady=(18, 6)
        )
        ttk.Label(panel, text=self._ui("text_size_hint"), style="Muted.TLabel").grid(
            row=1, column=0, columnspan=3, sticky="w", padx=18, pady=(0, 12)
        )

        self.input_font_size_var = tk.IntVar(value=self.config_data.get("input_font_size", 13))
        self.output_font_size_var = tk.IntVar(value=self.config_data.get("output_font_size", 13))
        self.back_font_size_var = tk.IntVar(value=self.config_data.get("back_font_size", 11))
        self._font_size_control(panel, 2, self._ui("input_font_size"), self.input_font_size_var)
        self._font_size_control(panel, 3, self._ui("output_font_size"), self.output_font_size_var)
        self._font_size_control(panel, 4, self._ui("back_font_size"), self.back_font_size_var)

        actions = ttk.Frame(panel, style="Panel.TFrame")
        actions.grid(row=5, column=0, columnspan=3, sticky="ew", padx=18, pady=(10, 18))
        actions.grid_columnconfigure(0, weight=1)
        ttk.Button(actions, text=self._ui("save_settings"), style="Primary.TButton", command=self.save_settings).grid(row=0, column=1)

    def _build_display_page(self):
        self.display_page.grid_columnconfigure(0, weight=1)
        panel = self._panel(self.display_page)
        panel.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        panel.grid_columnconfigure(1, weight=1)

        ttk.Label(panel, text=self._ui("interface_language_title"), style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(18, 6)
        )
        ttk.Label(panel, text=self._ui("interface_language_hint"), style="Muted.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 12)
        )
        self._labeled_combo(panel, 2, self._ui("ui_language"), self.ui_language_var, UI_LANGUAGE_LABELS)

        actions = ttk.Frame(panel, style="Panel.TFrame")
        actions.grid(row=3, column=0, columnspan=2, sticky="ew", padx=18, pady=(10, 18))
        actions.grid_columnconfigure(0, weight=1)
        ttk.Button(actions, text=self._ui("save_settings"), style="Primary.TButton", command=self.save_settings).grid(row=0, column=1)

    def _font_size_control(self, parent, row: int, label: str, variable: tk.IntVar):
        ttk.Label(parent, text=label, style="Label.TLabel").grid(row=row, column=0, sticky="w", padx=18, pady=8)
        scale = tk.Scale(
            parent,
            variable=variable,
            from_=8,
            to=32,
            orient="horizontal",
            showvalue=False,
            resolution=1,
            bg=PANEL,
            highlightthickness=0,
            command=lambda _value: self._apply_text_fonts(),
        )
        scale.grid(row=row, column=1, sticky="ew", padx=12, pady=8)
        spinbox = tk.Spinbox(
            parent,
            from_=8,
            to=32,
            width=5,
            textvariable=variable,
            command=self._apply_text_fonts,
            font=self._font_name("body"),
        )
        spinbox.grid(row=row, column=2, sticky="w", padx=(0, 18), pady=8)
        spinbox.bind("<KeyRelease>", lambda _event: self._apply_text_fonts())

    def _safe_font_size(self, variable: tk.IntVar, fallback: int) -> int:
        try:
            return min(32, max(8, int(variable.get())))
        except (tk.TclError, ValueError):
            return fallback

    def _apply_text_fonts(self):
        input_size = self._safe_font_size(getattr(self, "input_font_size_var", tk.IntVar(value=13)), 13)
        output_size = self._safe_font_size(getattr(self, "output_font_size_var", tk.IntVar(value=13)), 13)
        back_size = self._safe_font_size(getattr(self, "back_font_size_var", tk.IntVar(value=11)), 11)
        self.config_data["input_font_size"] = input_size
        self.config_data["output_font_size"] = output_size
        self.config_data["back_font_size"] = back_size
        self._apply_font_scale(force=True)

    def _on_window_resize(self, event):
        if event.widget is not self:
            return
        scale = min(event.width / 700, event.height / 540)
        scale = max(0.58, min(1.35, scale))
        if abs(scale - self.ui_scale) < 0.04:
            return
        self.ui_scale = scale
        self._apply_font_scale()

    def _scaled_size(self, size: int) -> int:
        return max(8, int(round(size * self.ui_scale)))

    def _apply_font_scale(self, force: bool = False):
        for key, (_name, base_size, _weight) in self.font_specs.items():
            if key == "input":
                base_size = self.config_data.get("input_font_size", 13)
            elif key == "output":
                base_size = self.config_data.get("output_font_size", 13)
            elif key == "back":
                base_size = self.config_data.get("back_font_size", 11)
            if key in ("input", "output", "back"):
                self.fonts[key].configure(size=max(8, int(base_size)))
            else:
                self.fonts[key].configure(size=self._scaled_size(int(base_size)))

        if hasattr(self, "translate_panes") and hasattr(self, "back_panel"):
            try:
                self.translate_panes.paneconfigure(self.source_panel, minsize=max(48, int(round(64 * self.ui_scale))))
                self.translate_panes.paneconfigure(self.target_panel, minsize=max(48, int(round(64 * self.ui_scale))))
                self.translate_panes.paneconfigure(self.back_panel, minsize=max(34, int(round(44 * self.ui_scale))))
            except tk.TclError:
                pass

    def _set_initial_pane_sizes(self):
        if not hasattr(self, "translate_panes") or not self.back_panel_visible:
            return
        height = self.translate_panes.winfo_height()
        if height < 150:
            self.after(150, self._set_initial_pane_sizes)
            return
        try:
            back_height = max(36, min(82, int(height * 0.16)))
            main_height = max(52, (height - back_height) // 2)
            self.translate_panes.sash_place(0, 0, main_height)
            self.translate_panes.sash_place(1, 0, main_height * 2)
        except tk.TclError:
            pass

    def _own_hwnd(self):
        try:
            hwnd = int(self.winfo_id())
            if IS_WINDOWS and USER32 is not None:
                root_hwnd = int(USER32.GetAncestor(hwnd, GA_ROOT))
                return root_hwnd or hwnd
            return hwnd
        except tk.TclError:
            return 0

    def _window_process_id(self, hwnd) -> int:
        if not IS_WINDOWS or USER32 is None:
            return 0
        try:
            process_id = ctypes.c_ulong()
            USER32.GetWindowThreadProcessId(int(hwnd), ctypes.byref(process_id))
            return int(process_id.value)
        except Exception:
            return 0

    def _track_foreground_window(self):
        if IS_WINDOWS and USER32 is not None:
            try:
                hwnd = int(USER32.GetForegroundWindow())
                if self._is_valid_external_window(hwnd):
                    self.last_external_hwnd = hwnd
            except Exception:
                pass
        self.after(250, self._track_foreground_window)

    def _is_valid_external_window(self, hwnd) -> bool:
        if not IS_WINDOWS or USER32 is None:
            return False
        try:
            hwnd = int(hwnd or 0)
        except (TypeError, ValueError):
            return False
        if hwnd == 0 or hwnd == self._own_hwnd():
            return False
        if self._window_process_id(hwnd) == self.process_id:
            return False
        return bool(USER32.IsWindow(hwnd) and USER32.IsWindowVisible(hwnd))

    def _next_external_window(self):
        if not IS_WINDOWS or USER32 is None:
            return None
        hwnd = self._own_hwnd()
        for _ in range(80):
            hwnd = int(USER32.GetWindow(hwnd, GW_HWNDNEXT))
            if not hwnd:
                break
            if self._is_valid_external_window(hwnd):
                return hwnd
        return None

    def _paste_target_hwnd(self):
        if self._is_valid_external_window(self.last_external_hwnd):
            return self.last_external_hwnd
        return self._next_external_window()

    def _focus_external_window(self, hwnd) -> bool:
        if not self._is_valid_external_window(hwnd):
            return False
        try:
            if USER32.IsIconic(hwnd):
                USER32.ShowWindow(hwnd, SW_RESTORE)
            current_thread = int(KERNEL32.GetCurrentThreadId())
            target_thread = int(USER32.GetWindowThreadProcessId(hwnd, None))
            foreground = int(USER32.GetForegroundWindow())
            if self._window_process_id(foreground) == self.process_id and self._is_valid_external_window(self.last_external_hwnd):
                foreground = int(self.last_external_hwnd)
            foreground_thread = int(USER32.GetWindowThreadProcessId(foreground, None)) if foreground else 0

            attached_target = False
            attached_foreground = False
            if target_thread and target_thread != current_thread:
                attached_target = bool(USER32.AttachThreadInput(current_thread, target_thread, True))
            if foreground_thread and foreground_thread != current_thread and foreground_thread != target_thread:
                attached_foreground = bool(USER32.AttachThreadInput(current_thread, foreground_thread, True))
            try:
                USER32.BringWindowToTop(hwnd)
                return bool(USER32.SetForegroundWindow(hwnd))
            finally:
                if attached_foreground:
                    USER32.AttachThreadInput(current_thread, foreground_thread, False)
                if attached_target:
                    USER32.AttachThreadInput(current_thread, target_thread, False)
        except Exception:
            return False

    def _send_ctrl_v(self):
        if not IS_WINDOWS or USER32 is None:
            return
        USER32.keybd_event(VK_CONTROL, 0, 0, 0)
        USER32.keybd_event(VK_V, 0, 0, 0)
        USER32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
        USER32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

    def _send_enter_key(self):
        if not IS_WINDOWS or USER32 is None:
            return
        USER32.keybd_event(VK_RETURN, 0, 0, 0)
        USER32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)

    def _send_ctrl_v_and_remember_external_focus(self, hwnd):
        self._send_ctrl_v()
        self.after(180, lambda: self._remember_external_input_focus(hwnd))

    def _remember_external_input_focus(self, hwnd):
        if not IS_WINDOWS or USER32 is None or not self._is_valid_external_window(hwnd):
            return
        try:
            thread_id = int(USER32.GetWindowThreadProcessId(int(hwnd), None))
            info = GUITHREADINFO()
            info.cbSize = ctypes.sizeof(GUITHREADINFO)
            if not USER32.GetGUIThreadInfo(thread_id, ctypes.byref(info)):
                return

            focus_hwnd = int(info.hwndFocus or info.hwndCaret or 0)
            if focus_hwnd and USER32.IsWindow(focus_hwnd):
                self.external_focus_hwnd = focus_hwnd

            rect = info.rcCaret
            x = int((rect.left + rect.right) / 2) if rect.right or rect.left else int(rect.left)
            y = int((rect.top + rect.bottom) / 2) if rect.bottom or rect.top else int(rect.top)
            if x > 0 and y > 0:
                self.external_caret_point = (x, y)
        except Exception:
            pass

    def _restore_external_input_focus(self):
        if not IS_WINDOWS or USER32 is None:
            return
        focus_hwnd = int(self.external_focus_hwnd or 0)
        if focus_hwnd and USER32.IsWindow(focus_hwnd):
            try:
                current_thread = int(KERNEL32.GetCurrentThreadId())
                focus_thread = int(USER32.GetWindowThreadProcessId(focus_hwnd, None))
                attached = False
                if focus_thread and focus_thread != current_thread:
                    attached = bool(USER32.AttachThreadInput(current_thread, focus_thread, True))
                try:
                    USER32.SetFocus(focus_hwnd)
                finally:
                    if attached:
                        USER32.AttachThreadInput(current_thread, focus_thread, False)
            except Exception:
                pass

        if self.external_caret_point:
            try:
                x, y = self.external_caret_point
                USER32.SetCursorPos(int(x), int(y))
                USER32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                USER32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            except Exception:
                pass

    def _focus_app_window(self):
        try:
            self.lift()
            self.focus_force()
            if IS_WINDOWS and USER32 is not None:
                USER32.SetForegroundWindow(self._own_hwnd())
        except tk.TclError:
            pass

    def _focus_input_text_end(self):
        if not hasattr(self, "input_text"):
            return
        self._focus_app_window()
        try:
            self.input_text.focus_set()
            self.input_text.mark_set("insert", "end-1c")
            self.input_text.see("insert")
        except tk.TclError:
            pass

    def _restore_clipboard_text(self, text: str | None, had_text: bool):
        if not had_text:
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(text or "")
        except tk.TclError:
            pass

    def _panel(self, parent):
        frame = ttk.Frame(parent, style="Panel.TFrame", padding=1)
        frame.configure(borderwidth=1, relief="solid")
        return frame

    def _labeled_entry(self, parent, row: int, label: str, variable: tk.StringVar, placeholder: str = ""):
        ttk.Label(parent, text=label, style="Label.TLabel").grid(row=row, column=0, sticky="w", padx=18, pady=8)
        entry = ttk.Entry(parent, textvariable=variable, font=self._font_name("body"))
        entry.grid(row=row, column=1, sticky="ew", padx=12, pady=8)
        if placeholder and not variable.get():
            entry.insert(0, "")
            entry.configure(foreground=TEXT)
        return entry

    def _labeled_combo(self, parent, row: int, label: str, variable: tk.StringVar, values: list[str]):
        ttk.Label(parent, text=label, style="Label.TLabel").grid(row=row, column=0, sticky="w", padx=18, pady=8)
        combo = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", font=self._font_name("body"), width=30)
        combo.grid(row=row, column=1, sticky="w", padx=12, pady=8)
        if variable.get() not in values:
            variable.set(values[0])
        return combo

    def _labeled_text(self, parent, row: int, label: str, value: str):
        ttk.Label(parent, text=label, style="Label.TLabel").grid(row=row, column=0, sticky="nw", padx=18, pady=8)
        text = tk.Text(
            parent,
            height=4,
            wrap="none",
            font=self._font_name("mono"),
            foreground=TEXT,
            background=PANEL,
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=7,
        )
        text.insert("1.0", value)
        text.grid(row=row, column=1, sticky="ew", padx=12, pady=8)
        return text

    def _refresh_translation_method_visibility(self):
        if not hasattr(self, "ai_options_panel"):
            return

        use_ai = self.translation_mode_var.get() == "ai"
        self.use_ai_var.set(use_ai)
        if not use_ai:
            self.ai_options_panel.grid_remove()
            return

        self.ai_options_panel.grid()
        if self.ai_provider_var.get() == "gemini":
            self.gemini_panel.grid()
            self.groq_panel.grid_remove()
        else:
            self.gemini_panel.grid_remove()
            self.groq_panel.grid()

    def _submit_from_keyboard(self, _event=None):
        if getattr(self, "current_page", "translate") != "translate":
            return None

        current_input = self.input_text.get("1.0", "end").strip()
        output = self._get_text(self.output_text)
        if self.ready_to_send_external and output and current_input == self.last_translation_source:
            self.send_external_message_and_clear()
        elif self.ready_to_paste and output and current_input == self.last_translation_source:
            self.paste_output_to_external()
        else:
            focus_widget = self.focus_get()
            if focus_widget is not self.input_text and not current_input:
                self._focus_input_text_end()
                return "break"
            self.start_translation()
        return "break"

    def _insert_newline(self, _event=None):
        self.input_text.insert("insert", "\n")
        return "break"

    def _sync_settings_from_widgets(self, validate: bool = False) -> bool:
        if not hasattr(self, "my_picker"):
            return True

        my_languages = self.my_picker.value()
        their_languages = self.their_picker.value()
        if validate and (not my_languages or not their_languages):
            messagebox.showerror("设置错误", "我的语言和对方语言都至少需要选择一种。")
            return False

        if not my_languages:
            my_languages = self.config_data.get("my_languages", DEFAULT_CONFIG["my_languages"])
        if not their_languages:
            their_languages = self.config_data.get("their_languages", DEFAULT_CONFIG["their_languages"])

        ui_language = UI_LANGUAGE_CODES.get(self.ui_language_var.get(), "zh-CN")
        translation_mode = self.translation_mode_var.get() if self.translation_mode_var.get() in ("ai", "google") else "google"
        ai_provider = self.ai_provider_var.get() if self.ai_provider_var.get() in ("gemini", "groq") else "gemini"
        translation_platform = self.translation_platform_var.get() if self.translation_platform_var.get() in ("Google", "Microsoft") else "Google"
        back_platform = self.back_platform_var.get() if self.back_platform_var.get() in ("Google", "Microsoft") else "Google"
        input_font_size = self._safe_font_size(self.input_font_size_var, self.config_data.get("input_font_size", 13))
        output_font_size = self._safe_font_size(self.output_font_size_var, self.config_data.get("output_font_size", 13))
        back_font_size = self._safe_font_size(self.back_font_size_var, self.config_data.get("back_font_size", 11))

        self.config_data.update(
            {
                "always_on_top": self.always_on_top_var.get(),
                "ui_language": ui_language,
                "translation_mode": translation_mode,
                "use_ai": translation_mode == "ai",
                "ai_provider": ai_provider,
                "country": self.country_var.get().strip(),
                "gender": self.gender_var.get(),
                "gemini_keys": self.gemini_keys.get("1.0", "end").strip(),
                "groq_keys": self.groq_keys.get("1.0", "end").strip(),
                "gemini_model": self.gemini_model_var.get(),
                "groq_model": self.groq_model_var.get(),
                "translation_platform": translation_platform,
                "back_platform": back_platform,
                "microsoft_key": self.microsoft_key_var.get().strip(),
                "microsoft_region": self.microsoft_region_var.get().strip(),
                "my_languages": normalize_language_list(my_languages, DEFAULT_CONFIG["my_languages"]),
                "their_languages": normalize_language_list(their_languages, DEFAULT_CONFIG["their_languages"]),
                "back_translate": self.back_translate_var.get(),
                "input_font_size": input_font_size,
                "output_font_size": output_font_size,
                "back_font_size": back_font_size,
            }
        )

        if self.config_data.get("source_lang") not in self.config_data["my_languages"]:
            self.config_data["source_lang"] = self.config_data["my_languages"][0]
        if self.config_data.get("target_lang") not in self.config_data["their_languages"]:
            self.config_data["target_lang"] = self.config_data["their_languages"][0]

        return True

    def _refresh_language_bars(self):
        self.source_bar.set_languages(self.config_data.get("my_languages", []), self.config_data.get("source_lang", "en"))
        self.target_bar.set_languages(self.config_data.get("their_languages", []), self.config_data.get("target_lang", "zh-CN"))

    def _refresh_back_panel(self):
        source_name = LANGUAGE_NAMES.get(self.config_data.get("source_lang", "en"), "")
        self.back_title_var.set(self._ui("back_to").format(source=source_name))
        if self.config_data.get("back_translate"):
            if not getattr(self, "back_panel_visible", False):
                self.translate_panes.add(self.back_panel, minsize=max(34, int(round(44 * self.ui_scale))))
                self.back_panel_visible = True
                self.after(50, self._set_initial_pane_sizes)
        else:
            if getattr(self, "back_panel_visible", False):
                self.translate_panes.forget(self.back_panel)
                self.back_panel_visible = False
                self.after(100, self._set_two_pane_sizes)

    def _set_two_pane_sizes(self):
        if not hasattr(self, "translate_panes") or getattr(self, "back_panel_visible", False):
            return
        height = self.translate_panes.winfo_height()
        if height < 160:
            self.after(150, self._set_two_pane_sizes)
            return
        try:
            self.translate_panes.sash_place(0, 0, height // 2)
        except tk.TclError:
            pass

    def _source_language_changed(self, code: str, language_codes: list[str]):
        self.config_data["source_lang"] = code
        self.config_data["my_languages"] = normalize_language_list(language_codes, self.config_data["my_languages"])
        if hasattr(self, "my_picker"):
            self.my_picker.set_selected(self.config_data["my_languages"])
        self._refresh_back_panel()

    def _target_language_changed(self, code: str, language_codes: list[str]):
        self.config_data["target_lang"] = code
        self.config_data["their_languages"] = normalize_language_list(language_codes, self.config_data["their_languages"])
        if hasattr(self, "their_picker"):
            self.their_picker.set_selected(self.config_data["their_languages"])

    def swap_languages(self):
        source = self.config_data.get("source_lang")
        target = self.config_data.get("target_lang")
        self.config_data["source_lang"], self.config_data["target_lang"] = target, source
        self._ensure_in_language_list("my_languages", target)
        self._ensure_in_language_list("their_languages", source)

        output = self._get_text(self.output_text)
        if output:
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", output)
            self._set_text(self.output_text, "")
            self._set_text(self.back_text, "")
            self.ready_to_paste = False

        self._refresh_language_bars()
        self._refresh_back_panel()
        self.status_var.set(self._ui("swapped"))

    def _ensure_in_language_list(self, field: str, code: str):
        if code not in LANGUAGE_NAMES:
            return
        languages = normalize_language_list(self.config_data.get(field), DEFAULT_CONFIG[field])
        if code not in languages:
            languages[-1] = code
        self.config_data[field] = languages

    def start_translation(self):
        if self.translation_running:
            return
        self._sync_settings_from_widgets(validate=False)
        text = self.input_text.get("1.0", "end").strip()
        if not text:
            self.status_var.set(self._ui("input_required"))
            return

        source_lang = self.config_data.get("source_lang", "en")
        target_lang = self.config_data.get("target_lang", "zh-CN")
        if source_lang == target_lang:
            self.status_var.set(self._ui("same_language"))
            return

        config_snapshot = self.config_data.copy()
        self.translation_running = True
        self.ready_to_paste = False
        self.ready_to_send_external = False
        self.external_send_hwnd = None
        self.external_focus_hwnd = None
        self.external_caret_point = None
        self.external_restore_topmost = False
        self.pending_translation_source = text
        self.translate_button.configure(state="disabled")
        self.status_var.set(self._ui("translating"))
        self._set_text(self.output_text, "")
        self._set_text(self.back_text, "")

        thread = threading.Thread(
            target=self._translation_worker,
            args=(text, source_lang, target_lang, config_snapshot),
            daemon=True,
        )
        thread.start()

    def _translation_worker(self, text: str, source_lang: str, target_lang: str, config: dict):
        try:
            translated, provider, warning = translate_text(text, source_lang, target_lang, config)
            back_text = ""
            provider_label = provider
            if config.get("back_translate"):
                back_text, back_provider, back_warning = translate_text(translated, target_lang, source_lang, config, back_translate=True)
                provider_label = f"{provider_label} / 回译 {back_provider}"
                warning = warning or back_warning
            self.result_queue.put(("success", TranslationResult(translated, back_text, provider_label, warning)))
        except Exception as exc:
            self.result_queue.put(("error", exc))

    def _poll_results(self):
        try:
            status, payload = self.result_queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_results)
            return

        self.translation_running = False
        self.translate_button.configure(state="normal")

        if status == "success" and isinstance(payload, TranslationResult):
            self._set_text(self.output_text, payload.text)
            self._set_text(self.back_text, payload.back_text)
            self.last_translation_source = self.pending_translation_source
            self.ready_to_paste = bool(payload.text)
            self.ready_to_send_external = False
            self.external_send_hwnd = None
            self.external_focus_hwnd = None
            self.external_caret_point = None
            self.external_restore_topmost = False
            if payload.warning:
                self.status_var.set(f"{self._ui('done').format(provider=payload.provider)}（{payload.warning[:80]}）")
            else:
                self.status_var.set(self._ui("done").format(provider=payload.provider))
        elif isinstance(payload, Exception):
            self.ready_to_paste = False
            self.ready_to_send_external = False
            self.external_send_hwnd = None
            self.external_focus_hwnd = None
            self.external_caret_point = None
            self.external_restore_topmost = False
            self.status_var.set(self._ui("failed"))
            messagebox.showerror(self._ui("failed"), str(payload))

        self.after(100, self._poll_results)

    def save_settings(self):
        if not self._sync_settings_from_widgets(validate=True):
            return

        save_config(self.config_data)
        self.attributes("-topmost", bool(self.config_data.get("always_on_top")))
        self._refresh_language_bars()
        self._refresh_back_panel()
        self.status_var.set(self._ui("settings_saved"))
        messagebox.showinfo(self._ui("settings_saved"), self._ui("settings_saved_body"))

    def copy_output(self):
        output = self._get_text(self.output_text)
        if not output:
            self.status_var.set(self._ui("no_output"))
            return
        self.clipboard_clear()
        self.clipboard_append(output)
        self.status_var.set(self._ui("copied"))

    def start_speech_input(self):
        if self.speech_running:
            return
        self._sync_settings_from_widgets(validate=False)
        source_lang = self.config_data.get("source_lang", "en")
        self.speech_running = True
        self.listen_button.configure(state="disabled")
        self.status_var.set(self._ui("listening"))
        threading.Thread(target=self._speech_input_worker, args=(source_lang,), daemon=True).start()

    def _speech_input_worker(self, source_lang: str):
        try:
            text = recognize_speech(source_lang)
            self.after(0, self._speech_input_finished, text, None)
        except Exception as exc:
            self.after(0, self._speech_input_finished, "", exc)

    def _speech_input_finished(self, text: str, error: Exception | None):
        self.speech_running = False
        self.listen_button.configure(state="normal")
        if error is not None:
            self.status_var.set(self._ui("speech_failed"))
            messagebox.showerror(self._ui("speech_failed"), str(error))
            return

        current = self.input_text.get("1.0", "end-1c")
        if current and not current.endswith((" ", "\n")):
            self.input_text.insert("insert", " ")
        self.input_text.insert("insert", text)
        self.status_var.set(self._ui("speech_done"))

    def speak_input_text(self):
        self._start_speaking(self.input_text.get("1.0", "end").strip(), self.config_data.get("source_lang", "en"))

    def speak_output_text(self):
        self._start_speaking(self._get_text(self.output_text), self.config_data.get("target_lang", "zh-CN"))

    def _start_speaking(self, text: str, language_code: str):
        if self.speaking_running:
            return
        if not text:
            self.status_var.set(self._ui("speech_no_text"))
            return

        self.speaking_running = True
        self.speak_input_button.configure(state="disabled")
        self.speak_output_button.configure(state="disabled")
        self.status_var.set(self._ui("speaking"))
        threading.Thread(target=self._speak_worker, args=(text, language_code), daemon=True).start()

    def _speak_worker(self, text: str, language_code: str):
        try:
            speak_text(text, language_code)
            self.after(0, self._speak_finished, None)
        except Exception as exc:
            self.after(0, self._speak_finished, exc)

    def _speak_finished(self, error: Exception | None):
        self.speaking_running = False
        self.speak_input_button.configure(state="normal")
        self.speak_output_button.configure(state="normal")
        if error is not None:
            self.status_var.set(self._ui("speech_failed"))
            messagebox.showerror(self._ui("speech_failed"), str(error))
        else:
            self.status_var.set(self._ui("ready"))

    def paste_output_to_external(self):
        output = self._get_text(self.output_text)
        if not output:
            self.status_var.set(self._ui("no_output"))
            return

        if not IS_WINDOWS:
            self.copy_output()
            self.status_var.set(self._ui("paste_target_missing"))
            return

        hwnd = self._paste_target_hwnd()
        if not hwnd:
            self.copy_output()
            self.status_var.set(self._ui("paste_target_missing"))
            return

        had_clipboard_text = False
        old_clipboard_text = None
        try:
            old_clipboard_text = self.clipboard_get()
            had_clipboard_text = True
        except tk.TclError:
            pass

        self.clipboard_clear()
        self.clipboard_append(output)
        self.update()

        if not self._focus_external_window(hwnd):
            self.copy_output()
            self.status_var.set(self._ui("paste_failed"))
            return

        self.after(120, lambda: self._send_ctrl_v_and_remember_external_focus(hwnd))
        self.ready_to_paste = False
        self.ready_to_send_external = True
        self.external_send_hwnd = hwnd
        self.after(450, self._focus_input_text_end)
        self.after(900, lambda: self._restore_clipboard_text(old_clipboard_text, had_clipboard_text))
        self.status_var.set(self._ui("pasted_external"))

    def send_external_message_and_clear(self):
        if not IS_WINDOWS:
            self.status_var.set(self._ui("paste_target_missing"))
            return

        hwnd = self.external_send_hwnd if self._is_valid_external_window(self.external_send_hwnd) else self._paste_target_hwnd()
        if not hwnd:
            self.status_var.set(self._ui("paste_failed"))
            return

        try:
            self.external_restore_topmost = bool(self.attributes("-topmost"))
            if self.external_restore_topmost:
                self.attributes("-topmost", False)
        except tk.TclError:
            self.external_restore_topmost = False

        focused = self._focus_external_window(hwnd)
        if not focused and not self.external_caret_point:
            self._restore_topmost_after_external_send()
            self.status_var.set(self._ui("paste_failed"))
            return

        self.after(160, self._restore_external_input_focus)
        self.after(340, self._send_enter_key)
        self.after(560, self._clear_input_after_external_send)

    def _clear_input_after_external_send(self):
        self.input_text.delete("1.0", "end")
        self.ready_to_paste = False
        self.ready_to_send_external = False
        self.external_send_hwnd = None
        self.external_focus_hwnd = None
        self.external_caret_point = None
        self.pending_translation_source = ""
        self.last_translation_source = ""
        self.status_var.set(self._ui("sent_external"))
        self._restore_topmost_after_external_send()
        self._focus_input_text_end()

    def _restore_topmost_after_external_send(self):
        if not self.external_restore_topmost:
            return
        try:
            self.attributes("-topmost", True)
        except tk.TclError:
            pass
        self.external_restore_topmost = False

    def clear_texts(self):
        self.input_text.delete("1.0", "end")
        self._set_text(self.output_text, "")
        self._set_text(self.back_text, "")
        self.ready_to_paste = False
        self.ready_to_send_external = False
        self.external_send_hwnd = None
        self.external_focus_hwnd = None
        self.external_caret_point = None
        self.external_restore_topmost = False
        self.pending_translation_source = ""
        self.last_translation_source = ""
        self.status_var.set(self._ui("cleared"))

    def _get_text(self, widget: tk.Text) -> str:
        state = str(widget.cget("state"))
        if state == "disabled":
            widget.configure(state="normal")
            value = widget.get("1.0", "end").strip()
            widget.configure(state="disabled")
            return value
        return widget.get("1.0", "end").strip()

    def _set_text(self, widget: tk.Text, value: str):
        state = str(widget.cget("state"))
        if state == "disabled":
            widget.configure(state="normal")
        widget.delete("1.0", "end")
        if value:
            widget.insert("1.0", value)
        if state == "disabled":
            widget.configure(state="disabled")

    def _on_close(self):
        try:
            self._sync_settings_from_widgets(validate=False)
            save_config(self.config_data)
        finally:
            self.destroy()


if __name__ == "__main__":
    app = TranslatorApp()
    app.mainloop()
