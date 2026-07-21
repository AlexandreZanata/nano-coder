# FreeMarker parser spike (Phase 4 / T-042)

Minimal JVM wrapper: read template from stdin, construct `new Template(...)`, exit **0** on success / **1** on `ParseException`.

## Prerequisites

- JDK **17+** (`javac`, `jar`, `java`)
- `curl` (downloads FreeMarker 2.3.34 from Maven Central once into `lib/`)

## Build

```bash
cd nano-orchestrator/scripts/ftl_parser_spike
./build.sh
```

Produces `target/ftl-parser-spike.jar` (+ `target/freemarker-2.3.34.jar` on Class-Path).

## Examples

```bash
# Pass
echo '<#list items as i>${i}</#list>' | java -jar target/ftl-parser-spike.jar
echo $?   # 0

# Fail (unclosed list)
echo '<#list items as i>${i}' | java -jar target/ftl-parser-spike.jar
echo $?   # 1
```

## Integration

`ftl_sandbox.py` shells out to this jar. Until `./build.sh` succeeds, checks report `syntax=false` and `ftl_spike_missing=false` (honest — never fake green).

`lib/` and `target/` are gitignored; rebuild after clone.
