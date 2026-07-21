#!/usr/bin/env bash
# Build ftl-parser-spike.jar (JDK 17+, curl, jar/javac). No Maven required.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LIB="$ROOT/lib"
TARGET="$ROOT/target"
CLASSES="$TARGET/classes"
VERSION="2.3.34"
FM_JAR="freemarker-${VERSION}.jar"
FM_URL="https://repo1.maven.org/maven2/org/freemarker/freemarker/${VERSION}/${FM_JAR}"
OUT_JAR="$TARGET/ftl-parser-spike.jar"

mkdir -p "$LIB" "$CLASSES"

if [[ ! -f "$LIB/$FM_JAR" ]]; then
  echo "Downloading $FM_JAR ..."
  curl -fsSL -o "$LIB/$FM_JAR" "$FM_URL"
fi

echo "Compiling FtlParseMain.java ..."
javac -encoding UTF-8 -cp "$LIB/$FM_JAR" -d "$CLASSES" "$ROOT/src/FtlParseMain.java"

# Place freemarker next to spike jar (Class-Path is relative to the jar).
cp -f "$LIB/$FM_JAR" "$TARGET/$FM_JAR"

MANIFEST="$TARGET/MANIFEST.MF"
cat >"$MANIFEST" <<EOF
Main-Class: FtlParseMain
Class-Path: ${FM_JAR}
EOF

jar cfm "$OUT_JAR" "$MANIFEST" -C "$CLASSES" .
echo "Built $OUT_JAR"
echo "Try: echo '<#list items as i>\${i}</#list>' | java -jar $OUT_JAR"
