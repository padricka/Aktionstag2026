import { it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import StartMenu from "../src/StartMenu.vue";

it("titel wird angezeigt", () => {
  // komponente einmal hochfahren zum testen
  const wrapper = mount(StartMenu);

  // guck ob im h1 wirklich der richtige text steht
  expect(wrapper.find("h1").text()).toBe("DRV-BOX");
});

it("spieler-button ist disabled wenn kein name eingegeben wurde", () => {
  const wrapper = mount(StartMenu);

  // der spieler-button ist .btn-primary (der erste button im DOM ist der Einstellungen-Link)
  const button = wrapper.find(".btn-primary");
  // sollte am anfang disabled sein weil noch kein name da ist
  expect(button.attributes("disabled")).toBeDefined();
});

it("spieler-button geht wenn man einen namen eingibt", async () => {
  const wrapper = mount(StartMenu);

  // name reinschreiben wie ein user das machen wuerde
  await wrapper.find("input").setValue("David");

  const button = wrapper.find(".btn-primary");
  // jetzt sollte disabled weg sein
  expect(button.attributes("disabled")).toBeUndefined();
});

it("klick auf host button schickt event mit rolle host", async () => {
  const wrapper = mount(StartMenu);

  await wrapper.find("input").setValue("David");
  // jetzt auf host klicken
  await wrapper.find(".btn-host").trigger("click");

  // schauen was die komponente rausgeschickt hat
  // die komponente emittet { name, role } — property heißt "role" (nicht "rolle")
  const event = wrapper.emitted("spiel-starten");
  expect(event[0][0].role).toBe("host");
});

it("klick auf Spieler schickt event mit rolle player und name", async () => {
  const wrapper = mount(StartMenu);

  await wrapper.find("input").setValue("Anna");
  await wrapper.find(".btn-primary").trigger("click");

  const event = wrapper.emitted("spiel-starten");
  expect(event[0][0]).toEqual({ name: "Anna", role: "player" });
});

it("Einstellungen-Link emittet open-settings", async () => {
  const wrapper = mount(StartMenu);

  await wrapper.find(".settings-link").trigger("click");

  expect(wrapper.emitted("open-settings")).toHaveLength(1);
});
