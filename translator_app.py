import ctypes
import json
import queue
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox, ttk
from urllib import parse, request
from urllib.error import HTTPError, URLError


APP_TITLE = "AI 翻译助手"


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


CONFIG_PATH = app_base_dir() / "translator_config.json"

BLUE = "#1a73e8"
TEXT = "#1f3552"
MUTED = "#7a8799"
BORDER = "#d7dee8"
BG = "#f5f8fc"
PANEL = "#ffffff"

IS_WINDOWS = sys.platform.startswith("win")
if IS_WINDOWS:
    USER32 = ctypes.WinDLL("user32", use_last_error=True)
    KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
    SW_RESTORE = 9
    GA_ROOT = 2
    GW_HWNDNEXT = 2
    VK_CONTROL = 0x11
    VK_V = 0x56
    KEYEVENTF_KEYUP = 0x0002
else:
    USER32 = None
    KERNEL32 = None
    SW_RESTORE = 9
    GA_ROOT = 2
    GW_HWNDNEXT = 2
    VK_CONTROL = 0x11
    VK_V = 0x56
    KEYEVENTF_KEYUP = 0x0002


LANGUAGES = [
    ("zh-CN", "中文（简体）"),
    ("zh-TW", "中文（繁體）"),
    ("en", "英语"),
    ("ja", "日语"),
    ("ko", "韩语"),
    ("fr", "法语"),
    ("de", "德语"),
    ("es", "西班牙语"),
    ("it", "意大利语"),
    ("pt", "葡萄牙语"),
    ("ru", "俄语"),
    ("ar", "阿拉伯语"),
    ("hi", "印地语"),
    ("ne", "尼泊尔语"),
    ("my", "缅甸语"),
    ("th", "泰语"),
    ("vi", "越南语"),
    ("id", "印尼语"),
    ("nl", "荷兰语"),
    ("pl", "波兰语"),
    ("tr", "土耳其语"),
    ("sv", "瑞典语"),
    ("uk", "乌克兰语"),
    ("el", "希腊语"),
    ("he", "希伯来语"),
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
    ("ru", "Русский"),
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
        "swap_languages": "⇅ 交换语言",
        "translate": "翻译",
        "copy_output": "复制译文",
        "clear": "清空",
        "back_translation": "回翻译",
        "back_to": "回翻译为：{source}",
        "always_on_top": "软件界面永远置顶",
        "ui_language": "软件界面显示语言",
        "translation_method": "翻译方式",
        "ai_translate": "AI 翻译",
        "google_translate": "Google 翻译",
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
        "back_yes": "是，显示回翻译小界面",
        "back_no": "否，不进行回翻译",
        "save_settings": "保存设置",
        "text_size_title": "翻译框文字大小",
        "input_font_size": "输入文字大小",
        "output_font_size": "译文文字大小",
        "back_font_size": "回翻译文字大小",
        "text_size_hint": "这里控制输入、翻译、回翻译三个文字区域的大小；系统界面文字会随窗口缩放自动变化。",
        "settings_saved": "设置已保存",
        "settings_saved_body": "设置已经保存并应用。界面显示语言会在下次启动时完整生效。",
        "input_required": "请输入需要翻译的文字",
        "same_language": "上下语言相同，请先切换其中一个语言",
        "translating": "正在翻译...",
        "done": "完成：{provider}",
        "failed": "翻译失败",
        "copied": "译文已复制",
        "pasted_external": "译文已输入到外部窗口",
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
        "swap_languages": "⇅ Swap Languages",
        "translate": "Translate",
        "copy_output": "Copy",
        "clear": "Clear",
        "back_translation": "Back Translation",
        "back_to": "Back to: {source}",
        "always_on_top": "Always keep window on top",
        "ui_language": "Interface language",
        "translation_method": "Translation Method",
        "ai_translate": "AI Translate",
        "google_translate": "Google Translate",
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
        "back_yes": "Yes, show the back-translation box",
        "back_no": "No, do not back-translate",
        "save_settings": "Save Settings",
        "text_size_title": "Translation Box Text Size",
        "input_font_size": "Input text size",
        "output_font_size": "Translation text size",
        "back_font_size": "Back-translation text size",
        "text_size_hint": "These settings control the three text boxes. The rest of the interface scales automatically with the window.",
        "settings_saved": "Settings Saved",
        "settings_saved_body": "Settings have been saved and applied. The interface language fully applies after restart.",
        "input_required": "Enter text to translate",
        "same_language": "Source and target languages are the same.",
        "translating": "Translating...",
        "done": "Done: {provider}",
        "failed": "Translation failed",
        "copied": "Translation copied",
        "pasted_external": "Translation pasted into the external window",
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
        "back_yes": "はい、逆翻訳欄を表示する",
        "back_no": "いいえ、逆翻訳しない",
        "save_settings": "設定を保存",
        "text_size_title": "翻訳欄の文字サイズ",
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
    "swap_languages": "⇅ 交換語言",
    "copy_output": "複製譯文",
    "back_translation": "回翻譯",
    "back_to": "回翻譯為：{source}",
    "always_on_top": "軟體介面永遠置頂",
    "ui_language": "軟體介面顯示語言",
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
    "swap_languages": "⇅ 언어 교환",
    "translate": "번역",
    "copy_output": "번역 복사",
    "clear": "지우기",
    "back_translation": "역번역",
    "back_to": "역번역 대상: {source}",
    "always_on_top": "창을 항상 위에 표시",
    "ui_language": "인터페이스 언어",
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
    "swap_languages": "⇅ Échanger les langues",
    "translate": "Traduire",
    "copy_output": "Copier",
    "clear": "Effacer",
    "back_translation": "Rétro-traduction",
    "back_to": "Retour vers : {source}",
    "always_on_top": "Toujours au premier plan",
    "ui_language": "Langue de l’interface",
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
    "swap_languages": "⇅ Sprachen tauschen",
    "translate": "Übersetzen",
    "copy_output": "Kopieren",
    "clear": "Leeren",
    "back_translation": "Rückübersetzung",
    "back_to": "Zurück nach: {source}",
    "always_on_top": "Fenster immer im Vordergrund",
    "ui_language": "Sprache der Oberfläche",
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
    "swap_languages": "⇅ Intercambiar idiomas",
    "translate": "Traducir",
    "copy_output": "Copiar",
    "clear": "Borrar",
    "back_translation": "Retraducción",
    "back_to": "Retraducir a: {source}",
    "always_on_top": "Mantener ventana siempre arriba",
    "ui_language": "Idioma de la interfaz",
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
    "swap_languages": "⇅ Поменять языки",
    "translate": "Перевести",
    "copy_output": "Копировать",
    "clear": "Очистить",
    "back_translation": "Обратный перевод",
    "back_to": "Обратно на: {source}",
    "always_on_top": "Окно всегда поверх остальных",
    "ui_language": "Язык интерфейса",
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


def read_http_json(url: str, payload: dict | None = None, headers: dict | None = None, timeout: int = 30):
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


def google_translate(text: str, source_lang: str, target_lang: str) -> str:
    params = parse.urlencode(
        {
            "client": "gtx",
            "sl": source_lang,
            "tl": target_lang,
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
    translation_mode = config.get("translation_mode") or ("ai" if config.get("use_ai") else "google")
    if translation_mode == "ai":
        translated, provider = translate_with_ai(text, source_lang, target_lang, config, back_translate)
        return translated, provider, ""

    translated = google_translate(text, source_lang, target_lang)
    return translated, "Google", ""


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
        self.more = ttk.Combobox(self, textvariable=self.more_var, values=LANGUAGE_LABELS, state="readonly", width=9)
        self.more.grid(row=0, column=1, sticky="w", padx=(14, 0))
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
                padx=12,
                pady=7,
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

        ttk.Label(self, text=title, style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.grid_columnconfigure(0, weight=1)
        self.options = ttk.Frame(self, style="Panel.TFrame")
        self.options.grid(row=1, column=0, sticky="ew")
        self._render_options()

    def _render_options(self):
        columns = 4
        for index, (code, label) in enumerate(LANGUAGES):
            button = tk.Button(
                self.options,
                relief="solid",
                borderwidth=1,
                padx=10,
                pady=6,
                cursor="hand2",
                font="TranslatorBodyFont",
                command=lambda value=code: self.toggle(value),
            )
            button.grid(row=index // columns, column=index % columns, sticky="ew", padx=(0, 8), pady=(0, 8))
            self.options.grid_columnconfigure(index % columns, weight=1)
            self.buttons[code] = button
        self.refresh()

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
        self.ui_scale = 1.0
        self.last_external_hwnd = None
        self.pending_translation_source = ""
        self.last_translation_source = ""
        self.ready_to_paste = False
        self.process_id = int(KERNEL32.GetCurrentProcessId()) if IS_WINDOWS and KERNEL32 is not None else 0

        self.title(self._ui("app_title"))
        self.minsize(420, 320)
        self.geometry("780x620")
        self.configure(bg=BG)
        self._setup_fonts()
        self._setup_styles()
        self.attributes("-topmost", bool(self.config_data.get("always_on_top")))
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._refresh_language_bars()
        self._refresh_back_panel()
        self.bind("<Configure>", self._on_window_resize)
        self.after(250, self._track_foreground_window)
        self.after(100, self._poll_results)

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
        self.nav.grid_columnconfigure(3, weight=1)
        self.nav_buttons = {}
        for column, (page_name, text) in enumerate(
            (
                ("translate", self._ui("translate_tab")),
                ("settings", self._ui("settings_tab")),
                ("font", self._ui("font_tab")),
            )
        ):
            button = tk.Button(
                self.nav,
                text=text,
                width=8,
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
        for page in (self.translate_page, self.settings_page, self.font_page):
            page.grid(row=0, column=0, sticky="nsew")

        self._build_translate_page()
        self._build_settings_page()
        self._build_font_page()
        self.show_page("translate")

    def show_page(self, page_name: str):
        pages = {
            "translate": self.translate_page,
            "settings": self.settings_page,
            "font": self.font_page,
        }
        pages[page_name].tkraise()
        for name, button in self.nav_buttons.items():
            selected = name == page_name
            button.configure(bg="#eaf2ff" if selected else PANEL, fg=BLUE if selected else TEXT)

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
        self.source_panel.grid_columnconfigure(1, weight=0)
        top_source = ttk.Frame(self.source_panel, style="Panel.TFrame")
        top_source.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(6, 2))
        top_source.grid_columnconfigure(0, weight=1)
        self.source_bar = LanguageBar(top_source, self._source_language_changed)
        self.source_bar.grid(row=0, column=0, sticky="w")
        self.swap_button = ttk.Button(top_source, text=self._ui("swap_languages"), command=self.swap_languages)
        self.swap_button.grid(row=0, column=1, sticky="e")
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
        self.input_text.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.input_text.bind("<Return>", self._submit_from_keyboard)
        self.input_text.bind("<Control-Return>", self._submit_from_keyboard)
        self.input_text.bind("<Shift-Return>", self._insert_newline)
        self.translate_panes.add(self.source_panel, minsize=80)

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
        self.translate_panes.add(self.target_panel, minsize=80)

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
        self.translate_panes.add(self.back_panel, minsize=60)
        self.back_panel_visible = True
        self.after(200, self._set_initial_pane_sizes)

        actions = ttk.Frame(page, style="App.TFrame")
        actions.grid(row=1, column=0, sticky="ew")
        actions.grid_columnconfigure(0, weight=1)
        self.translate_button = ttk.Button(actions, text=self._ui("translate"), style="Primary.TButton", command=self.start_translation)
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
        self.translation_platform_var = tk.StringVar(value="Google")
        self.back_platform_var = tk.StringVar(value="Google")
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

        language_panel = self._panel(content)
        language_panel.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        language_panel.grid_columnconfigure(0, weight=1)
        language_panel.grid_columnconfigure(1, weight=1)
        self.my_picker = LanguagePicker(language_panel, self._ui("my_languages"), self.config_data.get("my_languages", []))
        self.my_picker.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        self.their_picker = LanguagePicker(language_panel, self._ui("their_languages"), self.config_data.get("their_languages", []))
        self.their_picker.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)

        back_panel = self._panel(content)
        back_panel.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(back_panel, text=self._ui("back_setting"), style="Section.TLabel").grid(row=0, column=0, sticky="w", padx=18, pady=(18, 12))
        self.back_translate_var = tk.BooleanVar(value=bool(self.config_data.get("back_translate")))
        ttk.Radiobutton(back_panel, text=self._ui("back_yes"), variable=self.back_translate_var, value=True).grid(
            row=1, column=0, sticky="w", padx=18, pady=6
        )
        ttk.Radiobutton(back_panel, text=self._ui("back_no"), variable=self.back_translate_var, value=False).grid(
            row=2, column=0, sticky="w", padx=18, pady=(6, 18)
        )

        actions = ttk.Frame(content, style="App.TFrame")
        actions.grid(row=4, column=0, sticky="ew", pady=(0, 24))
        actions.grid_columnconfigure(0, weight=1)
        ttk.Button(actions, text=self._ui("save_settings"), style="Primary.TButton", command=self.save_settings).grid(row=0, column=1, padx=(8, 0))
        self._refresh_translation_method_visibility()

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
        scale = min(event.width / 780, event.height / 620)
        scale = max(0.72, min(1.35, scale))
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
                self.translate_panes.paneconfigure(self.source_panel, minsize=max(64, int(round(80 * self.ui_scale))))
                self.translate_panes.paneconfigure(self.target_panel, minsize=max(64, int(round(80 * self.ui_scale))))
                self.translate_panes.paneconfigure(self.back_panel, minsize=max(50, int(round(60 * self.ui_scale))))
            except tk.TclError:
                pass

    def _set_initial_pane_sizes(self):
        if not hasattr(self, "translate_panes") or not self.back_panel_visible:
            return
        height = self.translate_panes.winfo_height()
        if height < 220:
            self.after(150, self._set_initial_pane_sizes)
            return
        try:
            back_height = max(58, min(100, int(height * 0.16)))
            main_height = max(80, (height - back_height) // 2)
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
        current_input = self.input_text.get("1.0", "end").strip()
        output = self._get_text(self.output_text)
        if self.ready_to_paste and output and current_input == self.last_translation_source:
            self.paste_output_to_external()
        else:
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
                "translation_platform": self.translation_platform_var.get(),
                "back_platform": self.back_platform_var.get(),
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
                self.translate_panes.add(self.back_panel, minsize=max(50, int(round(60 * self.ui_scale))))
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
            if payload.warning:
                self.status_var.set(f"{self._ui('done').format(provider=payload.provider)}（{payload.warning[:80]}）")
            else:
                self.status_var.set(self._ui("done").format(provider=payload.provider))
        elif isinstance(payload, Exception):
            self.ready_to_paste = False
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

        self.after(120, self._send_ctrl_v)
        self.after(900, lambda: self._restore_clipboard_text(old_clipboard_text, had_clipboard_text))
        self.status_var.set(self._ui("pasted_external"))

    def clear_texts(self):
        self.input_text.delete("1.0", "end")
        self._set_text(self.output_text, "")
        self._set_text(self.back_text, "")
        self.ready_to_paste = False
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
