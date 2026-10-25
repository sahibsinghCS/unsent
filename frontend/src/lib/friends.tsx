/**
 * "Add your own friend": the friend the user made and the form values they typed, kept in React
 * state ONLY (no localStorage/sessionStorage), so a reload forgets them, like the server, which deletes
 * custom friends after 60 minutes of inactivity.
 */
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import type { ScenarioSummary } from '../api/models';

export interface FriendDraft {
  name: string;
  age: number;
  guardedness: 'open' | 'guarded';
  personality: string;
  situation: string;
  sample_texts: string[];
}

/** A custom friend as returned by POST /api/friends (a ScenarioSummary with custom: true). */
export type CustomFriend = ScenarioSummary & { custom?: boolean; /** set up from screenshots of a real friend's chat */ realFriend?: boolean };

export const EMPTY_DRAFT: FriendDraft = { name: '', age: 16, guardedness: 'guarded', personality: '', situation: '', sample_texts: [''] };

/** Limits from the API spec (also enforced by the server). */
export const LIMITS = { name: [1, 24], age: [13, 19], personality: 300, situation: [10, 400], sampleText: 160, sampleCount: 5 } as const;

export const isCustomId = (id: string) => id.startsWith('custom-');

interface FriendsState {
  draft: FriendDraft;
  setDraft: (draft: FriendDraft) => void;
  friend: CustomFriend | null;
  setFriend: (friend: CustomFriend | null) => void;
  /** True while the form holds a draft that came from screenshots of a real friend's chat. */
  fromRealFriend: boolean;
  setFromRealFriend: (value: boolean) => void;
}

const FriendsContext = createContext<FriendsState | null>(null);

export function FriendsProvider({ children }: { children: ReactNode }) {
  const [draft, setDraft] = useState<FriendDraft>(EMPTY_DRAFT);
  const [friend, setFriend] = useState<CustomFriend | null>(null);
  const [fromRealFriend, setFromRealFriend] = useState(false);
  const value = useMemo(() => ({ draft, setDraft, friend, setFriend, fromRealFriend, setFromRealFriend }), [draft, friend, fromRealFriend]);
  return <FriendsContext.Provider value={value}>{children}</FriendsContext.Provider>;
}

export function useFriends(): FriendsState {
  const state = useContext(FriendsContext);
  if (!state) throw new Error('useFriends must be used inside <FriendsProvider>');
  return state;
}

/** Client-side checks that mirror the server's limits (the server stays the authority). */
export function draftProblems(d: FriendDraft): Partial<Record<'name' | 'age' | 'situation', true>> {
  const problems: Partial<Record<'name' | 'age' | 'situation', true>> = {};
  if (d.name.trim().length < LIMITS.name[0] || d.name.length > LIMITS.name[1]) problems.name = true;
  if (!(d.age >= LIMITS.age[0] && d.age <= LIMITS.age[1])) problems.age = true;
  if (d.situation.trim().length < LIMITS.situation[0] || d.situation.length > LIMITS.situation[1]) problems.situation = true;
  return problems;
}
