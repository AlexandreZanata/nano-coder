# FreeMarker parser spike (Day 8)

Minimal JVM wrapper: read template from stdin, try `new Template(...)`, exit 0 on success / 1 on `ParseException`.

## Build (when you reach Day 8)

```bash
# Requires JDK 17+ and Maven OR javac + freemarker.jar on classpath
./build.sh
echo '<#list items as i>${i}</#list>' | java -jar target/ftl-parser-spike.jar
```

Until the jar exists, `ftl_sandbox.py` reports `syntax=false` + `ftl_spike_missing` — honest, not fake green.

## Why Java

There is no mature FreeMarker parser outside the JVM. Node wrappers still shell out to Java.
