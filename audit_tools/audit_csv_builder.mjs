import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Workbook } from "@oai/artifact-tool";

const here = path.dirname(fileURLToPath(import.meta.url));
const scratch = path.resolve(here, "..", "scratch", "audit_workbook");
const payloadPath = path.join(scratch, "audit_render_payload.json");

if (process.argv.includes("--help-api")) {
  const wb = Workbook.create();
  process.stdout.write(wb.help("csv export", { include: "index,examples,notes", maxChars: 5000 }).ndjson);
  process.exit(0);
}

const payload = JSON.parse(await fs.readFile(payloadPath, "utf8"));
for (const item of payload.files) {
  const baselinePath = path.join(path.dirname(item.outputPath), "audit", "2026-09-03", "baseline", item.name);
  const wb = await Workbook.fromCSV(await fs.readFile(baselinePath, "utf8"), { sheetName: item.sheetName });
  const sheet = wb.worksheets.getItem(item.sheetName);
  const rows = [item.headers, ...item.rows];
  const previewOnly = process.argv.includes("--preview-baseline");
  if (!previewOnly) sheet.getUsedRange().clear({ applyTo: "contents" });
  if (!previewOnly) sheet.getRangeByIndexes(0, 0, rows.length, item.headers.length).values = rows;
  const previewRange = item.name === "by_day.csv" ? "A1:H6" : item.name === "cities.csv" ? "A1:E6" : "A1:D4";
  sheet.getRange(previewRange).format.columnWidthPx = item.name === "publications.csv" ? 250 : 120;
  sheet.getRange(previewRange).format.wrapText = true;
  sheet.getRange(previewRange).format.rowHeightPx = item.name === "publications.csv" ? 100 : 34;
  sheet.getRange("A1:H1").format.font.bold = true;
  sheet.getRange("A:A").format.columnWidthPx = 180;
  const preview = await wb.render({ sheetName: item.sheetName, range: previewRange, scale: 1, format: "png" });
  await fs.writeFile(path.join(scratch, `${previewOnly ? "baseline" : "final"}-${item.sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
  if (previewOnly) continue;
  const inspected = await wb.inspect({
    kind: "table",
    range: `${item.sheetName}!A1:${item.lastColumn}${Math.min(rows.length, 8)}`,
    include: "values,formulas",
    tableMaxRows: 8,
    tableMaxCols: Math.min(item.headers.length, 12),
    maxChars: 4000,
  });
  process.stdout.write(`${item.name}: ${inspected.ndjson}\n`);
  // The public API has no documented CSV exporter. Read the authored workbook
  // values back, then use plain RFC-4180 serialization (no alternate workbook library).
  const authored = sheet.getRangeByIndexes(0, 0, rows.length, item.headers.length).values;
  const encode = (v) => {
    const text = v == null ? "" : String(v);
    return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  };
  const csv = authored.map((row) => row.map(encode).join(",")).join("\n") + "\n";
  await fs.writeFile(item.outputPath, csv, "utf8");
}
process.stdout.write("All requested CSV outputs and previews completed.\n");
process.exit(0);
