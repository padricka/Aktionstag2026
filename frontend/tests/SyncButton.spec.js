/**
 * SyncButton – Pilz-Notknopf unter Klappe, Aufgabe 3 (siehe frontend/PANELS.md).
 *
 * Diese Tests legen die Bedien-Schnittstelle fest:
 *   Klappe    <button aria-label="Klappe">   öffnet/schließt die Schutzklappe
 *   Notknopf  <button aria-label="Notknopf"> löst `press` aus
 *   Status    Element .sb__status mit dem Statustext
 *   Ring      Element .sb__ring, CSS-Variable --window = "<windowMs>ms"
 *   Wurzel    Klassen sb--<state>, dazu is-cover-open bei offener Klappe
 * Statustexte: gesperrt "VERPLOMBT", idle "BEREIT", waiting "WARTE AUF PARTNER",
 *              synced "DATEN GERETTET", error "NICHT SYNCHRON".
 */
import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import SyncButton from "../src/components/SyncButton.vue";

const klappe = (w) => w.find('button[aria-label="Klappe"]');
const knopf = (w) => w.find('button[aria-label="Notknopf"]');
const status = (w) => w.find(".sb__status").text();

async function offen(props = {}) {
  const w = mount(SyncButton, { props: { unlocked: true, ...props } });
  await klappe(w).trigger("click");
  return w;
}

describe("SyncButton – Klappe", () => {
  it("ist verplombt, solange das Rätsel nicht gelöst ist", async () => {
    const w = mount(SyncButton, { props: { unlocked: false } });
    await klappe(w).trigger("click");
    await knopf(w).trigger("click");

    expect(status(w)).toBe("VERPLOMBT");
    expect(w.classes()).not.toContain("is-cover-open");
    expect(w.emitted("press")).toBeUndefined();
  });

  it("freigeschaltet lässt sich die Klappe öffnen", async () => {
    const w = await offen();

    expect(status(w)).toBe("BEREIT");
    expect(w.classes()).toContain("is-cover-open");
  });

  it("bei geschlossener Klappe löst der Knopf nicht aus", async () => {
    const w = mount(SyncButton, { props: { unlocked: true } });
    await knopf(w).trigger("click");

    expect(w.emitted("press")).toBeUndefined();
  });
});

describe("SyncButton – Drücken", () => {
  it("Klappe offen + Druck sendet press", async () => {
    const w = await offen();
    await knopf(w).trigger("click");

    expect(w.emitted("press")).toHaveLength(1);
  });

  it.each(["waiting", "synced"])("im Zustand %s löst der Knopf nicht erneut aus", async (state) => {
    const w = await offen({ state });
    await knopf(w).trigger("click");

    expect(w.emitted("press")).toBeUndefined();
  });

  it("nach error bleibt die Klappe offen und man kann erneut drücken", async () => {
    const w = await offen();
    await w.setProps({ state: "error" });
    expect(status(w)).toBe("NICHT SYNCHRON");

    await w.setProps({ state: "idle" });
    expect(w.classes()).toContain("is-cover-open");
    await knopf(w).trigger("click");
    expect(w.emitted("press")).toHaveLength(1);
  });
});

describe("SyncButton – Anzeige", () => {
  it("zeigt Warten und Erfolg an", async () => {
    const w = await offen({ state: "waiting" });
    expect(status(w)).toBe("WARTE AUF PARTNER");

    await w.setProps({ state: "synced" });
    expect(status(w)).toBe("DATEN GERETTET");
  });

  it("Ring läuft über das Zeitfenster", () => {
    const w = mount(SyncButton, { props: { unlocked: true, windowMs: 2500 } });
    expect(w.find(".sb__ring").attributes("style")).toContain("--window: 2500ms");
  });

  it("Zeitfenster ist standardmäßig 3 Sekunden", () => {
    const w = mount(SyncButton, { props: { unlocked: true } });
    expect(w.find(".sb__ring").attributes("style")).toContain("--window: 3000ms");
  });

  it.each(["idle", "waiting", "synced", "error"])("setzt die Klasse sb--%s", (state) => {
    const w = mount(SyncButton, { props: { unlocked: true, state } });
    expect(w.classes()).toContain(`sb--${state}`);
  });
});
