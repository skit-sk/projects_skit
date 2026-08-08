#!/bin/bash
# Сборка EPF "Загрузка контрагентов из XML"
SRC="$(dirname "$0")/src"
BUILD="$(dirname "$0")/build"
EPF="$BUILD/ЗагрузкаКонтрагентовИзXML_v1.epf"

source /home/user_aioc/workspace/venv/bin/activate

# Очистка
rm -rf "$BUILD"
mkdir -p "$BUILD"

# Копируем исходники в build
cp -r "$SRC"/ {ExternalDataProcessor.json,ExternalDataProcessor.obj.bsl} "$BUILD/" 2>/dev/null
mkdir -p "$BUILD/Form/Форма"
cp -r "$SRC/Form/Форма/"* "$BUILD/Form/Форма/" 2>/dev/null

# Сборка
echo "Сборка $EPF ..."
v8unpack -B "$BUILD" "$EPF"
if [ $? -eq 0 ]; then
    echo "OK: $EPF"
else
    echo "ERROR: сборка не удалась"
    exit 1
fi
