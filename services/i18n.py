"""
Lightweight translation table for the app chrome (sidebar, titlebar, page
titles, the auth screens and the settings labels).

The deep content of every page (draft-analysis text, history cards,
statistics tables, AI explanations, etc.) stays in Ukrainian regardless of
the language switch -- fully localising every string in the app is a much
bigger job than this table covers. What IS wired up here switches live,
both from the login screen's language picker and from Settings.
"""
import database as db

UK = "Українська"
EN = "English"

_TR = {
    # ---- app chrome ----
    "app_title":        {UK: "Інтелектуальний помічник для аналізу драфту Dota 2", EN: "Intelligent Dota 2 Draft Analysis Assistant"},
    "app_subtitle":      {UK: "Аналізуй. Обирай. Перемагай.",                        EN: "Analyze. Choose. Win."},
    "nav_home":          {UK: "Головна",             EN: "Home"},
    "nav_history":       {UK: "Історія аналізів",     EN: "Analysis history"},
    "nav_stats":         {UK: "Статистика",           EN: "Statistics"},
    "nav_settings":      {UK: "Налаштування",         EN: "Settings"},
    "nav_about":         {UK: "Про програму",         EN: "About"},
    "guest":             {UK: "Гість",                EN: "Guest"},
    "logout":            {UK: "Вийти з акаунту",       EN: "Log out"},
    "stratz_connected":  {UK: "Підключено\nSTRATZ API", EN: "Connected to\nSTRATZ API"},
    "stratz_disconnected": {UK: "Не підключено\nSTRATZ API", EN: "Not connected to\nSTRATZ API"},

    # ---- auth ----
    "login_title":       {UK: "Вхід у програму",       EN: "Sign in"},
    "login_subtitle":    {UK: "Користуйтесь усіма можливостями\nінтелектуального аналізу драфту",
                           EN: "Get access to every feature of the\nintelligent draft analyzer"},
    "field_id":          {UK: "Ім'я користувача або Email", EN: "Username or Email"},
    "field_password":    {UK: "Пароль",                EN: "Password"},
    "remember_me":       {UK: "Запам'ятати мене",       EN: "Remember me"},
    "btn_login":         {UK: "Увійти",                EN: "Sign in"},
    "or_divider":        {UK: "або",                   EN: "or"},
    "continue_guest":    {UK: "👤   Продовжити без входу", EN: "👤   Continue as guest"},
    "create_account":    {UK: "👤+   Створити акаунт",  EN: "👤+   Create an account"},
    "forgot_password":   {UK: "🔒   Забули пароль?",    EN: "🔒   Forgot password?"},
    "register_title":    {UK: "Створення акаунту",      EN: "Create account"},
    "register_subtitle": {UK: "Зареєструйтесь, щоб отримати доступ до\nвсіх можливостей програми",
                           EN: "Sign up to unlock every feature\nof the app"},
    "field_firstname":   {UK: "Ім'я",                  EN: "First name"},
    "field_lastname":    {UK: "Прізвище",              EN: "Last name"},
    "field_email":       {UK: "Email",                 EN: "Email"},
    "field_password2":   {UK: "Підтвердіть пароль",     EN: "Confirm password"},
    "btn_register":      {UK: "Зареєструватися",        EN: "Create account"},
    "have_account":      {UK: "Вже маєте акаунт? ",     EN: "Already have an account? "},
    "login_link":        {UK: "Увійти",                 EN: "Sign in"},
    "google_continue":   {UK: "Продовжити з Google",    EN: "Continue with Google"},

    # ---- settings ----
    "settings_title":    {UK: "Налаштування",        EN: "Settings"},
    "settings_subtitle": {UK: "Налаштуйте програму під себе", EN: "Make the app your own"},
    "save_settings":     {UK: "✓  Зберегти налаштування", EN: "✓  Save settings"},

    # ---- page titles ----
    "home_title":        {UK: "Головна",   EN: "Home"},
    "history_title":     {UK: "Історія аналізів", EN: "Analysis history"},
    "stats_title":       {UK: "Статистика героїв", EN: "Hero statistics"},
    "about_title":       {UK: "Про програму", EN: "About"},
}


def get_language() -> str:
    lang = db.get_setting("ui_language", UK)
    return lang if lang in (UK, EN) else UK


def t(key: str) -> str:
    lang = get_language()
    entry = _TR.get(key)
    if not entry:
        return key
    return entry.get(lang, entry.get(UK, key))
