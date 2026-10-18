import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import VaultDoor from "../src/components/VaultDoor.vue";

const raeder = (w) => w.findAll('[role="spinbutton"]');
const werte = (w) => raeder(w).map((r) => r.attributes("aria-valuenow"));

describe("VaultDoor – Beamer (display)", () => {
  it("zeigt unbekannte Ziffern ohne Wert und zählt gefundene", () => {
    const w = mount(VaultDoor, { props: { mode: "display", digits: [4, null, null] } });

    expect(werte(w)).toEqual(["4", undefined, undefined]);
    expect(w.findAll(".vd-drum--unknown")).toHaveLength(2);
    expect(w.find(".vd-panel__status").text()).toBe("GESPERRT · 1/3");
  });

  it("hat keine Bedienelemente", () => {
    const w = mount(VaultDoor, { props: { mode: "display" } });

    expect(w.find(".vd-panel__unlock").exists()).toBe(false);
    expect(w.findAll(".vd-drum__btn")).toHaveLength(0);
  });

  it("übernimmt neu gefundene Ziffern", async () => {
    const w = mount(VaultDoor, { props: { mode: "display", digits: [null, null, null] } });
    await w.setProps({ digits: [4, 7, null] });

    expect(werte(w)).toEqual(["4", "7", undefined]);
    expect(w.find(".vd-panel__status").text()).toBe("GESPERRT · 2/3");
  });
});

describe("VaultDoor – Leitstand (input)", () => {
  it("startet bei 000 und sendet den eingestellten Code", async () => {
    const w = mount(VaultDoor, { props: { mode: "input" } });
    expect(werte(w)).toEqual(["0", "0", "0"]);

    const [r1, r2, r3] = raeder(w);
    for (let i = 0; i < 4; i++) await r1.trigger("keydown", { key: "ArrowUp" });
    for (let i = 0; i < 3; i++) await r2.trigger("keydown", { key: "ArrowDown" });
    await r3.find(".vd-drum__btn--up").trigger("click");
    await r3.find(".vd-drum__btn--up").trigger("click");
    await w.find(".vd-panel__unlock").trigger("click");

    expect(w.emitted("unlock")).toEqual([["472"]]);
  });

  it("dreht über 9 hinaus auf 0 und unter 0 auf 9", async () => {
    const w = mount(VaultDoor, { props: { mode: "input", digits: [9, 0, 5] } });
    const [r1, r2] = raeder(w);
    await r1.trigger("keydown", { key: "ArrowUp" });
    await r2.trigger("keydown", { key: "ArrowDown" });

    expect(werte(w)).toEqual(["0", "9", "5"]);
  });

  it("Mausrad nach oben erhöht, nach unten verringert", async () => {
    const w = mount(VaultDoor, { props: { mode: "input", digits: [5, 5, 5] } });
    const [r1, r2] = raeder(w);
    await r1.trigger("wheel", { deltaY: -100 });
    await r2.trigger("wheel", { deltaY: 100 });

    expect(werte(w)).toEqual(["6", "4", "5"]);
  });

  it.each(["checking", "open"])("ist im Zustand %s gesperrt", async (state) => {
    const w = mount(VaultDoor, { props: { mode: "input", state, digits: [1, 2, 3] } });

    await raeder(w)[0].trigger("keydown", { key: "ArrowUp" });
    await w.find(".vd-panel__unlock").trigger("click");

    expect(werte(w)).toEqual(["1", "2", "3"]);
    expect(w.find(".vd-panel__unlock").attributes("disabled")).toBeDefined();
    expect(w.emitted("unlock")).toBeUndefined();
  });

  it("erlaubt nach falschem Code sofort eine neue Eingabe", async () => {
    const w = mount(VaultDoor, { props: { mode: "input", state: "error", digits: [1, 1, 6] } });
    expect(w.find(".vd-panel__window").classes()).toContain("is-error");

    await raeder(w)[2].trigger("keydown", { key: "ArrowDown" });
    await w.find(".vd-panel__unlock").trigger("click");

    expect(w.emitted("unlock")).toEqual([["115"]]);
  });
});

describe("VaultDoor – Zustände", () => {
  it.each(["locked", "checking", "open", "error"])("setzt die Klasse vault--%s", (state) => {
    const w = mount(VaultDoor, { props: { mode: "display", state } });
    expect(w.classes()).toContain(`vault--${state}`);
  });

  it("meldet den geöffneten Tresor für Screenreader", () => {
    const w = mount(VaultDoor, { props: { mode: "display", state: "open" } });
    expect(w.attributes("aria-label")).toBe("Tresor geöffnet");
  });
});
