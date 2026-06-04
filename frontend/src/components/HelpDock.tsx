import { useEffect, useState } from "react";
import type { ReactNode } from "react";

interface DocSection {
  id: string;
  title: string;
  content: ReactNode;
}

const SECTIONS: DocSection[] = [
  {
    id: "overview",
    title: "Overview",
    content: (
      <>
        <p>
          <strong>GEOTHERM</strong> sizes and prices a geothermal <strong>district heating + cooling</strong>{" "}
          system for the Utrecht region (Netherlands), targeting the deep{" "}
          <strong>Rotliegend (Slochteren) sandstone</strong>. It chooses the well programme and the
          integrated surface system that meet the demand, <strong>≥10 MWth heating</strong> and{" "}
          <strong>≥5 MWth cooling</strong>, at the lowest, most credible{" "}
          <strong>levelised cost of energy (LCoE)</strong>.
        </p>
        <p>
          The guiding principle is <em>not</em> maximum megawatts: the best design is the cheapest one
          that reliably serves the load, with every well (including the four provided) paid for.
        </p>
      </>
    ),
  },
  {
    id: "recommendation",
    title: "Recommendation",
    content: (
      <>
        <p>
          A <strong>staged 1-doublet system</strong>: one deep doublet → a central{" "}
          <strong>heat pump</strong> (lifts the brine to district temperature) → seasonal{" "}
          <strong>HT-ATES</strong> storage (banks summer surplus for the winter peak) →{" "}
          <strong>heat-driven cooling</strong>, with free cooling and a small backup boiler.
        </p>
        <ul>
          <li>
            <strong>LCoE 20.9 €/GJ</strong>, P10 16.8 / P50 20.9 / P90 36.9 (transmissivity uncertainty).
          </li>
          <li>Firm heating 7.9 MWth; HT-ATES covers the winter peak so backup is near-zero.</li>
          <li>
            Geothermal utilisation rises to <strong>99%</strong> by doing cooling as well as heating
            (vs 59% heating-only). Running the wells hard year-round is why it is cheap.
          </li>
          <li>CAPEX ≈ 17 M€.</li>
        </ul>
        <p>
          One well carries large resource uncertainty, and a second nearby well shares the same geology,
          so it does <strong>not</strong> de-risk the first. The advice is therefore to{" "}
          <strong>drill one doublet, well-test it, and expand only if the data justify it.</strong>
        </p>
      </>
    ),
  },
  {
    id: "pipeline",
    title: "How the model works",
    content: (
      <>
        <p>Four stages turn the raw well data into a priced design:</p>
        <ul>
          <li>
            <strong>Data foundation.</strong> Reconstructs true vertical depth from the directional
            surveys (minimum curvature), repairs unit artefacts, and imputes missing porosity from the
            density logs, validated against the independent ThermoGIS regional model.
          </li>
          <li>
            <strong>Resource (Challenge 1).</strong> Doublet power per well as a P10/P50/P90 band (only
            BLT-01 and JUT-01 are viable); an IDW resource map across the area; and a recommended new
            doublet next to the demand centre.
          </li>
          <li>
            <strong>System design (Challenge 2A).</strong> Geothermal doublet → heat pump → HT-ATES →
            absorption cooling, on a monthly energy balance. Cooling monetises otherwise-idle summer
            capacity: that is the cost win.
          </li>
          <li>
            <strong>Techno-economics (Challenge 2B).</strong> A Python port of the TNO/ECN LCoE model
            (reproduces its 5.77 €/GJ base case), extended for the hybrid system; a design search over
            the doublet count; a <strong>Monte-Carlo</strong> for the P10/50/90 cost band; and a{" "}
            <strong>tornado</strong> showing which assumptions actually move LCoE.
          </li>
        </ul>
      </>
    ),
  },
  {
    id: "usage",
    title: "Using the app",
    content: (
      <>
        <ul>
          <li>
            <strong>Parameters panel.</strong> Grouped, collapsible inputs. <em>Drag</em> a value to
            scrub it or <em>click</em> to type; filter to jump to any parameter; import / export an{" "}
            <code>inputs.toml</code> (interoperable with the command-line tool).
          </li>
          <li>
            <strong>Evaluate vs Optimise.</strong> <em>Evaluate</em> computes the design and LCoE for
            your exact inputs. <em>Optimise</em> searches the doublet/HT-ATES count plus the design
            levers you mark as ranges (return temperature, free cooling) for the least-cost design that
            satisfies your constraints. Economic and demand inputs stay fixed: their uncertainty is the
            job of the Monte-Carlo and tornado, not the optimiser.
          </li>
          <li>
            <strong>Results.</strong> Resource map, per-well percentiles, monthly dispatch + capacity
            factor, Monte-Carlo LCoE, sensitivity tornado, design comparison, the full technical report
            (downloadable), and a grounded chat.
          </li>
          <li>
            <strong>Keyboard.</strong> <span className="kbd">⌘↵</span> run ·{" "}
            <span className="kbd">O</span> mode · <span className="kbd">R</span> reset ·{" "}
            <span className="kbd">D</span> download report · <span className="kbd">/</span> chat ·{" "}
            <span className="kbd">?</span> shortcuts.
          </li>
        </ul>
      </>
    ),
  },
  {
    id: "code",
    title: "Code & CLI",
    content: (
      <>
        <p>
          Source &amp; reproduction steps:{" "}
          <a
            href="https://github.com/Aaron-Ontoyin/geodatathon-spe-june26"
            target="_blank"
            rel="noreferrer"
          >
            github.com/Aaron-Ontoyin/geodatathon-spe-june26
          </a>
          .
        </p>
        <p>
          The same deterministic engine behind this app also runs as a{" "}
          <strong>command-line tool</strong> (<code>geo-datathon</code>), driven by the very same{" "}
          <code>inputs.toml</code> the app imports and exports, so the full analysis reproduces with{" "}
          <strong>no web app and no API key</strong>:
        </p>
        <pre className="docs-code">{`# write a starting inputs.toml
uv run geo-datathon template --out inputs.toml

# run the pipeline → full technical report
uv run geo-datathon report --input inputs.toml --out report.md

# run the agentic workflow (narrated decisions)
uv run geo-datathon workflow --input inputs.toml`}</pre>
      </>
    ),
  },
  {
    id: "caveats",
    title: "Assumptions & limitations",
    content: (
      <>
        <ul>
          <li>
            Every input is a <strong>documented parameter</strong>, no hidden constants. Defaults come
            from the provided LCoE model plus public ranges.
          </li>
          <li>
            The system is modelled at a <strong>monthly energy-balance</strong> level (as the brief
            intends), not as a transient reservoir or thermodynamic simulation.
          </li>
          <li>
            The resource map is built from <strong>four wells (two viable)</strong>; a denser ThermoGIS
            grid would sharpen it and further de-risk the sited location.
          </li>
          <li>
            The Monte-Carlo assumes a single correlated transmissivity field; partial spatial
            correlation would narrow the band somewhat.
          </li>
          <li>
            The 1-doublet optimum relies on HT-ATES delivering the winter peak shortfall, a detailed
            storage design should confirm it.
          </li>
        </ul>
      </>
    ),
  },
];

/** Floating "?" button (bottom-right) that opens a structured documentation modal. */
export function HelpDock() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <>
      <button
        type="button"
        className="help-fab"
        onClick={() => setOpen(true)}
        aria-label="Open documentation"
      >
        ?
      </button>

      {open && (
        <div className="docs-overlay" onClick={() => setOpen(false)}>
          <div
            className="docs-modal rise"
            role="dialog"
            aria-modal="true"
            aria-label="GEOTHERM documentation"
            onClick={(e) => e.stopPropagation()}
          >
            <header className="docs-head">
              <span className="brand">GEOTHERM</span>
              <span className="docs-kicker">Documentation</span>
              <button
                type="button"
                className="docs-close"
                onClick={() => setOpen(false)}
                aria-label="Close documentation"
              >
                ×
              </button>
            </header>

            <div className="docs-wrap">
              <nav className="docs-toc" aria-label="Sections">
                {SECTIONS.map((s) => (
                  <button key={s.id} type="button" onClick={() => scrollTo(s.id)}>
                    {s.title}
                  </button>
                ))}
              </nav>
              <div className="docs-body">
                {SECTIONS.map((s) => (
                  <section key={s.id} id={s.id} className="docs-section">
                    <h3>{s.title}</h3>
                    {s.content}
                  </section>
                ))}
                <p className="docs-foot">
                  SPE Africa Geothermal Datathon 2026 · Utrecht · Rotliegend (Slochteren).
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
