/**
 * ControlDesk – Steuerpult für Aufgabe 2, Vorderseite (siehe frontend/PANELS.md).
 *
 * Diese Tests legen die Bedien-Schnittstelle fest:
 *   Drehregler   role="slider" aria-label="Ventil"  aria-valuetext = gewähltes Ventil
 *   Schieberegler role="slider" aria-label="Farbe"  aria-valuetext = gewählte Farbe
 *   Manometer    role="progressbar" aria-valuenow = step, aria-valuemax = sequenceLen
 *   Auslöser     <button aria-label="Auslösen">
 *   Wurzel       Klasse cd--<state>
 * Pfeil rechts/oben = nächste Stellung, links/unten = vorherige, an den Enden ist Anschlag.
 * Klick auf einen Regler dreht/schiebt eine Stellung weiter (am Ende wieder auf die erste).
 */
import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import ControlDesk from "../src/components/ControlDesk.vue";

const PROPS = {
  valves: ["V-31", "V-32", "V-33"],
  colors: ["ORANGE", "RED", "GREEN"],
  step: 0,
  sequenceLen: 3,
};
const ventil = (w) => w.find('[role="slider"][aria-label="Ventil"]');
const farbe = (w) => w.find('[role="slider"][aria-label="Farbe"]');
const ausloeser = (w) => w.find('button[aria-label="Auslösen"]');
const manometer = (w) => w.find('[role="progressbar"]');

describe("ControlDesk – Regler", () => {
  it("startet auf erstem Ventil und erster Farbe", () => {
    const w = mount(ControlDesk, { props: PROPS });

    expect(ventil(w).attributes("aria-valuetext")).toBe("V-31");
    expect(farbe(w).attributes("aria-valuetext")).toBe("ORANGE");
  });

  it("Pfeiltasten verstellen die Regler", async () => {
    const w = mount(ControlDesk, { props: PROPS });
    await ventil(w).trigger("keydown", { key: "ArrowRight" });
    await ventil(w).trigger("keydown", { key: "ArrowUp" });
    await farbe(w).trigger("keydown", { key: "ArrowRight" });

    expect(ventil(w).attributes("aria-valuetext")).toBe("V-33");
    expect(farbe(w).attributes("aria-valuetext")).toBe("RED");

    await ventil(w).trigger("keydown", { key: "ArrowLeft" });
    expect(ventil(w).attributes("aria-valuetext")).toBe("V-32");
  });

  it("an den Enden ist Anschlag", async () => {
    const w = mount(ControlDesk, { props: PROPS });
    await ventil(w).trigger("keydown", { key: "ArrowLeft" });
    expect(ventil(w).attributes("aria-valuetext")).toBe("V-31");

    for (let i = 0; i < 5; i++) await farbe(w).trigger("keydown", { key: "ArrowRight" });
    expect(farbe(w).attributes("aria-valuetext")).toBe("GREEN");
  });

  it("Klick dreht eine Stellung weiter und läuft am Ende auf die erste", async () => {
    const w = mount(ControlDesk, { props: PROPS });
    for (let i = 0; i < 3; i++) await ventil(w).trigger("click");
    expect(ventil(w).attributes("aria-valuetext")).toBe("V-31");

    await farbe(w).trigger("click");
    expect(farbe(w).attributes("aria-valuetext")).toBe("RED");
  });
});

describe("ControlDesk – Auslösen", () => {
  it("sendet submit als VENTIL:FARBE", async () => {
    const w = mount(ControlDesk, { props: PROPS });
    await ventil(w).trigger("keydown", { key: "ArrowRight" });
    await farbe(w).trigger("keydown", { key: "ArrowRight" });
    await ausloeser(w).trigger("click");

    expect(w.emitted("submit")).toEqual([["V-32:RED"]]);
  });

  it.each(["checking", "done"])("im Zustand %s ist alles gesperrt", async (state) => {
    const w = mount(ControlDesk, { props: { ...PROPS, state } });
    await ventil(w).trigger("keydown", { key: "ArrowRight" });
    await ausloeser(w).trigger("click");

    expect(ventil(w).attributes("aria-valuetext")).toBe("V-31");
    expect(ausloeser(w).attributes("disabled")).toBeDefined();
    expect(w.emitted("submit")).toBeUndefined();
  });

  it("nach Fehler bleiben die Regler stehen und es geht weiter", async () => {
    const w = mount(ControlDesk, { props: PROPS });
    await ventil(w).trigger("keydown", { key: "ArrowRight" });
    await w.setProps({ state: "error" });
    await w.setProps({ state: "idle" });

    expect(ventil(w).attributes("aria-valuetext")).toBe("V-32");
    await ausloeser(w).trigger("click");
    expect(w.emitted("submit")).toEqual([["V-32:ORANGE"]]);
  });
});

describe("ControlDesk – Anzeige", () => {
  it("Manometer zeigt den Fortschritt", async () => {
    const w = mount(ControlDesk, { props: { ...PROPS, step: 1 } });
    expect(manometer(w).attributes("aria-valuenow")).toBe("1");
    expect(manometer(w).attributes("aria-valuemax")).toBe("3");

    await w.setProps({ step: 2 });
    expect(manometer(w).attributes("aria-valuenow")).toBe("2");
  });

  it.each(["idle", "checking", "error", "done"])("setzt die Klasse cd--%s", (state) => {
    const w = mount(ControlDesk, { props: { ...PROPS, state } });
    expect(w.classes()).toContain(`cd--${state}`);
  });
});

describe("ControlDesk – Beschriftung", () => {
  it("Regler lassen sich umbenennen (Aufgabe 2: Rack / Löschmittel)", () => {
    const w = mount(ControlDesk, {
      props: { ...PROPS, valves: ["A-01", "B-02"], colors: ["WASSER", "CO2"], valveLabel: "Rack", colorLabel: "Löschmittel" },
    });
    expect(w.find('[role="slider"][aria-label="Rack"]').attributes("aria-valuetext")).toBe("A-01");
    expect(w.find('[role="slider"][aria-label="Löschmittel"]').attributes("aria-valuetext")).toBe("WASSER");
    expect(w.text()).toContain("RACK");
    expect(w.text()).toContain("LÖSCHMITTEL");
  });
});

describe("ControlDesk – von außen gestellt (Tutorial, feat/tutorial-loeschanlage)", () => {
  it("valveIndex und colorIndex stellen die Regler", async () => {
    const w = mount(ControlDesk, { props: { ...PROPS, valves: ["A-01", "B-01"], colors: ["WASSER", "CO2"], valveLabel: "Schrank", colorLabel: "Löschmittel" } });
    const dreh = () => w.find('[role="slider"][aria-label="Schrank"]');
    const schieber = () => w.find('[role="slider"][aria-label="Löschmittel"]');
    expect(dreh().attributes("aria-valuetext")).toBe("A-01");
    await w.setProps({ valveIndex: 1, colorIndex: 1 });
    expect(dreh().attributes("aria-valuetext")).toBe("B-01");
    expect(schieber().attributes("aria-valuetext")).toBe("CO2");
  });
});
