import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import WirePanel from "../src/components/WirePanel.vue";

const WIRES = ["raute", "dreieck", "quadrat", "kreis"];
const kabel = (w) => w.findAll(".wp-wire");
const knopf = (w) => w.find(".wp__cut");

describe("WirePanel – Auswahl und Kappen", () => {
  it("zeigt ein Kabel pro Symbol mit Steckplatz im Label", () => {
    const w = mount(WirePanel, { props: { wires: WIRES } });

    expect(kabel(w)).toHaveLength(4);
    expect(kabel(w)[2].attributes("aria-label")).toBe("Kabel 3: quadrat");
  });

  it("Knopf ist gesperrt, solange kein Kabel gewählt ist", () => {
    const w = mount(WirePanel, { props: { wires: WIRES } });

    expect(knopf(w).attributes("disabled")).toBeDefined();
    expect(knopf(w).text()).toBe("KABEL WÄHLEN");
  });

  it("Klick wählt ein Kabel, Knopf sendet cut mit Index und Symbol", async () => {
    const w = mount(WirePanel, { props: { wires: WIRES } });
    await kabel(w)[2].trigger("click");

    expect(kabel(w)[2].classes()).toContain("is-selected");
    expect(knopf(w).text()).toBe("KABEL 3 KAPPEN");

    await knopf(w).trigger("click");
    expect(w.emitted("cut")).toEqual([[{ index: 2, symbol: "quadrat" }]]);
    expect(kabel(w)[2].classes()).toContain("is-cut");
  });

  it("zweiter Klick auf dasselbe Kabel hebt die Auswahl auf", async () => {
    const w = mount(WirePanel, { props: { wires: WIRES } });
    await kabel(w)[1].trigger("click");
    await kabel(w)[1].trigger("click");

    expect(knopf(w).attributes("disabled")).toBeDefined();
  });

  it("ist per Tastatur bedienbar", async () => {
    const w = mount(WirePanel, { props: { wires: WIRES } });
    await kabel(w)[0].trigger("keydown", { key: "Enter" });
    await knopf(w).trigger("click");

    expect(w.emitted("cut")).toEqual([[{ index: 0, symbol: "raute" }]]);
  });
});

describe("WirePanel – Zustände", () => {
  it.each(["checking", "defused"])("im Zustand %s ist nichts bedienbar", async (state) => {
    const w = mount(WirePanel, { props: { wires: WIRES, state } });
    await kabel(w)[0].trigger("click");
    await knopf(w).trigger("click");

    expect(w.emitted("cut")).toBeUndefined();
    expect(knopf(w).attributes("disabled")).toBeDefined();
  });

  it("nach Fehler und Rückkehr auf armed ist das Kabel wieder heil", async () => {
    const w = mount(WirePanel, { props: { wires: WIRES } });
    await kabel(w)[1].trigger("click");
    await knopf(w).trigger("click");
    await w.setProps({ state: "error" });
    expect(kabel(w)[1].classes()).toContain("is-cut");

    await w.setProps({ state: "armed" });
    expect(w.findAll(".is-cut")).toHaveLength(0);
    expect(knopf(w).text()).toBe("KABEL WÄHLEN");
  });

  it("entschärft: Titel und Knopf melden Erfolg", () => {
    const w = mount(WirePanel, { props: { wires: WIRES, state: "defused" } });

    expect(w.find(".wp__title").text()).toBe("SYSTEM SICHER");
    expect(knopf(w).text()).toBe("ENTSCHÄRFT");
  });
});

describe("WirePanel – Countdown", () => {
  it("ohne seconds keine Anzeige", () => {
    const w = mount(WirePanel, { props: { wires: WIRES } });
    expect(w.find(".wp__timer").exists()).toBe(false);
  });

  it("formatiert Sekunden als MM:SS und warnt unter 30 s", () => {
    const w = mount(WirePanel, { props: { wires: WIRES, seconds: 95 } });
    expect(w.find(".wp__timer text").text()).toBe("01:35");
    expect(w.find(".wp__timer").classes()).not.toContain("is-low");
  });

  it("warnt ab 30 Sekunden und zeigt nie negative Zeit", async () => {
    const w = mount(WirePanel, { props: { wires: WIRES, seconds: 30 } });
    expect(w.find(".wp__timer").classes()).toContain("is-low");

    await w.setProps({ seconds: -4 });
    expect(w.find(".wp__timer text").text()).toBe("00:00");
  });
});
