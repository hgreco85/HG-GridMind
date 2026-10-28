// Minimal JDBC runner for the real Zetaris Lightning engine. No third-party deps (JSON hand-built).
// Usage: java -cp <ndp-jdbc-driver.jar> ZetarisJdbcRunner.java <jdbc-url> <user> <sql-file-or-"-"> 
// Password is read from env ZETARIS_PASSWORD (never from argv). Each statement (split on ';' at line end)
// is executed; result sets are emitted as JSON: {"statements":[{"sql":..,"columns":[..],"rows":[[..]],"elapsed_ms":n}|{"sql":..,"error":..}]}
import java.sql.*;
import java.nio.file.*;
import java.util.*;

public class ZetarisJdbcRunner {
    static String esc(String s) {
        if (s == null) return "null";
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            switch (c) {
                case '"': b.append("\\\""); break; case '\\': b.append("\\\\"); break;
                case '\n': b.append("\\n"); break; case '\r': b.append("\\r"); break; case '\t': b.append("\\t"); break;
                default: if (c < 0x20) b.append(String.format("\\u%04x", (int) c)); else b.append(c);
            }
        }
        return b.append('"').toString();
    }
    public static void main(String[] a) throws Exception {
        String url = a[0], user = a[1];
        String sqlText = a[2].equals("-") ? new String(System.in.readAllBytes(), "UTF-8") : Files.readString(Paths.get(a[2]));
        if (sqlText.startsWith("\uFEFF")) sqlText = sqlText.substring(1);
        String pw = System.getenv("ZETARIS_PASSWORD");
        Class.forName("com.zetaris.lightning.jdbc.LightningDriver");
        List<String> stmts = new ArrayList<>();
        StringBuilder cur = new StringBuilder();
        for (String line : sqlText.split("\n")) {
            if (line.trim().startsWith("--")) continue;
            cur.append(line).append("\n");
            if (line.trim().endsWith(";")) { stmts.add(cur.toString().trim().replaceAll(";\\s*$", "")); cur.setLength(0); }
        }
        if (cur.toString().trim().length() > 0) stmts.add(cur.toString().trim());
        StringBuilder out = new StringBuilder("{\"statements\":[");
        try (Connection c = DriverManager.getConnection(url, user, pw)) {
            boolean first = true;
            for (String s : stmts) {
                if (!first) out.append(","); first = false;
                long t0 = System.currentTimeMillis();
                try (Statement st = c.createStatement()) {
                    boolean rs = st.execute(s);
                    out.append("{\"sql\":").append(esc(s));
                    if (rs) {
                        ResultSet r = st.getResultSet(); ResultSetMetaData m = r.getMetaData();
                        out.append(",\"columns\":[");
                        for (int i = 1; i <= m.getColumnCount(); i++) out.append(i > 1 ? "," : "").append(esc(m.getColumnLabel(i)));
                        out.append("],\"rows\":[");
                        boolean fr = true;
                        while (r.next()) {
                            out.append(fr ? "" : ",").append("["); fr = false;
                            for (int i = 1; i <= m.getColumnCount(); i++) { out.append(i > 1 ? "," : "").append(esc(r.getString(i))); }
                            out.append("]");
                        }
                        out.append("]");
                    }
                    out.append(",\"elapsed_ms\":").append(System.currentTimeMillis() - t0).append("}");
                } catch (SQLException e) {
                    out.append("{\"sql\":").append(esc(s)).append(",\"error\":").append(esc(String.valueOf(e.getMessage()).split("\n\tat ")[0])).append("}");
                }
            }
        }
        out.append("]}");
        System.out.println(out);
    }
}
