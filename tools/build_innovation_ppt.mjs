import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "C:/Users/daish/Documents/Auto Power Factory";
const OUTPUT_DIR = path.join(ROOT, "outputs");
const CSV_PATH = path.join(OUTPUT_DIR, "n_minus_1_short_circuit_bus_5.csv");
const FINAL_PPTX = path.join(OUTPUT_DIR, "Innovation_Project_Idea_PowerFactory_MCP.pptx");
const PREVIEW_DIR = path.join(OUTPUT_DIR, "ppt_preview");

const W = 1280;
const H = 720;
const ink = "#111111";
const muted = "#555555";
const panel = "#EDEDED";
const rule = "#B8BCC4";
const highlight = "#FF6B35";

function parseCsv(text) {
  const [headerLine, ...lines] = text.trim().split(/\r?\n/);
  const headers = headerLine.split(",");
  return lines.map((line) => {
    const values = line.split(",");
    return Object.fromEntries(headers.map((h, i) => [h, values[i]]));
  });
}

function addText(slide, text, x, y, width, height, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: opts.size ?? 22,
    bold: opts.bold ?? false,
    color: opts.color ?? ink,
    alignment: opts.align ?? "left",
  };
  return shape;
}

function addRule(slide, x, y, width) {
  slide.shapes.add({
    geometry: "line",
    position: { left: x, top: y, width, height: 0 },
    fill: "none",
    line: { style: "solid", fill: rule, width: 1 },
  });
}

function addFooter(slide, n) {
  addText(slide, "PowerFactory MCP innovation proposal", 42, 668, 520, 24, {
    size: 13,
    color: muted,
  });
  addText(slide, String(n).padStart(2, "0"), 1188, 668, 50, 24, {
    size: 13,
    color: muted,
    align: "right",
  });
}

function addHeader(slide, title, n) {
  addText(slide, title, 42, 38, 980, 72, { size: 44, bold: true });
  addRule(slide, 42, 122, 1196);
  addFooter(slide, n);
}

function addBox(slide, x, y, width, height, fill = panel) {
  return slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width, height },
    fill,
    line: { style: "solid", fill: "none", width: 0 },
  });
}

function addMetric(slide, label, value, x, y, width = 260) {
  addText(slide, value, x, y, width, 64, { size: 50, bold: true });
  addText(slide, label, x, y + 70, width, 46, { size: 18, color: muted });
}

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function main() {
  await fs.mkdir(OUTPUT_DIR, { recursive: true });
  await fs.mkdir(PREVIEW_DIR, { recursive: true });

  const results = parseCsv(await fs.readFile(CSV_PATH, "utf8"));
  const skss = results.map((r) => Number(r.short_circuit_power_mva));
  const ikss = results.map((r) => Number(r.short_circuit_current_ka));
  const worst = results.reduce((a, b) =>
    Number(a.short_circuit_power_mva) < Number(b.short_circuit_power_mva) ? a : b
  );
  const best = results.reduce((a, b) =>
    Number(a.short_circuit_power_mva) > Number(b.short_circuit_power_mva) ? a : b
  );

  const presentation = Presentation.create({ slideSize: { width: W, height: H } });

  // Slide 1
  {
    const s = presentation.slides.add();
    s.background.fill = "white";
    addText(s, "PowerFactory MCP Automation", 42, 58, 1030, 96, { size: 58, bold: true });
    addText(
      s,
      "Innovation project idea for natural-language grid simulation and N-1 short-circuit studies",
      42,
      174,
      760,
      88,
      { size: 25, color: muted }
    );
    addBox(s, 42, 342, 1196, 132, panel);
    addMetric(s, "Line N-1 contingencies executed", "6", 78, 370);
    addMetric(s, "Target bus in prototype", "Bus 5", 392, 370);
    addMetric(s, "Lowest Skss observed", "404 MVA", 708, 370, 340);
    addText(s, "Prototype evidence from DIgSILENT PowerFactory 2024", 42, 612, 760, 36, {
      size: 18,
      color: muted,
    });
    addFooter(s, 1);
  }

  // Slide 2
  {
    const s = presentation.slides.add();
    s.background.fill = "white";
    addHeader(s, "Why this is worth pursuing", 2);
    addText(
      s,
      "Manual simulation workflows are reliable but slow to repeat at scale.",
      42,
      160,
      760,
      76,
      { size: 35, bold: true }
    );
    const bullets = [
      "Engineers repeatedly change network states, run studies, export data, and restore models.",
      "Scenario coverage is often limited by time rather than engineering value.",
      "A controlled natural-language layer can speed repeatable analysis while preserving PowerFactory as the calculation engine.",
    ];
    bullets.forEach((b, i) => addText(s, b, 82, 278 + i * 82, 760, 56, { size: 23, color: ink }));
    addBox(s, 908, 170, 250, 300, panel);
    addText(s, "Opportunity", 930, 204, 210, 40, { size: 25, bold: true });
    addText(s, "Turn repetitive studies into governed, auditable automation.", 930, 266, 210, 142, {
      size: 24,
    });
  }

  // Slide 3
  {
    const s = presentation.slides.add();
    s.background.fill = "white";
    addHeader(s, "Innovation concept", 3);
    const steps = [
      ["Engineer", "Natural-language request"],
      ["MCP Server", "Tool call and validation"],
      ["PF Agent", "In-app API execution"],
      ["Evidence", "CSV and report output"],
    ];
    steps.forEach(([label, body], i) => {
      const x = 58 + i * 300;
      addBox(s, x, 230, 226, 160, i === 1 ? "#F6F6F6" : panel);
      addText(s, label, x + 20, 254, 186, 36, { size: 25, bold: true });
      addText(s, body, x + 20, 306, 186, 58, { size: 20, color: muted });
      if (i < steps.length - 1) {
        addText(s, ">", x + 246, 285, 34, 42, { size: 34, bold: true, color: highlight, align: "center" });
      }
    });
    addText(
      s,
      "The innovation is not replacing PowerFactory. It is wrapping validated PowerFactory operations in a repeatable command interface that can be driven by natural language.",
      100,
      476,
      1080,
      82,
      { size: 24, color: ink, align: "center" }
    );
  }

  // Slide 4
  {
    const s = presentation.slides.add();
    s.background.fill = "white";
    addHeader(s, "Prototype workflow", 4);
    const workflow = [
      "Start MCP_Agent inside PowerFactory",
      "Run base simulation or setup commands",
      "Open one line outage",
      "Run 3-phase short circuit at Bus 5",
      "Capture Ikss and Skss",
      "Restore line and repeat",
    ];
    workflow.forEach((item, i) => {
      const y = 172 + i * 70;
      addText(s, String(i + 1), 70, y, 42, 42, { size: 28, bold: true, color: highlight, align: "center" });
      addText(s, item, 132, y + 2, 820, 42, { size: 25 });
      addRule(s, 132, y + 52, 840);
    });
    addBox(s, 1000, 190, 200, 260, panel);
    addText(s, "Repeatable", 1024, 226, 152, 42, { size: 26, bold: true });
    addText(s, "Every contingency follows the same controlled sequence and returns structured data.", 1024, 292, 152, 116, {
      size: 20,
      color: muted,
    });
  }

  // Slide 5
  {
    const s = presentation.slides.add();
    s.background.fill = "white";
    addHeader(s, "N-1 validation setup", 5);
    addMetric(s, "Target calculation point", "Bus 5", 66, 176, 320);
    addMetric(s, "Outage type", "Line", 426, 176, 260);
    addMetric(s, "Short-circuit type", "3-phase", 746, 176, 320);
    addText(
      s,
      "For each transmission line, the agent sets the line out of service, runs the short-circuit command, reads Bus 5 Ikss and Skss, and restores the original line state.",
      88,
      374,
      1030,
      86,
      { size: 26, align: "center" }
    );
    addText(s, "All six test cases returned PowerFactory code 0.", 88, 506, 1030, 42, {
      size: 25,
      bold: true,
      color: highlight,
      align: "center",
    });
  }

  // Slide 6
  {
    const s = presentation.slides.add();
    s.background.fill = "white";
    addHeader(s, "Bus 5 short-circuit capacity", 6);
    s.charts.add("bar", {
      position: { left: 74, top: 170, width: 760, height: 396 },
      categories: results.map((r) => r.outaged_line),
      series: [{ name: "Skss MVA", values: skss, fill: highlight }],
      hasLegend: false,
      barOptions: { direction: "bar", grouping: "clustered", gapWidth: 50 },
      xAxis: {
        title: "Short-circuit capacity (MVA)",
        majorGridlines: { style: "solid", fill: "#DDDDDD", width: 1 },
        textStyle: { fill: muted, fontSize: 13 },
      },
      yAxis: { textStyle: { fill: ink, fontSize: 14 }, line: { style: "solid", fill: rule, width: 1 } },
      dataLabels: { showValue: true, position: "outEnd", textStyle: { fill: ink, fontSize: 13, bold: true } },
    });
    addBox(s, 894, 180, 286, 260, panel);
    addText(s, "Limiting case", 920, 212, 230, 36, { size: 24, bold: true });
    addText(s, worst.outaged_line, 920, 270, 230, 52, { size: 32, bold: true, color: highlight });
    addText(s, `${Number(worst.short_circuit_power_mva).toFixed(2)} MVA`, 920, 342, 230, 44, {
      size: 30,
      bold: true,
    });
    addText(s, `Ikss ${Number(worst.short_circuit_current_ka).toFixed(4)} kA`, 920, 394, 230, 34, {
      size: 19,
      color: muted,
    });
  }

  // Slide 7
  {
    const s = presentation.slides.add();
    s.background.fill = "white";
    addHeader(s, "Value proposition", 7);
    const values = [
      ["Speed", "Batch execution of repetitive studies"],
      ["Traceability", "Structured command and result records"],
      ["Coverage", "More scenarios with less manual effort"],
      ["Accessibility", "Plain-English study requests"],
    ];
    values.forEach(([label, body], i) => {
      const x = i % 2 === 0 ? 90 : 680;
      const y = i < 2 ? 190 : 408;
      addText(s, label, x, y, 360, 40, { size: 31, bold: true, color: highlight });
      addText(s, body, x, y + 54, 420, 70, { size: 25 });
      addRule(s, x, y + 138, 420);
    });
  }

  // Slide 8
  {
    const s = presentation.slides.add();
    s.background.fill = "white";
    addHeader(s, "Proposed next step", 8);
    addText(s, "Approve a small pilot to harden the workflow on real study cases.", 70, 178, 1000, 76, {
      size: 38,
      bold: true,
    });
    const phases = [
      ["1", "Harden", "Validation checks, model-state restore, error logging"],
      ["2", "Expand", "Transformer N-1, voltage limits, load-flow violations"],
      ["3", "Package", "Reusable MCP config, installation guide, standard outputs"],
    ];
    phases.forEach(([num, title, body], i) => {
      const x = 82 + i * 390;
      addText(s, num, x, 342, 60, 60, { size: 48, bold: true, color: highlight, align: "center" });
      addText(s, title, x + 78, 340, 250, 40, { size: 28, bold: true });
      addText(s, body, x + 78, 394, 250, 80, { size: 20, color: muted });
    });
    addText(s, "Decision ask: permission to run a 2-3 week engineering automation pilot.", 96, 586, 1088, 42, {
      size: 26,
      bold: true,
      align: "center",
    });
  }

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(path.join(PREVIEW_DIR, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 1 }));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(PREVIEW_DIR, `${stem}.layout.json`), await layout.text());
  }

  await writeBlob(path.join(PREVIEW_DIR, "deck-montage.webp"), await presentation.export({ format: "webp", montage: true, scale: 1 }));
  const inspect = await presentation.inspect({ kind: "slide,textbox,shape,chart,table,layout", maxChars: 12000 });
  await fs.writeFile(path.join(PREVIEW_DIR, "inspect.ndjson"), inspect.ndjson);
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(FINAL_PPTX);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
