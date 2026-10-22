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
