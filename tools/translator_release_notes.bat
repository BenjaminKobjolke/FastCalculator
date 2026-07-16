d:
cd "d:\GIT\BenjaminKobjolke\GPT-json-translator"

call .\.venv\Scripts\python.exe json_translator.py "D:\GIT\BenjaminKobjolke\calculator\release_notes" --translate-recursive="en.json"

cd %~dp0
