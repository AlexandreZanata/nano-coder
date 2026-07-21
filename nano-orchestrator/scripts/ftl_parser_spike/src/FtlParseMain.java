import freemarker.core.ParseException;
import freemarker.template.Configuration;
import freemarker.template.Template;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;

/**
 * FreeMarker syntax spike: read template from stdin, exit 0 on parse OK, 1 on ParseException.
 */
public final class FtlParseMain {
    private FtlParseMain() {}

    public static void main(String[] args) throws Exception {
        String source = readStdin();
        Configuration cfg = new Configuration(Configuration.VERSION_2_3_34);
        cfg.setDefaultEncoding("UTF-8");
        cfg.setLogTemplateExceptions(false);
        try {
            new Template("stdin", new StringReader(source), cfg);
            System.exit(0);
        } catch (ParseException e) {
            System.err.println(e.getMessage());
            System.exit(1);
        }
    }

    private static String readStdin() throws Exception {
        StringBuilder sb = new StringBuilder();
        try (BufferedReader reader =
                new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line).append('\n');
            }
        }
        return sb.toString();
    }
}
