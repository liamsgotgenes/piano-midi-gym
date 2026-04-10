# MIDI Reaction Trainer Design Doc

## 1. Overview

Build a browser-based training app that improves note and chord muscle memory by showing the player a random target and timing how quickly they play the correct answer on a connected MIDI keyboard.

The app must support:
- Single-note drills
- Chord drills
- Filtering by one key or multiple keys
- Reaction-time tracking
- Accuracy tracking
- MIDI keyboard input

This app is designed to answer the question: "If I see a note or chord name, how fast can I find and play it correctly?"

---

## 2. Goals

### Primary goals
- Help users build faster note and chord recall on a MIDI keyboard
- Measure reaction time from prompt display to correct input
- Allow exercises to be constrained to one key or a selected set of keys
- Provide simple statistics that show improvement over time

### Secondary goals
- Make setup very fast: connect MIDI keyboard, choose settings, start training
- Support short focused drills and longer practice sessions
- Keep the UI simple enough to use daily

### Non-goals for v1
- Full ear training
- Microphone/audio note detection
- Sight-reading with staff notation
- Advanced jazz chord spelling with every extension/inversion
- Multiplayer or online leaderboards

---

## 3. Core User Stories

### Beginner note drill
As a user, I want to practice random notes within C major so I can build muscle memory for that key first.

### Multi-key note drill
As a user, I want to select multiple keys, such as C, G, and F, so the app only generates targets from those keys.

### Chord drill
As a user, I want to practice major and minor triads inside a selected key so I can quickly find common chord shapes.

### Performance tracking
As a user, I want to see my average reaction time and accuracy so I know whether I am improving.

### Focused weak-spot practice
As a user, I want to review which notes or chords are slowest for me so I can target weak areas.

---

## 4. Product Scope

## 4.1 Exercise Types

### Single Note Mode
The app displays one target note at a time, for example:
- C
- F#
- Bb

The user must press the matching key on their MIDI keyboard.

Optional submodes:
- Note name only
- Note name plus octave, such as C4
- White keys only
- Accidentals included

### Chord Mode
The app displays one target chord at a time, for example:
- C major
- A minor
- G diminished

The user must play the correct set of notes.

Recommended v1 chord set:
- Major triads
- Minor triads
- Diminished triads

Possible later expansion:
- Augmented triads
- Seventh chords
- Suspended chords
- Inversions

---

## 4.2 Key Filtering

This is a core requirement.

The user must be able to choose:
- A single key, such as C major
- Multiple keys, such as C major + G major + D major
- All keys

The exercise generator should only create notes or chords that belong to the selected key set.

### Example behavior
If the user selects only C major:
- Single-note mode should generate only notes from C major, unless the user explicitly enables chromatic notes
- Chord mode should generate only diatonic chords from C major

If the user selects C major and G major:
- The generator builds the allowed note/chord pool from the union of those keys
- Any displayed target must belong to at least one selected key

### Key model recommendation
Represent each key as:
- Root note
- Mode type, starting with Major and Minor in v1
- Derived scale notes
- Derived allowed diatonic chords

---

## 4.3 Timing and Scoring

### Reaction time definition
Reaction time starts when the target is shown.
Reaction time ends when the correct answer is detected.

### Accuracy definition
A trial is correct if the played MIDI input matches the expected target within the configured validation rules.

### Single-note scoring
- Correct when the MIDI note pitch class matches the target note
- Optional octave-sensitive mode for stricter validation

### Chord scoring
- Correct when the set of currently held pitch classes matches the target chord
- By default, ignore inversions in v1 unless inversion mode is turned on later

### Suggested metrics
Per session:
- Total attempts
- Correct attempts
- Accuracy percentage
- Average reaction time
- Median reaction time
- Fastest correct response
- Slowest correct response
- Best streak

Per item:
- Average response time by note
- Average response time by chord
- Error count by note/chord

---

## 5. Functional Requirements

## 5.1 MIDI Input
- App must detect available MIDI input devices
- User must be able to select a MIDI input device
- App must listen for note-on and note-off messages
- App should handle sustain pedal carefully in later versions, but v1 can ignore pedal-specific logic if needed

## 5.2 Exercise Configuration
User can configure:
- Exercise type: note or chord
- Key selection: one or many keys
- Tempo/pace mode:
  - Manual next prompt after correct answer
  - Auto-advance after delay
- Session length:
  - Number of questions
  - Timed session
- Allowed chord qualities
- Octave-sensitive vs octave-insensitive note detection
- Whether repeated targets are allowed

## 5.3 Prompt Generation
- App generates a valid target from the active allowed pool
- Target pool changes immediately when settings change
- Prompt generator should avoid showing the exact same target repeatedly unless the pool is very small

## 5.4 Input Validation
### Note mode
- Compare incoming MIDI note against expected target
- If octave-insensitive, compare pitch class only
- If octave-sensitive, compare exact MIDI note number or exact note name plus octave

### Chord mode
- Collect currently depressed notes
- Convert to normalized pitch classes
- Compare against expected chord pitch-class set
- Chord should count as correct once the required set is present, even if notes were not pressed at exactly the same millisecond

## 5.5 Results and History
- Show results at end of session
- Save local history per session
- Show trend lines over time later, but v1 can start with a simple history list

---

## 6. UX Requirements

## 6.1 Main Screens

### Home / Setup Screen
Controls for:
- MIDI device selection
- Exercise type
- Key selection
- Allowed chord types
- Session mode
- Start button

### Practice Screen
Display:
- Large current target
- Running timer for current prompt
- Current streak
- Progress in session
- Optional visual indicator of currently pressed MIDI notes

### Results Screen
Display:
- Accuracy
- Average reaction time
- Fastest response
- Slowest response
- Missed items
- Slowest items
- Restart / modify settings

---

## 6.2 Interaction Principles
- One-click start after MIDI device is connected
- Large readable note/chord prompt
- Immediate feedback on correct answer
- Feedback should feel rewarding but not distracting
- Mistakes should be obvious but not punishing

### Feedback options
Correct:
- Green confirmation
- Short sound effect optional
- Auto-next after short delay

Incorrect:
- Red flash or subtle warning
- Keep timer running until correct answer, or optionally count as miss and move on

---

## 7. Music Theory Rules for Generation

## 7.1 Notes
For note mode, targets are drawn from an allowed note pool.

Possible pool strategies:
- Scale-only notes in selected keys
- Full chromatic notes, but weighted toward selected keys
- User-defined subsets later

For v1, use scale-only notes by default when keys are selected.

## 7.2 Chords
For chord mode, generate chords from the selected keys.

### Example for C major
Diatonic triads:
- C major
- D minor
- E minor
- F major
- G major
- A minor
- B diminished

### Multiple-key behavior
If multiple keys are selected, create a combined allowed chord pool.

Need a clear deduplication policy. Example:
- A minor may appear in both C major and G major
- It should only exist once in the pool unless weighted by key occurrence

### Recommendation for v1
Use deduplicated pools by chord spelling, not weighted by how many selected keys contain the chord.

---

## 8. Technical Architecture

## 8.1 Platform Choice
Recommended v1 platform: web app

Why:
- Easy MIDI keyboard access in supported browsers
- No install friction
- Easy to iterate and deploy
- Good fit for a personal training tool

Alternative later:
- Electron desktop app if browser MIDI support becomes limiting

## 8.2 Frontend Stack
Recommended:
- React or Next.js frontend
- TypeScript
- Web MIDI API for MIDI input
- Local storage or IndexedDB for session history
- Optional Tone.js for UI sounds and metronome-style feedback

## 8.3 Core Modules

### MIDI Module
Responsibilities:
- Enumerate devices
- Request MIDI access
- Subscribe to device events
- Parse note-on/note-off messages
- Normalize incoming MIDI data

### Theory Engine
Responsibilities:
- Build scales for selected keys
- Build allowed note pools
- Build allowed chord pools
- Normalize enharmonic spelling rules

### Exercise Engine
Responsibilities:
- Generate next target
- Start/stop timers
- Validate input
- Record attempt results
- Advance session state

### Scoring Module
Responsibilities:
- Compute session stats
- Compute per-target stats
- Store history

### UI Layer
Responsibilities:
- Render setup, practice, results
- Show live pressed notes
- Show current timer and feedback

---

## 9. Data Model

## 9.1 Key
```ts
type KeyMode = "major" | "minor";

type KeySpec = {
  root: string;      // e.g. "C", "F#", "Bb"
  mode: KeyMode;
};
```

## 9.2 Note Target
```ts
type NoteTarget = {
  type: "note";
  label: string;     // e.g. "C", "F#", "Bb"
  pitchClass: number; // 0-11
  octave?: number;
};
```

## 9.3 Chord Target
```ts
type ChordQuality = "maj" | "min" | "dim";

type ChordTarget = {
  type: "chord";
  root: string;
  quality: ChordQuality;
  label: string;            // e.g. "C major"
  pitchClasses: number[];   // normalized sorted set
};
```

## 9.4 Session Config
```ts
type SessionConfig = {
  mode: "note" | "chord";
  selectedKeys: KeySpec[];
  octaveSensitive: boolean;
  chordQualities: ChordQuality[];
  questionCount?: number;
  timedDurationSec?: number;
  allowRepeats: boolean;
};
```

## 9.5 Attempt Record
```ts
type AttemptRecord = {
  targetLabel: string;
  startedAt: number;
  completedAt?: number;
  reactionMs?: number;
  correct: boolean;
  incorrectInputs: number;
};
```

---

## 10. Validation Logic

## 10.1 MIDI Parsing
Typical messages of interest:
- Note on
- Note off

The parser should maintain a set of currently pressed notes.

## 10.2 Note Validation
### Octave-insensitive mode
Correct when:
- incomingMidiNote % 12 === target.pitchClass

### Octave-sensitive mode
Correct when:
- incomingMidiNote equals exact target MIDI note

## 10.3 Chord Validation
Maintain active pressed notes as MIDI note numbers.
Convert active notes to pitch classes.
Normalize to a set.
Correct when:
- active pitch-class set equals target pitch-class set

### Recommendation for v1
Ignore voicing and inversion.
Only require correct pitch-class membership.

This makes the exercise better for chord recall and less frustrating.

---

## 11. Key Selection Behavior

This is one of the most important product decisions.

## 11.1 UI for Key Selection
Recommended UI:
- Multi-select checklist of keys
- Separate toggle for major/minor
- Quick presets:
  - C major only
  - Common sharp keys
  - Common flat keys
  - All major keys
  - All minor keys

## 11.2 Generation Semantics
### Single key selected
Use only that key's note/chord pool.

### Multiple keys selected
Use the union of all selected pools.

### Important question: display context
If multiple keys are selected and target A minor is shown, should the user also see which key context it came from?

Recommendation for v1:
- No, not unless a later “functional harmony” mode is added
- Treat the target as an abstract note/chord recognition drill

---

## 12. Edge Cases
- MIDI keyboard disconnected during session
- Browser does not support MIDI
- No MIDI permission granted
- Same note retriggered rapidly
- User holds extra notes while playing a chord
- Sustain pedal causes stale active notes
- Enharmonic spelling confusion, such as A# vs Bb

### Recommendation for v1 spelling
Use a consistent display system with preference by key signature where possible, but do not overcomplicate early versions.

---

## 13. MVP Definition

A successful MVP should include:
- Browser app
- MIDI input selection
- Single-note mode
- Chord mode with major/minor/diminished triads
- Key multi-select
- Prompt generation constrained by selected keys
- Reaction timing
- Accuracy tracking
- End-of-session summary
- Basic local session history

If all of the above works reliably, the product already delivers the main value.

---

## 14. Suggested Future Enhancements
- Staff notation mode
- Inversion-specific chord drills
- Seventh chords and suspended chords
- Left-hand and right-hand specific exercises
- Weak-item adaptive training
- Daily streaks and long-term analytics
- Sound playback of target before/after answer
- Game modes with score multipliers
- Custom note subsets and custom chord libraries
- Teacher mode / lesson packs
- Exportable practice history
- Desktop app version

---

## 15. Recommended Build Plan

### Phase 1: Foundations
- Set up frontend app
- Connect Web MIDI
- Show currently pressed notes
- Build theory helpers for keys, scales, and chords

### Phase 2: Single Note Mode
- Generate note targets from selected keys
- Validate note input
- Track reaction times and accuracy
- Build results screen

### Phase 3: Chord Mode
- Generate diatonic triads from selected keys
- Track active notes and validate chord sets
- Add chord quality filters

### Phase 4: Persistence and polish
- Save session history locally
- Improve feedback and UX
- Add stats by note/chord

---

## 16. Open Product Decisions
These should be finalized before implementation starts:

1. In note mode, should targets include octave by default or not?
2. In chord mode, should inversions count as correct in v1?
3. Should wrong notes end a trial immediately, or should the timer continue until the right answer is found?
4. For multiple selected keys, should repeated shared chords be weighted more heavily or deduplicated?
5. Should note mode default to scale-only notes or full chromatic notes?
6. How should enharmonic spellings be displayed for mixed-key practice?

Recommended defaults:
- No octave by default
- Inversions accepted in v1
- Wrong notes do not end trial; keep timing until correct answer
- Deduplicate shared chords
- Scale-only by default
- Use key-aware spelling where practical

---

## 17. Final Recommendation

Build this as a browser-based MIDI app first.

That approach gives the lowest friction and is more than capable for the core experience. The most important design choice is to keep v1 focused on fast, clean drills:
- random prompt
- immediate MIDI validation
- reaction timing
- key-based filtering
- useful session stats

If the app feels instant and simple, it will actually get used, which matters more than packing in too many theory features too early.

