import { fireEvent, screen } from '@testing-library/react';
import { Layout } from '../components/Layout';
import { CheckInModal, CrisisModal } from '../components/Safety';
import { renderApp } from './render';

describe('crisis pause', () => {
  it("can't be dismissed until the resources are acknowledged", () => {
    const onAck = vi.fn();
    renderApp(<CrisisModal open onAcknowledge={onAck} />);
    const back = screen.getByRole('button', { name: 'Return to practice' });
    expect(back).toBeDisabled();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Close' })).not.toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("I've seen these resources"));
    expect(back).toBeEnabled();
    fireEvent.click(back);
    expect(onAck).toHaveBeenCalledOnce();
  });

  it('offers call and text 988 links', () => {
    renderApp(<CrisisModal open onAcknowledge={() => undefined} />);
    expect(screen.getByRole('link', { name: /Call 988/ })).toHaveAttribute('href', 'tel:988');
    expect(screen.getByRole('link', { name: /Text 988/ })).toHaveAttribute('href', 'sms:988');
  });
});

describe('after-session check-in', () => {
  it('shows resources only when the user feels low', () => {
    renderApp(<CheckInModal open onClose={() => undefined} />);
    fireEvent.click(screen.getByRole('radio', { name: /Good/ }));
    expect(screen.queryByTestId('checkin-resources')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('radio', { name: /Not great/ }));
    expect(screen.getByTestId('checkin-resources')).toHaveTextContent('988');
  });
});

describe('app shell', () => {
  it('always shows "I need help now" linking to Real mode, and the safety footer', () => {
    renderApp(<Layout />);
    expect(screen.getByTestId('help-now')).toHaveAttribute('href', '/real');
    expect(screen.getByRole('contentinfo')).toHaveTextContent(/988/);
  });
});

describe('X-ray voice chip (contracts 1.1)', () => {
  it('says who wrote the friend\'s words', async () => {
    const { VoiceChip } = await import('../components/Xray');
    renderApp(
      <>
        <VoiceChip voice="llm" />
        <VoiceChip voice="bank" />
        <VoiceChip voice="fallback" />
      </>,
    );
    expect(screen.getAllByTestId('voice-chip').map((c) => c.textContent)).toEqual(['AI, verified ✓', 'Reviewed line', 'Fallback']);
  });
  it('renders nothing for old payloads without a voice', async () => {
    const { VoiceChip } = await import('../components/Xray');
    renderApp(<VoiceChip voice={null} />);
    expect(screen.queryByTestId('voice-chip')).not.toBeInTheDocument();
  });
});

describe('X-ray clamp note', () => {
  it('explains a change clamped at 0', async () => {
    const { TrustMath } = await import('../components/Xray');
    const state = (trust: number, last_delta: number, last_breakdown: Record<string, number> = {}) => ({ trust, level: 0, turn: 1, status: 'active' as const, last_delta, last_breakdown, flags: { asked_directly_ever: false, promised_secrecy: false, referral_turns: [] } });
    const node = { id: 'u', parent_id: 'f', role: 'user' as const, bubbles: ['lol'], seen_no_reply: false, events: { dismissed: 0.9 }, state_after: state(0, -22, { dismissed: -20, decay: -2 }) };
    renderApp(<TrustMath node={node} before={state(5, 0)} />);
    expect(screen.getByTestId('clamp-note')).toHaveTextContent("(trust can't go below 0, actual change −5)");
    expect(screen.getByText('time')).toBeInTheDocument();
  });
});
