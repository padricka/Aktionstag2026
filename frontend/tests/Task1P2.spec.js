/**
 * Task1P2 — Code eingeben; bei falschem Server-Feedback wieder freigeben.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Task1P2 from '../src/components/tasks/task1/Task1P2.vue'

const stubs = {
  SymbolIcon: { name: 'SymbolIcon', template: '<span class="sym" />', props: ['name', 'size'] },
}

describe('Task1P2.vue', () => {
  it('sammelt Symbole und emittiert solved erst bei Ausführen', async () => {
    const wrapper = mount(Task1P2, {
      props: { codeLength: 4 },
      global: { stubs },
    })

    const keys = wrapper.findAll('.key')
    expect(keys.length).toBeGreaterThanOrEqual(4)

    for (let i = 0; i < 4; i++) {
      await keys[i].trigger('click')
    }

    expect(wrapper.find('.btn-action').attributes('disabled')).toBeUndefined()
    await wrapper.find('.btn-action').trigger('click')

    const solved = wrapper.emitted('solved')
    expect(solved).toHaveLength(1)
    expect(solved[0][0].player).toBe('P2')
    expect(solved[0][0].code).toHaveLength(4)
    expect(wrapper.find('.btn-action').text()).toContain('Prüfen')
  })

  it('gibt UI nach serverError + Nonce wieder frei', async () => {
    const wrapper = mount(Task1P2, {
      props: { codeLength: 2, serverError: '', inputResultNonce: 0 },
      global: { stubs },
    })

    const keys = wrapper.findAll('.key')
    await keys[0].trigger('click')
    await keys[1].trigger('click')
    await wrapper.find('.btn-action').trigger('click')
    expect(wrapper.find('.btn-action').text()).toContain('Prüfen')

    await wrapper.setProps({ serverError: 'Falsche Eingabe', inputResultNonce: 1 })

    expect(wrapper.find('.btn-action').text()).toBe('Ausführen')
    expect(wrapper.find('.msg-err').text()).toContain('Falsche Eingabe')
    // Eingabe geleert → Ausführen wieder disabled
    expect(wrapper.find('.btn-action').attributes('disabled')).toBeDefined()
  })
})
