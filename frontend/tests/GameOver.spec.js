import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import GameOver from '../src/components/GameOver.vue'

describe('GameOver.vue', () => {
  it('zeigt Niederlage bei meltdown', () => {
    const wrapper = mount(GameOver, {
      props: { result: 'meltdown', score: 12, survivedSeconds: 90 },
    })

    expect(wrapper.find('.end-status').text()).toBe('Server ausgefallen')
    expect(wrapper.find('.end-status').classes()).toContain('lose')
    expect(wrapper.find('.end-score').text()).toBe('12')
    expect(wrapper.text()).toContain('90s')
  })

  it('zeigt Sieg bei victory', () => {
    const wrapper = mount(GameOver, {
      props: { result: 'victory', score: 500, survivedSeconds: 200 },
    })

    expect(wrapper.find('.end-status').text()).toBe('Mission erfüllt')
    expect(wrapper.find('.end-status').classes()).toContain('win')
  })

  it('emittiert restart wenn Neustart geklickt wird', async () => {
    const wrapper = mount(GameOver, {
      props: { result: 'meltdown', showRestart: true },
    })

    await wrapper.find('.restart-btn').trigger('click')
    expect(wrapper.emitted('restart')).toHaveLength(1)
  })

  it('versteckt Neustart-Button ohne showRestart', () => {
    const wrapper = mount(GameOver, {
      props: { result: 'meltdown', showRestart: false },
    })
    expect(wrapper.find('.restart-btn').exists()).toBe(false)
  })
})
